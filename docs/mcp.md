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

## Hosting MCP Servers

Every Sparsi workflow can be hosted as an MCP server. The `run_dual_mode` helper allows your script to act either as a CLI tool or as an MCP server.

```python
from dagor import Builder
from sparsi import run_dual_mode
import dagor.builtin
import sparsi.library

def build_graph():
    b = Builder("my_tool")
    b.vertex("in").op("ContextValOp").params({"key": "val"}).output("result", "in_wire")
    # ... logic
    b.vertex("out").op("SomeOp").input("in", "in_wire").output("result", "final_result")
    return b

if __name__ == "__main__":
    # Map MCP argument 'input' to ContextValOp key 'val'
    # The 'final_result' wire will be returned as the tool result.
    run_dual_mode("my_tool", build_graph, {"input": "val"}, output_wire="final_result")
```

Run as CLI:
```bash
python my_script.py --input "hello"
```

Run as MCP Server (via stdio):
```bash
python my_script.py --mcp
```

## Using the MCP Client

You can also use the `MCPClient` class directly in your custom operators or scripts for more fine-grained control:

```python
from sparsi.library.mcp_client import MCPClient

client = MCPClient("node", ["server.js"])
await client.connect()
result = await client.call_tool("my_tool", {"arg1": "val"})
await client.disconnect()
```
