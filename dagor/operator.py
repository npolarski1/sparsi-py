import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar, Generic, Annotated, get_origin, get_args
from pydantic import BaseModel, ConfigDict

# Metadata markers for wires
Input = Annotated[Any, "dag_input"]
Output = Annotated[Any, "dag_output"]

class Operator(ABC):
    """
    Base class for all dagor operators.
    Operators should inherit from both Operator and pydantic.BaseModel
    to support automatic field discovery.
    """
    
    def setup(self, params: Dict[str, Any]) -> None:
        """Called once during engine initialization."""
        pass

    async def reset(self) -> None:
        """Called before each run if the operator is reused."""
        self.reset_fields()

    @abstractmethod
    async def run(self, ctx: Any) -> None:
        """Executes the operator logic."""
        pass

    def get_input_fields(self) -> Dict[str, Any]:
        """Returns a mapping of field name to current value for all inputs."""
        if not isinstance(self, BaseModel):
            return {}
        
        inputs = {}
        for name, field in self.__class__.model_fields.items():
            if self._is_dag_input(field):
                inputs[name] = getattr(self, name)
        return inputs

    def get_output_fields(self) -> Dict[str, Any]:
        """Returns a mapping of field name to current value for all outputs."""
        if not isinstance(self, BaseModel):
            return {}
        
        outputs = {}
        for name, field in self.__class__.model_fields.items():
            if self._is_dag_output(field):
                outputs[name] = getattr(self, name)
        return outputs

    def set_input_field(self, name: str, value: Any) -> None:
        """Sets a specific input field."""
        if not hasattr(self, name):
            raise AttributeError(f"Operator {self.__class__.__name__} has no field {name}")
        setattr(self, name, value)

    def reset_fields(self) -> None:
        """Resets all input and output fields to their default values (None)."""
        if not isinstance(self, BaseModel):
            return
            
        for name, field in self.__class__.model_fields.items():
            if self._is_dag_output(field):
                setattr(self, name, None)
            # Input fields are NOT reset here, they are overwritten by wires in the engine
            # if they are connected, or they retain their setup() values.

    def _is_dag_input(self, field: Any) -> bool:
        return self._has_metadata(field, "dag_input")

    def _is_dag_output(self, field: Any) -> bool:
        return self._has_metadata(field, "dag_output")

    def _has_metadata(self, field: Any, marker: str) -> bool:
        return marker in field.metadata

# Registry for operator types
_OPERATOR_REGISTRY: Dict[str, Type[Operator]] = {}

def register_operator(name: Optional[str] = None):
    """Decorator to register an operator type."""
    def decorator(cls: Type[Operator]):
        reg_name = name or cls.__name__
        _OPERATOR_REGISTRY[reg_name] = cls
        return cls
    return decorator

def get_operator_type(name: str) -> Type[Operator]:
    if name not in _OPERATOR_REGISTRY:
        raise ValueError(f"Operator '{name}' not found in registry")
    return _OPERATOR_REGISTRY[name]
