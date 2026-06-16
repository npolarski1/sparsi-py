from typing import Any, Dict, Optional
from pydantic import BaseModel
from dagor import Operator, register_operator, Input, Output

@register_operator("ConstOp")
class ConstOp(Operator, BaseModel):
    value: Any = None
    result: Output = None

    def setup(self, params: Dict[str, Any]) -> None:
        if "value" in params:
            self.value = params["value"]

    async def run(self, ctx: Any) -> None:
        self.result = self.value
