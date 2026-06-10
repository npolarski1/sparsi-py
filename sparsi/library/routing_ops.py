import os
import json
import asyncio
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from dagor import Operator, register_operator, Input, Output
from anthropic import AsyncAnthropic
from google import genai
from google.genai import types

@register_operator("IfStringEqOp")
class IfStringEqOp(Operator, BaseModel):
    a: Input = ""
    b: Input = ""
    match: Output = False

    def setup(self, params: Dict[str, Any]) -> None:
        pass

    async def run(self, ctx: Any) -> None:
        self.match = self.a == self.b

@register_operator("ModeSelectOp")
class ModeSelectOp(Operator, BaseModel):
    input: Input = ""
    result: Output = ""
    
    categories: List[str] = []
    max_retries: int = 3
    provider: str = "gemini"
    model: str = "gemini-3.5-flash"

    def setup(self, params: Dict[str, Any]) -> None:
        raw_cats = params.get("categories", "")
        if raw_cats:
            self.categories = [c.strip() for c in raw_cats.split(",") if c.strip()]
        
        self.max_retries = int(params.get("max_retries", self.max_retries))
        self.provider = params.get("provider", self.provider)
        self.model = params.get("model", self.model)

    async def run(self, ctx: Any) -> None:
        if not self.categories:
            raise ValueError("ModeSelectOp: 'categories' param is required")
        
        cat_list = ", ".join(self.categories)
        base_prompt = f"Classify the following input as exactly one of these categories: {cat_list}.\nRespond with only the category name — no other text.\nInput: {self.input}"
        
        system_text = "Respond with only the requested value. No explanation, no punctuation, no formatting."
        
        cat_set = set(self.categories)
        prompt = base_prompt
        
        for attempt in range(self.max_retries + 1):
            try:
                if self.provider == "claude" or "claude" in self.model:
                    res_text = await self._call_anthropic(system_text, prompt)
                else:
                    res_text = await self._call_gemini(system_text, prompt)
                
                result = res_text.strip()
                if result in cat_set:
                    self.result = result
                    return
                
                # If we got here, it's an invalid category
                prompt = base_prompt + f"\n\nPrevious result '{result}' was invalid — must be exactly one of: {cat_list}."
            except Exception as e:
                if attempt == self.max_retries:
                    raise e
                await asyncio.sleep(0.5 * (2 ** attempt)) # Basic exponential backoff

        raise ValueError(f"ModeSelectOp: all {self.max_retries + 1} attempts failed")

    async def _call_anthropic(self, system: str, prompt: str) -> str:
        client = AsyncAnthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        response = await client.messages.create(
            model=self.model,
            max_tokens=64,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    async def _call_gemini(self, system: str, prompt: str) -> str:
        client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
        config = types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=64,
        )
        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config,
        )
        return response.text
