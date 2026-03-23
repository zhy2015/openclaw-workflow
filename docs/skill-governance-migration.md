# Skill Governance Migration Notes

## Current split

### New control plane
Use these as the forward path:
- `core.infra.skill_contracts`
- `core.infra.skill_manager`

Responsibilities:
- `ISkill` contract
- `ToolSchema` aggregation
- `ExecutionResult` normalization
- governance-side registration and dispatch

### Legacy compatibility path
Keep these for transition only:
- `core.infra.registry.manager`
- `core.infra.registry.*`

Responsibilities:
- legacy manifest discovery
- legacy `skill://...` URI execution
- old CLI / install / discovery compatibility

## Decision

`RegistryManager` is now treated as a **legacy manifest executor**, not the long-term global control plane.

## Refactor direction

1. New adapters implement `ISkill`
2. `SkillManager` becomes the canonical governance bus
3. `registry/` remains as a legacy bridge until old manifest-based integrations are migrated
4. Avoid introducing new global governance logic into domain repositories such as `memory-master`
