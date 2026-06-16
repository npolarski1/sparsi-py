import pytest
import os
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from dagor import Builder, Engine
import dagor.builtin
import sparsi.library
from sparsi.library.reasoning import ReasoningLog

import datetime
from datetime import tzinfo, timedelta

class MockTz(tzinfo):
    def utcoffset(self, dt): return timedelta(hours=9)
    def dst(self, dt): return timedelta(0)
    def tzname(self, dt): return "JST"

@pytest.mark.asyncio
async def test_city_time_op():
    # Mock ZoneInfo to avoid tzdata dependency issues on all platforms
    with patch("zoneinfo.ZoneInfo", return_value=MockTz()):
        b = Builder("time_test")
        b.vertex("time").op("CityTimeOp").params({"city": "Tokyo"}).output("result", "tokyo_time")
        
        graph = b.build()
        engine = Engine(graph)
        await engine.run({})
        
        res, ok = engine.get_output("tokyo_time")
        assert ok
        assert isinstance(res, str)
        assert "+09:00" in res or "JST" in res or "T" in res

@pytest.mark.asyncio
async def test_env_op():
    os.environ["SPARSI_TEST_VAR"] = "present"
    b = Builder("env_test")
    # EnvOp output field is 'value', not 'result'
    b.vertex("env").op("EnvOp").params({"name": "SPARSI_TEST_VAR"}).output("value", "val")
    
    graph = b.build()
    engine = Engine(graph)
    await engine.run({})
    
    res, _ = engine.get_output("val")
    assert res == "present"

@pytest.mark.asyncio
async def test_const_op():
    b = Builder("const_test")
    b.vertex("c").op("ConstOp").params({"value": "fixed"}).output("result", "out")
    
    graph = b.build()
    engine = Engine(graph)
    await engine.run({})
    
    res, _ = engine.get_output("out")
    assert res == "fixed"

@pytest.mark.asyncio
async def test_file_read_op(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("hello sparsi", encoding="utf-8")
    
    b = Builder("file_test")
    b.vertex("read").op("FileReadOp").params({"path": str(f)}).output("result", "content")
    
    graph = b.build()
    engine = Engine(graph)
    await engine.run({})
    
    res, _ = engine.get_output("content")
    assert res == "hello sparsi"

@pytest.mark.asyncio
async def test_embedding_op_mocked():
    # We mock the factory to avoid API calls
    mock_client = MagicMock()
    mock_client.embed = MagicMock(return_value=asyncio.Future())
    mock_client.embed.return_value.set_result([[0.1, 0.2]])
    
    mock_factory = MagicMock()
    mock_factory.embedder = MagicMock(return_value=asyncio.Future())
    mock_factory.embedder.return_value.set_result(mock_client)
    
    with patch("sparsi.library.embedding_ops._default_embedding_factory", mock_factory):
        b = Builder("embed_test")
        b.vertex("embed").op("EmbeddingOp").params({"input": "test text"}).output("embeddings", "vecs")
        
        graph = b.build()
        engine = Engine(graph)
        await engine.run({})
        
        res, _ = engine.get_output("vecs")
        assert res == [[0.1, 0.2]]

@pytest.mark.asyncio
async def test_http_get_op_mocked():
    mock_resp = MagicMock()
    mock_resp.text = "body content"
    mock_resp.status_code = 200
    
    # We need to mock the AsyncClient's get method
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        
        b = Builder("http_test")
        b.vertex("get").op("HTTPGetOp").params({"url": "http://example.com"}).output("body", "res_body")
        
        graph = b.build()
        engine = Engine(graph)
        await engine.run({})
        
        res, _ = engine.get_output("res_body")
        assert res == "body content"
        mock_get.assert_called_with("http://example.com")

@pytest.mark.asyncio
async def test_reasoning_log_integration():
    # A simple custom op that records reasoning
    from sparsi.library.reasoning import record_reasoning
    from dagor import Operator, register_operator
    from pydantic import BaseModel
    
    @register_operator("ReasoningOp")
    class ReasoningOp(Operator, BaseModel):
        async def run(self, ctx: Any) -> None:
            record_reasoning(ctx, "ReasoningOp", {}, "ok", "I reasoned well.")
    
    b = Builder("reason_test")
    b.vertex("r").op("ReasoningOp")
    
    graph = b.build()
    log = ReasoningLog()
    engine = Engine(graph)
    
    await engine.run({"reasoning_log": log})
    
    entries = log.entries()
    assert len(entries) == 1
    assert entries[0].op == "ReasoningOp"
    assert entries[0].reasoning == "I reasoned well."
