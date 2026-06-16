import asyncio
import os
import sys
import json
import argparse
import structlog
import urllib.parse
import httpx
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, ConfigDict
from dagor import Builder, Engine, Operator, register_operator, Input, Output, Reporter, get_run_id
from dagor.builtin import ContextValOp
import sparsi.library # Registers standard ops

logger = structlog.get_logger(__name__)

# --- Custom Ops ---

@register_operator("ExtractTitlesOp")
class ExtractTitlesOp(Operator, BaseModel):
    json_str: Input = ""
    result: Output = []

    async def run(self, ctx: Any) -> None:
        if not self.json_str:
            self.result = []
            return
        try:
            data = json.loads(self.json_str)
            self.result = [h["title"] for h in data.get("hits", []) if h.get("title")]
        except Exception as e:
            logger.error("ExtractTitlesOp.failed", error=str(e))
            self.result = []

@register_operator("FilterAndFlattenOp")
class FilterAndFlattenOp(Operator, BaseModel):
    titles: Input = []
    relevant_flags: Input = []
    label_lists: Input = []
    kept_titles: Output = []
    all_labels: Output = []

    async def run(self, ctx: Any) -> None:
        n = min(len(self.titles), len(self.relevant_flags), len(self.label_lists))
        
        self.kept_titles = []
        self.all_labels = []
        
        for i in range(n):
            if self.relevant_flags[i]:
                self.kept_titles.append(self.titles[i])
                labels = self.label_lists[i]
                if isinstance(labels, list):
                    self.all_labels.extend(labels)
                elif isinstance(labels, str) and labels:
                    self.all_labels.extend([s.strip() for s in labels.split(",") if s.strip()])

@register_operator("DominantCategoryOp")
class DominantCategoryOp(Operator, BaseModel):
    all_labels: Input = []
    dominant: Output = "technical"

    async def run(self, ctx: Any) -> None:
        if not self.all_labels:
            self.dominant = "technical"
            return
            
        counts = {}
        for label in self.all_labels:
            counts[label] = counts.get(label, 0) + 1
            
        # Tie break alphabetically
        sorted_counts = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
        self.dominant = sorted_counts[0][0]

@register_operator("AISummarizeOp")
class AISummarizeOp(Operator, BaseModel):
    input: Input = [] # List of strings
    operation: str = ""
    result: Output = ""
    model: str = "gemini-3.5-flash"

    def setup(self, params: Dict[str, Any]) -> None:
        self.operation = params.get("operation", "")
        self.model = params.get("model", self.model)

    async def run(self, ctx: Any) -> None:
        if not self.input:
            self.result = ""
            return
            
        items_text = "\n".join(f"- {s}" for s in self.input)
        prompt = f"Perform the following operation on these items:\n{self.operation}\n\nItems:\n{items_text}"
        
        from sparsi.library.ai_ops import AIComputeOp
        ai = AIComputeOp(model=self.model, prompt=prompt)
        await ai.run(ctx)
        self.result = ai.result

# --- Graph ---

def build_graph(query: str):
    # Register predicates needed for lanes
    from sparsi.library.predicate_ops import register_predicate
    register_predicate("style_is_technical_brief", lambda inputs: inputs.get("brief_style") == "technical_brief")
    register_predicate("style_is_business_brief", lambda inputs: inputs.get("brief_style") == "business_brief")
    register_predicate("style_is_policy_brief", lambda inputs: inputs.get("brief_style") == "policy_brief")

    b = Builder("hn_topic_brief")

    # 1. Inject API response
    b.vertex("response_const").op("ContextValOp").params({"key": "response"}).output("result", "response_json")
    
    # 2. Extract titles
    b.vertex("extract_titles").op("ExtractTitlesOp").input("json_str", "response_json").output("result", "titles")
    
    # 3a. Relevance check (MapOver)
    b.vertex("map_relevance").map_over("titles", "title") \
        .vertex("relevant").op("AIBoolOp").params({
            "predicate": f"Is this HackerNews story title actually about the topic {query!r}? Respond true or false.",
        }).input("input", "title").output("result", "is_relevant") \
        .collect_into("is_relevant", "relevant_flags")
        
    # 3b. Label classification (MapOver)
    b.vertex("map_classify").map_over("titles", "title") \
        .vertex("classify").op("AIClassifyMultiLabelOp").params({
            "categories": "technical,business,policy,human_interest,other",
        }).input("input", "title").output("result", "labels") \
        .collect_into("labels", "label_lists")
        
    # 4. Filter + Flatten
    b.vertex("filter_flatten").op("FilterAndFlattenOp") \
        .input("titles", "titles") \
        .input("relevant_flags", "relevant_flags") \
        .input("label_lists", "label_lists") \
        .output("kept_titles", "kept_titles") \
        .output("all_labels", "all_labels")
        
    # 5. Dominant Category
    b.vertex("dominant_cat").op("DominantCategoryOp").input("all_labels", "all_labels").output("dominant", "dominant")
    
    # 6. AI Style Selector
    b.vertex("mode_select").op("ModeSelectOp").params({
        "categories": "technical_brief,business_brief,policy_brief",
    }).input("input", "dominant").output("result", "brief_style")
    
    # 7. Brief Style Lanes
    lanes = [
        ("technical", "style_is_technical_brief", "summarize the following HackerNews story titles as a technical engineering newsletter: write one concise bullet point per story and group related stories by sub-topic"),
        ("business", "style_is_business_brief", "summarize the following HackerNews story titles as an executive business brief: write a 3-sentence overview then a bulleted impact list"),
        ("policy", "style_is_policy_brief", "summarize the following HackerNews story titles as a policy memo: list legislative items, affected parties, and likely timeline"),
    ]
    
    for name, cond, op_text in lanes:
        b.vertex(f"{name}_lane").op("AISummarizeOp") \
            .condition(cond).condition_input("brief_style") \
            .params({"operation": op_text}) \
            .input("input", "kept_titles") \
            .output("result", f"{name}_text")
            
    # 8. Coalesce
    b.vertex("final_op").op("CoalesceNStringOp").params({"n": 3}) \
        .merge("coalesce") \
        .input("Input0", "technical_text") \
        .input("Input1", "business_text") \
        .input("Input2", "policy_text") \
        .output("result", "final_brief")
        
    return b.build()

# --- Execution ---

async def fetch_hn(query: str) -> str:
    endpoint = f"https://hn.algolia.com/api/v1/search?query={urllib.parse.quote(query)}&hitsPerPage=10"
    logger.info("hn_fetch_start", endpoint=endpoint)
    async with httpx.AsyncClient() as client:
        resp = await client.get(endpoint)
        resp.raise_for_status()
        return resp.text

async def run_workflow(query: str, verbose: bool):
    response_json = await fetch_hn(query)
    
    graph = build_graph(query)
    engine = Engine(graph, reporter=Reporter() if verbose else None)
    
    await engine.run({"response": response_json})
    
    brief, _ = engine.get_output("final_brief")
    style, _ = engine.get_output("brief_style")
    
    return {
        "query": query,
        "style": style,
        "brief": brief
    }

# --- Main ---

async def main():
    parser = argparse.ArgumentParser(description="HackerNews topic brief generator.")
    parser.add_argument("--query", required=True, help="HN search query")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        structlog.configure(
            processors=[
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.dev.ConsoleRenderer(),
            ]
        )

    print(f"Generating HN brief for: {args.query}...")
    try:
        result = await run_workflow(args.query, args.verbose)
        print("\n--- Topic Brief ---")
        print(f"Style: {result['style']}")
        print("\n" + result["brief"])
    except Exception as e:
        if args.verbose:
            logger.error("workflow_failed", error=str(e))
        else:
            print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
