import asyncio
import pytest
import os
from unittest.mock import MagicMock, AsyncMock
from sparsi.library.ai_ops import AIComputeOp
from sparsi.library.reasoning import ReasoningLog

@pytest.mark.asyncio
async def test_ai_compute_reasoning_parsing():
    # Setup context with reasoning enabled and a log
    log = ReasoningLog()
    ctx = {"reasoning": True, "reasoning_log": log}
    
    op = AIComputeOp(prompt="What is 2+2?", system="Be helpful")
    
    # Mock _run_gemini to return a JSON reasoning envelope
    # We mock the internal _run_gemini to avoid actual API calls
    op._run_gemini = AsyncMock()
    op.result = '{"result": "4", "reasoning": "Simple addition of two and two equals four."}'
    
    await op.run(ctx)
    
    # Verify result was extracted
    assert op.result == "4"
    
    # Verify reasoning was logged
    entries = log.entries()
    assert len(entries) == 1
    assert entries[0].reasoning == "Simple addition of two and two equals four."
    assert entries[0].output == "4"
    assert entries[0].op == "AIComputeOp"

@pytest.mark.asyncio
async def test_ai_compute_reasoning_fence_stripping():
    log = ReasoningLog()
    ctx = {"reasoning": True, "reasoning_log": log}
    
    op = AIComputeOp(prompt="test")
    op._run_gemini = AsyncMock()
    # Test with markdown fences
    op.result = '```json\n{"result": "ok", "reasoning": "done"}\n```'
    
    await op.run(ctx)
    
    assert op.result == "ok"
    assert log.entries()[0].reasoning == "done"

if __name__ == "__main__":
    asyncio.run(test_ai_compute_reasoning_parsing())
    asyncio.run(test_ai_compute_reasoning_fence_stripping())
    print("All tests passed!")
