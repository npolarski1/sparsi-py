import asyncio
import structlog
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel, Field
from dagor import Operator, register_operator, Input, Output, get_operator_type
from .ai_ops import AIComputeOp

logger = structlog.get_logger(__name__)

from .repair_base import ErrRepairable

@register_operator("WithRepair")
class WithRepair(Operator, BaseModel):
    """
    WithRepair: AI-driven recovery wrapper around a deterministic op.
    When the inner op raises ErrRepairable, this wrapper calls an LLM to fix the input.
    """
    inner_op_name: str = ""
    input_field: str = ""
    max_attempts: int = 3
    provider: str = "gemini"
    model: str = "gemini-3.5-flash"
    max_tokens: int = 2048
    prompt_prefix: str = ""
    prompt_suffix: str = ""

    _inner: Optional[Operator] = None
    _ai_op: Optional[AIComputeOp] = None

    def setup(self, params: Dict[str, Any]) -> None:
        self.inner_op_name = params.get("inner_op_name", "")
        self.input_field = params.get("input_field", "")
        self.max_attempts = int(params.get("max_attempts", 3))
        self.provider = params.get("provider", "gemini")
        self.model = params.get("model", "gemini-3.5-flash")
        self.max_tokens = int(params.get("max_tokens", 2048))
        self.prompt_prefix = params.get("prompt_prefix", "")
        self.prompt_suffix = params.get("prompt_suffix", "")
        
        if not self.inner_op_name:
            raise ValueError("WithRepair requires inner_op_name param")
        if not self.input_field:
            raise ValueError("WithRepair requires input_field param")
        
        op_type = get_operator_type(self.inner_op_name)
        # Pass all params to inner op as well
        self._inner = op_type(**params) if hasattr(op_type, 'model_fields') else op_type()
        self._inner.setup(params)

        # Helper AI op for repair calls
        self._ai_op = AIComputeOp(model=self.model)
        self._ai_op.setup({"model": self.model})

    async def reset(self) -> None:
        await super().reset()
        if self._inner:
            await self._inner.reset()
        if self._ai_op:
            await self._ai_op.reset()

    def get_input_fields(self) -> Dict[str, Any]:
        return self._inner.get_input_fields()

    def get_output_fields(self) -> Dict[str, Any]:
        return self._inner.get_output_fields()

    def set_input_field(self, name: str, value: Any) -> None:
        self._inner.set_input_field(name, value)

    async def run(self, ctx: Any) -> None:
        try:
            await self._inner.run(ctx)
            return
        except ErrRepairable as rep:
            logger.info("repair_triggered", vertex=self.inner_op_name, prompt=rep.prompt)
            await self._repair_loop(ctx, rep)

    async def _repair_loop(self, ctx: Any, rep: ErrRepairable) -> None:
        for attempt in range(1, self.max_attempts + 1):
            full_prompt = self.prompt_prefix + rep.prompt + self.prompt_suffix
            
            # Use AIComputeOp to perform the repair call
            self._ai_op.prompt = full_prompt
            self._ai_op.system = "You are a strict data-repair assistant. Output exactly what the user asks for, with no prose, no commentary, and no markdown fences."
            
            await self._ai_op.run(ctx)
            llm_response = self._ai_op.result
            
            logger.info("repair_attempt", attempt=attempt, tokens_in=self._ai_op.usage_input_tokens, tokens_out=self._ai_op.usage_output_tokens)

            try:
                # Update the input field with the LLM's suggested fix
                target_field = self.input_field
                
                # Check if we need to do any unmarshaling
                # We peek at the type of the current value to decide
                current_val = getattr(self._inner, target_field, None)
                
                if hasattr(current_val, "unmarshal_repair"):
                    current_val.unmarshal_repair(llm_response)
                elif isinstance(current_val, dict):
                    # Attempt to parse as JSON first
                    llm_response_clean = self._strip_code_fences(llm_response)
                    try:
                        import json
                        fixed_val = json.loads(llm_response_clean)
                        setattr(self._inner, target_field, fixed_val)
                    except json.JSONDecodeError:
                        # Try XML if it looks like XML
                        if llm_response_clean.strip().startswith("<"):
                            try:
                                import xml.etree.ElementTree as ET
                                root = ET.fromstring(llm_response_clean)
                                fixed_val = {child.tag: child.text for child in root}
                                setattr(self._inner, target_field, fixed_val)
                            except Exception:
                                raise ValueError(f"Failed to parse repair response as JSON or XML: {llm_response_clean[:100]}...")
                        else:
                            raise
                else:
                    self._inner.set_input_field(target_field, llm_response)
                
                # Re-run the inner op
                await self._inner.run(ctx)
                logger.info("repair_success", attempt=attempt)
                return 
            except ErrRepairable as next_rep:
                rep = next_rep
                rep.prompt = rep.prompt + f"\n\nYour previous response was: {llm_response}. It was still invalid. Try again."
            except Exception as e:
                logger.error("repair_fatal_error", error=str(e))
                raise e
        
        raise RuntimeError(f"WithRepair[{self.inner_op_name}] exhausted {self.max_attempts} attempts")

    def _strip_code_fences(self, s: str) -> str:
        s = s.strip()
        if s.startswith("```"):
            lines = s.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            s = "\n".join(lines).strip()
        return s
