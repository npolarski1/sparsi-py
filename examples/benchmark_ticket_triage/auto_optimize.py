import os
import json
import subprocess
import re

# Generation 2 Champions
BASELINE_SPARSI_SENTIMENT = "Return 'sentiment' (positive/neutral/negative) and 'urgency_score' (1-5)."
BASELINE_SPARSI_INTENT = "Classify 'intent' into EXACTLY one of: {INTENT_LIST_STR}"
BASELINE_SPARSI_POLICY = "Return 'policy_action': 'escalate' if ['complaint', 'payment_issue', 'contact_human_agent'], 'reject' if ['cancel_order', 'get_refund'], else 'standard_process'."
BASELINE_SPARSI_DRAFT = "Draft polite email for UTTERANCE, acknowledging SENTIMENT/urgency, using POLICY. MUST end with 'Security Token: [token from metadata]'. Return 'draft_email'."

# Langchain plateaued at its Gen 0 baseline, so we lock it in.
BASELINE_LANGCHAIN = """You are an AI customer support agent. A customer said: '{utterance}'.
Your goal is to perform the following:
1. Fetch the user's profile using the `fetch_user_context` tool.
2. Analyze the sentiment (positive/neutral/negative) and assign an urgency_score (1-5).
3. Classify their intent into EXACTLY one of the following: {INTENT_LIST_STR}.
4. Determine the policy_action ('escalate', 'standard_process', 'reject'). Rules: if intent is in ['complaint', 'payment_issue', 'contact_human_agent'] then 'escalate'. If intent is in ['cancel_order', 'get_refund'] then 'reject'. Otherwise 'standard_process'.
5. Draft a polite customer support email response based on the utterance, intent, policy action, and the user profile. Make sure to acknowledge the user's sentiment and urgency in the response. The email MUST end with 'Security Token: [token from metadata]'.
6. Send the drafted email using the `send_email` tool, passing your drafted email as 'body' and the exact user profile dictionary you fetched as 'user_profile'.

Finally, return your answer as a JSON object with exactly three keys: 'intent', 'policy_action', and 'draft_email' (the email you sent). Do not include Markdown code blocks around the JSON."""

# GENERATION 3: Final Plateau Check
# Branching off the S2 champion to see if we can shave a few more words without breaking it.

SPARSI_CANDIDATES = [
    # G3-S1: Remove explicit choices from sentiment
    {
        "sparsi_sentiment": "Return 'sentiment' and 'urgency_score'.",
        "sparsi_intent": BASELINE_SPARSI_INTENT,
        "sparsi_policy": BASELINE_SPARSI_POLICY,
        "sparsi_draft": BASELINE_SPARSI_DRAFT
    },
    # G3-S2: Condense policy array syntax
    {
        "sparsi_sentiment": BASELINE_SPARSI_SENTIMENT,
        "sparsi_intent": BASELINE_SPARSI_INTENT,
        "sparsi_policy": "Return 'policy_action': 'escalate' if complaint/payment_issue/contact_human, 'reject' if cancel_order/get_refund, else 'standard_process'.",
        "sparsi_draft": BASELINE_SPARSI_DRAFT
    }
]

def run_benchmark():
    result = subprocess.run(["python3", "main.py", "--samples", "20"], capture_output=True, text=True)
    
    sparsi_acc, sparsi_tokens = 0, 0
    lc_acc, lc_tokens = 0, 0
    
    for line in result.stdout.splitlines():
        if "Sparsi (Multi-Step DAG)" in line:
            parts = line.split()
            sparsi_acc = float(parts[-5].replace("%", ""))
            sparsi_tokens = int(parts[-2])
        if "LangChain (ReAct Agent)" in line:
            parts = line.split()
            lc_acc = float(parts[-5].replace("%", ""))
            lc_tokens = int(parts[-2])
            
    return sparsi_acc, sparsi_tokens, lc_acc, lc_tokens

def save_prompts(prompts_dict):
    with open("prompts.json", "w") as f:
        json.dump(prompts_dict, f, indent=4)

if __name__ == "__main__":
    best_sparsi_prompts = {
        "sparsi_sentiment": BASELINE_SPARSI_SENTIMENT,
        "sparsi_intent": BASELINE_SPARSI_INTENT,
        "sparsi_policy": BASELINE_SPARSI_POLICY,
        "sparsi_draft": BASELINE_SPARSI_DRAFT
    }
    
    print("--- EVALUATING BASELINE (GEN 2 WINNER) ---")
    prompts = {**best_sparsi_prompts, "langchain_prompt": BASELINE_LANGCHAIN}
    save_prompts(prompts)
    sa, st, la, lt = run_benchmark()
    
    best_sparsi_acc = sa
    best_sparsi_tokens = st
    
    print(f"Baseline -> Sparsi: {sa}% ({st} tokens)")
    
    # Test Sparsi Candidates
    for i, candidate in enumerate(SPARSI_CANDIDATES):
        print(f"\\n--- EVALUATING SPARSI G3-S{i+1} ---")
        prompts = {**candidate, "langchain_prompt": BASELINE_LANGCHAIN}
        save_prompts(prompts)
        sa, st, la, lt = run_benchmark()
        print(f"Candidate S{i+1} -> Sparsi: {sa}% ({st} tokens)")
        
        if sa > best_sparsi_acc or (sa == best_sparsi_acc and st < best_sparsi_tokens):
            print("  *** NEW SPARSI CHAMPION ***")
            best_sparsi_acc = sa
            best_sparsi_tokens = st
            best_sparsi_prompts = candidate
            
    # Save best
    print("\\n--- GENERATION 3 COMPLETE ---")
    final_prompts = {**best_sparsi_prompts, "langchain_prompt": BASELINE_LANGCHAIN}
    save_prompts(final_prompts)
    print("Saved best Generation 3 prompts to prompts.json!")
    print(f"Final Winning Sparsi: {best_sparsi_acc}% ({best_sparsi_tokens} tokens)")
