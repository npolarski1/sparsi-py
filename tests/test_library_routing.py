import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from dagor import Builder, Engine
import dagor.builtin
import sparsi.library

@pytest.mark.asyncio
async def test_mode_select_op_mocked():
    # Mock _run_gemini since ModeSelectOp calls it internally
    with patch("sparsi.library.routing_ops.ModeSelectOp._run_gemini", new_callable=AsyncMock) as mock_gemini:
        mock_gemini.return_value = "tech"
        
        b = Builder("mode_test")
        b.vertex("in").op("ContextValOp").params({"key": "txt"}).output("result", "txt_wire")
        b.vertex("mode").op("ModeSelectOp").params({
            "categories": "tech, business, life"
        }).input("input", "txt_wire").output("result", "selected")
        
        graph = b.build()
        engine = Engine(graph)
        
        await engine.run({"txt": "some tech stuff"})
        
        res, _ = engine.get_output("selected")
        assert res == "tech"
        mock_gemini.assert_called()

@pytest.mark.asyncio
async def test_if_string_eq_op():
    b = Builder("str_eq_test")
    b.vertex("in_a").op("ContextValOp").params({"key": "a"}).output("result", "a_wire")
    b.vertex("in_b").op("ContextValOp").params({"key": "b"}).output("result", "b_wire")
    b.vertex("eq").op("IfStringEqOp").input("a", "a_wire").input("b", "b_wire").output("match", "is_eq")
    
    graph = b.build()
    engine = Engine(graph)
    
    await engine.run({"a": "foo", "b": "foo"})
    res, _ = engine.get_output("is_eq")
    assert res is True
    
    await engine.run({"a": "foo", "b": "bar"})
    res, _ = engine.get_output("is_eq")
    assert res is False
