from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field

@dataclass
class WireConnection:
    from_vertex: str
    output_field: str
    to_vertex: str
    input_field: str

@dataclass
class Vertex:
    name: str
    operator_name: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    inputs: Dict[str, str] = field(default_factory=dict)  # op_field -> wire_name
    outputs: Dict[str, str] = field(default_factory=dict) # op_field -> wire_name
    conditions: List[str] = field(default_factory=list)   # list of predicate names
    condition_inputs: List[str] = field(default_factory=list) # wire names needed for predicates
    merge_strategy: Optional[str] = None
    error_action: Optional[str] = None
    
    # For Map/Filter/Reduce
    is_map: bool = False
    is_filter: bool = False
    is_reduce: bool = False
    
    iterator_wire: Optional[str] = None # The wire to iterate over (e.g. slice_wire)
    item_wire: Optional[str] = None     # The wire name for the current item inside sub-graph
    
    # Reducer specific
    initial_value_wire: Optional[str] = None
    accumulator_wire: Optional[str] = None
    
    sub_graph: Optional['Graph'] = None
    collect_into_wire: Optional[str] = None # Terminating wire of sub-graph to collect into list

@dataclass
class Graph:
    name: str
    vertices: Dict[str, Vertex] = field(default_factory=dict)
    
    def add_vertex(self, vertex: Vertex):
        self.vertices[vertex.name] = vertex

    def validate(self):
        # Basic validation: check for cycles, dangling wires, etc.
        # Implementation can be expanded as needed.
        pass
