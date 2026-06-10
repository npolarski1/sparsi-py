import os
import aiofiles
import httpx
from typing import Any, Dict, Optional
from pydantic import BaseModel
from dagor import Operator, register_operator, Input, Output

@register_operator("FileReadOp")
class FileReadOp(Operator, BaseModel):
    path: Input = ""
    result: Output = ""

    def setup(self, params: Dict[str, Any]) -> None:
        pass

    async def run(self, ctx: Any) -> None:
        if not self.path or not os.path.exists(self.path):
            return
        
        try:
            async with aiofiles.open(self.path, mode='r', encoding='utf-8') as f:
                self.result = await f.read()
        except Exception:
            self.result = ""

@register_operator("HTTPGetOp")
class HTTPGetOp(Operator, BaseModel):
    url: Input = ""
    body: Output = ""
    status_code: Output = 0

    async def run(self, ctx: Any) -> None:
        if not self.url:
            return
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(self.url)
                self.body = resp.text
                self.status_code = resp.status_code
        except Exception:
            self.body = ""
            self.status_code = 0

@register_operator("EnvOp")
class EnvOp(Operator, BaseModel):
    name: Input = ""
    value: Output = ""
    async def run(self, ctx: Any) -> None:
        self.value = os.environ.get(self.name or "", "")
