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
        # 1. Build adjacency list of vertices
        # A vertex A depends on B if A has an input wire that B outputs.
        adj = {v_name: [] for v_name in self.vertices}
        
        # Wire name -> Producer vertex
        wire_producers = {}
        for v in self.vertices.values():
            for wire in v.outputs.values():
                wire_producers[wire] = v.name
        
        for v_name, v in self.vertices.items():
            inputs = list(v.inputs.values()) + v.condition_inputs
            if v.iterator_wire:
                inputs.append(v.iterator_wire)
            
            for wire in inputs:
                producer = wire_producers.get(wire)
                if producer:
                    # u -> v means u produces wire consumed by v
                    # So B -> A means B produces wire consumed by A
                    if v_name not in adj[producer]:
                        adj[producer].append(v_name)
        
        # 2. Check for cycles using DFS
        visited = set()
        path = set()
        
        def check(u):
            visited.add(u)
            path.add(u)
            for v in adj[u]:
                if v in path:
                    return True
                if v not in visited:
                    if check(v):
                        return True
            path.remove(u)
            return False
            
        for v_name in self.vertices:
            if v_name not in visited:
                if check(v_name):
                    raise ValueError(f"Graph '{self.name}' has a cycle involving vertex '{v_name}'")
