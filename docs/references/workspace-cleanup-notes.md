# Workspace cleanup notes

- `.env` was centralized out of workspace root into `~/.config/openclaw/qqmail.env`.
- `127.0.0.1:7890` was treated as malformed noise/output artifact and removed.
- Legacy memory scripts moved to `scripts/governance/` as `_legacy` references instead of staying in active path.
- Project-affiliated output snapshots from `output/projects/` were copied into `projects/_outputs/` to reduce global output sprawl.
- Resource noise file `resources/game-assets/127.0.0.1:7890` was removed.
