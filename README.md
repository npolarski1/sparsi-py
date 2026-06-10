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

## Features

- **MCP First**: Every workflow can be served as a standard MCP tool via stdio or HTTP.
- **Rich Operator Library**: 60+ built-in ops for Math, Strings, JSON, I/O, and advanced AI tasks.
- **AI-Assisted Repair**: Gracefully recover from LLM hallucinations with bounded retry loops.
- **Async Fan-out**: Concurrent `MapOver` and `FilterBy` support for high-scale document processing.
- **RAG & Retrieval**: First-class support for retrieval-augmented generation with citation validation.
- **Persistent MCP Pool**: Efficiently manage external tools like Playwright or sandboxed filesystems.

---

## Quick Start

The fastest way to build Sparsi workflows is using our bundled skills. They allow you to design and generate Python code automatically within your AI assistant.

### 1. Install the Library
```bash
pip install sparsi-py
```

### 2. Install the AI Skills
Copy the `sparsi-py-design` and `sparsi-py-codegen` directories to your assistant's skills folder:

**macOS / Linux:**
```bash
cp -r skills/sparsi-py-design skills/sparsi-py-codegen ~/.claude/skills/
```

**Windows (PowerShell):**
```powershell
Copy-Item -Recurse skills/sparsi-py-design, skills/sparsi-py-codegen "$env:USERPROFILE\.claude\skills\"
```

### 3. Start Designing
Invoke the design skill from your assistant with your task description:
```bash
/sparsi-py-design <your task here>
```

---

## Examples

Discover what you can build with Sparsi:

| Example | Highlights |
| :--- | :--- |
| [**Ticket Triager**](./examples/ticket_triager.py) | Classification & structured routing. |
| [**Recipe Analyzer**](./examples/recipe_analyzer.py) | Parallel extraction & Gemini 3.5 Flash integration. |
| [**Faithful Summary**](./examples/faithful_summary.py) | Cross-model verification (Claude + Gemini). |
| [**HN Topic Brief**](./examples/hn_topic_brief.py) | API integration with parallel relevance filtering. |
| [**README Quality**](./examples/readme_quality.py) | Automated code review with concurrent AI probes. |
| [**Stock Analyzer**](./examples/stock_analyzer.py) | Parallel data fetching and sentiment analysis. |

---

## Documentation

- [**Core Concepts**](./docs/concepts.md) — DAGs, Ops, and the Engine.
- [**Operator Library**](./docs/operators.md) — Exhaustive list of all built-in operators.
- [**Writing Workflows**](./docs/writing-workflows.md) — AI ops, Conditionals, and Map nodes.
- [**MCP Integration**](./docs/mcp.md) — Hosting your workflows as MCP servers.
