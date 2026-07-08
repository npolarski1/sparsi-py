import asyncio
import os
import time
import argparse
import pandas as pd
from tqdm import tqdm
from datasets import load_dataset
from typing import Any
import contextvars
import json

with open("prompts.json", "r") as f:
    PROMPTS = json.load(f)

# Sparsi imports
from dagor import Builder, Engine, Operator, register_operator, Input, Output
from pydantic import BaseModel, ConfigDict
from dagor.builtin import ContextValOp 
import sparsi.library

# Langchain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain_core.tools import tool

# Ensure API key is set
if "GEMINI_API_KEY" not in os.environ and "GOOGLE_API_KEY" not in os.environ:
    print("Warning: Neither GEMINI_API_KEY nor GOOGLE_API_KEY is set. Execution might fail.")

# -------------------------------------------------------------------
# INTENT DEFINITIONS & GROUND TRUTH RULES
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


def get_mock_user_profile(utterance: str) -> dict:
    import hashlib
    token = hashlib.md5(utterance.encode()).hexdigest()[:16]
    return {
        "user_email": "customer@example.com",
        "account_status": "active",
        "metadata": {
            "security_token": token,
            "session_id": "sess_" + token[:8]
        },
        "loyalty": {"tier": "gold", "points": 1450},
        "preferences": {"language": "en", "notifications": True}
    }

def get_true_policy(intent: str) -> str:
    """Deterministic rule to calculate the true policy action based on intent."""
    escalate_intents = ["complaint", "payment_issue", "contact_human_agent"]
    reject_intents = ["cancel_order", "get_refund"]
    
    if intent in escalate_intents:
        return "escalate"
    elif intent in reject_intents:
        return "reject"
    else:
        return "standard_process"

async def evaluate_response(utterance: str, intent: str, policy: str, email: str, expected_token: str) -> bool:
    """LLM-as-a-Judge to evaluate if the drafted email is accurate and appropriate."""
    if not email:
        return False
    if expected_token not in email:
        return False
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)
    prompt = f"""You are a strict Judge evaluating a customer support email.
UTTERANCE: '{utterance}'
EXPECTED INTENT: '{intent}'
EXPECTED POLICY ACTION: '{policy}'
DRAFT EMAIL TO EVALUATE: '{email}'

Does the draft email politely address the user's utterance, reflect the expected intent, and follow the expected policy action?
Respond with exactly one word: PASS or FAIL."""
    try:
        res = await llm.ainvoke(prompt)
        content = res.content
        if isinstance(content, list):
            text_parts = [p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"]
            text_content = " ".join(text_parts)
        else:
            text_content = str(content)
        text_content = text_content.strip().upper()
        return "PASS" in text_content
    except Exception as e:
        print(f"Judge error: {e}")
        return False

# -------------------------------------------------------------------
# SPARSI WORKFLOW (Context-Aware Multi-Step DAG)
# -------------------------------------------------------------------


@register_operator("FetchUserContextOp")
class FetchUserContextOp(Operator, BaseModel):
    model_config = ConfigDict(extra="allow")
    utterance: Input = None
    result: Output = None
    async def run(self, ctx: Any) -> None:
        self.result = get_mock_user_profile(self.utterance)

@register_operator("SendEmailOp")
class SendEmailOp(Operator, BaseModel):
    model_config = ConfigDict(extra="allow")
    intent_json: Input = None
    policy_json: Input = None
    draft_json: Input = None
    user_profile: Input = None
    result: Output = None
    
    async def run(self, ctx: Any) -> None:
        intent = self.intent_json.get("intent", "") if isinstance(self.intent_json, dict) else ""
        policy = self.policy_json.get("policy_action", "") if isinstance(self.policy_json, dict) else ""
        draft = self.draft_json.get("draft_email", "") if isinstance(self.draft_json, dict) else ""
        self.result = {"intent": intent, "policy_action": policy, "draft_email": draft, "user_profile": self.user_profile}

@register_operator("DeterministicPolicyOp")
class DeterministicPolicyOp(Operator, BaseModel):
    model_config = ConfigDict(extra="allow")
    intent_json: Input = None
    result: Output = None
    
    async def run(self, ctx: Any) -> None:
        intent = self.intent_json.get("intent", "") if isinstance(self.intent_json, dict) else ""
        policy = get_true_policy(intent)
        self.result = {"policy_action": policy}

@register_operator("FormatPolicyContextOp")
class FormatPolicyContextOp(Operator, BaseModel):
    model_config = ConfigDict(extra="allow")
    intent: Input = None
    sentiment: Input = None
    result: Output = None
    
    async def run(self, ctx: Any) -> None:
        self.result = f"INTENT: {self.intent}\nSENTIMENT: {self.sentiment}"

@register_operator("FormatDraftContextOp")
class FormatDraftContextOp(Operator, BaseModel):
    model_config = ConfigDict(extra="allow")
    utterance: Input = None
    intent: Input = None
    policy: Input = None
    profile: Input = None
    sentiment: Input = None
    result: Output = None
    
    async def run(self, ctx: Any) -> None:
        self.result = f"UTTERANCE: {self.utterance}\nINTENT: {self.intent}\nPOLICY: {self.policy}\nPROFILE: {self.profile}\nSENTIMENT: {self.sentiment}"

@register_operator("Sum4TokensOp")
class Sum4TokensOp(Operator, BaseModel):
    model_config = ConfigDict(extra="allow")
    in2: Input = None
    out2: Input = None
    in3: Input = None
    out3: Input = None
    in4: Input = None
    out4: Input = None
    in5: Input = None
    out5: Input = None
    total_in: Output = None
    total_out: Output = None
    
    async def run(self, ctx: Any) -> None:
        self.total_in = sum(filter(None, [self.in2, self.in3, self.in4, self.in5]))
        self.total_out = sum(filter(None, [self.out2, self.out3, self.out4, self.out5]))

def build_sparsi_graph():
    b = Builder("advanced_triage")
    b.vertex("input").op("ContextValOp").params({"key": "utterance"}).output("result", "raw_utterance")
    
    # 1. Fetch Context
    b.vertex("fetch_user_context").op("FetchUserContextOp") \
      .input("utterance", "raw_utterance") \
      .output("result", "user_profile")
      
    # 2. Analyze Sentiment
    b.vertex("analyze_sentiment").op("AIExtractMapOp").params({
        "model": "gemini-3.1-flash-lite",
        "operation": PROMPTS["sparsi_sentiment"]
    }).input("input", "raw_utterance") \
      .output("result", "sentiment_json").output("usage_input_tokens", "in2").output("usage_output_tokens", "out2")
      
    # 3. Classify Intent
    b.vertex("classify_intent").op("AIExtractMapOp").params({
        "model": "gemini-3.1-flash-lite",
        "operation": PROMPTS["sparsi_intent"].replace("{INTENT_LIST_STR}", INTENT_LIST_STR)
    }).input("input", "raw_utterance") \
      .output("result", "intent_json").output("usage_input_tokens", "in3").output("usage_output_tokens", "out3")
      
    # 4. Check Policy
    b.vertex("check_policy").op("DeterministicPolicyOp") \
      .input("intent_json", "intent_json") \
      .output("result", "policy_json")

    # Helper: Format Draft Context
    b.vertex("format_draft_ctx").op("FormatDraftContextOp") \
      .input("utterance", "raw_utterance").input("intent", "intent_json").input("policy", "policy_json").input("profile", "user_profile").input("sentiment", "sentiment_json") \
      .output("result", "draft_ctx")

    # 5. Draft Response
    b.vertex("draft_response").op("AIExtractMapOp").params({
        "model": "gemini-3.1-flash-lite",
        "operation": PROMPTS["sparsi_draft"]
    }).input("input", "draft_ctx") \
      .output("result", "draft_json").output("usage_input_tokens", "in5").output("usage_output_tokens", "out5")
      
    # Helper: Combine Results
    b.vertex("combine_results").op("SendEmailOp") \
      .input("intent_json", "intent_json").input("policy_json", "policy_json").input("draft_json", "draft_json").input("user_profile", "user_profile") \
      .output("result", "final_result")

    # Helper: Sum Tokens
    b.vertex("sum_tokens").op("Sum4TokensOp") \
        .input("in2", "in2").input("out2", "out2") \
        .input("in3", "in3").input("out3", "out3") \
        .input("in5", "in5").input("out5", "out5") \
        .output("total_in", "in_toks").output("total_out", "out_toks")
        
    return b.build()

async def run_sparsi(engine: Engine, utterance: str) -> tuple[dict, int, int]:
    await engine.run({"utterance": utterance})
    final_result, _ = engine.get_output("final_result")
    in_toks, _ = engine.get_output("in_toks")
    out_toks, _ = engine.get_output("out_toks")
    
    return final_result or {}, in_toks or 0, out_toks or 0

# -------------------------------------------------------------------
# LANGCHAIN AGENT (Multi-Step ReAct)
# -------------------------------------------------------------------
lc_tokens_var = contextvars.ContextVar("lc_tokens", default=0)

def track_tokens(res):
    if hasattr(res, "usage_metadata") and res.usage_metadata:
        toks = res.usage_metadata.get("input_tokens", 0) + res.usage_metadata.get("output_tokens", 0)
        lc_tokens_var.set(lc_tokens_var.get() + toks)

lc_profile_var = contextvars.ContextVar("lc_profile")

@tool
async def fetch_user_context(utterance: str) -> str:
    """Fetch the complex JSON user profile for the customer using their utterance."""
    import json
    return json.dumps(get_mock_user_profile(utterance))

@tool
async def send_email(body: str, user_profile: dict) -> str:
    """Send the drafted email to the customer. You MUST pass the exact user_profile dictionary you fetched."""
    state = lc_profile_var.get()
    state.clear()
    state.update(user_profile)
    return "Email sent successfully."

def build_langchain_agent():
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0)
    tools = [fetch_user_context, send_email]
    agent_executor = create_agent(llm, tools)
    return agent_executor

# -------------------------------------------------------------------
# BENCHMARK RUNNER
# -------------------------------------------------------------------
async def main():
    parser = argparse.ArgumentParser(description="Benchmark Sparsi vs LangChain - Advanced Triage")
    parser.add_argument("--samples", type=int, default=50, help="Number of samples to process")
    args = parser.parse_args()

    print(f"Loading {args.samples} samples from bitext/Bitext-customer-support-llm-chatbot-training-dataset...")
    dataset: Any = load_dataset("bitext/Bitext-customer-support-llm-chatbot-training-dataset", split=f"train[:{args.samples}]")
    test_batch = [{"utterance": item["instruction"], "true_intent": item["intent"]} for item in dataset]

    print("Initializing systems...")
    sparsi_graph = build_sparsi_graph()
    lc_agent = build_langchain_agent()

    results = {
        "sparsi": {"correct": 0, "total_time": 0.0, "failures": 0, "wall_time": 0.0, "tokens": 0},
        "langchain": {"correct": 0, "total_time": 0.0, "failures": 0, "wall_time": 0.0, "tokens": 0}
    }

    print("\n--- Running Sparsi Benchmark ---")
    sparsi_sem = asyncio.Semaphore(20)
    
    async def run_sparsi_item(item):
        async with sparsi_sem:
            start_time = time.time()
            try:
                engine = Engine(sparsi_graph, reporter=None)
                final_result, in_toks, out_toks = await run_sparsi(engine, item["utterance"])
                elapsed = time.time() - start_time
                
                predicted_intent = final_result.get("intent", "")
                predicted_policy = final_result.get("policy_action", "")
                predicted_email = final_result.get("draft_email", "")
                
                true_intent = item["true_intent"]
                true_policy = get_true_policy(true_intent)
                
                # Check all components for full pipeline accuracy
                intent_correct = int(predicted_intent == true_intent)
                policy_correct = int(predicted_policy == true_policy)
                
                predicted_profile = final_result.get("user_profile", {})
                true_profile = get_mock_user_profile(item["utterance"])
                profile_correct = 1 if predicted_profile == true_profile else 0
                
                response_correct = 1 if await evaluate_response(item["utterance"], true_intent, true_policy, predicted_email, true_profile["metadata"]["security_token"]) else 0
                pipeline_correct = 1 if (intent_correct and policy_correct and response_correct and profile_correct) else 0
                print(f"Sparsi [Intent: {intent_correct}] [Policy: {policy_correct}] [Profile: {profile_correct}] [Response: {response_correct}]")
                
                return {"elapsed": elapsed, "correct": pipeline_correct, "failure": 0, "tokens": in_toks + out_toks}
            except Exception as e:
                import traceback
                traceback.print_exc()
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
    lc_sem = asyncio.Semaphore(20)
    
    async def run_lc_item(item):
        async with lc_sem:
            start_time = time.time()
            # Reset contextvar for this run
            lc_tokens_var.set(0)
            profile_state = {}
            lc_profile_var.set(profile_state)
            try:
                prompt = PROMPTS["langchain_prompt"].replace("{utterance}", item['utterance']).replace("{INTENT_LIST_STR}", INTENT_LIST_STR)
                
                response = await lc_agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
                elapsed = time.time() - start_time
                
                content = response["messages"][-1].content
                if isinstance(content, list):
                    text_parts = [p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"]
                    final_text = " ".join(text_parts).strip()
                else:
                    final_text = str(content).strip()
                
                # Extract predictions from the text response
                predicted_intent = ""
                for intent in AVAILABLE_INTENTS:
                    if intent in final_text:
                        predicted_intent = intent
                        break
                        
                predicted_policy = ""
                for policy in ["escalate", "standard_process", "reject"]:
                    if policy in final_text:
                        predicted_policy = policy
                        break
                
                true_intent = item["true_intent"]
                true_policy = get_true_policy(true_intent)
                
                intent_correct = int(predicted_intent == true_intent)
                policy_correct = int(predicted_policy == true_policy)
                
                # Attempt to extract draft email (everything after 'draft_email': if present)
                predicted_email = ""
                try:
                    if "{" in final_text and "}" in final_text:
                        json_str = final_text[final_text.find("{"):final_text.rfind("}")+1]
                        parsed = json.loads(json_str)
                        predicted_email = parsed.get("draft_email", "")
                except:
                    predicted_email = final_text
                
                true_profile = get_mock_user_profile(item["utterance"])
                response_correct = 1 if await evaluate_response(item["utterance"], true_intent, true_policy, predicted_email, true_profile["metadata"]["security_token"]) else 0
                
                actual_profile = profile_state
                profile_correct = 1 if actual_profile == true_profile else 0
                
                pipeline_correct = 1 if (intent_correct and policy_correct and response_correct and profile_correct) else 0
                print(f"LC [Intent: {intent_correct}] [Policy: {policy_correct}] [Profile: {profile_correct}] [Response: {response_correct}]")
                
                # Add agent's ReAct loop tokens
                agent_toks = 0
                if "messages" in response:
                    for msg in response["messages"]:
                        if hasattr(msg, "usage_metadata") and msg.usage_metadata:
                            agent_toks += msg.usage_metadata.get("input_tokens", 0)
                            agent_toks += msg.usage_metadata.get("output_tokens", 0)
                
                total_toks = agent_toks + lc_tokens_var.get()
                
                return {"elapsed": elapsed, "correct": pipeline_correct, "failure": 0, "tokens": total_toks}
            except Exception as e:
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
            "System": "Sparsi (Multi-Step DAG)",
            "Pipeline Accuracy": f"{(results['sparsi']['correct'] / args.samples) * 100:.2f}%",
            "Avg Latency (s)": f"{(results['sparsi']['total_time'] / args.samples):.2f}",
            "Wall Time (s)": f"{results['sparsi']['wall_time']:.2f}",
            "Total Tokens": results["sparsi"]["tokens"],
            "Failures": results["sparsi"]["failures"]
        },
        {
            "System": "LangChain (ReAct Agent)",
            "Pipeline Accuracy": f"{(results['langchain']['correct'] / args.samples) * 100:.2f}%",
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
