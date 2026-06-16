import os
import asyncio
import structlog
import re
import json
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
from dagor import Operator, register_operator, Input, Output, get_run_id
from anthropic import AsyncAnthropic
from google import genai
from google.genai import types

logger = structlog.get_logger(__name__)

from .repair_base import ErrRepairable

@register_operator("AIComputeOp")
@register_operator("AIComputeStringToStringOp")
class AIComputeOp(Operator, BaseModel):
    prompt: Input = ""
    system: Input = ""
    model: str = "gemini-3.5-flash" # default model
    result: Output = ""
    usage_input_tokens: Output = 0
    usage_output_tokens: Output = 0

    def setup(self, params: Dict[str, Any]) -> None:
        # Support "operation" param from Go version
        if "operation" in params:
            self.system = params["operation"]
        self.model = params.get("model", self.model)

    async def run(self, ctx: Any) -> None:
        run_id = get_run_id()
        logger.debug("AIComputeOp.run", run_id=run_id, model=self.model)
        
        if "claude" in self.model:
            await self._run_anthropic()
        elif "gemini" in self.model:
            await self._run_gemini()
        else:
            raise ValueError(f"Unsupported model: {self.model}")
        
        logger.debug("AIComputeOp.done", run_id=run_id, input_tokens=self.usage_input_tokens, output_tokens=self.usage_output_tokens)

    async def _run_anthropic(self):
        client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        messages = [{"role": "user", "content": self.prompt}]
        
        kwargs = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": messages,
        }
        if self.system:
            kwargs["system"] = self.system
            
        response = await client.messages.create(**kwargs)
        self.result = response.content[0].text
        self.usage_input_tokens = response.usage.input_tokens
        self.usage_output_tokens = response.usage.output_tokens

    async def _run_gemini(self):
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Gemini requires either GEMINI_API_KEY or GOOGLE_API_KEY environment variable")
            
        client = genai.Client(api_key=api_key)
        config = types.GenerateContentConfig(
            system_instruction=self.system if self.system else None,
        )
        # Using sync client for now as per previous implementation but wrapping in executor if needed
        # google-genai 1.0.0+ has native sync/async.
        response = client.models.generate_content(
            model=self.model,
            contents=self.prompt,
            config=config,
        )
        self.result = response.text
        if response.usage_metadata:
            self.usage_input_tokens = response.usage_metadata.prompt_token_count
            self.usage_output_tokens = response.usage_metadata.candidates_token_count

@register_operator("AIBoolOp")
class AIBoolOp(Operator, BaseModel):
    input: Input = ""
    predicate: str = ""
    result: Output = False
    model: str = "gemini-3.5-flash"

    def setup(self, params: Dict[str, Any]) -> None:
        self.predicate = params.get("predicate", "")
        self.model = params.get("model", self.model)

    async def run(self, ctx: Any) -> None:
        prompt = f"Answer the following question about the text with only 'true' or 'false'.\nQuestion: {self.predicate}\nText: {self.input}"
        system = "Respond with only 'true' or 'false'."
        
        # Re-use logic from AIComputeOp for simplicity or call it
        ai = AIComputeOp(model=self.model, prompt=prompt, system=system)
        await ai.run(ctx)
        
        raw = ai.result.strip().lower()
        if "true" in raw:
            self.result = True
        elif "false" in raw:
            self.result = False
        else:
            self.result = "true" in raw

@register_operator("AIScoreOp")
class AIScoreOp(Operator, BaseModel):
    input: Input = ""
    criterion: str = ""
    result: Output = 0.0
    model: str = "gemini-3.5-flash"

    def setup(self, params: Dict[str, Any]) -> None:
        self.criterion = params.get("criterion", "")
        self.model = params.get("model", self.model)

    async def run(self, ctx: Any) -> None:
        prompt = f"Score the following text for {self.criterion} on a scale from 0.0 to 1.0.\nRespond with only the numeric score. No explanation.\nText: {self.input}"
        system = "Respond with only a decimal number between 0.0 and 1.0. No other text."
        
        ai = AIComputeOp(model=self.model, prompt=prompt, system=system)
        await ai.run(ctx)
        
        try:
            match = re.search(r"(\d+\.\d+|\d+)", ai.result)
            self.result = float(match.group(1)) if match else 0.0
        except:
            self.result = 0.0

@register_operator("AIClassifyMultiLabelOp")
class AIClassifyMultiLabelOp(Operator, BaseModel):
    input: Input = ""
    categories: Any = [] # Use Any to allow string from params before setup() splits it
    result: Output = []
    model: str = "gemini-3.5-flash"

    def setup(self, params: Dict[str, Any]) -> None:
        raw = params.get("categories", [])
        if isinstance(raw, str):
            self.categories = [c.strip() for c in raw.split(",") if c.strip()]
        else:
            self.categories = raw
        self.model = params.get("model", self.model)

    async def run(self, ctx: Any) -> None:
        cat_list = ", ".join(self.categories)
        prompt = f"Classify the following input into zero or more of these categories: {cat_list}.\nRespond with matching categories as a comma-separated list. If none match, respond with an empty line.\nInput: {self.input}"
        system = "Respond with only the requested value. No explanation, no punctuation beyond commas, no formatting."
        
        ai = AIComputeOp(model=self.model, prompt=prompt, system=system)
        await ai.run(ctx)
        
        self.result = [s.strip() for s in ai.result.split(",") if s.strip() in self.categories]

@register_operator("AIExtractStringSliceOp")
class AIExtractStringSliceOp(Operator, BaseModel):
    input: Input = ""
    operation: str = ""
    result: Output = []
    model: str = "gemini-3.5-flash"

    def setup(self, params: Dict[str, Any]) -> None:
        self.operation = params.get("operation", "")
        self.model = params.get("model", self.model)

    async def run(self, ctx: Any) -> None:
        prompt = f"Extract the following from the text as a list: {self.operation}\n\nText: {self.input}"
        system = "Respond with a comma-separated list. One item per entry. No other text."
        
        ai = AIComputeOp(model=self.model, prompt=prompt, system=system)
        await ai.run(ctx)
        
        self.result = [s.strip() for s in ai.result.split(",") if s.strip()]

@register_operator("AIParseNumberOp")
class AIParseNumberOp(Operator, BaseModel):
    input: Input = ""
    operation: str = ""
    result: Output = 0.0
    model: str = "gemini-3.5-flash"

    def setup(self, params: Dict[str, Any]) -> None:
        self.operation = params.get("operation", "")
        self.model = params.get("model", self.model)

    async def run(self, ctx: Any) -> None:
        prompt = f"Extract the number from the text as requested: {self.operation}\n\nText: {self.input}"
        system = "Respond with ONLY the number. No units, no prose."
        
        ai = AIComputeOp(model=self.model, prompt=prompt, system=system)
        await ai.run(ctx)
        
        match = re.search(r"(\d+\.\d+|\d+)", ai.result)
        if not match:
            raise ErrRepairable(f"Could not find a number in LLM response: {ai.result}")
        self.result = float(match.group(1))

@register_operator("AIExtractMapOp")
class AIExtractMapOp(Operator, BaseModel):
    input: Input = ""
    operation: str = ""
    result: Output = {}
    model: str = "gemini-3.5-flash"

    def setup(self, params: Dict[str, Any]) -> None:
        self.operation = params.get("operation", "")
        self.model = params.get("model", self.model)

    async def run(self, ctx: Any) -> None:
        prompt = f"Extract the following key-value pairs from the text: {self.operation}\n\nText: {self.input}"
        system = "Respond with a JSON object containing the extracted fields. No other text."
        
        ai = AIComputeOp(model=self.model, prompt=prompt, system=system)
        await ai.run(ctx)
        
        try:
            self.result = json.loads(ai.result)
        except json.JSONDecodeError as e:
            raise ErrRepairable(f"Invalid JSON from LLM: {ai.result}. Error: {str(e)}", cause=e)

@register_operator("AIBestMatchOp")
class AIBestMatchOp(Operator, BaseModel):
    query: Input = ""
    candidates: Input = []
    result: Output = 0
    model: str = "gemini-3.5-flash"

    async def run(self, ctx: Any) -> None:
        if not self.candidates:
            self.result = -1
            return
            
        cand_text = "\n".join(f"{i}. {c}" for i, c in enumerate(self.candidates))
        prompt = f"Given the query, return the 0-based index of the best matching candidate.\nQuery: {self.query}\nCandidates:\n{cand_text}"
        system = "Respond with only the integer index."
        
        ai = AIComputeOp(model=self.model, prompt=prompt, system=system)
        await ai.run(ctx)
        
        match = re.search(r"(\d+)", ai.result)
        self.result = int(match.group(1)) if match else 0

@register_operator("AIRerankOp")
class AIRerankOp(Operator, BaseModel):
    query: Input = ""
    candidates: Input = []
    result: Output = []
    model: str = "gemini-3.5-flash"

    async def run(self, ctx: Any) -> None:
        if not self.candidates:
            self.result = []
            return
            
        cand_text = "\n".join(f"{i}. {c}" for i, c in enumerate(self.candidates))
        prompt = f"Rerank the following candidates by relevance to the query, best first.\nQuery: {self.query}\nCandidates:\n{cand_text}"
        system = "Respond with only the 0-based indices as a comma-separated list."
        
        ai = AIComputeOp(model=self.model, prompt=prompt, system=system)
        await ai.run(ctx)
        
        try:
            self.result = [int(s.strip()) for s in ai.result.split(",") if s.strip().isdigit()]
        except:
            self.result = list(range(len(self.candidates)))

@register_operator("AISummarizeOp")
class AISummarizeOp(Operator, BaseModel):
    input: Input = None
    operation: str = ""
    result: Output = ""
    model: str = "gemini-3.5-flash"

    def setup(self, params: Dict[str, Any]) -> None:
        self.operation = params.get("operation", "")
        self.model = params.get("model", self.model)

    async def run(self, ctx: Any) -> None:
        text = self.input
        if isinstance(self.input, list):
            text = "\n".join(f"- {s}" for s in self.input)
            
        prompt = f"Summarize the following as requested: {self.operation}\n\nText:\n{text}"
        
        ai = AIComputeOp(model=self.model, prompt=prompt)
        await ai.run(ctx)
        self.result = ai.result
