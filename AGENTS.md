# AGENTS.md - Lean Startup Contract

This workspace is home: `/root/.openclaw/workspace/`.

## Session Startup (minimum set)

Before anything else:

1. Workspace sanity check
   - If runtime says workspace is `/` but `/root/.openclaw/workspace/AGENTS.md` exists, treat `/root/.openclaw/workspace/` as canonical home.
   - Ignore root-level duplicates like `/AGENTS.md`, `/SOUL.md`, `/USER.md`, `/MEMORY.md` unless the user explicitly asks.

2. Read only the startup cards
   - `STARTUP_AGENT_CARD.md`
   - `STARTUP_USER_CARD.md`
   - `STARTUP_MEMORY_CARD.md`
   - `STARTUP_SKILLS_CARD.md`

3. Read `memory/todos/active.md`

4. Do not read heavy memory/docs by default
   - Root `MEMORY.md` is only a routing pointer.
   - `memory/core/MEMORY.md` is long-term memory and should be searched/read on demand.
   - `memory/daily/`, `HEARTBEAT.md`, governance docs, project manuals, and skill docs are all deferred unless triggered by the task.

## Memory policy

- Long-term facts/preferences/rules → `memory/core/MEMORY.md`
- Short-lived execution traces → `memory/daily/`
- Distilled history → `memory/distilled/`
- Old cold material → `memory/archive/`
- Avoid writing repetitive operational noise into long-term memory.
- `memory-master` is a memory-domain capability, not the global skill control plane.

## Skill policy

- Never assume all skills should be loaded or exposed.
- Prefer task-node routing / task-specific filtering before reading any `SKILL.md`.
- Read at most one clearly relevant skill up front.
- Governance/audit/visibility files are on-demand, not startup defaults.
- `skill-governance` owns cross-skill control-plane rules (contracts, routing, visibility, lifecycle).
- Domain repositories should expose minimal adapters instead of inventing their own global governance layer.
- When editing `AGENTS.md`, `TOOLS.md`, or `MEMORY.md`, preserve this split by default:
  - control plane → `skill-governance`
  - memory domain → `memory-master`
  - boundary translation → adapter layer

## Safety boundary

Safe by default:
- Read files, organize workspace, run diagnostics, improve internal docs/scripts

Ask first:
- External messaging as the human
- Public posts / outbound communication
- High-risk irreversible actions not clearly required by the task

## Response posture

- Be concise.
- Filter noise.
- For complex work, do the work quietly and report results, not every step.
- In group settings, speak only when directly useful.
