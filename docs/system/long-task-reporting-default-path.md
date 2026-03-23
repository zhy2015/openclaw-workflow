# Long Task Reporting Default Path

## Current default

The current default path for long-task reporting is the **heartbeat sentinel file** approach:

- active file: `memory/runtime/active_long_tasks.json`
- archive directory: `memory/runtime/archive/YYYY-MM-DD/task_<id>.json`
- runtime helpers:
  - `core/runtime/long_task_registry.py`
  - `core/runtime/heartbeat_long_task_check.py`

## Why this is the default

This path is simpler, durable across session refreshes, and does not depend on unresolved runtime-edge sender injection.

## Non-default / experimental path

The following modules are retained but are not the default reporting path right now:

- `core/runtime/progress_notifier.py`
- `core/runtime/progress_watcher.py`
- `core/runtime/progress_bridge.py`
- `core/runtime/progress_delivery.py`
- `core/runtime/session_progress_adapter.py`

Reason: they depend on a runtime-edge session sender binding that is not yet wired in this workspace.

## Operational rule

When preparing a real long-running task now, prefer:
1. write/update `active_long_tasks.json`
2. let heartbeat inspect it
3. on terminal status, report once and archive/remove
