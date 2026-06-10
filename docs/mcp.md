# MCP Integration

`MCPCallOp` and `MCPScriptOp` invoke an MCP server (local subprocess via stdio) as a workflow step.

## Persistent MCP Pool

By default, every Model Context Protocol tool call starts a fresh subprocess and tears it down on completion. When the cold start dominates execution time, opt into the persistent pool by setting `pool_size` on the vertex params.

```python
b.vertex("call_tool").op("MCPCallOp").params({
    "command": "node",
    "args": ["server.js"],
    "tool_name": "my_tool",
    "pool_size": 3  # Keep 3 instances warm
}).input("input", "data").output("result", "tool_res")
```

The pool keeps sessions ready and replenishes them in the background after each use, ensuring subsequent vertices skip the cold start.

## Using the MCP Client

You can also use the `MCPClient` class directly in your custom operators or scripts for more fine-grained control:

```python
from sparsi.library.mcp_client import MCPClient

client = MCPClient("node", ["server.js"])
await client.connect()
result = await client.call_tool("my_tool", {"arg1": "val"})
await client.disconnect()
```
