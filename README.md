# OpenClaw Workflow Engine

A rebuilt engine-only repository for the workflow runtime.

## Scope

This repository contains only the core pieces needed to understand and evolve the workflow engine:

- DAG/YAML workflow loading and execution
- constitution/governed dispatch runtime
- skill contracts and manager
- minimal tests
- minimal workflow examples

## Quickstart

```bash
python3 -m pip install -r requirements.txt
python3 scripts/check_constitution_boundaries.py
python3 -m pytest -q tests/test_skill_manager_smoke.py tests/test_base_agent_constitution.py tests/test_constitution_runtime.py
```

## Current status

This is a rebuilt minimal engine skeleton extracted from a larger workspace. The next milestone is to make `workflow run` form a fully standalone execution closure.
