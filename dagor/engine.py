import asyncio
import structlog
import uuid
import time
import contextvars
from typing import Any, Dict, List, Optional, Set, Tuple
from .graph import Graph, Vertex
from .operator import get_operator_type, Operator
from .reporter import Reporter

logger = structlog.get_logger(__name__)

# contextvars for run_id, mirroring dagor.RunID(ctx) in Go
_run_id_var = contextvars.ContextVar("dagor_run_id", default="")

def get_run_id() -> str:
    """Returns the current workflow run ID, or empty string if not running."""
    return _run_id_var.get()

class Engine:
    def __init__(self, graph: Graph, reporter: Optional[Reporter] = None):
        self.graph = graph
        self.reporter = reporter
        self.wires: Dict[str, Any] = {}
        self.skipped_vertices: Set[str] = set()
        self.skipped_wires: Set[str] = set()
        self._wire_events: Dict[str, asyncio.Event] = {}

    async def run(self, ctx: Any, initial_wires: Optional[Dict[str, Any]] = None) -> None:
        """Executes the graph."""
        run_id = str(uuid.uuid4())
        token = _run_id_var.set(run_id)
        
        start_time = time.time()
        if self.reporter:
            self.reporter.engine_started(self.graph.name, run_id)
        
        try:
            self.wires = initial_wires.copy() if initial_wires else {}
            self.skipped_vertices = set()
            self.skipped_wires = set()
            
            # 1. Gather all potential wires in this graph
            all_potential_wires = set()
            for v in self.graph.vertices.values():
                all_potential_wires.update(v.outputs.values())
                all_potential_wires.update(v.inputs.values())
                all_potential_wires.update(v.condition_inputs)

            # 2. Setup events for all wires
            self._wire_events = {w: asyncio.Event() for w in all_potential_wires}
            
            # 3. Mark initial wires as ready
            for w in self.wires:
                if w in self._wire_events:
                    self._wire_events[w].set()

            # Launch all vertices as tasks.
            tasks = []
            for vertex_name in self.graph.vertices:
                tasks.append(asyncio.create_task(self._run_vertex(vertex_name, ctx, run_id)))
            
            await asyncio.gather(*tasks)
            
            if self.reporter:
                duration_ms = (time.time() - start_time) * 1000
                self.reporter.engine_finished(self.graph.name, run_id, duration_ms)
                
        except Exception as e:
            if self.reporter:
                duration_ms = (time.time() - start_time) * 1000
                self.reporter.engine_finished(self.graph.name, run_id, duration_ms, error=e)
            raise e
        finally:
            _run_id_var.reset(token)

    async def _run_vertex(self, name: str, ctx: Any, run_id: str) -> None:
        vertex = self.graph.vertices[name]
        
        # 1. Wait for all input wires
        input_wires = list(vertex.inputs.values()) + vertex.condition_inputs
        for wire in input_wires:
            if wire in self._wire_events:
                await self._wire_events[wire].wait()
        
        # 2. Check for upstream skips
        upstream_skipped = any(w in self.skipped_wires for w in input_wires)
        if upstream_skipped and vertex.merge_strategy != "coalesce":
            self._skip_vertex(name, run_id, "upstream_skipped")
            return

        # 3. Check conditions
        if vertex.conditions:
            # Gather condition inputs
            cond_inputs = {}
            for wire in vertex.condition_inputs:
                cond_inputs[wire] = self.wires.get(wire)
            
            # Also include direct inputs in cond_inputs if they are not already there
            for wire in vertex.inputs.values():
                if wire not in cond_inputs:
                    cond_inputs[wire] = self.wires.get(wire)
            
            from sparsi.library.predicate_ops import evaluate_predicate
            try:
                for pred_name in vertex.conditions:
                    if not evaluate_predicate(pred_name, cond_inputs):
                        self._skip_vertex(name, run_id, f"predicate_{pred_name}_failed")
                        return
            except Exception as e:
                logger.error("predicate_evaluation_failed", vertex=name, error=str(e))
                if self.reporter:
                    self.reporter.vertex_failed(name, run_id, vertex.operator_name or "fanout", e, 0)
                # Fail outputs to avoid deadlocks
                for wire_name in vertex.outputs.values():
                    if wire_name in self._wire_events:
                        self._wire_events[wire_name].set()
                raise e
        
        # 4. Instantiate and run operator
        start_time = time.time()
        if vertex.operator_name:
            op_type = get_operator_type(vertex.operator_name)
            op = op_type(**vertex.params) if hasattr(op_type, 'model_fields') else op_type()

            # 1. Set values from vertex.params first
            op.setup(vertex.params)

            # 2. Reset internal state
            await op.reset()

            # 3. OVERWRITE with values from wires
            inputs_for_reporter = {}
            for op_field, wire_name in vertex.inputs.items():
                val = self.wires.get(wire_name)
                inputs_for_reporter[op_field] = val
                op.set_input_field(op_field, val)
            
            if self.reporter:
                self.reporter.vertex_started(name, run_id, vertex.operator_name, inputs_for_reporter)

            try:
                await op.run(ctx)
                
                # Capture outputs
                outputs = op.get_output_fields()
                for op_field, wire_name in vertex.outputs.items():
                    self.wires[wire_name] = outputs.get(op_field)
                    if wire_name in self._wire_events:
                        self._wire_events[wire_name].set()
                
                if self.reporter:
                    duration_ms = (time.time() - start_time) * 1000
                    self.reporter.vertex_finished(name, run_id, vertex.operator_name, outputs, duration_ms)
            except Exception as e:
                logger.error("vertex_failed", vertex=name, error=str(e))
                if self.reporter:
                    duration_ms = (time.time() - start_time) * 1000
                    self.reporter.vertex_failed(name, run_id, vertex.operator_name, e, duration_ms)
                raise e
        elif vertex.is_map or vertex.is_filter:
            if self.reporter:
                self.reporter.vertex_started(name, run_id, "fanout", {"iterator": vertex.iterator_wire})
            
            await self._run_fanout(name, ctx, run_id)
            
            if self.reporter:
                duration_ms = (time.time() - start_time) * 1000
                self.reporter.vertex_finished(name, run_id, "fanout", {}, duration_ms)
        else:
            # Handle empty nodes or base cases
            for wire_name in vertex.outputs.values():
                if wire_name in self._wire_events:
                    self._wire_events[wire_name].set()

    def _skip_vertex(self, name: str, run_id: str, reason: str) -> None:
        self.skipped_vertices.add(name)
        if self.reporter:
            self.reporter.vertex_skipped(name, run_id, reason)
        
        # Mark outputs as skipped
        vertex = self.graph.vertices[name]
        for wire_name in vertex.outputs.values():
            if wire_name not in self.wires:
                self.wires[wire_name] = None
            self.skipped_wires.add(wire_name)
            if wire_name in self._wire_events:
                self._wire_events[wire_name].set()

    async def _run_fanout(self, name: str, ctx: Any, parent_run_id: str) -> None:
        vertex = self.graph.vertices[name]
        items = self.wires.get(vertex.iterator_wire)
        logger.debug("fanout_start", vertex=name, wire=vertex.iterator_wire, count=len(items) if items else 0)
        if not items or not isinstance(items, list):
            # Mark outputs as ready (empty)
            for wire_name in vertex.outputs.values():
                self.wires[wire_name] = []
                if wire_name in self._wire_events:
                    self._wire_events[wire_name].set()
            return

        results = []
        for i, item in enumerate(items):
            # Create a sub-engine for each item
            sub_engine = Engine(vertex.sub_graph, reporter=self.reporter)
            
            # 1. Setup initial wires for sub-engine
            # Sub-engine starts with a copy of parent wires so it can access
            # other global wires if needed.
            initial_wires = self.wires.copy()
            initial_wires[vertex.item_wire] = item
            logger.debug("fanout_inject", vertex=name, index=i, item_wire=vertex.item_wire, value=item)
            
            await sub_engine.run(ctx, initial_wires=initial_wires)
            
            if vertex.is_map:
                val, ok = sub_engine.get_output(vertex.collect_into_wire)
                results.append(val if ok else None)
            elif vertex.is_filter:
                val, ok = sub_engine.get_output(vertex.collect_into_wire)
                if val: # Truthy check for filter
                    results.append(item)

        # Set final output
        # Map/Filter usually have a single 'Result' output wire mapped via collect_into
        for op_field, wire_name in vertex.outputs.items():
            if op_field == "Result":
                self.wires[wire_name] = results
                if wire_name in self._wire_events:
                    self._wire_events[wire_name].set()

    def get_output(self, wire: str) -> Tuple[Any, bool]:
        if wire in self.wires:
            return self.wires[wire], True
        return None, False

    def vertex_skipped(self, name: str) -> bool:
        return name in self.skipped_vertices
