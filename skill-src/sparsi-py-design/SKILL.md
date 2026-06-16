---
name: sparsi-py-design
description: Design a maximally deterministic sparsi-py DAG workflow
version: 0.1.0
library_version: sparsi-py v0.1.0
triggers: [sparsi py design, design python dag, sparsi python workflow design]
input:
  task: {type: string, description: "Task description", required: true}
---

# Context

You are designing a DAG workflow using the sparsi-py library. Your goal is a maximally
deterministic design: every step that can be a library op or custom deterministic Python op MUST be.
AI calls are reserved for genuine natural-language parsing or subjective judgment where no
deterministic alternative exists.

# Dual-mode runtime (CLI + MCP server)

Every generated program is dual-mode: a one-shot CLI tool by default, or a
local stdin/stdout MCP server when invoked with `--mcp`. In MCP mode the whole
workflow is exposed as **one MCP tool**; every external input is deserialized
out of the incoming `tools/call` request, and the final outputs are returned as
the tool result.

# Retrieval (RAG)

When the workflow needs facts that are not in the user's input, fan in retrieved context via `RetrieveOp`. 
The op outputs `results` (List of search results).

# AI Recovery (WithRepair)

Use `WithRepair` at the upstream boundary to wrap ops that ingest outside input.
Downstream vertices can then treat the value as well-formed.

# Output format

Respond ONLY with the following structured document.

## Workflow: [short name]

### ASCII DAG
[diagram showing vertices and data flow]

### Vertices
List each vertex in topological order:
N. **vertex_name** — `OpName` — [Condition: pred_name] — Params: key=value, ...
   - In: FieldName ← `wire_name`
   - Out: FieldName → `wire_name`

For map vertices:
N. **vertex_name** — `[MAP]` — item_wire: `item`
   - In: Items ← `slice_wire`
   - Sub-graph: ...
   - CollectInto: `result_wire` → `output_wire`
