import pytest
from dagor import Builder, Engine
import dagor.builtin
import sparsi.library

@pytest.mark.asyncio
async def test_json_extract_nested():
    b = Builder("json_nest_test")
    b.vertex("in").op("ContextValOp").params({"key": "data"}).output("result", "json_wire")
    b.vertex("ex").op("JsonExtractOp").params({"path": "users.1.name"}).input("json_str", "json_wire").output("result", "user_name")
    
    graph = b.build()
    engine = Engine(graph)
    
    data = {
        "users": [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]
    }
    await engine.run({"data": data})
    
    name, _ = engine.get_output("user_name")
    assert name == "Bob"

@pytest.mark.asyncio
async def test_json_parse_valid():
    b = Builder("json_parse_test")
    b.vertex("in").op("ContextValOp").params({"key": "raw"}).output("result", "raw_wire")
    b.vertex("parse").op("JsonParseOp").input("json_str", "raw_wire").output("result", "parsed")
    
    graph = b.build()
    engine = Engine(graph)
    
    await engine.run({"raw": '{"score": 42}'})
    res, _ = engine.get_output("parsed")
    assert res == {"score": 42}

@pytest.mark.asyncio
async def test_json_parse_invalid_raises_repairable():
    from sparsi.library.repair import ErrRepairable
    
    b = Builder("json_fail_test")
    b.vertex("parse").op("JsonParseOp").params({"json_str": '{"broken": '}).output("result", "parsed")
    
    graph = b.build()
    engine = Engine(graph)
    
    with pytest.raises(ErrRepairable) as excinfo:
        await engine.run({})
    
    assert "Invalid JSON" in str(excinfo.value)
