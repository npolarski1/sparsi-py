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
Always declare the mapping in the `run_dual_mode` call.

## Dual-mode entrypoint
Always use `sparsi.run_dual_mode` for the `main()` entrypoint.

# Steps

1.  **Strict Adherence**: Implement the approved design EXACTLY.
2.  **Imports**: Import `asyncio`, `dagor`, and `sparsi.library`.
3.  **Graph Construction**: Define a `build_graph()` function.
4.  **Operator Registration**: Use `@register_operator` for custom ops.
5.  **Main**: Use `run_dual_mode` to support both CLI and MCP.

# Example structure

```python
import asyncio
from dagor import Builder, register_operator, Operator, Input, Output
from sparsi import run_dual_mode
from pydantic import BaseModel
import sparsi.library

def build_graph():
    b = Builder("hello_workflow")
    b.vertex("in").op("ContextValOp").params({"key": "name"}).output("result", "name_wire")
    b.vertex("greet").op("StringConcatOp").params({"a": "Hello, "}).input("b", "name_wire").output("result", "final_result")
    return b

if __name__ == "__main__":
    run_dual_mode("hello_tool", build_graph, {"name": "name"})
```
