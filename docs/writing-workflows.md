# Writing Workflows

## AI ops

AI ops default to Gemini 3.5 Flash (`gemini-3.5-flash`) but accept a `provider` param (`"claude"` or `"gemini"`) and a `model` param. They send structured prompts, retry on parse failure, and emit reasoning traces alongside the result.

```python
b.vertex("summarize").op("AISummarizeOp").params({
    "operation": "summarize into 3 bullet points",
    "model": "claude-3-5-sonnet-20240620"
}).input("input", "document").output("result", "summary")
```

## Conditionals

Register a named predicate and attach it to a vertex with `.condition(...)`:

```python
from sparsi.library.predicate_ops import register_predicate

register_predicate("is_positive", lambda inputs: inputs.get("val_wire") > 0)

# In the builder:
b.vertex("conditional_step").op("MyOp") \
    .condition("is_positive") \
    .condition_input("val_wire") \
    .input("in", "val_wire")
```

Vertices that fail their condition are **skipped**. Their outputs are marked as skipped, and this skip propagates transitively to all downstream vertices unless a `merge` strategy is used.

## Map and Filter Nodes

Fan out a sub-graph over each element of a slice concurrently:

```python
b.vertex("process_items").map_over("items_wire", "item") \
    .vertex("op").op("AIScoreOp").params({"criterion": "relevance"}) \
    .input("input", "item").output("result", "score") \
    .collect_into("score", "all_scores")
```

The `map_over` method returns a `SubGraphBuilder`. Use `collect_into(sub_wire, parent_wire)` to terminate the sub-graph and gather results into a list on the parent vertex.

## Retrieval (RAG)

`RetrieveOp` fans external context into a graph via a registered `Retriever` implementation.

```python
from sparsi.library import set_default_retriever

class MyRetriever:
    async def retrieve(self, ctx, query, k):
        # call vector DB
        return [Document(id="1", content="...")]

set_default_retriever(MyRetriever())
```

**Citation validation.** Treat LLM-emitted citations as untrusted. Wire `ValidateCitationsOp` between the AI generator and your final output to ensure every referenced source actually exists in the retrieved documents.
