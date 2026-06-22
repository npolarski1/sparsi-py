# Basic RAG Example

A simple Retrieval-Augmented Generation (RAG) workflow demonstrating the core components of grounded question answering.

## Overview

1.  **Retrieve**: Fetches "documents" (mocked in this example) relevant to the user's query.
2.  **Generate**: Uses Gemini to answer the query based on the retrieved context.
3.  **Validate**: Uses `ValidateCitationsOp` to ensure any citations in the answer actually exist in the retrieved set.

## Usage

```bash
python main.py --query "How do I return an item?"
```

## Prerequisites

- `GEMINI_API_KEY` or `GOOGLE_API_KEY` environment variable.
