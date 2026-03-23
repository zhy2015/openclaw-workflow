## [ERR-20260321-001] tool-edit-and-false-green-gate

**Logged**: 2026-03-21T16:02:30Z
**Priority**: high
**Status**: pending
**Area**: infra

### Summary
An `edit` operation failed to match exact file text, and I did not immediately record the failure pattern. I also validated a governance gate in an empty local `skills/` directory and reported success too early, which did not prove real repository integration quality.

### Error
- `edit` failed on `scripts/print_skill_governance_summary.py` because the exact old text did not match.
- Later verification showed the repo had an unintended file `127.0.0.1:7890` and an empty local `skills/` directory, so `python3 scripts/enforce_skill_governance.py` returned a false-green result (`skills: 0`).

### Context
- Repository: `/root/.openclaw/workspace/projects/skill-governance`
- Related command: `python3 scripts/enforce_skill_governance.py`
- Related tool: `edit`

### Suggested Fix
- When `edit` fails, immediately log the failure pattern and switch to `read` + `write` or a smaller exact replacement.
- Never treat a governance gate as validated unless it runs against realistic fixture data or the real target tree with non-empty skill inventory.
- Clean accidental shell artifacts before commit/push.

### Metadata
- Reproducible: yes
- Related Files: /root/.openclaw/workspace/projects/skill-governance/scripts/print_skill_governance_summary.py, /root/.openclaw/workspace/projects/skill-governance/scripts/enforce_skill_governance.py

---
