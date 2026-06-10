import asyncio
import pytest
from dagor import Builder, Engine
from dagor.builtin import ContextValOp, CoalesceOp
import sparsi.library

@pytest.mark.asyncio
async def test_conditional_dag():
    # Build a graph with a condition:
    #   input -> branch (if positive) -> add10
    #         -> branch (if negative) -> sub10
    #         -> merge
    
    # Register custom predicate for this test
    from sparsi.library.predicate_ops import register_predicate
    register_predicate("is_pos", lambda inputs: inputs.get("data") > 0)
    register_predicate("is_neg", lambda inputs: inputs.get("data") <= 0)

    b = Builder("cond_graph")
    b.vertex("in").op("ContextValOp").params({"key": "val"}).output("result", "data")
    
    b.vertex("pos_branch").op("MathAddOp").params({"b": 10}).condition("is_pos").condition_input("data").input("a", "data").output("result", "pos_res")
    b.vertex("neg_branch").op("MathAddOp").params({"b": -10}).condition("is_neg").condition_input("data").input("a", "data").output("result", "neg_res")
    
    b.vertex("merge").op("CoalesceOp").input("a", "pos_res").input("b", "neg_res").output("result", "final")
    
    graph = b.build()
    
    # Test positive
    engine = Engine(graph)
    await engine.run({"val": 5})
    res, _ = engine.get_output("final")
    assert res == 15
    assert engine.vertex_skipped("neg_branch")
    assert not engine.vertex_skipped("pos_branch")
    
    # Test negative
    engine = Engine(graph)
    await engine.run({"val": -5})
    res, _ = engine.get_output("final")
    assert res == -15
    assert engine.vertex_skipped("pos_branch")
    assert not engine.vertex_skipped("neg_branch")

@pytest.mark.asyncio
async def test_json_and_file_ops(tmp_path):
    # Create a temp json file
    p = tmp_path / "test.json"
    p.write_text('{"name": "sparsi", "version": 0.1}')
    
    b = Builder("json_file_graph")
    b.vertex("read").op("FileReadOp").params({"path": str(p)}).output("result", "raw_json")
    b.vertex("extract").op("JsonExtractOp").params({"path": "name"}).input("json_str", "raw_json").output("result", "name")
    
    graph = b.build()
    engine = Engine(graph)
    await engine.run({})
    
    name, _ = engine.get_output("name")
    assert name == "sparsi"
