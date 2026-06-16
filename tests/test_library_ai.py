import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from dagor import Builder, Engine
import dagor.builtin
import sparsi.library

@pytest.mark.asyncio
async def test_ai_best_match_mocked():
    with patch("sparsi.library.ai_ops.AIComputeOp", new_callable=MagicMock) as MockAI:
        mock_ai_instance = AsyncMock()
        MockAI.return_value = mock_ai_instance
        mock_ai_instance.result = "1"
        
        b = Builder("best_match_test")
        b.vertex("in_q").op("ContextValOp").params({"key": "q"}).output("result", "q_wire")
        b.vertex("in_c").op("ContextValOp").params({"key": "c"}).output("result", "c_wire")
        b.vertex("match").op("AIBestMatchOp").input("query", "q_wire").input("candidates", "c_wire").output("result", "best")
        
        graph = b.build()
        engine = Engine(graph)
        await engine.run({"q": "find the best fruit", "c": ["apple", "banana", "cherry"]})
        
        res, _ = engine.get_output("best")
        assert res == 1

@pytest.mark.asyncio
async def test_ai_extract_string_slice_mocked():
    with patch("sparsi.library.ai_ops.AIComputeOp", new_callable=MagicMock) as MockAI:
        mock_ai_instance = AsyncMock()
        MockAI.return_value = mock_ai_instance
        mock_ai_instance.result = "apple, banana, cherry"
        
        b = Builder("slice_extract_test")
        b.vertex("in").op("ContextValOp").params({"key": "txt"}).output("result", "txt_wire")
        b.vertex("ex").op("AIExtractStringSliceOp").input("input", "txt_wire").output("result", "items")
        
        graph = b.build()
        engine = Engine(graph)
        await engine.run({"txt": "I like apple, banana and cherry."})
        
        res, _ = engine.get_output("items")
        assert res == ["apple", "banana", "cherry"]

@pytest.mark.asyncio
async def test_ai_parse_number_mocked():
    with patch("sparsi.library.ai_ops.AIComputeOp", new_callable=MagicMock) as MockAI:
        mock_ai_instance = AsyncMock()
        MockAI.return_value = mock_ai_instance
        mock_ai_instance.result = "The value is 42.5"
        
        b = Builder("parse_num_test")
        b.vertex("in").op("ContextValOp").params({"key": "txt"}).output("result", "txt_wire")
        b.vertex("parse").op("AIParseNumberOp").input("input", "txt_wire").output("result", "num")
        
        graph = b.build()
        engine = Engine(graph)
        await engine.run({"txt": "Price is 42.5 dollars"})
        
        res, _ = engine.get_output("num")
        assert res == 42.5

@pytest.mark.asyncio
async def test_ai_extract_map_mocked():
    with patch("sparsi.library.ai_ops.AIComputeOp", new_callable=MagicMock) as MockAI:
        mock_ai_instance = AsyncMock()
        MockAI.return_value = mock_ai_instance
        mock_ai_instance.result = '{"name": "sparsi", "version": "0.1"}'
        
        b = Builder("extract_map_test")
        b.vertex("in").op("ContextValOp").params({"key": "txt"}).output("result", "txt_wire")
        b.vertex("ex").op("AIExtractMapOp").input("input", "txt_wire").output("result", "data")
        
        graph = b.build()
        engine = Engine(graph)
        await engine.run({"txt": "Sparsi version 0.1"})
        
        res, _ = engine.get_output("data")
        assert res == {"name": "sparsi", "version": "0.1"}

@pytest.mark.asyncio
async def test_ai_bool_mocked():
    with patch("sparsi.library.ai_ops.AIComputeOp", new_callable=MagicMock) as MockAI:
        mock_ai_instance = AsyncMock()
        MockAI.return_value = mock_ai_instance
        mock_ai_instance.result = "True"
        
        b = Builder("bool_test")
        b.vertex("in").op("ContextValOp").params({"key": "txt"}).output("result", "txt_wire")
        b.vertex("b").op("AIBoolOp").params({"predicate": "is it true?"}).input("input", "txt_wire").output("result", "out")
        
        graph = b.build()
        engine = Engine(graph)
        await engine.run({"txt": "some text"})
        
        res, _ = engine.get_output("out")
        assert res is True

@pytest.mark.asyncio
async def test_ai_rerank_mocked():
    with patch("sparsi.library.ai_ops.AIComputeOp", new_callable=MagicMock) as MockAI:
        mock_ai_instance = AsyncMock()
        MockAI.return_value = mock_ai_instance
        mock_ai_instance.result = "1, 0"
        
        b = Builder("rerank_test")
        b.vertex("in_q").op("ContextValOp").params({"key": "q"}).output("result", "q_wire")
        b.vertex("in_c").op("ContextValOp").params({"key": "c"}).output("result", "c_wire")
        b.vertex("r").op("AIRerankOp").input("query", "q_wire").input("candidates", "c_wire").output("result", "order")
        
        graph = b.build()
        engine = Engine(graph)
        await engine.run({"q": "best", "c": ["bad", "good"]})
        
        res, _ = engine.get_output("order")
        assert res == [1, 0]

@pytest.mark.asyncio
async def test_ai_summarize_mocked():
    with patch("sparsi.library.ai_ops.AIComputeOp", new_callable=MagicMock) as MockAI:
        mock_ai_instance = AsyncMock()
        MockAI.return_value = mock_ai_instance
        mock_ai_instance.result = "short"
        
        b = Builder("sum_test")
        b.vertex("in").op("ContextValOp").params({"key": "text"}).output("result", "text_wire")
        b.vertex("s").op("AISummarizeOp").params({"operation": "sum"}).input("input", "text_wire").output("result", "summary")
        
        graph = b.build()
        engine = Engine(graph)
        await engine.run({"text": "long long text"})
        
        res, _ = engine.get_output("summary")
        assert res == "short"

@pytest.mark.asyncio
async def test_ai_score_mocked():
    with patch("sparsi.library.ai_ops.AIComputeOp", new_callable=MagicMock) as MockAI:
        mock_ai_instance = AsyncMock()
        MockAI.return_value = mock_ai_instance
        mock_ai_instance.result = "0.85"
        
        b = Builder("score_test")
        b.vertex("in").op("ContextValOp").params({"key": "txt"}).output("result", "txt_wire")
        b.vertex("score").op("AIScoreOp").params({"criterion": "politeness"}).input("input", "txt_wire").output("result", "score_out")
        
        graph = b.build()
        engine = Engine(graph)
        await engine.run({"txt": "hello sir"})
        
        res, _ = engine.get_output("score_out")
        assert res == 0.85

@pytest.mark.asyncio
async def test_ai_classify_multi_label_mocked():
    with patch("sparsi.library.ai_ops.AIComputeOp", new_callable=MagicMock) as MockAI:
        mock_ai_instance = AsyncMock()
        MockAI.return_value = mock_ai_instance
        mock_ai_instance.result = "tech, business"
        
        b = Builder("classify_test")
        b.vertex("in").op("ContextValOp").params({"key": "text"}).output("result", "text_wire")
        b.vertex("c").op("AIClassifyMultiLabelOp").params({
            "categories": ["tech", "business", "life"]
        }).input("input", "text_wire").output("result", "labels")
        
        graph = b.build()
        engine = Engine(graph)
        await engine.run({"text": "startup news"})
        
        res, _ = engine.get_output("labels")
        assert res == ["tech", "business"]
