# Comic Adapters

This document defines the first real adapter boundary for comic workflow integration.

## Goals

Keep unstable external skill behavior outside the DAG core by adding:

- strict input validation
- normalized output contracts
- timeout / adapter error isolation
- structured node-level logging

## First adapters

### 1. `comic-script`
Tool: `real-comic-workflow/script_generate`

Input contract:
- `topic: str`
- `panels: int > 0`

Output contract:
- `script_outline: str`
- `panels: int`
- `source_skill: "comic-script"`

### 2. `baoyu-comic`
Tool: `real-comic-workflow/knowledge_comic_plan`

Input contract:
- `topic: str`
- `source_text: str`
- optional style fields: `art`, `tone`, `layout`, `aspect`, `lang`

Output contract:
- `topic: str`
- `command_preview: str`
- `output_dir: str`
- `source_skill: "baoyu-comic"`

## Failure model

Adapters return normalized failure classes:

- `ADAPTER_VALIDATION_ERROR`
- `ADAPTER_TIMEOUT`
- `ADAPTER_ERROR`
- `ADAPTER_UNEXPECTED_ERROR`

## Logging

Structured logs are written to:

- `workflows/logs/comic-adapters.jsonl`

Each subprocess-backed adapter should log:
- start
- finish
- elapsed time
- preview of stdout / stderr
- timeout events
