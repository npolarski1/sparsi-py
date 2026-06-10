from typing import Any, Dict, Optional
from pydantic import BaseModel
from dagor import Operator, register_operator, Input, Output

@register_operator("BoolAndOp")
class BoolAndOp(Operator, BaseModel):
    a: Input = False
    b: Input = False
    result: Output = False

    def setup(self, params: Dict[str, Any]) -> None:
        pass

    async def run(self, ctx: Any) -> None:
        self.result = bool(self.a) and bool(self.b)

@register_operator("BoolOrOp")
class BoolOrOp(Operator, BaseModel):
    a: Input = False
    b: Input = False
    result: Output = False

    def setup(self, params: Dict[str, Any]) -> None:
        pass

    async def run(self, ctx: Any) -> None:
        self.result = bool(self.a) or bool(self.b)

@register_operator("BoolNotOp")
class BoolNotOp(Operator, BaseModel):
    val: Input = False
    result: Output = True

    def setup(self, params: Dict[str, Any]) -> None:
        pass

    async def run(self, ctx: Any) -> None:
        self.result = not bool(self.val)
