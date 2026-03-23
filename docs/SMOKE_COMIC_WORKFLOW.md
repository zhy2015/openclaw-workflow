# Comic Workflow Smoke

This smoke workflow validates the intended high-level comic workflow topology before wiring real external skills.

## Goal

Model this chain inside the workflow engine:

1. `intent_classify`
2. `script_generate`
3. `character_reference_generate`
4. `comic_render_generate`
5. `package_output`

## Current mode

For now, all nodes use the built-in deterministic `builtin-smoke` skill.
This proves that:

- YAML workflow loading works
- node-to-node output chaining works
- DAG execution order works
- workflow registry + WAL capture a complete end-to-end run

## Planned next step

Replace the placeholder nodes with real adapters for:

- `comic-script`
- `anime-avatar-generation`
- `comi-cog`
- `baoyu-comic`

## Workflow file

- `workflows/comic_workflow_smoke.yaml`
