import asyncio
import pytest
from dagor import Builder, Engine
from dagor.builtin import ContextValOp, CoalesceOp
import sparsi.library

@pytest.mark.asyncio
async def test_map_fanout():
    # input: [1, 2, 3] -> map (x * 10) -> [10, 20, 30]
    b = Builder("map_graph")
    b.vertex("in").op("ContextValOp").params({"key": "items"}).output("result", "data_list")
    
    # Define map vertex
    b.vertex("multiply").map_over("data_list", "item") \
        .vertex("op").op("MathMulOp").params({"b": 10}).input("a", "item").output("result", "out") \
        .collect_into("out", "final_list")
    
    graph = b.build()
    engine = Engine(graph)
    
    await engine.run({"items": [1, 2, 3]})
    
    res, ok = engine.get_output("final_list")
    assert ok
    assert res == [10, 20, 30]

@pytest.mark.asyncio
async def test_filter_fanout():
    # input: [1, 5, 15] -> filter (x > 10) -> [15]
    b = Builder("filter_graph")
    b.vertex("in").op("ContextValOp").params({"key": "items"}).output("result", "data_list")
    
    # Register a predicate for filtering
    from sparsi.library.predicate_ops import register_predicate
    register_predicate("is_gt_10", lambda inputs: inputs.get("item") > 10)
    
    b.vertex("sieve").filter_by("data_list", "item") \
        .vertex("check").op("PredicateIfNotEmptyOp").condition("is_gt_10").condition_input("item").input("val", "item").output("result", "keep") \
        .collect_into("keep", "filtered_list")
    
    graph = b.build()
    engine = Engine(graph)
    
    await engine.run({"items": [1, 5, 15]})
    
    res, ok = engine.get_output("filtered_list")
    assert ok
    assert res == [15]
