# OpenClaw Workflow Engine — Rebuild Plan

## Goal

Rebuild a **real workflow engine repository** from the current workspace, instead of continuing to polish a polluted workspace snapshot.

The new repository should satisfy this bar:

1. clone
2. install
3. run one smoke workflow
4. pass one minimal CI workflow

## What should be in the new repo

### Keep (core product)

- `core/engine/`
- `core/runtime/`
- `core/infra/skill_contracts.py`
- `core/infra/skill_manager.py`
- `core/infra/legacy_registry_adapter.py` (only if still required by runtime closure)
- `core/agent/base_agent.py` (only if runtime/constitution path requires it)
- selected tests:
  - `core/tests/test_skill_manager_smoke.py`
  - `core/tests/test_base_agent_constitution.py`
  - `core/tests/test_constitution_runtime.py`
- `workflows/test_chaining.yaml`
- `workflows/test_chaos_core.yaml`
- one clean smoke workflow
- minimal CLI entrypoint
- minimal CI
- root README
- dependency manifest

### Maybe keep (only if needed)

- `core/infra/circuit_breaker.py`
- `core/engine/task_verifier.py`
- `core/engine/wal_engine.py`
- `core/engine/workflow_context.py`
- `core/engine/workflow_registry.py`
- progress/long-task modules under `core/runtime/`

### Exclude (do not carry into new repo)

- `.openclaw/`
- `.clawhub/`
- `.learnings/`
- `memory/`
- `projects/`
- `domain/`
- host persona files: `AGENTS.md`, `SOUL.md`, `USER.md`, `HEARTBEAT.md`, `IDENTITY.md`, `KILL_SWITCH.md`, `SESSION-STATE.md`, startup cards
- unrelated skills bulk under `skills/`
- workflow logs and registry runtime artifacts
- operational scripts not directly tied to engine runtime

## Why the old repo is wrong

The current public repo is not an engine repo. It is a mixed host workspace snapshot containing:

- runtime code
- host memory system
- user/persona configuration
- side projects
- operational residue
- workflow runtime artifacts

That makes the repo misleading, hard to onboard, and structurally invalid as a reusable engine codebase.

## Minimal target repo shape

```text
openclaw-workflow-engine/
├─ README.md
├─ pyproject.toml            # or requirements.txt
├─ .gitignore
├─ .github/
│  └─ workflows/
│     └─ ci.yml
├─ core/
│  ├─ engine/
│  ├─ runtime/
│  ├─ infra/
│  └─ agent/
├─ tests/
│  ├─ test_skill_manager_smoke.py
│  ├─ test_base_agent_constitution.py
│  └─ test_constitution_runtime.py
├─ workflows/
│  ├─ smoke.yaml
│  ├─ test_chaining.yaml
│  └─ test_chaos_core.yaml
└─ scripts/
   └─ check_constitution_boundaries.py
```

## Immediate next steps

1. Create a fresh directory/repo, do not continue mutating the polluted repo.
2. Copy only runtime-critical files.
3. Rename `core/tests/` selected files into top-level `tests/` if possible.
4. Replace legacy skill coupling with one deterministic built-in smoke adapter.
5. Make `workflow run smoke.yaml` pass locally.
6. Make CI run that smoke path plus minimal tests.

## Current blocker to true usability

The current workflow runtime does not form a clean standalone execution closure.
Example: `test_chaining.yaml` fails with `Skill not found: echo-skill`, so the engine is not yet independently runnable as a public product.
