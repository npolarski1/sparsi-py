import math
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel
from dagor import Operator, register_operator, Input, Output

@register_operator("SliceLenOp")
class SliceLenOp(Operator, BaseModel):
    input: Input = []
    result: Output = 0
    async def run(self, ctx: Any) -> None:
        self.result = len(self.input or [])

@register_operator("SliceAtOp")
class SliceAtOp(Operator, BaseModel):
    input: Input = []
    index: Input = 0
    result: Output = None
    _idx_param: int = 0
    def setup(self, params: Dict[str, Any]) -> None:
        self._idx_param = int(params.get("index", 0))
    async def run(self, ctx: Any) -> None:
        idx = self.index if self.index is not None else self._idx_param
        sl = self.input or []
        if 0 <= idx < len(sl):
            self.result = sl[idx]
        else:
            raise IndexError(f"SliceAtOp: index {idx} out of range (len {len(sl)})")

@register_operator("SliceFirstOp")
class SliceFirstOp(Operator, BaseModel):
    input: Input = []
    result: Output = None
    async def run(self, ctx: Any) -> None:
        if not self.input: raise ValueError("SliceFirstOp: empty list")
        self.result = self.input[0]

@register_operator("SliceLastOp")
class SliceLastOp(Operator, BaseModel):
    input: Input = []
    result: Output = None
    async def run(self, ctx: Any) -> None:
        if not self.input: raise ValueError("SliceLastOp: empty list")
        self.result = self.input[-1]

@register_operator("SliceContainsOp")
class SliceContainsOp(Operator, BaseModel):
    input: Input = []
    value: Input = None
    match: Output = False
    async def run(self, ctx: Any) -> None:
        self.match = (self.value in self.input) if self.input else False

@register_operator("SliceJoinOp")
class SliceJoinOp(Operator, BaseModel):
    input: Input = []
    sep: str = ","
    result: Output = ""
    def setup(self, params: Dict[str, Any]) -> None:
        self.sep = params.get("sep", ",")
    async def run(self, ctx: Any) -> None:
        self.result = self.sep.join(str(v) for v in (self.input or []))

@register_operator("SliceFilterEqOp")
class SliceFilterEqOp(Operator, BaseModel):
    input: Input = []
    value: Input = None
    result: Output = []
    async def run(self, ctx: Any) -> None:
        self.result = [v for v in (self.input or []) if v == self.value]

@register_operator("SliceTopKOp")
class SliceTopKOp(Operator, BaseModel):
    scores: Input = []
    k: int = 1
    result: Output = []
    def setup(self, params: Dict[str, Any]) -> None:
        self.k = int(params.get("k", 1))
    async def run(self, ctx: Any) -> None:
        if not self.scores:
            self.result = []
            return
        indices = sorted(range(len(self.scores)), key=lambda i: self.scores[i], reverse=True)
        self.result = indices[:min(self.k, len(indices))]
