import json
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict
from dagor import Operator, register_operator, Input, Output

@register_operator("SelectStringOp")
class SelectStringOp(Operator, BaseModel):
    cond: Input = False
    if_true: Input = ""
    if_false: Input = ""
    result: Output = ""
    async def run(self, ctx: Any) -> None:
        self.result = self.if_true if self.cond else self.if_false

@register_operator("SelectFloatOp")
@register_operator("SelectFloat64Op")
class SelectFloatOp(Operator, BaseModel):
    cond: Input = False
    if_true: Input = 0.0
    if_false: Input = 0.0
    result: Output = 0.0
    async def run(self, ctx: Any) -> None:
        self.result = float(self.if_true or 0.0) if self.cond else float(self.if_false or 0.0)

@register_operator("SelectIntOp")
class SelectIntOp(Operator, BaseModel):
    cond: Input = False
    if_true: Input = 0
    if_false: Input = 0
    result: Output = 0
    async def run(self, ctx: Any) -> None:
        self.result = int(self.if_true or 0) if self.cond else int(self.if_false or 0)

@register_operator("SelectBoolOp")
class SelectBoolOp(Operator, BaseModel):
    cond: Input = False
    if_true: Input = True
    if_false: Input = False
    result: Output = False
    async def run(self, ctx: Any) -> None:
        self.result = bool(self.if_true) if self.cond else bool(self.if_false)

@register_operator("SwitchStringOp")
class SwitchStringOp(Operator, BaseModel):
    key: Input = ""
    cases: Dict[str, str] = {}
    default: str = ""
    result: Output = ""
    def setup(self, params: Dict[str, Any]) -> None:
        raw = params.get("cases", "{}")
        if isinstance(raw, str):
            self.cases = json.loads(raw)
        else:
            self.cases = raw
        self.default = params.get("default", "")
    async def run(self, ctx: Any) -> None:
        self.result = self.cases.get(self.key or "", self.default)

@register_operator("DefaultStringOp")
class DefaultStringOp(Operator, BaseModel):
    value: Input = ""
    default: Input = ""
    result: Output = ""
    async def run(self, ctx: Any) -> None:
        self.result = self.value if (self.value is not None and self.value != "") else self.default

@register_operator("DefaultFloatOp")
@register_operator("DefaultFloat64Op")
class DefaultFloatOp(Operator, BaseModel):
    value: Input = None
    default: Input = 0.0
    result: Output = 0.0
    async def run(self, ctx: Any) -> None:
        self.result = float(self.value) if self.value is not None else float(self.default)

@register_operator("DefaultIntOp")
class DefaultIntOp(Operator, BaseModel):
    value: Input = None
    default: Input = 0
    result: Output = 0
    async def run(self, ctx: Any) -> None:
        self.result = int(self.value) if self.value is not None else int(self.default)
