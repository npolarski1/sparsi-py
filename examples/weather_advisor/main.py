import asyncio
import os
import sys
import json
import argparse
import structlog
import urllib.parse
from typing import Any, List, Optional
from pydantic import BaseModel
from dagor import Builder, Engine, Operator, register_operator, Input, Output, Reporter
from dagor.builtin import ContextValOp
import sparsi.library # Registers standard ops

logger = structlog.get_logger(__name__)

# --- Custom Ops ---

@register_operator("PackOutfitInputsOp")
class PackOutfitInputsOp(Operator, BaseModel):
    band: Input = None # str
    wet: Input = None # bool
    windy: Input = None # bool
    temp_c: Input = None # float
    conditions: Input = None # List[str]
    result: Output = ""

    async def run(self, ctx: Any) -> None:
        wet_str = "rainy/wet" if self.wet else "dry"
        windy_str = "windy" if self.windy else "calm"
        band_str = self.band or "unknown"
        temp_val = self.temp_c if self.temp_c is not None else 0.0
        cond_str = ", ".join(self.conditions) if self.conditions else "unspecified"
        
        self.result = (
            f"Temperature: {temp_val:.1f}°C ({band_str}), "
            f"precipitation: {wet_str}, wind: {windy_str}, "
            f"conditions: {cond_str}"
        )

# --- Predicates ---

def register_predicates():
    from sparsi.library.predicate_ops import register_predicate
    register_predicate("temp_c < 10.0", lambda inputs: (inputs.get("temp_c") or 0.0) < 10.0)
    register_predicate("temp_c >= 10.0 and temp_c < 22.0", lambda inputs: 10.0 <= (inputs.get("temp_c") or 0.0) < 22.0)
    register_predicate("temp_c >= 22.0", lambda inputs: (inputs.get("temp_c") or 0.0) >= 22.0)

# --- Graph ---

def build_graph(source_mode: str):
    b = Builder("weather_advisor")

    # Stage 1 — produce a single `body` wire containing the wttr.in j1 JSON.
    if source_mode == "fixture":
        b.vertex("body_const").op("ContextValOp").params({"key": "body"}).output("result", "body")
    else:
        b.vertex("url_const").op("ContextValOp").params({"key": "url"}).output("result", "url")
        b.vertex("fetch").op("HTTPGetOp").input("url", "url").output("body", "body").output("status_code", "http_status")

    # Stage 2 — extract the four numeric/text fields from JSON (run in parallel).
    paths = {
        "temp_str": "current_condition.0.temp_C",
        "precip_str": "current_condition.0.precipMM",
        "wind_str": "current_condition.0.windspeedKmph",
        "desc_str": "current_condition.0.weatherDesc.0.value"
    }
    for wire, path in paths.items():
        b.vertex(f"path_{wire}").op("ConstOp").params({"value": path}).output("result", f"p_{wire}")
        b.vertex(f"extract_{wire}").op("JSONExtractOp") \
            .input("json_str", "body") \
            .input("path", f"p_{wire}") \
            .output("result", wire)

    # Stage 3 — AI parse numbers (three run concurrently).
    b.vertex("parse_temp").op("AIParseNumberOp").params({"operation": "extract the temperature value as a plain number with no units"}) \
        .input("input", "temp_str").output("result", "temp_c")
    b.vertex("parse_precip").op("AIParseNumberOp").params({"operation": "extract the precipitation amount as a plain number with no units"}) \
        .input("input", "precip_str").output("result", "precip_mm")
    b.vertex("parse_wind").op("AIParseNumberOp").params({"operation": "extract the wind speed as a plain number with no units"}) \
        .input("input", "wind_str").output("result", "wind_kph")

    # Stage 4 — deterministic temperature band
    b.vertex("cold_const").op("ConstOp").params({"value": "cold"}).condition("temp_c < 10.0").condition_input("temp_c").output("result", "cold_band")
    b.vertex("mild_const").op("ConstOp").params({"value": "mild"}).condition("temp_c >= 10.0 and temp_c < 22.0").condition_input("temp_c").output("result", "mild_band")
    b.vertex("hot_const").op("ConstOp").params({"value": "hot"}).condition("temp_c >= 22.0").condition_input("temp_c").output("result", "hot_band")
    
    b.vertex("band_merge").op("CoalesceNOp").params({"n": 3}) \
        .merge("coalesce") \
        .input("Input0", "cold_band").input("Input1", "mild_band").input("Input2", "hot_band") \
        .output("result", "band")

    # Stage 5 — deterministic wet / windy boolean flags.
    b.vertex("precip_thresh").op("ContextValOp").params({"key": "precip_thresh"}).output("result", "p_thresh")
    b.vertex("wet_check").op("IfFloatGtOp").input("a", "precip_mm").input("b", "p_thresh").output("match", "wet")

    b.vertex("wind_thresh").op("ContextValOp").params({"key": "wind_thresh"}).output("result", "w_thresh")
    b.vertex("windy_check").op("IfFloatGtOp").input("a", "wind_kph").input("b", "w_thresh").output("match", "windy")

    # Stage 6 — multi-label weather condition classifier (AI).
    b.vertex("classify_conditions").op("AIClassifyMultiLabelOp").params({"categories": "rain,snow,fog,sun,cloud,storm"}) \
        .input("input", "desc_str").output("result", "conditions")

    # Stage 7 — pack all signals into one description string for the final AI.
    b.vertex("pack_outfit").op("PackOutfitInputsOp") \
        .input("band", "band") \
        .input("wet", "wet") \
        .input("windy", "windy") \
        .input("temp_c", "temp_c") \
        .input("conditions", "conditions") \
        .output("result", "outfit_input")

    # Stage 8 — AI outfit advice.
    b.vertex("outfit_advice_op").op("AIComputeStringToStringOp").params({
        "operation": "Given the weather conditions described, write exactly 2 sentences recommending an appropriate outfit. Be specific about clothing items.",
    }).input("prompt", "outfit_input").output("result", "outfit_advice")

    # Stage 9 — orthogonal unusual-weather probe + optional warning suffix.
    b.vertex("unusual_check").op("AIBoolOp").params({"predicate": "Is the described weather unusual or extreme for typical human experience?"}) \
        .input("input", "desc_str").output("result", "unusual_flag")

    b.vertex("warning_const").op("ContextValOp").params({"key": "warning_str"}).output("result", "w_str")
    b.vertex("empty_const").op("ContextValOp").params({"key": "empty_str"}).output("result", "e_str")

    b.vertex("warning_select").op("SelectStringOp") \
        .input("cond", "unusual_flag") \
        .input("if_true", "w_str") \
        .input("if_false", "e_str") \
        .output("result", "warning_suffix")

    b.vertex("final_concat").op("StringConcatOp") \
        .input("a", "outfit_advice") \
        .input("b", "warning_suffix") \
        .output("result", "final_advice")

    return b.build()

# --- Shared Execution ---

async def run_workflow(city: str, fixture_path: Optional[str], verbose: bool):
    register_predicates()
    source_mode = "fixture" if fixture_path else "live"
    graph = build_graph(source_mode)
    engine = Engine(graph, reporter=Reporter() if verbose else None)
    
    inputs = {
        "precip_thresh": 0.1,
        "wind_thresh": 25.0,
        "warning_str": "  ⚠ unusual weather",
        "empty_str": "",
    }
    
    if source_mode == "fixture":
        with open(fixture_path, "r") as f:
            inputs["body"] = f.read()
    else:
        inputs["url"] = f"https://wttr.in/{urllib.parse.quote(city)}?format=j1"
    
    await engine.run(inputs)
    
    advice, _ = engine.get_output("final_advice")
    temp_c, _ = engine.get_output("temp_c")
    precip_mm, _ = engine.get_output("precip_mm")
    wind_kph, _ = engine.get_output("wind_kph")
    band, _ = engine.get_output("band")
    wet, _ = engine.get_output("wet")
    windy, _ = engine.get_output("windy")
    conditions, _ = engine.get_output("conditions")
    
    return {
        "city": city,
        "temp_c": temp_c,
        "precip_mm": precip_mm,
        "wind_kph": wind_kph,
        "band": band,
        "wet": wet,
        "windy": windy,
        "conditions": conditions,
        "advice": advice
    }

# --- Main ---

async def main():
    parser = argparse.ArgumentParser(description="Weather-aware outfit advisor.")
    parser.add_argument("--city", help="city name for live wttr.in API")
    parser.add_argument("--fixture", help="path to captured wttr.in j1 JSON fixture")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    if not args.city and not args.fixture:
        parser.error("specify either --city or --fixture")

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

    print(f"Running weather-advisor workflow...")
    try:
        result = await run_workflow(args.city, args.fixture, args.verbose)
        print("\n--- Workflow Result ---")
        print(json.dumps(result, indent=2))
    except Exception as e:
        if args.verbose:
            logger.exception("workflow_failed")
        else:
            print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
