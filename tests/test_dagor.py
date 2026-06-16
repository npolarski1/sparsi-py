import asyncio
import pytest
from dagor import Builder, Engine, Operator, register_operator, Input, Output
from dagor.builtin import ContextValOp, CoalesceOp
from pydantic import BaseModel
from typing import Dict, Any

@register_operator("AddOp")
class AddOp(Operator, BaseModel):
    a: Input = None
    b: Input = None
    sum: Output = None

    def setup(self, params: Dict[str, Any]) -> None:
        pass

    async def reset(self) -> None:
        self.a = None
        self.b = None
        self.sum = None

    async def run(self, ctx: Any) -> None:
        self.sum = (self.a or 0) + (self.b or 0)

@register_operator("SlowOp")
class SlowOp(Operator, BaseModel):
    val: Input = None
    result: Output = None
    delay: float = 0.1

    def setup(self, params: Dict[str, Any]) -> None:
        self.delay = params.get("delay", 0.1)

    async def reset(self) -> None:
        self.val = None
        self.result = None

    async def run(self, ctx: Any) -> None:
        await asyncio.sleep(self.delay)
        self.result = self.val

@pytest.mark.asyncio
async def test_simple_dag():
    # Build a graph:
    #   input -> slow1 -> add
    #   input -> slow2 /
    b = Builder("test_graph")
    b.vertex("in").op("ContextValOp").params({"key": "val"}).output("result", "data")
    b.vertex("slow1").op("SlowOp").params({"delay": 0.2}).input("val", "data").output("result", "s1")
    b.vertex("slow2").op("SlowOp").params({"delay": 0.2}).input("val", "data").output("result", "s2")
    b.vertex("add").op("AddOp").input("a", "s1").input("b", "s2").output("sum", "final")
    
    graph = b.build()
    engine = Engine(graph)
    
    import time
    start = time.time()
    await engine.run({"val": 10})
    duration = time.time() - start
    
    res, ok = engine.get_output("final")
    assert ok
    assert res == 20
    # Should run slow1 and slow2 in parallel (~0.2s + overhead, not 0.4s)
    assert duration < 0.35

@pytest.mark.asyncio
async def test_coalesce():
    b = Builder("coalesce_graph")
    b.vertex("in_a").op("ContextValOp").params({"key": "a"}).output("result", "wire_a")
    b.vertex("in_b").op("ContextValOp").params({"key": "b"}).output("result", "wire_b")
    b.vertex("merge").op("CoalesceOp").input("a", "wire_a").input("b", "wire_b").output("result", "final")
    
    graph = b.build()
    
    # Test A wins
    engine = Engine(graph)
    await engine.run({"a": "hello", "b": "world"})
    res, ok = engine.get_output("final")
    assert res == "hello"
    
    # Test B wins if A is None
    engine = Engine(graph)
    await engine.run({"a": None, "b": "world"})
    res, ok = engine.get_output("final")
    assert res == "world"

@register_operator("RunIDOp")
class RunIDOp(Operator, BaseModel):
    result: Output = ""
    async def run(self, ctx: Any) -> None:
        from dagor import get_run_id
        self.result = get_run_id()

@pytest.mark.asyncio
async def test_reporter_and_run_id():
    from dagor import Reporter
    from unittest import mock
    
    mock_logger = mock.Mock()
    rep = Reporter(logger=mock_logger)
    
    b = Builder("test_reporter")
    b.vertex("id").op("RunIDOp").output("result", "rid")
    graph = b.build()
    
    engine = Engine(graph, reporter=rep)
    await engine.run({})
    
    rid, _ = engine.get_output("rid")
    assert rid != ""
    assert len(rid) > 10 # uuid
    
    # Check if reporter was called
    # Should have started engine, started vertex, finished vertex, finished engine
    assert mock_logger.info.call_count >= 4
    
    # Verify first call was engine.started with correct run_id
    args, kwargs = mock_logger.info.call_args_list[0]
    assert args[0] == "engine.started"
    assert kwargs["run_id"] == rid

def test_cycle_detection():
    b = Builder("cycle")
    # Vertex A depends on B, B depends on A
    b.vertex("A").op("ContextValOp").input("val", "wire_b").output("result", "wire_a")
    b.vertex("B").op("ContextValOp").input("val", "wire_a").output("result", "wire_b")
    
    with pytest.raises(ValueError) as excinfo:
        b.build()
    
    assert "cycle" in str(excinfo.value)

@pytest.mark.asyncio
async def test_coalesce_n_dynamic():
    b = Builder("coalesce_n")
    # Test dynamic Input0, Input1... assignment
    # We'll use ContextValOp to inject values into Input0 and Input1
    b.vertex("in0").op("ContextValOp").params({"key": "v0"}).output("result", "wire0")
    b.vertex("in1").op("ContextValOp").params({"key": "v1"}).output("result", "wire1")
    
    # CoalesceNStringOp uses model_config extra="allow"
    b.vertex("coal").op("CoalesceNStringOp").params({"n": 2})\
        .input("Input0", "wire0")\
        .input("Input1", "wire1")\
        .output("result", "final")
    
    graph = b.build()
    engine = Engine(graph)
    
    # Input0 is None, Input1 should be picked
    await engine.run({"v0": None, "v1": "hello"})
    res, _ = engine.get_output("final")
    assert res == "hello"
    
    # Input0 is set, should be picked
    await engine.run({"v0": "first", "v1": "second"})
    res, _ = engine.get_output("final")
    assert res == "first"

@pytest.mark.asyncio
async def test_vertex_failure_no_deadlock():
    @register_operator("FailOp")
    class FailOp(Operator, BaseModel):
        async def run(self, ctx: Any) -> None:
            raise RuntimeError("intentional failure")
            
    b = Builder("fail_test")
    b.vertex("f").op("FailOp").output("result", "fail_wire")
    b.vertex("down").op("AddOp").input("a", "fail_wire").output("sum", "out")
    
    graph = b.build()
    engine = Engine(graph)
    
    # Should not hang, but engine.run will raise the exception
    with pytest.raises(RuntimeError) as excinfo:
        await engine.run({})
    
    assert "intentional failure" in str(excinfo.value)
    
    # We don't strictly assert if 'down' was skipped or run, 
    # as gather() cancellation timing can vary.
    # The key is that we reached this point without hanging.

@pytest.mark.asyncio
async def test_predicate_ops():
    b = Builder("pred_ops")
    b.vertex("in").op("ContextValOp").params({"key": "val"}).output("result", "data")
    b.vertex("empty").op("PredicateIfEmptyOp").input("val", "data").output("result", "is_empty")
    b.vertex("not_empty").op("PredicateIfNotEmptyOp").input("val", "data").output("result", "is_not_empty")
    
    graph = b.build()
    engine = Engine(graph)
    
    await engine.run({"val": ""})
    assert engine.get_output("is_empty")[0] is True
    assert engine.get_output("is_not_empty")[0] is False
    
    await engine.run({"val": "content"})
    assert engine.get_output("is_empty")[0] is False
    assert engine.get_output("is_not_empty")[0] is True
