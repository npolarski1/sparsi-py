import re
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from dagor import Operator, register_operator, Input, Output

@register_operator("StringConcatOp")
class StringConcatOp(Operator, BaseModel):
    a: Input = ""
    b: Input = ""
    result: Output = ""

    async def run(self, ctx: Any) -> None:
        self.result = str(self.a or "") + str(self.b or "")

@register_operator("StringRegexExtractOp")
class StringRegexExtractOp(Operator, BaseModel):
    text: Input = ""
    pattern: str = ""
    result: Output = None

    def setup(self, params: Dict[str, Any]) -> None:
        self.pattern = params.get("pattern", "")

    async def run(self, ctx: Any) -> None:
        if not self.text or not self.pattern:
            return
        match = re.search(self.pattern, self.text)
        if match:
            self.result = match.group(1) if match.groups() else match.group(0)

@register_operator("StringLowerOp")
class StringLowerOp(Operator, BaseModel):
    text: Input = ""
    result: Output = ""

    async def run(self, ctx: Any) -> None:
        if self.text:
            self.result = self.text.lower()

@register_operator("StringUpperOp")
class StringUpperOp(Operator, BaseModel):
    text: Input = ""
    result: Output = ""

    async def run(self, ctx: Any) -> None:
        if self.text:
            self.result = self.text.upper()

@register_operator("StringTrimOp")
class StringTrimOp(Operator, BaseModel):
    text: Input = ""
    result: Output = ""

    async def run(self, ctx: Any) -> None:
        if self.text:
            self.result = self.text.strip()

@register_operator("StringReplaceOp")
class StringReplaceOp(Operator, BaseModel):
    text: Input = ""
    old: str = ""
    new: str = ""
    result: Output = ""

    def setup(self, params: Dict[str, Any]) -> None:
        self.old = params.get("old", "")
        self.new = params.get("new", "")

    async def run(self, ctx: Any) -> None:
        if self.text:
            self.result = self.text.replace(self.old, self.new)

@register_operator("StringSplitOp")
class StringSplitOp(Operator, BaseModel):
    text: Input = ""
    sep: str = ","
    result: Output = []

    def setup(self, params: Dict[str, Any]) -> None:
        self.sep = params.get("sep", ",")

    async def run(self, ctx: Any) -> None:
        if self.text:
            self.result = [s.strip() for s in self.text.split(self.sep) if s.strip()]

@register_operator("StringJoinOp")
class StringJoinOp(Operator, BaseModel):
    items: Input = []
    sep: str = ", "
    result: Output = ""

    def setup(self, params: Dict[str, Any]) -> None:
        self.sep = params.get("sep", ", ")

    async def run(self, ctx: Any) -> None:
        if self.items:
            self.result = self.sep.join(str(i) for i in self.items)

@register_operator("StringLenOp")
class StringLenOp(Operator, BaseModel):
    text: Input = ""
    result: Output = 0

    async def run(self, ctx: Any) -> None:
        if self.text:
            self.result = len(self.text)

@register_operator("StringTruncateOp")
class StringTruncateOp(Operator, BaseModel):
    text: Input = ""
    max_bytes: int = 8192
    result: Output = ""

    def setup(self, params: Dict[str, Any]) -> None:
        self.max_bytes = int(params.get("max_bytes", 8192))

    async def run(self, ctx: Any) -> None:
        if not self.text:
            self.result = ""
            return
        
        # Simple string slicing for truncation (not strictly byte-wise but safe for UTF-8 in Python)
        if len(self.text) > self.max_bytes:
            self.result = self.text[:self.max_bytes]
        else:
            self.result = self.text

@register_operator("StringContainsOp")
class StringContainsOp(Operator, BaseModel):
    text: Input = ""
    sub: str = ""
    result: Output = False

    def setup(self, params: Dict[str, Any]) -> None:
        self.sub = params.get("sub", "")

    async def run(self, ctx: Any) -> None:
        if self.text:
            self.result = self.sub in self.text

@register_operator("StringLookupOp")
class StringLookupOp(Operator, BaseModel):
    key: Input = ""
    entries: Dict[str, str] = {}
    result: Output = ""

    def setup(self, params: Dict[str, Any]) -> None:
        raw = params.get("map", "{}")
        if isinstance(raw, str):
            self.entries = json.loads(raw)
        else:
            self.entries = raw

    async def run(self, ctx: Any) -> None:
        if self.key:
            self.result = self.entries.get(self.key, "")

# Cast operators
@register_operator("IntToStringOp")
class IntToStringOp(Operator, BaseModel):
    val: Input = 0
    result: Output = ""

    async def run(self, ctx: Any) -> None:
        self.result = str(self.val)

@register_operator("FloatToStringOp")
class FloatToStringOp(Operator, BaseModel):
    val: Input = 0.0
    result: Output = ""

    async def run(self, ctx: Any) -> None:
        self.result = str(self.val)

@register_operator("BoolToStringOp")
class BoolToStringOp(Operator, BaseModel):
    val: Input = False
    result: Output = ""

    async def run(self, ctx: Any) -> None:
        self.result = str(self.val).lower()

@register_operator("ToStringOp")
class ToStringOp(Operator, BaseModel):
    val: Input = None
    result: Output = ""

    async def run(self, ctx: Any) -> None:
        self.result = str(self.val) if self.val is not None else ""
