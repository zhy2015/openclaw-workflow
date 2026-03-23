# Review Workflow Rules

Approved by user on 2026-03-21.

## Core workflow
1. When receiving external code review feedback, first apply the `receiving-code-review` posture:
   - understand the claim
   - verify against actual code/repo state
   - do not blindly agree
   - push back when technically necessary
2. After runtime blockers and mergeability issues are cleared, switch to `architecture-designer` posture for higher-level review:
   - boundaries
   - abstractions
   - long-term maintainability
   - ADR/trade-off quality
3. Prefer concise, structured summaries back to the user.
4. In Feishu, prefer interactive cards for higher-value review/status summaries when useful.

## Output preference
- Early phase: plain text or compact card with blockers/fixes
- Mid/late phase: review verdict card with status, what changed, remaining concerns, next step

## Decision style
- Technical rigor over performative agreement
- Mergeability first, architecture second
- External review comments are inputs to evaluate, not orders to obey
