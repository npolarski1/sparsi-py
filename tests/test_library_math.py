import pytest
from dagor import Builder, Engine
import dagor.builtin
import sparsi.library

@pytest.mark.asyncio
async def test_math_float_ops():
    b = Builder("float_test")
    b.vertex("add").op("AddFloatOp").params({"a": 1.5, "b": 2.5}).output("result", "sum")
    b.vertex("sub").op("SubFloatOp").input("a", "sum").params({"b": 1.0}).output("result", "diff")
    b.vertex("mul").op("MulFloatOp").input("a", "diff").params({"b": 2.0}).output("result", "prod")
    b.vertex("div").op("DivFloatOp").input("a", "prod").params({"b": 3.0}).output("result", "quot")
    b.vertex("clamp").op("ClampFloatOp").input("value", "quot").params({"min": 0.0, "max": 1.0}).output("result", "clamped")
    
    graph = b.build()
    engine = Engine(graph)
    await engine.run({})
    
    # (1.5 + 2.5) = 4.0
    # 4.0 - 1.0 = 3.0
    # 3.0 * 2.0 = 6.0
    # 6.0 / 3.0 = 2.0
    # clamp(2.0, 0, 1) = 1.0
    res, _ = engine.get_output("clamped")
    assert res == 1.0

@pytest.mark.asyncio
async def test_math_int_ops():
    b = Builder("int_test")
    b.vertex("add").op("AddIntOp").params({"a": 10, "b": 20}).output("result", "sum")
    b.vertex("mod").op("ModIntOp").input("a", "sum").params({"b": 7}).output("result", "remainder")
    
    graph = b.build()
    engine = Engine(graph)
    await engine.run({})
    
    # (10 + 20) % 7 = 30 % 7 = 2
    res, _ = engine.get_output("remainder")
    assert res == 2

@pytest.mark.asyncio
async def test_math_predicates():
    b = Builder("pred_test")
    b.vertex("gt").op("IfIntGtOp").params({"a": 10, "b": 5}).output("match", "is_gt")
    b.vertex("between").op("BetweenFloatOp").params({"value": 0.5, "min": 0.0, "max": 1.0}).output("match", "is_between")
    
    graph = b.build()
    engine = Engine(graph)
    await engine.run({})
    
    gt, _ = engine.get_output("is_gt")
    assert gt is True
    
    between, _ = engine.get_output("is_between")
    assert between is True

@pytest.mark.asyncio
async def test_aggregate_math():
    b = Builder("agg_test")
    b.vertex("sum").op("SumIntOp").params({"values": [1, 2, 3, 4]}).output("result", "total")
    b.vertex("max").op("MaxIntOp").params({"values": [1, 5, 2]}).output("result", "maximum")
    
    graph = b.build()
    engine = Engine(graph)
    await engine.run({})
    
    total, _ = engine.get_output("total")
    assert total == 10
    
    maximum, _ = engine.get_output("maximum")
    assert maximum == 5

@pytest.mark.asyncio
async def test_math_misc():
    b = Builder("math_misc")
    b.vertex("in").op("ContextValOp").params({"key": "in_val"}).output("result", "in_wire")
    b.vertex("round").op("RoundOp").params({"value": 3.6}).output("result", "rounded")
    b.vertex("clamp").op("ClampIntOp").params({"min": 0, "max": 10}).input("value", "in_wire").output("result", "clamped")
    
    graph = b.build()
    engine = Engine(graph)
    
    await engine.run({"in_val": 15})
    r, _ = engine.get_output("rounded")
    assert r == 4
    
    c, _ = engine.get_output("clamped")
    assert c == 10
    
    await engine.run({"in_val": -5})
    c, _ = engine.get_output("clamped")
    assert c == 0

@pytest.mark.asyncio
async def test_math_pow_min_max():
    b = Builder("math_ext")
    b.vertex("pow").op("PowIntOp").params({"a": 2, "b": 3}).output("result", "p")
    b.vertex("min").op("MinIntOp").params({"values": [10, 5, 8]}).output("result", "mi")
    b.vertex("max_f").op("MaxFloatOp").params({"values": [1.1, 5.5, 2.2]}).output("result", "ma")
    
    graph = b.build()
    engine = Engine(graph)
    await engine.run({})
    
    assert engine.get_output("p")[0] == 8
    assert engine.get_output("mi")[0] == 5
    assert engine.get_output("ma")[0] == 5.5

@pytest.mark.asyncio
async def test_math_casts_and_pack():
    b = Builder("math_casts")
    b.vertex("f2i").op("Float64ToIntOp").params({"value": 3.9}).output("result", "i")
    b.vertex("i2f").op("IntToFloat64Op").params({"value": 5}).output("result", "f")
    b.vertex("pack").op("PackMathOperandsOp").input("a", "f").input("b", "i").output("result", "packed")
    
    graph = b.build()
    engine = Engine(graph)
    await engine.run({})
    
    assert engine.get_output("i")[0] == 3
    assert engine.get_output("f")[0] == 5.0
    assert engine.get_output("packed")[0] == {"a": 5.0, "b": 3.0}

@pytest.mark.asyncio
async def test_math_all_predicates():
    b = Builder("math_preds")
    # Int predicates
    b.vertex("i_eq").op("IfIntEqOp").params({"a": 5, "b": 5}).output("match", "i_eq")
    b.vertex("i_gt").op("IfIntGtOp").params({"a": 6, "b": 5}).output("match", "i_gt")
    b.vertex("i_lt").op("IfIntLtOp").params({"a": 4, "b": 5}).output("match", "i_lt")
    b.vertex("i_ge").op("IfIntGeOp").params({"a": 5, "b": 5}).output("match", "i_ge")
    b.vertex("i_le").op("IfIntLeOp").params({"a": 5, "b": 5}).output("match", "i_le")
    
    # Float predicates
    b.vertex("f_eq").op("IfFloatEqOp").params({"a": 5.5, "b": 5.5}).output("match", "f_eq")
    b.vertex("f_gt").op("IfFloatGtOp").params({"a": 5.6, "b": 5.5}).output("match", "f_gt")
    b.vertex("f_lt").op("IfFloatLtOp").params({"a": 5.4, "b": 5.5}).output("match", "f_lt")
    b.vertex("f_ge").op("IfFloatGeOp").params({"a": 5.5, "b": 5.5}).output("match", "f_ge")
    b.vertex("f_le").op("IfFloatLeOp").params({"a": 5.5, "b": 5.5}).output("match", "f_le")
    
    graph = b.build()
    engine = Engine(graph)
    await engine.run({})
    
    for wire in ["i_eq", "i_gt", "i_lt", "i_ge", "i_le", "f_eq", "f_gt", "f_lt", "f_ge", "f_le"]:
        val, ok = engine.get_output(wire)
        assert ok and val is True, f"Wire {wire} should be True"

@pytest.mark.asyncio
async def test_math_float_aggregates():
    b = Builder("float_agg")
    b.vertex("sum").op("SumFloatOp").params({"values": [1.1, 2.2, 3.3]}).output("result", "s")
    b.vertex("min").op("MinFloatOp").params({"values": [1.1, 2.2, 3.3]}).output("result", "mi")
    b.vertex("max").op("MaxFloatOp").params({"values": [1.1, 2.2, 3.3]}).output("result", "ma")
    
    graph = b.build()
    engine = Engine(graph)
    await engine.run({})
    
    s, _ = engine.get_output("s")
    assert abs(s - 6.6) < 0.001
    assert engine.get_output("mi")[0] == 1.1
    assert engine.get_output("ma")[0] == 3.3
