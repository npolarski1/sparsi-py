# Core Concepts

## The DAG model

Workflows are Directed Acyclic Graphs (DAGs) built from **operators (ops)**. Each op is a Python class inheriting from `dagor.Operator` and `pydantic.BaseModel`. 

Instead of manual boilerplate, `sparsi-py` uses Pydantic field annotations with metadata to discover **wires**:

```python
from dagor import Operator, Input, Output
from pydantic import BaseModel

class AddOp(Operator, BaseModel):
    a: Input = 0
    b: Input = 0
    result: Output = 0

    async def run(self, ctx):
        self.result = (self.a or 0) + (self.b or 0)
```

The `dagor` engine resolves dependencies, schedules ops in parallel via `asyncio`, and threads **wire values** between them. A `Vertex(...).output("result", "x")` writes wire `x`; a downstream `Vertex(...).input("a", "x")` reads it.

The builder also performs **cycle detection** at build time to ensure the graph is a valid DAG.

## Params vs `ContextValOp`

A vertex gets configuration from two places:

- **Params** — static configuration that is part of the op's definition: operation names, map keys, regex patterns, flags. These are set via `.params({...})` in the builder and passed to the op's `setup()` method.
- **`ContextValOp`** — any value that varies per execution: user input, request data, file content, computed URLs. These are supplied through the `inputs` dictionary in `engine.run()`.

### Injecting per-execution values

Use `ContextValOp` to inject values at run time. The graph is built once at startup; each `engine.run(inputs)` call supplies different values through the input dictionary.

```python
from dagor import Builder, Engine
import dagor.builtin
import sparsi.library

# 1. Build the graph once
b = Builder("my_graph")
b.vertex("items_src").op("ContextValOp").params({"key": "items"}).output("result", "items_wire")
b.vertex("threshold_src").op("ContextValOp").params({"key": "threshold"}).output("result", "threshold_wire")
# ... downstream vertices consume the wires
graph = b.build()

# 2. Run many times with different inputs
engine = Engine(graph)
await engine.run({"items": ["foo", "bar"], "threshold": 0.75})
```

For truly static constants, use `ConstOp` which emits a fixed value captured in its params.

## Environment Variables

- `GEMINI_API_KEY` or `GOOGLE_API_KEY`: Required for all Gemini-based operators (`AIComputeOp`, `AIRerankOp`, etc.).
- `ANTHROPIC_API_KEY`: Required for Claude-based operators.
