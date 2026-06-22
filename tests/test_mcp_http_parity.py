import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from sparsi.library.mcp_client import MCPClient
from sparsi.library.mcp_ops import MCPCallOp

@pytest.mark.asyncio
async def test_mcp_http_transport_selection():
    # Test that providing a URL selects sse_client
    client = MCPClient(url="http://example.com/sse")
    
    # Mock sse_client
    mock_sse = AsyncMock()
    mock_streams = (AsyncMock(), AsyncMock())
    mock_sse.__aenter__.return_value = mock_streams
    
    with patch("mcp.client.sse.sse_client", return_value=mock_sse) as sse_mock:
        # We also need to mock ClientSession to avoid it actually trying to initialize
        with patch("sparsi.library.mcp_client.ClientSession") as session_mock:
            session_inst = session_mock.return_value
            session_inst.__aenter__.return_value = session_inst
            session_inst.initialize = AsyncMock()
            
            await client.connect()
            
            sse_mock.assert_called_once_with("http://example.com/sse", headers={})

@pytest.mark.asyncio
async def test_mcp_call_op_with_url():
    op = MCPCallOp()
    op.setup({
        "url": "http://api.sparsi.ai/mcp",
        "tool_name": "search",
        "headers": {"Authorization": "Bearer token"}
    })
    
    assert op.url == "http://api.sparsi.ai/mcp"
    assert op.headers == {"Authorization": "Bearer token"}
    
    # Mock global_mcp_pool.acquire
    with patch("sparsi.library.mcp_ops.global_mcp_pool.acquire", new_callable=AsyncMock) as mock_acquire:
        mock_client = AsyncMock()
        mock_acquire.return_value = mock_client
        mock_client.call_tool.return_value = "results"
        
        await op.run({})
        
        mock_acquire.assert_called_once()
        args, kwargs = mock_acquire.call_args
        assert kwargs["url"] == "http://api.sparsi.ai/mcp"
        assert kwargs["headers"] == {"Authorization": "Bearer token"}

if __name__ == "__main__":
    asyncio.run(test_mcp_http_transport_selection())
    asyncio.run(test_mcp_call_op_with_url())
    print("All MCP HTTP tests passed!")
