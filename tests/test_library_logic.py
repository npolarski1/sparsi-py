import pytest
from dagor import Builder, Engine
import dagor.builtin
import sparsi.library

@pytest.mark.asyncio
async def test_slice_ops():
    b = Builder("slice_test")
    b.vertex("in").op("ContextValOp").params({"key": "list_in"}).output("result", "list_wire")
    b.vertex("len").op("SliceLenOp").input("input", "list_wire").output("result", "length")
    b.vertex("first").op("SliceFirstOp").input("input", "list_wire").output("result", "first_val")
    b.vertex("last").op("SliceLastOp").input("input", "list_wire").output("result", "last_val")
    b.vertex("at").op("SliceAtOp").params({"index": 1}).input("input", "list_wire").output("result", "at_1")
    b.vertex("contains").op("SliceContainsOp").params({"value": "b"}).input("input", "list_wire").output("match", "has_b")
    b.vertex("filter").op("SliceFilterEqOp").params({"value": "a"}).input("input", "list_wire").output("result", "filtered")
    
    graph = b.build()
    engine = Engine(graph)
    await engine.run({"list_in": ["a", "b", "c", "a"]})
    
    length, _ = engine.get_output("length")
    assert length == 4
    
    first, _ = engine.get_output("first_val")
    assert first == "a"
    
    last, _ = engine.get_output("last_val")
    assert last == "a"
    
    at1, _ = engine.get_output("at_1")
    assert at1 == "b"
    
    has_b, _ = engine.get_output("has_b")
    assert has_b is True
    
    filtered, _ = engine.get_output("filtered")
    assert filtered == ["a", "a"]

@pytest.mark.asyncio
async def test_slice_sort_indices_op():
    b = Builder("sort_test")
    b.vertex("in_scores").op("ContextValOp").params({"key": "scores"}).output("result", "scores_wire")
    b.vertex("sort").op("SliceTopKOp").params({"k": 2}).input("scores", "scores_wire").output("result", "top_k")
    
    graph = b.build()
    engine = Engine(graph)
    
    # Sort indices by score descending
    await engine.run({"scores": [10, 50, 30]})
    res, _ = engine.get_output("top_k")
    assert res == [1, 2] # Index 1 is 50, Index 2 is 30

@pytest.mark.asyncio
async def test_switch_string_op():
    b = Builder("switch_test")
    b.vertex("in").op("ContextValOp").params({"key": "input_key"}).output("result", "key_wire")
    b.vertex("sw").op("SwitchStringOp").params({
        "cases": {"a": "Apple", "b": "Banana"},
        "default": "Unknown"
    }).input("key", "key_wire").output("result", "out")
    
    graph = b.build()
    engine = Engine(graph)
    
    await engine.run({"input_key": "a"})
    res, _ = engine.get_output("out")
    assert res == "Apple"
    
    await engine.run({"input_key": "c"})
    res, _ = engine.get_output("out")
    assert res == "Unknown"

@pytest.mark.asyncio
async def test_slice_join_op():
    b = Builder("join_test")
    b.vertex("in").op("ContextValOp").params({"key": "items"}).output("result", "items_wire")
    b.vertex("join").op("SliceJoinOp").params({"sep": "-"}).input("input", "items_wire").output("result", "out")
    
    graph = b.build()
    engine = Engine(graph)
    await engine.run({"items": ["a", "b", "c"]})
    res, _ = engine.get_output("out")
    assert res == "a-b-c"

@pytest.mark.asyncio
async def test_bool_ops():
    b = Builder("bool_test")
    b.vertex("and").op("BoolAndOp").params({"a": True, "b": False}).output("result", "and_res")
    b.vertex("or").op("BoolOrOp").params({"a": True, "b": False}).output("result", "or_res")
    b.vertex("not").op("BoolNotOp").params({"val": True}).output("result", "not_res")
    
    graph = b.build()
    engine = Engine(graph)
    await engine.run({})
    
    and_res, _ = engine.get_output("and_res")
    assert and_res is False
    
    or_res, _ = engine.get_output("or_res")
    assert or_res is True
    
    not_res, _ = engine.get_output("not_res")
    assert not_res is False

@pytest.mark.asyncio
async def test_select_ops():
    b = Builder("select_test")
    b.vertex("in_val").op("ContextValOp").params({"key": "missing"}).output("result", "missing_wire")
    b.vertex("in_cond").op("ContextValOp").params({"key": "condition"}).output("result", "cond_wire")
    
    b.vertex("default").op("DefaultStringOp").params({"default": "fallback"}).input("value", "missing_wire").output("result", "with_default")
    b.vertex("sel").op("SelectStringOp").params({"if_true": "YES", "if_false": "NO"}).input("cond", "cond_wire").output("result", "selected")
    
    graph = b.build()
    engine = Engine(graph)
    
    # Test with None value for default
    await engine.run({"missing": None, "condition": True})
    d, _ = engine.get_output("with_default")
    assert d == "fallback"
    s, _ = engine.get_output("selected")
    assert s == "YES"
    
    # Test with actual value for default
    await engine.run({"missing": "actual", "condition": False})
    d, _ = engine.get_output("with_default")
    assert d == "actual"
    s, _ = engine.get_output("selected")
    assert s == "NO"

@pytest.mark.asyncio
async def test_numeric_select_and_default():
    b = Builder("num_select")
    b.vertex("in_c").op("ContextValOp").params({"key": "c"}).output("result", "c_wire")
    b.vertex("in_v").op("ContextValOp").params({"key": "v"}).output("result", "v_wire")
    
    b.vertex("sel_i").op("SelectIntOp").params({"if_true": 10, "if_false": 20}).input("cond", "c_wire").output("result", "out_i")
    b.vertex("def_f").op("DefaultFloatOp").params({"default": 1.1}).input("value", "v_wire").output("result", "out_f")
    b.vertex("sel_b").op("SelectBoolOp").params({"if_true": True, "if_false": False}).input("cond", "c_wire").output("result", "out_b")
    
    graph = b.build()
    engine = Engine(graph)
    
    await engine.run({"c": True, "v": None})
    i, _ = engine.get_output("out_i")
    f, _ = engine.get_output("out_f")
    b_val, _ = engine.get_output("out_b")
    assert i == 10
    assert f == 1.1
    assert b_val is True
    
    await engine.run({"c": False, "v": 2.2})
    i, _ = engine.get_output("out_i")
    f, _ = engine.get_output("out_f")
    assert i == 20
    assert f == 2.2

@pytest.mark.asyncio
async def test_extra_select_and_default():
    b = Builder("extra_select")
    b.vertex("in_c").op("ContextValOp").params({"key": "c"}).output("result", "c_wire")
    b.vertex("in_v").op("ContextValOp").params({"key": "v"}).output("result", "v_wire")
    
    b.vertex("sel_f").op("SelectFloatOp").params({"if_true": 1.5, "if_false": 2.5}).input("cond", "c_wire").output("result", "out_f")
    b.vertex("def_i").op("DefaultIntOp").params({"default": 42}).input("value", "v_wire").output("result", "out_i")
    
    graph = b.build()
    engine = Engine(graph)
    
    await engine.run({"c": True, "v": None})
    f, _ = engine.get_output("out_f")
    i, _ = engine.get_output("out_i")
    assert f == 1.5
    assert i == 42
    
    await engine.run({"c": False, "v": 7})
    f, _ = engine.get_output("out_f")
    i, _ = engine.get_output("out_i")
    assert f == 2.5
    assert i == 7
