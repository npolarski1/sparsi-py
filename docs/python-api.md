# sparsi-py API

`sparsi-py` is a Python port of the Sparsi DAG execution engine. It uses `dagor` as the core engine and `pydantic` for operator definitions.

## Operator Implementation

Every operator must inherit from `dagor.Operator` and `pydantic.BaseModel`.

```python
from typing import Any, Dict
from pydantic import BaseModel
from dagor import Operator, register_operator, Input, Output

@register_operator("AddIntOp")
class AddIntOp(Operator, BaseModel):
    a: Input = 0
    b: Input = 0
    result: Output = 0

    async def run(self, ctx: Any) -> None:
        self.result = (self.a or 0) + (self.b or 0)
```

### Metadata Markers
- `Input`: Marker for fields that receive data from wires.
- `Output`: Marker for fields that produce data for wires.

## Building a Graph

Use the `Builder` to define your DAG.

```python
from dagor import Builder, Engine
import dagor.builtin
import sparsi.library

def build_graph():
    b = Builder("my_workflow")
    
    # Inject input from context
    b.vertex("in").op("ContextValOp").params({"key": "val"}).output("result", "data")
    
    # Process
    b.vertex("add").op("AddIntOp").params({"b": 10}).input("a", "data").output("result", "final")
    
    return b.build()

async def main():
    graph = build_graph()
    engine = Engine(graph)
    
    await engine.run({"val": 5})
    res, ok = engine.get_output("final")
    print(res) # 15
```

## Advanced Features

### Conditional Execution
Vertices can have conditions (predicates) attached.

```python
from sparsi.library.predicate_ops import register_predicate

register_predicate("is_positive", lambda inputs: inputs.get("data", 0) > 0)

b.vertex("pos_only").op("SomeOp").condition("is_positive").input("in", "data")
```

### Fan-out (Map/Filter)
Use `map_over` or `filter_by` to process lists in parallel.

```python
b.vertex("process_list").map_over("items_wire", "item")\
    .vertex("sub_op").op("UpperOp").input("text", "item").output("result", "up")\
    .collect_into("up", "processed_list")
```

### AI-Driven Recovery (WithRepair)
Wrap deterministic ops to handle and fix bad input using an LLM.

```python
b.vertex("parse").op("WithRepair").params({
    "inner_op_name": "JsonParseOp",
    "input_field": "json_str",
    "max_attempts": 3
}).input("json_str", "raw_wire").output("result", "parsed")
```

## Model Context Protocol (MCP)

### Hosting a Server
Use `run_dual_mode` to expose your workflow as an MCP tool.

```python
from sparsi import run_dual_mode

run_dual_mode("my_tool", build_graph, {"input": "ctx_key"})
```

### Calling other Servers
Use `MCPCallOp` to invoke tools from other MCP servers.

```python
b.vertex("call").op("MCPCallOp").params({
    "command": "npx",
    "args": ["@modelcontextprotocol/server-everything"],
    "tool_name": "echo"
}).input("input", "data").output("result", "echo_res")
```

## Environment Variables
- `GEMINI_API_KEY` (or `GOOGLE_API_KEY`): Required for Gemini-based operators.
- `ANTHROPIC_API_KEY`: Required for Claude-based operators.
