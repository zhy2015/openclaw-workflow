# Archived Skills

Primary archive location for retired / legacy / reference-only skills.

## Status
This archive is **historical only**.
It contains legacy materials that may still mention old engine paths such as:
- `skills/video-production/core`
- `dag_engine_resilient.py`
- `wal_threadsafe.py`
- `workflow_resumer.py`

These references are **not active runtime dependencies** anymore.
The authoritative runtime stack is now:
- `core/infra/registry/`
- `core/engine/`

## Structure
- direct archived skills may live under `skills/.archived/<name-or-stamp>/`
- imported legacy history from old `skills/.archived_skills/` is mirrored under `skills/.archived/legacy-imports/`

## Rule
- archived content is not part of the active skill surface
- do not restore archived engine code into active runtime paths
- keep only for reference, migration, or historical recovery
