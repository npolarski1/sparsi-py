# Ticket Triage Benchmark

This benchmark evaluates the performance of Sparsi vs LangChain for a structured extraction and classification task: Customer Support Ticket Triage.

## Task Description
The goal is to accurately classify incoming customer support messages into one of several predefined intents. 

## Dataset
We use the `bitext/Bitext-customer-support-llm-chatbot-training-dataset` from Hugging Face.

## Systems Compared
1. **Sparsi (Structured)**: Uses a compiled workflow graph (`dagor`) and the `gemini-3.1-flash-lite` model to perform a single-step, constrained generation extraction of the intent.
2. **LangChain (Structured)**: Uses LangChain's `with_structured_output` capability and the `gemini-3.1-flash-lite` model to extract the exact intent structure.

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
- **Failures**: Number of failed extractions (due to LLM format errors, timeout, etc.).
