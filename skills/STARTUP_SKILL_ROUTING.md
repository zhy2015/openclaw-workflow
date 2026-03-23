# STARTUP_SKILL_ROUTING

## Goal
Prevent full skill-surface injection during cold start.

## Startup default
- Do not preload full skill catalogs.
- Do not read multiple SKILL.md files speculatively.
- Select the most specific matching skill only when a task clearly triggers it.
- If a manifest sets `routing.startup_expose=false`, suppress that skill from default cold-start routing unless the task explicitly requires it.

## Preferred routing order
1. Native first-class tools
2. Startup skill card / task-node hint
3. Single relevant SKILL.md on demand
4. Governance/audit artifacts only when diagnosing routing/governance issues

## Trigger examples
- Feishu doc/calendar/task/bitable/message requests → read only the matching Feishu skill if needed
- Web browsing/scraping → read only the matching browser/scraper skill if needed
- Data/report/file analysis → read only the matching analysis skill if needed

## Anti-bloat rules
- Never load broad skill lists just because they exist
- Never use archived/internal/deprecated skills unless explicitly needed
- Prefer task-specific narrowing over category-wide expansion
- Consult `skills/startup_suppress_list.json` to avoid surfacing low-priority or specialized skills during cold start
