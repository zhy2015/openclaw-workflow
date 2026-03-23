# Config Centralization

系统级配置统一收口到：
- `~/.config/openclaw/`

当前已收口：
- `qqmail.env` ← 原 workspace `.env`
- `resource_config.json` ← 原 `core/resource_config.json`
- `tools-config.md` ← 原 `memory/preferences/tools-config.md`
- 既有配置保留：`config.env` / `hidream_config.json` / `memory.conf` / `workflow-commands.json`

原则：
- **系统级配置** → `~/.config/openclaw/`
- **项目级配置**（例如项目自己的 `.env`）→ 保留在项目目录，不强行抽走
- **敏感凭据** 不再留在 workspace 根目录散落
