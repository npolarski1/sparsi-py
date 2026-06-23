# Ticket Triage Benchmark

This benchmark evaluates the performance of Sparsi vs LangChain for a realistic multi-step workflow: Context-Aware Customer Support Ticket Triage.

## Task Description
Real-world pipelines rarely classify intent blindly. This benchmark tests a strict 2-step sequence:
1. **Context Extraction**: The system must extract the tone, language, and key entities from the ticket.
2. **Intent Classification**: The system uses the raw utterance *combined* with the extracted context to classify the message into one of 27 predefined intents.

## Dataset
We use the `bitext/Bitext-customer-support-llm-chatbot-training-dataset` from Hugging Face.

## Systems Compared
1. **Sparsi (Multi-Step DAG)**: Uses a compiled workflow graph (`dagor`) and `gemini-3.1-flash-lite` to execute the two steps. Node 1 extracts context and feeds it directly into Node 2 which classifies the intent. This deterministic routing guarantees execution order with zero ReAct scratchpad overhead.
2. **LangChain (ReAct Agent)**: Uses a LangChain `create_react_agent` equipped with two tools (`extract_context`, `classify_intent`) and strict system prompt instructions to execute them in order. This represents the common dynamic agent approach.

## How to Run

Ensure your environment variables for `GEMINI_API_KEY` are set.

```bash
python main.py --samples 500
```

You can adjust the number of samples with the `--samples` flag.

## Metrics
The benchmark measures:
- **Accuracy**: Percentage of correctly identified intents.
- **Avg Latency (s)**: Average time taken per request.
- **Total Time (s)**: Total processing time for the batch.
- **Failures**: Number of failed extractions.
- **Total Tokens**: The sum of input and output tokens consumed across all LLM calls.

### Results
Based on a run of 500 samples from `bitext/Bitext-customer-support-llm-chatbot-training-dataset` using `gemini-3.1-flash-lite`:

| System | Accuracy | Avg Latency (s) | Wall Time (s) | Total Tokens | Failures |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Sparsi (Multi-Step DAG) | 98.40% | 1.14 | 10.09 | 165,395 | 0 |
| LangChain (ReAct Agent) | 98.60% | 7.15 | 65.80 | 1,166,121 | 0 |

### Conclusion
When tasked with a realistic multi-step pipeline, Sparsi's deterministic DAG architecture provides an enormous advantage. While both systems achieved high accuracy (>98%), LangChain's reliance on dynamic ReAct loops caused its token consumption to skyrocket to over **1.1 million tokens (a 7x increase)** and its latency to spike to over **7 seconds per request (a 6x slowdown)**. Sparsi executed the exact same logic sequence nearly instantaneously with minimal token overhead.
