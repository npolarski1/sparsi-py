import asyncio
import os
import sys
import json
import argparse
import structlog
from typing import Any, Dict, Optional, List
from pydantic import BaseModel
from dagor import Builder, Engine, Operator, register_operator, Input, Output, Reporter
from dagor.builtin import ContextValOp
import sparsi.library # Registers standard ops

logger = structlog.get_logger(__name__)

# --- Graph ---

def build_graph(mode: str):
    # Register predicates needed for quality lanes
    from sparsi.library.predicate_ops import register_predicate
    register_predicate("readme_excellent", lambda inputs: (inputs.get("avg_score") or 0.0) >= 0.75)
    register_predicate("readme_ok", lambda inputs: 0.40 <= (inputs.get("avg_score") or 0.0) < 0.75)
    register_predicate("readme_poor", lambda inputs: (inputs.get("avg_score") or 0.0) < 0.40)

    b = Builder("readme_quality")

    # 1. Produce readme_raw
    if mode == "fixture":
        b.vertex("readme_const").op("ContextValOp").params({"key": "readme_body"}).output("result", "readme_raw")
    else:
        b.vertex("main_url_const").op("ContextValOp").params({"key": "main_url"}).output("result", "main_url")
        b.vertex("master_url_const").op("ContextValOp").params({"key": "master_url"}).output("result", "master_url")
        
        b.vertex("fetch_main").op("HTTPGetOp").input("url", "main_url").output("body", "main_body").output("status_code", "main_status")
        b.vertex("fetch_master").op("HTTPGetOp").input("url", "master_url").output("body", "master_body")
        
        b.vertex("const_200").op("ContextValOp").params({"key": "status_200"}).output("result", "int_200")
        b.vertex("check_main").op("IfIntEqOp").input("a", "main_status").input("b", "int_200").output("match", "main_ok")
        
        b.vertex("pick_readme").op("SelectStringOp").input("cond", "main_ok").input("if_true", "main_body").input("if_false", "master_body").output("result", "readme_raw")

    # 2. Truncate
    b.vertex("truncate").op("StringTruncateOp").params({"max_bytes": 8192}).input("text", "readme_raw").output("result", "readme")

    # 3. AI Probes
    b.vertex("purpose_op").op("AIComputeStringToStringOp").params({
        "operation": "summarize the purpose of this project in one concise sentence",
    }).input("prompt", "readme").output("result", "purpose_str")
    
    b.vertex("doc_score_op").op("AIScoreOp").params({"criterion": "documentation completeness"}).input("input", "readme").output("result", "doc_score")
    b.vertex("clarity_op").op("AIScoreOp").params({"criterion": "clarity for new contributors"}).input("input", "readme").output("result", "clarity_score")
    b.vertex("has_tests_op").op("AIBoolOp").params({"predicate": "does this README mention tests, CI, or automated checks?"}).input("input", "readme").output("result", "has_tests")
    
    # 4. Average Score
    b.vertex("sum_scores").op("MathAddOp").input("a", "doc_score").input("b", "clarity_score").output("result", "sum_scores_val")
    b.vertex("const_2").op("ContextValOp").params({"key": "val_2"}).output("result", "two_f")
    b.vertex("avg_score_op").op("MathDivOp").input("a", "sum_scores_val").input("b", "two_f").output("result", "avg_score")

    # 5. Quality Lanes
    lanes = [
        ("excellent", "readme_excellent", "write a one-paragraph endorsement of this README, highlighting what makes it exemplary for open-source projects"),
        ("ok", "readme_ok", "write a one-paragraph constructive critique of this README with 2 specific, actionable suggestions for improvement"),
        ("poor", "readme_poor", "write a one-paragraph improvement plan for this README listing the 3 highest-impact fixes that would help new contributors"),
    ]
    
    for name, cond, op_text in lanes:
        b.vertex(f"{name}_lane").op("AIComputeStringToStringOp") \
            .condition(cond).condition_input("avg_score") \
            .params({"operation": op_text}) \
            .input("prompt", "readme") \
            .output("result", f"{name}_text")
            
    # 6. Coalesce + Final
    b.vertex("narrative_op").op("CoalesceNStringOp").params({"n": 3}) \
        .merge("coalesce") \
        .input("Input0", "excellent_text") \
        .input("Input1", "ok_text") \
        .input("Input2", "poor_text") \
        .output("result", "narrative")
        
    b.vertex("warning_const").op("ContextValOp").params({"key": "warning_text"}).output("result", "w_text")
    b.vertex("empty_const").op("ContextValOp").params({"key": "empty_text"}).output("result", "e_text")
    
    b.vertex("test_warning").op("SelectStringOp").input("cond", "has_tests").input("if_true", "e_text").input("if_false", "w_text").output("result", "test_warning_str")
    
    b.vertex("final_narrative").op("StringConcatOp").input("a", "narrative").input("b", "test_warning_str").output("result", "final_narrative")
    
    return b.build()

# --- Execution ---

async def run_workflow(slug: Optional[str] = None, fixture_path: Optional[str] = None):
    mode = "fixture" if fixture_path else "live"
    graph = build_graph(mode)
    engine = Engine(graph, reporter=Reporter())
    
    inputs = {
        "status_200": 200,
        "val_2": 2.0,
        "warning_text": "\n\nWARNING: tests not mentioned",
        "empty_text": ""
    }
    
    if mode == "fixture":
        with open(fixture_path, "r", encoding="utf-8") as f:
            inputs["readme_body"] = f.read()
    else:
        inputs["main_url"] = f"https://raw.githubusercontent.com/{slug}/main/README.md"
        inputs["master_url"] = f"https://raw.githubusercontent.com/{slug}/master/README.md"
        
    await engine.run(inputs)
    
    narrative, _ = engine.get_output("final_narrative")
    avg_score, _ = engine.get_output("avg_score")
    
    return {
        "slug": slug or fixture_path,
        "avg_score": avg_score,
        "narrative": narrative
    }

# --- Main ---

async def main():
    parser = argparse.ArgumentParser(description="Assess GitHub README quality.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--slug", help="owner/repo slug, e.g. golang/go")
    group.add_argument("--fixture", help="path to a local README file")
    
    args = parser.parse_args()
    
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ]
    )

    print(f"Assessing README quality...")
    try:
        result = await run_workflow(slug=args.slug, fixture_path=args.fixture)
        print("\n--- Assessment Result ---")
        print(f"Average Score: {result['avg_score']:.2f}")
        print("\n" + result["narrative"])
    except Exception as e:
        logger.error("workflow_failed", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
