# Advanced Ticket Triage Benchmark

This benchmark evaluates the performance of Sparsi vs LangChain for a realistic multi-step workflow: **Advanced Customer Support Ticket Triage**.

## Task Description
Real-world pipelines rarely classify intent blindly. This benchmark tests a strict 5-step sequence:
1. **Information Extraction**: Extract `order_id`, `product_details`, and `user_email` from the ticket.
2. **Sentiment Analysis**: Analyze the sentiment and assign an `urgency_score` (1-5).
3. **Intent Classification**: Classify the core intent based on the raw utterance, extracted info, and sentiment.
4. **Policy Checking**: Determine the appropriate action (`escalate`, `standard_process`, `reject`) based on the intent and urgency score.
5. **Draft Response**: Draft a final polite response email to the user based on the original utterance, classified intent, and policy action.

## Dataset
We use the `bitext/Bitext-customer-support-llm-chatbot-training-dataset` from Hugging Face.

## Systems Compared
1. **Sparsi (Multi-Step DAG)**: Uses a compiled workflow graph (`dagor`) and `gemini-3.1-flash-lite` to execute the 5 steps. Each step is represented as a distinct `Operator` node. Sparsi extracts the exact data needed from each node and feeds it sequentially downstream. This deterministic routing guarantees execution order with zero ReAct scratchpad overhead.
2. **LangChain (ReAct Agent)**: Uses a LangChain `create_react_agent` equipped with 5 tools matching the steps above, and strict system prompt instructions to execute them in exact sequential order. This represents the common dynamic agentic ReAct loop approach.

## How to Run

Ensure your environment variables for `GEMINI_API_KEY` are set.

```bash
python main.py --samples 50
```

You can adjust the number of samples with the `--samples` flag.

## Metrics
The benchmark measures several performance characteristics. Notably, it measures a strict **Pipeline Accuracy**.

### Pipeline Accuracy Evaluation
A pipeline's execution is considered correct **ONLY IF** it correctly executes all three of the major outputs:
1. **Intent Matching**: The predicted intent string must exactly match the dataset's ground truth intent.
2. **Policy Matching**: The predicted policy action must exactly match the deterministically generated ground truth policy action. The ground truth rules are:
   - `escalate` if intent is `complaint`, `payment_issue`, or `contact_human_agent`
   - `reject` if intent is `cancel_order` or `get_refund`
   - `standard_process` for all others
3. **Draft Response Judging**: A completely separate LLM call (`gemini-3.5-flash`) acts as a Judge. It reviews the original utterance, true intent, true policy, and the generated email. It must return a `PASS` (meaning the email politely addressed the user and followed the policy). The time and tokens for this evaluation are **not** counted against the benchmark.

If any of these three checks fail, the entire sample is marked as a failure for accuracy.

### Other Metrics
- **Avg Latency (s)**: Average time taken per request across the 5 steps.
- **Total Time (s)**: Total wall-clock processing time for the batch.
- **Failures**: Number of pipeline crashes or exceptions.
- **Total Tokens**: The sum of input and output tokens consumed across all benchmarked LLM calls.

### Results
For a 100 sample test batch, there is a massive disparity in token usage, latency, and accuracy:

| System | Pipeline Accuracy | Avg Latency (s) | Total Tokens (100 samples) |
| :--- | :--- | :--- | :--- |
| Sparsi (Multi-Step DAG) | 100.00% | ~2.59s | ~86,101 |
| LangChain (ReAct Agent) | 0.00% | ~7.65s | ~681,447 |

### Conclusion
When tasked with a realistic 5-step pipeline, Sparsi's deterministic DAG architecture provides an enormous advantage. LangChain's reliance on dynamic ReAct loops causes its token consumption to skyrocket by roughly **8x** due to its expanding history scratchpad, and its latency spikes to nearly **3x** slower than Sparsi.

More importantly, LangChain achieves **0.00% pipeline accuracy** because it consistently fails the strict state-passing check. In a ReAct agent, state is simply appended as text to the context scratchpad. The agent receives the complex user profile JSON string from the `fetch_user_context` tool, and is later expected to perfectly reconstruct and pass that exact dictionary into the `send_email` tool. LLMs consistently struggle to perfectly preserve and reconstruct large, nested JSON objects (like the user profile with its generated tokens) across multiple tool calls from their text history.

Sparsi executes the exact same logic sequence but achieves **100.00% accuracy**. This is because its DAG architecture deterministically passes the native Python dictionary object directly between nodes. It never forces the LLM to reconstruct the state from its prompt history, resulting in a perfectly reliable, incredibly fast, and lightweight pipeline.
