<p align="center">
  <img src="sparsi_logo.svg" alt="sparsi-py logo" width="400">
</p>

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

**Fewer tokens, lower latency, better results.** 

`sparsi-py` is a Python framework for building **deterministic-first AI workflows** and serving them as high-performance [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) servers.

---

## Why sparsi-py?

Today's agents are interpreters. They re-derive the same routines — classify, route, extract, reply — from scratch on every request, paying the reasoning cost in tokens, latency, and reliability.

**Sparsi is the build step they never had.** It lets you author repeating request types as DAG workflows that are:

*   **Deterministic by Default** — The graph is plain, testable Python. AI runs only where language understanding is strictly required.
*   **Modular Building Blocks** — Compose workflows from reliable, reusable components instead of "black box" prompts.
*   **Parallel by Architecture** — Built on `asyncio`. Independent branches run concurrently; speed comes from the graph's shape, not manual threading.
*   **Model Agnostic** — Pin different models to different steps. A cheap classifier here, a strong synthesizer there.
*   **Bounded & Auditable** — Fixed AI call counts and full reasoning traces for every step.

---

## Quick Start

### 1. Install the Library
```bash
pip install sparsi-py
```

### 2. Install the AI Skills (Optional)
Sparsi provides bundled skills to help you design and generate Python code automatically within your AI assistant. Copy the skills to your assistant's skills folder:

**macOS / Linux:**
```bash
cp -r skills/sparsi-py-design skills/sparsi-py-codegen ~/.claude/skills/
```

**Windows (PowerShell):**
```powershell
Copy-Item -Recurse skills/sparsi-py-design, skills/sparsi-py-codegen "$env:USERPROFILE\.claude\skills\"
```

### 3. Build a Deterministic Workflow
```python
import asyncio
from dagor import Builder, Engine
import sparsi.library # Registers standard ops

async def main():
    b = Builder("ticket_triager")
    
    # Define inputs and ops
    b.vertex("input").op("ContextValOp").params({"key": "ticket"}).output("result", "raw_ticket")
    b.vertex("length").op("StringLenOp").input("input", "raw_ticket").output("result", "char_count")
    
    # Conditional branch: only process if ticket is not empty
    b.vertex("process").op("StringConcatOp").params({"a": "Processing: "}).input("b", "raw_ticket").output("result", "processed")\
        .condition_input("char_count").condition("is_not_empty")
        
    graph = b.build()
    engine = Engine(graph)
    
    await engine.run({"ticket": "My screen is flickering!"})
    res, ok = engine.get_output("processed")
    print(res)

asyncio.run(main())
```

### 4. Add AI
```python
from dagor import Builder
from sparsi.library import AIComputeOp, AIBoolOp

b = Builder("ai_workflow")
b.vertex("input").op("ContextValOp").params({"key": "text"}).output("result", "text")

# High-level AI operators
b.vertex("has_pii").op("AIBoolOp").params({"predicate": "contains PII?"}).input("input", "text")
b.vertex("summary").op("AIComputeOp").params({"operation": "summarize"}).input("prompt", "text")

# ... build and run with Engine
```

---

## Examples

| Example | Highlights |
| :--- | :--- |
| [**Ticket Triager**](./examples/ticket_triager/main.py) | Classification, structured routing, and multi-model support. |
| [**Recipe Analyzer**](./examples/recipe_analyzer/main.py) | Parallel extraction, difficulty scoring, and gated advice. |
| [**Faithful Summary**](./examples/faithful_summary/main.py) | **Mix Claude + Gemini** for cross-model verification. |
| [**HN Topic Brief**](./examples/hn_topic_brief/main.py) | API integration with parallel relevance filtering. |
| [**README Quality**](./examples/readme_quality/main.py) | Concurrent quality probes and automated code review. |
| [**Smart Doc Assistant**](./examples/smart_doc_assistant/main.py) | Advanced RAG with filtering, reranking, and citation validation. |
| [**Repair JSON**](./examples/repair_json/main.py) | `withRepair` — AI-driven self-healing for malformed JSON. |
| [**Weather Advisor**](./examples/weather_advisor/main.py) | Complex multi-stage workflow with parallel extraction. |
| [**Stock Analyzer**](./examples/stock_analyzer/main.py) | Hybrid deterministic/AI financial analysis. |

---

## Documentation

- [**Core Concepts**](./docs/concepts.md) — DAGs, Ops, and the Engine.
- [**Operator Library**](./docs/operators.md) — Exhaustive list of all built-in operators.
- [**Python API Reference**](./docs/python-api.md) — How to implement operators and build graphs.
- [**Writing Workflows**](./docs/writing-workflows.md) — AI ops, Conditionals, and Map nodes.
- [**MCP Integration**](./docs/mcp.md) — Hosting your workflows as MCP servers.
