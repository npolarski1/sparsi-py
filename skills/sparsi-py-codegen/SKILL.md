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
The output must use `asyncio` and `pydantic`. The code must run correctly.

# Steps

1. **Strict Adherence:** Implement the approved design EXACTLY. Do NOT improvise or omit vertices.
2. Write the complete Python source to `my_workflow.py`.
3. Write a `requirements.txt` file including `sparsi-py @ git+https://github.com/npolarski1/sparsi-py.git@main` and any other dependencies needed by custom ops (e.g. `beautifulsoup4`, `pandas`).
4. **Testing and Validation:** 
   - Before running the code, create a python virtual environment (`python3 -m venv .venv`) in the workflow directory if one doesn't already exist.
   - Activate the environment and install dependencies (`pip install -r requirements.txt`).
   - Run the workflow using the `--verbose` flag (e.g. `python3 my_workflow.py --verbose`) to ensure it executes correctly. 
   - **Live API Keys:** Tests MUST use actual API keys (read from environment variables) for any third-party services (LLMs, APIs). Ensure your environment has the necessary `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, etc.
   - **Rate Limits:** Monitor logs for rate limit errors. If a data API hits a limit, do not autonomously change the API in code; report it to the user and suggest alternative providers.
   - **Token Monitoring:** Review the `--verbose` logs for token usage metrics from AI operations. If token usage is exceptionally high (e.g., >20k tokens per request for a single item), you must iteratively refactor the workflow code to chunk the data and process it via `map_over` before finalizing the script.
   - **Semantic Verification (Hallucination Check):** After the workflow executes without crashing, critically review the final output. Compare the output against the raw test inputs you provided.
     - Look for "Out-of-Context Hallucinations": Did the AI output include specific facts, code signatures, types, or assertions that were NOT present in the test input data?
     - If the AI over-extrapolated, the prompts in your workflow are too loose. You must iteratively modify the prompt strings in `my_workflow.py` to add strict grounding constraints (e.g., "Base your answer STRICTLY on the provided text. Do NOT assume or guess definitions, types, or facts not visible in the input.") and re-test until the output is grounded.
   - If there are any errors or bugs, you must iteratively diagnose and fix them until the workflow runs successfully.
5. Notify the user once validation is successful.

# Implementation Rules

## Operator boilerplate
Every custom op must inherit from `dagor.Operator` and `pydantic.BaseModel`.
```python
from typing import Any
from pydantic import BaseModel
from dagor import Operator, register_operator, Input, Output

@register_operator("MyCustomOp")
class MyCustomOp(Operator, BaseModel):
    in_field: Input = ""
    out_field: Output = ""

    async def run(self, ctx: Any) -> None:
        self.out_field = self.in_field.upper()
```

## Builder DSL
Use the fluent `dagor.Builder` API:
```python
b = Builder("workflow_name")
b.vertex("v1").op("OpName").params({"key": "val"}).input("in_field", "wire").output("out_field", "out_wire")
```

## Map/Filter
Use `.map_over()` for fan-out execution.
```python
b.vertex("process_list").map_over("items_wire", "item")\
    .vertex("sub_op").op("UpperOp").input("text", "item").output("result", "up")\
    .collect_into("up", "processed_list")
```

## Value Injection Rule
Values must be injected from the context using `ContextValOp`. This operator is fully implemented in the standard library. You MUST import it from `dagor.builtin` instead of reinventing it.

```python
from dagor.builtin import ContextValOp

# In the builder
b.vertex("get_input").op("ContextValOp").params({"key": "user_query"}).output("result", "query_wire")

# In engine run
await engine.run({"user_query": user_text})
```

## AI Operations
AI generation uses `AIComputeOp` (which requires a `model` parameter), NOT `PromptOp`.
```python
b.vertex("ai_step").op("AIComputeOp").params({"model": "claude-3-5-sonnet"}).input("prompt", "prompt_wire").output("result", "out_wire")
```

## Dual-mode main (CLI + MCP)
Always support CLI and MCP mode. Use `sparsi.run_dual_mode`.
```python
import asyncio
from dagor import Builder, Engine
from sparsi import run_dual_mode
import sparsi.library

def build_graph():
    b = Builder("my_workflow")
    # ... build graph ...
    return b

if __name__ == "__main__":
    # run_dual_mode automatically handles --mcp flag, parses CLI args into context dict,
    # and handles standard dual-mode execution.
    run_dual_mode(
        name="my_workflow",
        builder_func=build_graph,
        input_mapping={"city": "city_key"}, # Map CLI flags to context keys
        output_wire="final_output"          # The wire name whose value should be printed/returned
    )
```
