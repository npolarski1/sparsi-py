import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from dagor import Builder, Engine
import dagor.builtin
import sparsi.library
from sparsi.library.mcp_pool import global_mcp_pool

@pytest.mark.asyncio
async def test_mcp_call_op_mocked():
    # Mock the MCP pool and client
    mock_client = AsyncMock()
    mock_client.call_tool.return_value = "mock response"
    mock_client.disconnect = AsyncMock()
    
    mock_pool = MagicMock()
    mock_pool.acquire = AsyncMock(return_value=mock_client)
    
    with patch("sparsi.library.mcp_ops.global_mcp_pool", mock_pool):
        b = Builder("mcp_test")
        b.vertex("call").op("MCPCallOp").params({
            "command": "npx",
            "args": ["some-server"],
            "tool_name": "some-tool"
        }).input("input", "tool_args").output("result", "tool_res")
        
        graph = b.build()
        engine = Engine(graph)
        
        # Inject tool_args wire directly
        await engine.run({}, initial_wires={"tool_args": {"input": "foo"}})
        
        res, _ = engine.get_output("tool_res")
        assert res == "mock response"
        
        # Verify call_tool was called correctly
        mock_client.call_tool.assert_called_with("some-tool", {"input": "foo"})

@pytest.mark.asyncio
async def test_mcp_script_op_mocked():
    mock_client = AsyncMock()
    mock_client.call_tool.return_value = "script response"
    mock_client.disconnect = AsyncMock()
    
    mock_pool = MagicMock()
    mock_pool.acquire = AsyncMock(return_value=mock_client)
    
    with patch("sparsi.library.mcp_ops.global_mcp_pool", mock_pool):
        b = Builder("mcp_script_test")
        b.vertex("script").op("MCPScriptOp").params({
            "command": "npx",
            "tool_name": "some-tool"
        }).input("arguments", "script_args").output("result", "script_res")
        
        graph = b.build()
        engine = Engine(graph)
        
        # Inject script_args wire directly
        await engine.run({}, initial_wires={"script_args": {"a": 1}})
        
        res, _ = engine.get_output("script_res")
        assert res == "script response"
