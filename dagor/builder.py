from typing import Any, Dict, List, Optional, Union
from .graph import Graph, Vertex

class Builder:
    def __init__(self, name: str):
        self.graph = Graph(name=name)

    def vertex(self, name: str) -> 'VertexBuilder':
        if name in self.graph.vertices:
            raise ValueError(f"Vertex '{name}' already exists")
        v = Vertex(name=name)
        self.graph.add_vertex(v)
        return VertexBuilder(self, v)

    def build(self) -> Graph:
        self.graph.validate()
        return self.graph

class VertexBuilder:
    def __init__(self, builder: Builder, vertex: Vertex):
        self._builder = builder
        self._vertex = vertex
        self._sub_graph_builder: Optional['SubGraphBuilder'] = None
        self._parent_vb_proxy: Optional['VertexBuilder'] = None

    def op(self, name: str) -> 'VertexBuilder':
        self._vertex.operator_name = name
        return self

    def params(self, p: Dict[str, Any]) -> 'VertexBuilder':
        self._vertex.params = p
        return self

    def input(self, op_field: str, wire: str) -> 'VertexBuilder':
        self._vertex.inputs[op_field] = wire
        return self

    def output(self, op_field: str, wire: str) -> 'VertexBuilder':
        self._vertex.outputs[op_field] = wire
        return self

    def condition(self, pred_name: str) -> 'VertexBuilder':
        self._vertex.conditions.append(pred_name)
        return self

    def condition_input(self, wire: str) -> 'VertexBuilder':
        self._vertex.condition_inputs.append(wire)
        return self

    def merge(self, strategy: str) -> 'VertexBuilder':
        self._vertex.merge_strategy = strategy
        return self

    def on_error(self, action: str) -> 'VertexBuilder':
        self._vertex.error_action = action
        return self

    def map_over(self, iterator_wire: str, item_wire: str) -> 'SubGraphBuilder':
        self._vertex.is_map = True
        self._vertex.iterator_wire = iterator_wire
        self._vertex.item_wire = item_wire
        self._vertex.sub_graph = Graph(name=f"{self._vertex.name}_map")
        self._sub_graph_builder = SubGraphBuilder(self, self._vertex.sub_graph)
        return self._sub_graph_builder

    def filter_by(self, iterator_wire: str, item_wire: str) -> 'SubGraphBuilder':
        self._vertex.is_filter = True
        self._vertex.iterator_wire = iterator_wire
        self._vertex.item_wire = item_wire
        self._vertex.sub_graph = Graph(name=f"{self._vertex.name}_filter")
        self._sub_graph_builder = SubGraphBuilder(self, self._vertex.sub_graph)
        return self._sub_graph_builder

    def collect_into(self, wire: str, output_wire: str) -> 'VertexBuilder':
        if self._parent_vb_proxy:
            return self._parent_vb_proxy.collect_into(wire, output_wire)
        if not self._sub_graph_builder:
            raise ValueError("collect_into can only be called on a Map/Filter/Reduce vertex or its children")
        return self._sub_graph_builder.collect_into(wire, output_wire)

    def done(self) -> Builder:
        if self._parent_vb_proxy:
            return self._parent_vb_proxy.done()
        return self._builder

    # Shortcuts
    def vertex(self, name: str) -> 'VertexBuilder':
        return self.done().vertex(name)

    def build(self) -> Graph:
        return self.done().build()

class SubGraphBuilder:
    def __init__(self, parent_vb: VertexBuilder, graph: Graph):
        self._parent_vb = parent_vb
        self.graph = graph

    def vertex(self, name: str) -> 'VertexBuilder':
        sub_builder = Builder(self.graph.name)
        sub_builder.graph = self.graph
        vb = sub_builder.vertex(name)
        # Proxy the parent back so we can return to it via collect_into or done
        vb._parent_vb_proxy = self._parent_vb 
        return vb

    def collect_into(self, wire: str, output_wire: str) -> VertexBuilder:
        self._parent_vb._vertex.collect_into_wire = wire
        # Register the result wire on the parent vertex outputs
        self._parent_vb.output("Result", output_wire) 
        return self._parent_vb
