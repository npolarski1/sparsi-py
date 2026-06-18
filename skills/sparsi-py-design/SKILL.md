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
workflow is exposed as **one MCP tool**.

# Example selection guide

| Workflow pattern | Example |
|---|---|
| Classification → routing → extraction | `examples/ticket_triager/` |
| Parallel extraction → deterministic scoring | `examples/recipe_analyzer/` |
| Parallel HTTP fetch → quality probes | `examples/readme_quality/` |
| Multi-stage extraction → banding → advice | `examples/weather_advisor/` |
| MapOver fan-out → aggregation | `examples/hn_topic_brief/` |
| Cross-model verification (Generation + Verification) | `examples/faithful_summary/` |
| AI-driven repair (`WithRepair`) | `examples/with_repair/` |
| RAG with lexical/vector retriever | `examples/rag_bm25/`, `examples/rag_gemini_embed/` |

# AI recovery wrapper (WithRepair) placement

WithRepair is most suitable at the **upstream boundary** of the DAG — wrap the op
that first ingests outside input so the workflow validates and, if necessary, repairs
that input before anything downstream depends on it.

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
