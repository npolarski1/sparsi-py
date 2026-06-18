import asyncio
import os
import sys
import json
import argparse
import structlog
import urllib.parse
from typing import Any, Dict, Optional, List
from pydantic import BaseModel
from dagor import Builder, Engine, Operator, register_operator, Input, Output, Reporter
from dagor.builtin import ContextValOp
import sparsi.library # Registers standard ops

logger = structlog.get_logger(__name__)

# --- Graph ---

def build_graph(mode: str):
    # Register predicates for difficulty lanes
    from sparsi.library.predicate_ops import register_predicate
    register_predicate("score_is_easy", lambda inputs: (inputs.get("difficulty_score") or 0.0) < 20.0)
    register_predicate("score_is_medium", lambda inputs: 20.0 <= (inputs.get("difficulty_score") or 0.0) < 50.0)
    register_predicate("score_is_hard", lambda inputs: (inputs.get("difficulty_score") or 0.0) >= 50.0)

    b = Builder("recipe_analyzer")

    # 1. Produce raw_json
    if mode == "fixture":
        b.vertex("body_const").op("ContextValOp").params({"key": "body"}).output("result", "raw_json")
    else:
        b.vertex("url_const").op("ContextValOp").params({"key": "url"}).output("result", "url")
        b.vertex("fetch").op("HTTPGetOp").input("url", "url").output("body", "raw_json").output("status_code", "http_status")

    # 2. Extract instructions and meal name
    b.vertex("path_instructions").op("ContextValOp").params({"key": "path_instr"}).output("result", "p_instr")
    b.vertex("path_mealname").op("ContextValOp").params({"key": "path_meal"}).output("result", "p_meal")
    
    b.vertex("extract_instructions").op("JSONExtractOp").input("json_str", "raw_json").input("path", "p_instr").output("result", "instructions_text")
    b.vertex("extract_mealname").op("JSONExtractOp").input("json_str", "raw_json").input("path", "p_meal").output("result", "meal_name")

    # 3. AI Extractors
    b.vertex("ingredients").op("AIExtractStringSliceOp").params({
        "operation": "extract every distinct ingredient name from this recipe as a flat list (one ingredient per item; no quantities or units)",
    }).input("input", "instructions_text").output("result", "ingredients")

    b.vertex("steps").op("AIExtractStringSliceOp").params({
        "operation": "extract every discrete step required to prepare and cook the meal as a flat list (one step per item); exclude optional storage (like freezing) and serving suggestions",
    }).input("input", "instructions_text").output("result", "steps")

    b.vertex("cook_minutes").op("AIParseNumberOp").params({
        "operation": "estimate total active and passive cooking time in minutes; if a step is optional or provides a time range, use the minimum time; respond with a single integer",
    }).input("input", "instructions_text").output("result", "cook_minutes")

    # 4. Scoring
    b.vertex("ingredient_count").op("SliceLenOp").input("input", "ingredients").output("result", "ing_count")
    b.vertex("step_count").op("SliceLenOp").input("input", "steps").output("result", "step_count")
    
    b.vertex("step_weight").op("ContextValOp").params({"key": "w_step"}).output("result", "w_step")
    b.vertex("cook_weight").op("ContextValOp").params({"key": "w_cook"}).output("result", "w_cook")
    
    b.vertex("step_term").op("MathMulOp").input("a", "step_count").input("b", "w_step").output("result", "step_term")
    b.vertex("cook_term").op("MathMulOp").input("a", "cook_minutes").input("b", "w_cook").output("result", "cook_term")
    
    b.vertex("partial_score").op("MathAddOp").input("a", "ing_count").input("b", "step_term").output("result", "p_score")
    b.vertex("difficulty_score").op("MathAddOp").input("a", "p_score").input("b", "cook_term").output("result", "difficulty_score")

    # 5. Difficulty Lanes
    lanes = [
        ("easy", "score_is_easy", "write a one-sentence encouraging tip for a beginner cook making this recipe; reference the recipe by name"),
        ("medium", "score_is_medium", "write a one-sentence intermediate tip for a home cook attempting this recipe; reference the recipe by name"),
        ("hard", "score_is_hard", "write a one-sentence pro-level tip for an experienced cook tackling this recipe; reference the recipe by name"),
    ]
    
    for name, cond, op_text in lanes:
        b.vertex(f"{name}_advice").op("AIComputeStringToStringOp") \
            .condition(cond).condition_input("difficulty_score") \
            .params({"operation": op_text}) \
            .input("prompt", "meal_name") \
            .output("result", f"{name}_text")
            
    # 6. Coalesce
    b.vertex("advice").op("CoalesceNStringOp").params({"n": 3}) \
        .merge("coalesce") \
        .input("Input0", "easy_text") \
        .input("Input1", "medium_text") \
        .input("Input2", "hard_text") \
        .output("result", "final_advice")
        
    return b.build()

# --- Execution ---

async def run_workflow(meal: Optional[str] = None, fixture_path: Optional[str] = None, verbose: bool = False):
    mode = "fixture" if fixture_path else "live"
    graph = build_graph(mode)
    engine = Engine(graph, reporter=Reporter() if verbose else None)
    
    inputs = {
        "path_instr": "meals.0.strInstructions",
        "path_meal": "meals.0.strMeal",
        "w_step": 1.0,
        "w_cook": 0.1
    }
    
    if mode == "fixture":
        with open(fixture_path, "r", encoding="utf-8") as f:
            inputs["body"] = f.read()
    else:
        inputs["url"] = f"https://www.themealdb.com/api/json/v1/1/search.php?s={urllib.parse.quote(meal)}"
        
    await engine.run(inputs)
    
    advice, _ = engine.get_output("final_advice")
    score, _ = engine.get_output("difficulty_score")
    meal_name, _ = engine.get_output("meal_name")
    
    return {
        "meal": meal_name or meal,
        "difficulty_score": score,
        "advice": advice
    }

# --- Main ---

async def main():
    parser = argparse.ArgumentParser(description="Analyze recipe difficulty.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--meal", help="meal name to search on TheMealDB")
    group.add_argument("--fixture", help="path to a local JSON response file")
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

    if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
        print("Error: Neither GEMINI_API_KEY nor GOOGLE_API_KEY found. This example requires Gemini.")
        sys.exit(1)

    print(f"Analyzing recipe...")
    try:
        result = await run_workflow(meal=args.meal, fixture_path=args.fixture, verbose=args.verbose)
        print("\n--- Analysis Result ---")
        print(f"Meal: {result['meal']}")
        if result['difficulty_score'] is not None:
            print(f"Difficulty Score: {result['difficulty_score']:.1f}")
        print(f"Advice: {result['advice']}")
    except Exception as e:
        if args.verbose:
            logger.error("workflow_failed", error=str(e))
        else:
            print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
