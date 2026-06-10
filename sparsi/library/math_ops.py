import math
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel
from dagor import Operator, register_operator, Input, Output

# --- Float Ops ---

@register_operator("AddFloatOp")
class AddFloatOp(Operator, BaseModel):
    a: Input = 0.0
    b: Input = 0.0
    result: Output = 0.0
    async def run(self, ctx: Any) -> None:
        self.result = float(self.a or 0.0) + float(self.b or 0.0)

@register_operator("SubFloatOp")
class SubFloatOp(Operator, BaseModel):
    a: Input = 0.0
    b: Input = 0.0
    result: Output = 0.0
    async def run(self, ctx: Any) -> None:
        self.result = float(self.a or 0.0) - float(self.b or 0.0)

@register_operator("MulFloatOp")
class MulFloatOp(Operator, BaseModel):
    a: Input = 0.0
    b: Input = 0.0
    result: Output = 0.0
    async def run(self, ctx: Any) -> None:
        self.result = float(self.a or 0.0) * float(self.b or 0.0)

@register_operator("DivFloatOp")
class DivFloatOp(Operator, BaseModel):
    a: Input = 0.0
    b: Input = 1.0
    result: Output = 0.0
    async def run(self, ctx: Any) -> None:
        if float(self.b or 0.0) == 0:
            raise ValueError("division by zero")
        self.result = float(self.a or 0.0) / float(self.b)

@register_operator("PowFloatOp")
class PowFloatOp(Operator, BaseModel):
    a: Input = 0.0
    b: Input = 0.0
    result: Output = 0.0
    async def run(self, ctx: Any) -> None:
        self.result = math.pow(float(self.a or 0.0), float(self.b or 0.0))

@register_operator("ModFloatOp")
class ModFloatOp(Operator, BaseModel):
    a: Input = 0.0
    b: Input = 1.0
    result: Output = 0.0
    async def run(self, ctx: Any) -> None:
        if float(self.b or 0.0) == 0:
            raise ValueError("modulo by zero")
        self.result = math.fmod(float(self.a or 0.0), float(self.b))

@register_operator("RoundOp")
class RoundOp(Operator, BaseModel):
    value: Input = 0.0
    result: Output = 0.0
    async def run(self, ctx: Any) -> None:
        self.result = float(round(self.value or 0.0))

@register_operator("ClampFloatOp")
class ClampFloatOp(Operator, BaseModel):
    value: Input = 0.0
    min: Input = 0.0
    max: Input = 1.0
    result: Output = 0.0
    async def run(self, ctx: Any) -> None:
        v = float(self.value or 0.0)
        self.result = max(float(self.min or 0.0), min(v, float(self.max or 1.0)))

@register_operator("SumFloatOp")
class SumFloatOp(Operator, BaseModel):
    values: Input = []
    result: Output = 0.0
    async def run(self, ctx: Any) -> None:
        self.result = sum(float(v) for v in (self.values or []))

@register_operator("MinFloatOp")
class MinFloatOp(Operator, BaseModel):
    values: Input = []
    result: Output = 0.0
    async def run(self, ctx: Any) -> None:
        if not self.values: raise ValueError("MinFloatOp: empty list")
        self.result = min(float(v) for v in self.values)

@register_operator("MaxFloatOp")
class MaxFloatOp(Operator, BaseModel):
    values: Input = []
    result: Output = 0.0
    async def run(self, ctx: Any) -> None:
        if not self.values: raise ValueError("MaxFloatOp: empty list")
        self.result = max(float(v) for v in self.values)

# --- Int Ops ---

@register_operator("AddIntOp")
@register_operator("MathAddOp")
class AddIntOp(Operator, BaseModel):
    a: Input = 0
    b: Input = 0
    result: Output = 0
    def setup(self, params: Dict[str, Any]) -> None:
        if "a" in params: self.a = params["a"]
        if "b" in params: self.b = params["b"]
    async def run(self, ctx: Any) -> None:
        self.result = int(self.a or 0) + int(self.b or 0)

@register_operator("SubIntOp")
class SubIntOp(Operator, BaseModel):
    a: Input = 0
    b: Input = 0
    result: Output = 0
    async def run(self, ctx: Any) -> None:
        self.result = int(self.a or 0) - int(self.b or 0)

@register_operator("MulIntOp")
@register_operator("MathMulOp")
class MulIntOp(Operator, BaseModel):
    a: Input = 0
    b: Input = 0
    result: Output = 0
    def setup(self, params: Dict[str, Any]) -> None:
        if "a" in params: self.a = params["a"]
        if "b" in params: self.b = params["b"]
    async def run(self, ctx: Any) -> None:
        self.result = int(self.a or 0) * int(self.b or 0)

@register_operator("DivIntOp")
@register_operator("MathDivOp")
class DivIntOp(Operator, BaseModel):
    a: Input = 0
    b: Input = 1
    result: Output = 0
    async def run(self, ctx: Any) -> None:
        if int(self.b or 0) == 0:
            raise ValueError("division by zero")
        self.result = int(self.a or 0) // int(self.b)

@register_operator("PowIntOp")
class PowIntOp(Operator, BaseModel):
    a: Input = 0
    b: Input = 0
    result: Output = 0
    async def run(self, ctx: Any) -> None:
        if int(self.b or 0) < 0: raise ValueError("negative exponent")
        self.result = int(math.pow(int(self.a or 0), int(self.b or 0)))

@register_operator("ModIntOp")
class ModIntOp(Operator, BaseModel):
    a: Input = 0
    b: Input = 1
    result: Output = 0
    async def run(self, ctx: Any) -> None:
        if int(self.b or 0) == 0: raise ValueError("modulo by zero")
        self.result = int(self.a or 0) % int(self.b)

@register_operator("ClampIntOp")
class ClampIntOp(Operator, BaseModel):
    value: Input = 0
    min: Input = 0
    max: Input = 100
    result: Output = 0
    async def run(self, ctx: Any) -> None:
        v = int(self.value or 0)
        self.result = max(int(self.min or 0), min(v, int(self.max or 100)))

@register_operator("SumIntOp")
class SumIntOp(Operator, BaseModel):
    values: Input = []
    result: Output = 0
    async def run(self, ctx: Any) -> None:
        self.result = sum(int(v) for v in (self.values or []))

@register_operator("MinIntOp")
class MinIntOp(Operator, BaseModel):
    values: Input = []
    result: Output = 0
    async def run(self, ctx: Any) -> None:
        if not self.values: raise ValueError("MinIntOp: empty list")
        self.result = min(int(v) for v in self.values)

@register_operator("MaxIntOp")
class MaxIntOp(Operator, BaseModel):
    values: Input = []
    result: Output = 0
    async def run(self, ctx: Any) -> None:
        if not self.values: raise ValueError("MaxIntOp: empty list")
        self.result = max(int(v) for v in self.values)

# --- Casts ---

@register_operator("IntToFloat64Op")
class IntToFloat64Op(Operator, BaseModel):
    value: Input = 0
    result: Output = 0.0
    async def run(self, ctx: Any) -> None:
        self.result = float(self.value or 0)

@register_operator("Float64ToIntOp")
@register_operator("MathFloatToIntOp")
class Float64ToIntOp(Operator, BaseModel):
    value: Input = 0.0
    result: Output = 0
    async def run(self, ctx: Any) -> None:
        self.result = int(self.value or 0.0)

# --- Aggregate ---

class MathOperands(BaseModel):
    a: float
    b: float

@register_operator("PackMathOperandsOp")
class PackMathOperandsOp(Operator, BaseModel):
    a: Input = 0.0
    b: Input = 0.0
    result: Output = None # MathOperands
    async def run(self, ctx: Any) -> None:
        self.result = {"a": float(self.a or 0.0), "b": float(self.b or 0.0)}

# --- Predicates ---

@register_operator("IfIntEqOp")
class IfIntEqOp(Operator, BaseModel):
    a: Input = 0
    b: Input = 0
    match: Output = False
    async def run(self, ctx: Any) -> None:
        self.match = int(self.a or 0) == int(self.b or 0)

@register_operator("IfIntGtOp")
class IfIntGtOp(Operator, BaseModel):
    a: Input = 0
    b: Input = 0
    match: Output = False
    async def run(self, ctx: Any) -> None:
        self.match = int(self.a or 0) > int(self.b or 0)

@register_operator("IfIntLtOp")
class IfIntLtOp(Operator, BaseModel):
    a: Input = 0
    b: Input = 0
    match: Output = False
    async def run(self, ctx: Any) -> None:
        self.match = int(self.a or 0) < int(self.b or 0)

@register_operator("IfIntGeOp")
class IfIntGeOp(Operator, BaseModel):
    a: Input = 0
    b: Input = 0
    match: Output = False
    async def run(self, ctx: Any) -> None:
        self.match = int(self.a or 0) >= int(self.b or 0)

@register_operator("IfIntLeOp")
class IfIntLeOp(Operator, BaseModel):
    a: Input = 0
    b: Input = 0
    match: Output = False
    async def run(self, ctx: Any) -> None:
        self.match = int(self.a or 0) <= int(self.b or 0)

@register_operator("IfFloatEqOp")
class IfFloatEqOp(Operator, BaseModel):
    a: Input = 0.0
    b: Input = 0.0
    match: Output = False
    async def run(self, ctx: Any) -> None:
        self.match = float(self.a or 0.0) == float(self.b or 0.0)

@register_operator("IfFloatGtOp")
class IfFloatGtOp(Operator, BaseModel):
    a: Input = 0.0
    b: Input = 0.0
    match: Output = False
    async def run(self, ctx: Any) -> None:
        self.match = float(self.a or 0.0) > float(self.b or 0.0)

@register_operator("IfFloatLtOp")
class IfFloatLtOp(Operator, BaseModel):
    a: Input = 0.0
    b: Input = 0.0
    match: Output = False
    async def run(self, ctx: Any) -> None:
        self.match = float(self.a or 0.0) < float(self.b or 0.0)

@register_operator("IfFloatGeOp")
class IfFloatGeOp(Operator, BaseModel):
    a: Input = 0.0
    b: Input = 0.0
    match: Output = False
    async def run(self, ctx: Any) -> None:
        self.match = float(self.a or 0.0) >= float(self.b or 0.0)

@register_operator("IfFloatLeOp")
class IfFloatLeOp(Operator, BaseModel):
    a: Input = 0.0
    b: Input = 0.0
    match: Output = False
    async def run(self, ctx: Any) -> None:
        self.match = float(self.a or 0.0) <= float(self.b or 0.0)

@register_operator("BetweenFloatOp")
class BetweenFloatOp(Operator, BaseModel):
    value: Input = 0.0
    min: Input = 0.0
    max: Input = 1.0
    match: Output = False
    async def run(self, ctx: Any) -> None:
        v = float(self.value or 0.0)
        self.match = float(self.min or 0.0) <= v <= float(self.max or 1.0)
