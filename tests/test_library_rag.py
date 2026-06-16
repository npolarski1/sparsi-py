import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from dagor import Builder, Engine
import dagor.builtin
import sparsi.library
from sparsi.library.rag_ops import Document

@pytest.mark.asyncio
async def test_retrieve_op_mocked():
    # Mock retriever implementation
    class MockRetriever:
        async def retrieve(self, ctx, query, k):
            return [Document(id="m1", content="mock context", metadata={"source": "mock.md"})]
            
    # Register mock retriever
    from sparsi.library.rag_ops import register_retriever
    register_retriever("mock-ret", MockRetriever())
    
    b = Builder("rag_test")
    b.vertex("in").op("ContextValOp").params({"key": "query"}).output("result", "q_wire")
    b.vertex("ret").op("RetrieveOp").params({
        "retriever_id": "mock-ret",
        "k": 1
    }).input("query", "q_wire").output("results", "docs")
    
    graph = b.build()
    engine = Engine(graph)
    await engine.run({"query": "where is mock?"})
    
    res, ok = engine.get_output("docs")
    assert ok
    assert len(res) == 1
    assert res[0].content == "mock context"

@pytest.mark.asyncio
async def test_retrieve_with_filters_mocked():
    from sparsi.library.rag_ops import get_retrieval_filters
    
    class FilteredRetriever:
        async def retrieve(self, ctx, query, k):
            filters = get_retrieval_filters()
            return [Document(id="f1", content=f"filtered by {filters.get('cat')}", metadata={})]
            
    from sparsi.library.rag_ops import register_retriever
    register_retriever("filtered-ret", FilteredRetriever())
    
    b = Builder("rag_filter_test")
    b.vertex("in_q").op("ContextValOp").params({"key": "query"}).output("result", "q_wire")
    b.vertex("in_f").op("ContextValOp").params({"key": "filters"}).output("result", "f_wire")
    b.vertex("ret").op("RetrieveWithFiltersOp").params({
        "retriever_id": "filtered-ret",
        "k": 1
    }).input("query", "q_wire").input("filters", "f_wire").output("results", "docs")
    
    graph = b.build()
    engine = Engine(graph)
    await engine.run({"query": "q", "filters": {"cat": "tech"}})
    
    res, _ = engine.get_output("docs")
    assert res[0].content == "filtered by tech"

@pytest.mark.asyncio
async def test_validate_citations_op():
    docs = [
        Document(id="1", content="...", metadata={"source": "a.md"}),
        Document(id="2", content="...", metadata={"source": "b.md"})
    ]
    
    b = Builder("val_test")
    b.vertex("in_ans").op("ContextValOp").params({"key": "ans"}).output("result", "ans_wire")
    b.vertex("in_docs").op("ContextValOp").params({"key": "docs"}).output("result", "docs_wire")
    
    b.vertex("val").op("ValidateCitationsOp")\
        .input("answer", "ans_wire")\
        .input("documents", "docs_wire")\
        .output("validated_answer", "final")\
        .output("is_valid", "valid")
    
    graph = b.build()
    
    # Valid case
    engine = Engine(graph)
    await engine.run({"ans": "Source [a.md].", "docs": docs})
    v, _ = engine.get_output("valid")
    assert v is True
    
    # Invalid case
    engine = Engine(graph)
    await engine.run({"ans": "Source [c.md].", "docs": docs})
    v, _ = engine.get_output("valid")
    assert v is False
    f, _ = engine.get_output("final")
    assert "[Warning: Invalid citations: c.md]" in f
