from typing import Any, Dict, List, Optional, Callable
from pydantic import BaseModel
from dagor import Operator, register_operator, Input, Output

# Registry for named predicates
_PREDICATE_REGISTRY: Dict[str, Callable[[Dict[str, Any]], bool]] = {}

def register_predicate(name: str, func: Callable[[Dict[str, Any]], bool]):
    _PREDICATE_REGISTRY[name] = func

def evaluate_predicate(name: str, inputs: Dict[str, Any]) -> bool:
    if name not in _PREDICATE_REGISTRY:
        raise ValueError(f"Predicate '{name}' not found in registry")
    return _PREDICATE_REGISTRY[name](inputs)

# Standard predicates
def register_standard_predicates():
    register_predicate("is_not_none", lambda inputs: any(v is not None for v in inputs.values()))
    register_predicate("is_empty", lambda inputs: any(not v for v in inputs.values()))
    register_predicate("is_not_empty", lambda inputs: any(bool(v) for v in inputs.values()))
    register_predicate("always_true", lambda _: True)
    register_predicate("always_false", lambda _: False)

@register_operator("PredicateIfEmptyOp")
class PredicateIfEmptyOp(Operator, BaseModel):
    val: Input = None
    result: Output = False

    def setup(self, params: Dict[str, Any]) -> None:
        pass

    async def reset(self) -> None:
        self.val = None
        self.result = False

    async def run(self, ctx: Any) -> None:
        self.result = not bool(self.val)

@register_operator("PredicateIfNotEmptyOp")
class PredicateIfNotEmptyOp(Operator, BaseModel):
    val: Input = None
    result: Output = False

    def setup(self, params: Dict[str, Any]) -> None:
        pass

    async def reset(self) -> None:
        self.val = None
        self.result = False

    async def run(self, ctx: Any) -> None:
        self.result = bool(self.val)
