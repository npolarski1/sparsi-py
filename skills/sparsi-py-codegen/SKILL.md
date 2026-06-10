---
name: sparsi-py-codegen
description: Generate a runnable Python workflow from an approved sparsi-py DAG design
version: 0.1.0
library_version: sparsi-py v0.1.0
triggers: [sparsi py codegen, generate python workflow]
input:
  design: {type: string, description: "Approved DAG design", required: true}
---

# Context

You are generating Python source code for a sparsi-py DAG workflow from an approved design.
The output must use `asyncio` and `pydantic`.

# Implementation Rules

## Builder DSL
Use the fluent `dagor.Builder` API:
```python
b = Builder("workflow_name")
b.vertex("v1").op("OpName").params({"key": "val"}).input("in_field", "wire").output("out_field", "out_wire")
```

## Input Injection
Use `ContextValOp` to read from the `initial_wires` dict passed to `engine.run()`.

## Dual-mode main
Always include a `main()` that supports `--mcp` for serving the workflow as an MCP tool.

# Example Structure

```python
import asyncio
from dagor import Builder, Engine, Reporter
import sparsi.library

async def run_workflow(inputs):
    b = Builder("my_workflow")
    # ... build graph ...
    engine = Engine(b.build(), reporter=Reporter())
    await engine.run(inputs)
    return engine.get_output("final")
```
