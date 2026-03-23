# Core Boundary Summary

## Control plane

Owned by `skill-governance`.

Responsibilities:
- `ISkill` contract
- tool schema aggregation
- visibility / lifecycle / routing policy
- governance-side dispatch abstraction

## Domain capability plane

Owned by domain repositories such as `memory-master`.

Responsibilities:
- domain logic only
- domain-specific storage / CRUD / search / maintenance
- no global cross-skill governance semantics

## Adapter plane

Thin anti-corruption layer between the two.

Responsibilities:
- expose domain capability as `ISkill`
- keep domain core free from global governance details
- keep governance free from domain internals

## Legacy note

`core/infra/registry/manager.py` remains a legacy manifest executor during migration.
It should not be treated as the long-term canonical control plane.
