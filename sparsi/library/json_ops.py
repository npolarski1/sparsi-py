import json
from typing import Any, Dict, Optional, List
from pydantic import BaseModel
from dagor import Operator, register_operator, Input, Output

from .repair import ErrRepairable

@register_operator("JsonExtractOp")
@register_operator("JSONExtractOp")
class JsonExtractOp(Operator, BaseModel):
    json_str: Input = ""
    path: Input = "" # Can be string path or wired
    result: Output = None

    def setup(self, params: Dict[str, Any]) -> None:
        if "path" in params:
            self.path = params["path"]

    async def run(self, ctx: Any) -> None:
        if not self.json_str or not self.path:
            return
        
        try:
            data = json.loads(self.json_str) if isinstance(self.json_str, str) else self.json_str
            
            # Nested path resolution: "meals.0.strMeal"
            parts = str(self.path).split(".")
            val = data
            for p in parts:
                if isinstance(val, list):
                    try:
                        val = val[int(p)]
                    except (ValueError, IndexError):
                        val = None
                        break
                elif isinstance(val, dict):
                    val = val.get(p)
                else:
                    val = None
                    break
            self.result = val
        except Exception:
            self.result = None

@register_operator("JsonParseOp")
class JsonParseOp(Operator, BaseModel):
    json_str: Input = ""
    result: Output = None

    def setup(self, params: Dict[str, Any]) -> None:
        pass

    async def run(self, ctx: Any) -> None:
        if not self.json_str:
            return
        try:
            self.result = json.loads(self.json_str)
        except json.JSONDecodeError as e:
            raise ErrRepairable(f"Invalid JSON string: {self.json_str}. Error: {str(e)}", cause=e)
