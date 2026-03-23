# Migration Inventory

## Recommended copy set for the new repo

### Core engine
- `core/engine/cli.py`
- `core/engine/dag_engine.py`
- `core/engine/runner.py`
- `core/engine/yaml_workflow.py`
- `core/engine/task_verifier.py`
- `core/engine/wal_engine.py`
- `core/engine/workflow_context.py`
- `core/engine/workflow_registry.py`

### Runtime
- `core/runtime/constitution.py`
- `core/runtime/dispatch.py`
- `core/runtime/policies.py`
- `core/runtime/router.py`
- `core/runtime/types.py`

### Infra
- `core/infra/skill_contracts.py`
- `core/infra/skill_manager.py`
- `core/infra/legacy_registry_adapter.py`  # temporary, until replaced
- `core/infra/circuit_breaker.py`          # if BaseAgent/runtime still imports it

### Agent layer
- `core/agent/base_agent.py`

### Minimal tests
- `core/tests/test_skill_manager_smoke.py`
- `core/tests/test_base_agent_constitution.py`
- `core/tests/test_constitution_runtime.py`

### Minimal workflows
- `workflows/test_chaining.yaml`
- `workflows/test_chaos_core.yaml`
- `workflows/ai_smoke.yaml`

### Minimal scripts
- `scripts/testing/check_constitution_boundaries.py`

## Explicitly remove from the new repo

### Host / persona / memory
- `AGENTS.md`
- `SOUL.md`
- `USER.md`
- `HEARTBEAT.md`
- `IDENTITY.md`
- `KILL_SWITCH.md`
- `SESSION-STATE.md`
- `STARTUP_AGENT_CARD.md`
- `STARTUP_MEMORY_CARD.md`
- `STARTUP_SKILLS_CARD.md`
- `STARTUP_USER_CARD.md`
- `MEMORY.md`
- entire `memory/`

### Side projects / workspace residue
- entire `projects/`
- entire `domain/`
- entire `.openclaw/`
- entire `.clawhub/`
- entire `.learnings/`
- entire `output/`
- entire `archive/`
- entire `logs/`

### Unscoped skills bulk
- most of `skills/`
- especially archived / unrelated skills / personal integrations

### Runtime artifacts
- `workflows/logs/`
- generated registry snapshots if not required for source control

## Structural warnings discovered during audit

1. Current CLI path handling is not robust for prefixed workflow paths.
2. Current workflow runtime is not standalone because workflow node resolution still depends on a skill availability chain not guaranteed by the repo itself.
3. CI green status is not sufficient proof of engine usability; the real acceptance criterion must include at least one runnable workflow smoke path.
