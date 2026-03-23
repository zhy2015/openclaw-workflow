# Skill Governance Round 4 Notes

## What was tightened

- Marked engine-side imports of `core.infra.registry.get_registry()` as legacy manifest-path usage.
- Marked `core/infra/registry/cli.py` as a migration-era CLI, not the forward governance abstraction.

## Why

Round 4 is about reducing the chance that contributors keep treating `registry/` as the canonical control plane.

## Remaining work

1. Migrate engine call sites from legacy manifest execution to adapter-based dispatch where appropriate.
2. Replace old registry CLI lifecycle flows with governance APIs built around `SkillManager` + `ISkill`.
3. Audit `health.py`, `discovery.py`, and other registry helpers for assumptions tied to the old registry model.
