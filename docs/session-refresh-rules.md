# Session Refresh Rules

Goal: after a fresh session, the system should still default to the same governance instincts.

## Default instincts

1. Cross-skill control-plane rules belong to `skill-governance`.
2. Memory-domain storage, routing, distillation, and recall belong to `memory-master`.
3. Boundary translation belongs to thin adapters, not to domain cores.
4. `core/infra/registry/manager.py` is a legacy manifest executor during migration, not the canonical new control plane.

## Core document rule

When editing these files, preserve the split above by default:
- `AGENTS.md`
- `TOOLS.md`
- `MEMORY.md`

## Startup implication

A fresh session should be able to recover the same boundary model by reading only the lightweight startup cards and core workspace rules, without needing the whole historical conversation.
