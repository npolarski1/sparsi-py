import asyncio
import os
import sys
import time
import argparse
import pandas as pd
from tqdm import tqdm
from datasets import load_dataset
import structlog

# Sparsi imports
from dagor import Builder, Engine, Reporter
from dagor.builtin import ContextValOp
import sparsi.library # Registers all ops

# Langchain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

# Ensure API key is set
if "GEMINI_API_KEY" not in os.environ and "GOOGLE_API_KEY" not in os.environ:
    print("Warning: Neither GEMINI_API_KEY nor GOOGLE_API_KEY is set. Execution might fail.")
    if "ANTHROPIC_API_KEY" in os.environ:
         print("Warning: Anthropic key is set but we are using Gemini for the benchmark.")

# -------------------------------------------------------------------
# INTENT DEFINITIONS
# -------------------------------------------------------------------
AVAILABLE_INTENTS = [
    "cancel_order", "change_order", "change_shipping_address",
    "check_cancellation_fee", "check_invoice", "check_payment_methods",
    "check_refund_policy", "complaint", "contact_customer_service",
    "contact_human_agent", "create_account", "delete_account",
    "delivery_options", "delivery_period", "edit_account", "get_invoice",
    "get_refund", "newsletter_subscription", "payment_issue",
    "place_order", "recover_password", "registration_problems",
    "review", "set_up_shipping_address", "switch_account",
    "track_order", "track_refund"
]
INTENT_LIST_STR = ", ".join(AVAILABLE_INTENTS)

# -------------------------------------------------------------------
# SPARSI WORKFLOW
# -------------------------------------------------------------------
from pydantic import BaseModel, Field
from dagor import Operator, register_operator, Input, Output

def build_sparsi_graph():
    b = Builder("intent_classifier")
    
    b.vertex("input").op("ContextValOp").params({"key": "utterance"}).output("result", "raw_utterance")
    
    b.vertex("extract").op("AIExtractMapOp").params({
        "model": "gemini-3.1-flash-lite",
        "operation": f"1. 'intent': EXACTLY one of {INTENT_LIST_STR}. 2. 'is_urgent': boolean true/false. 3. 'language': string (e.g. 'English')"
    }).input("input", "raw_utterance").output("result", "llm_json").output("usage_input_tokens", "in_toks").output("usage_output_tokens", "out_toks")
    
    return b.build()

async def run_sparsi(engine: Engine, utterance: str) -> tuple[dict, int, int]:
    await engine.run({"utterance": utterance})
    llm_json, _ = engine.get_output("llm_json")
    in_toks, _ = engine.get_output("in_toks")
    out_toks, _ = engine.get_output("out_toks")
    
    extracted = llm_json
    return extracted or {}, in_toks or 0, out_toks or 0

# -------------------------------------------------------------------
# LANGCHAIN AGENT
# -------------------------------------------------------------------
@tool
def get_available_intents() -> str:
    """Returns the list of valid intents for classification."""
    return f"The valid intents are: {INTENT_LIST_STR}"

def build_langchain_agent():
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0)
    tools = [get_available_intents]
    agent_executor = create_react_agent(llm, tools)
    return agent_executor

# -------------------------------------------------------------------
# BENCHMARK RUNNER
# -------------------------------------------------------------------
async def main():
    parser = argparse.ArgumentParser(description="Benchmark Sparsi vs LangChain")
    parser.add_argument("--samples", type=int, default=500, help="Number of samples to process")
    args = parser.parse_args()

    print(f"Loading {args.samples} samples from bitext/Bitext-customer-support-llm-chatbot-training-dataset...")
    dataset = load_dataset("bitext/Bitext-customer-support-llm-chatbot-training-dataset", split=f"train[:{args.samples}]")
    test_batch = [{"utterance": item["instruction"], "true_intent": item["intent"]} for item in dataset]

    # Initialize systems
    print("Initializing systems...")
    sparsi_graph = build_sparsi_graph()
    lc_agent = build_langchain_agent()

    results = {
        "sparsi": {"correct": 0, "total_time": 0.0, "failures": 0, "wall_time": 0.0, "tokens": 0},
        "langchain": {"correct": 0, "total_time": 0.0, "failures": 0, "wall_time": 0.0, "tokens": 0}
    }

    print("\n--- Running Sparsi Benchmark ---")
    sparsi_sem = asyncio.Semaphore(60)
    
    async def run_sparsi_item(item):
        async with sparsi_sem:
            start_time = time.time()
            try:
                engine = Engine(sparsi_graph, reporter=None)
                extracted_json, in_toks, out_toks = await run_sparsi(engine, item["utterance"])
                elapsed = time.time() - start_time
                
                predicted_intent = extracted_json.get("intent", "")
                
                true_intent = item["true_intent"]
                    
                correct = int(predicted_intent == true_intent)
                return {"elapsed": elapsed, "correct": correct, "failure": 0, "tokens": in_toks + out_toks}
            except Exception as e:
                return {"elapsed": time.time() - start_time, "correct": 0, "failure": 1, "tokens": 0}

    sparsi_wall_start = time.time()
    sparsi_tasks = [run_sparsi_item(item) for item in test_batch]
    for task in tqdm(asyncio.as_completed(sparsi_tasks), total=len(test_batch), desc="Sparsi"):
        res = await task
        results["sparsi"]["total_time"] += res["elapsed"]
        results["sparsi"]["correct"] += res["correct"]
        results["sparsi"]["failures"] += res["failure"]
        results["sparsi"]["tokens"] += res["tokens"]
    results["sparsi"]["wall_time"] = time.time() - sparsi_wall_start

    print("\n--- Running LangChain Benchmark ---")
    lc_sem = asyncio.Semaphore(60)
    
    async def run_lc_item(item):
        async with lc_sem:
            start_time = time.time()
            try:
                prompt = f"Classify the following utterance into one of the valid intents. You MUST use the get_available_intents tool to fetch the intents first. Then return ONLY the exact intent string and nothing else. Utterance: {item['utterance']}"
                response = await lc_agent.ainvoke({"messages": [("user", prompt)]})
                
                elapsed = time.time() - start_time
                
                content = response["messages"][-1].content
                if isinstance(content, list):
                    text_parts = [p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"]
                    predicted_intent = " ".join(text_parts).strip()
                else:
                    predicted_intent = str(content).strip()
                    
                # Clean markdown or common prefixes
                predicted_intent = predicted_intent.replace("**", "").replace("`", "")
                for intent in AVAILABLE_INTENTS:
                    if intent in predicted_intent:
                        predicted_intent = intent
                        break
                
                true_intent = item["true_intent"]
                    
                correct = int(predicted_intent == true_intent)
                
                # Extract tokens
                toks = 0
                if "messages" in response:
                    for msg in response["messages"]:
                        if hasattr(msg, "usage_metadata") and msg.usage_metadata:
                            toks += msg.usage_metadata.get("input_tokens", 0)
                            toks += msg.usage_metadata.get("output_tokens", 0)
                
                return {"elapsed": elapsed, "correct": correct, "failure": 0, "tokens": toks}
            except Exception as e:
                print(f"LangChain error: {e}")
                return {"elapsed": time.time() - start_time, "correct": 0, "failure": 1, "tokens": 0}

    lc_wall_start = time.time()
    lc_tasks = [run_lc_item(item) for item in test_batch]
    for task in tqdm(asyncio.as_completed(lc_tasks), total=len(test_batch), desc="LangChain"):
        res = await task
        results["langchain"]["total_time"] += res["elapsed"]
        results["langchain"]["correct"] += res["correct"]
        results["langchain"]["failures"] += res["failure"]
        results["langchain"]["tokens"] += res["tokens"]
    results["langchain"]["wall_time"] = time.time() - lc_wall_start

    # Calculate metrics
    print("\n\n==========================================")
    print("             BENCHMARK RESULTS            ")
    print("==========================================")
    
    df = pd.DataFrame([
        {
            "System": "Sparsi (Structured)",
            "Accuracy": f"{(results['sparsi']['correct'] / args.samples) * 100:.2f}%",
            "Avg Latency (s)": f"{(results['sparsi']['total_time'] / args.samples):.2f}",
            "Wall Time (s)": f"{results['sparsi']['wall_time']:.2f}",
            "Total Tokens": results["sparsi"]["tokens"],
            "Failures": results["sparsi"]["failures"]
        },
        {
            "System": "LangChain (Agentic)",
            "Accuracy": f"{(results['langchain']['correct'] / args.samples) * 100:.2f}%",
            "Avg Latency (s)": f"{(results['langchain']['total_time'] / args.samples):.2f}",
            "Wall Time (s)": f"{results['langchain']['wall_time']:.2f}",
            "Total Tokens": results["langchain"]["tokens"],
            "Failures": results["langchain"]["failures"]
        }
    ])
    
    print(df.to_string(index=False))
    print("==========================================")

if __name__ == "__main__":
    asyncio.run(main())
