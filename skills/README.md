# sparsi-py Skills

Two skill packages for designing and generating sparsi-py DAG workflows inside Claude Code
(or any AI assistant that supports the `SKILL.md / references/` convention).

**This bundle targets `github.com/akennis/sparsi-py v0.1.0`.**

## Packages

| Package | Purpose |
|---|---|
| `sparsi-py-design` | Design a maximally deterministic DAG workflow from a task description |
| `sparsi-py-codegen` | Generate runnable Python code from an approved DAG design |

## Typical workflow

1. `/sparsi-py-design` — describe your task; the skill produces a structured design document.
2. Refine the design until you approve it.
3. `/sparsi-py-codegen` — provide the approved design; the skill writes a Python workflow file using `dagor.Builder`.
4. Run the Python script.

## Installation

These skills work with **Claude Code** — available as a CLI, desktop app, and IDE extension.

### Project-local install (available only in the current project)

```
cp -r skills/sparsi-py-design  .claude/skills/
cp -r skills/sparsi-py-codegen .claude/skills/
```

Then invoke with `/sparsi-py-design` or `/sparsi-py-codegen`.

## Required environment variables

| Variable | When needed |
|---|---|
| `ANTHROPIC_API_KEY` | Any workflow that includes AI ops backed by Claude |
| `GOOGLE_API_KEY` | Any workflow that includes AI ops backed by Gemini (the default) |
