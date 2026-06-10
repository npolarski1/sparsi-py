from pydantic import BaseModel, ConfigDict
from .operator import Operator, register_operator, Input, Output

@register_operator("ContextValOp")
class ContextValOp(Operator, BaseModel):
    model_config = ConfigDict(extra="allow")
    key: str = ""
    result: Output = None

    def setup(self, params: Dict[str, Any]) -> None:
        self.key = params.get("key", "")

    async def reset(self) -> None:
        self.result = None

    async def run(self, ctx: Any) -> None:
        if isinstance(ctx, dict):
            self.result = ctx.get(self.key)
        else:
            # Assume ctx might be some other object with attributes
            self.result = getattr(ctx, self.key, None)

@register_operator("CoalesceOp")
class CoalesceOp(Operator, BaseModel):
    model_config = ConfigDict(extra="allow")
    a: Input = None
    b: Input = None
    result: Output = None

    def setup(self, params: Dict[str, Any]) -> None:
        pass

    async def reset(self) -> None:
        self.a = None
        self.b = None
        self.result = None

    async def run(self, ctx: Any) -> None:
        self.result = self.a if self.a is not None else self.b

@register_operator("CoalesceNOp")
@register_operator("CoalesceNStringOp")
class CoalesceNStringOp(Operator, BaseModel):
    model_config = ConfigDict(extra="allow")
    # Pydantic doesn't handle dynamic fields well with Annotated markers
    # So we'll use model_extra or just a flexible run() method.
    # In dagor-go, it uses Input0, Input1...
    # We'll support both a list in 'inputs' field or searching model_extra
    inputs: Input = None # Expected to be a list if wired collectively
    n: int = 0
    result: Output = None

    def setup(self, params: Dict[str, Any]) -> None:
        self.n = int(params.get("n", 0))

    async def run(self, ctx: Any) -> None:
        # 1. Check the explicit list input
        if self.inputs:
            for item in self.inputs:
                if item is not None:
                    self.result = item
                    return
        
        # 2. Check Input0, Input1... pattern in model_extra or self
        for i in range(self.n):
            name = f"Input{i}"
            val = getattr(self, name, None)
            if val is not None:
                self.result = val
                return

@register_operator("CoalesceNIntOp")
class CoalesceNIntOp(CoalesceNStringOp):
    pass

@register_operator("CoalesceNFloatOp")
@register_operator("CoalesceNFloat64Op")
class CoalesceNFloatOp(CoalesceNStringOp):
    pass
