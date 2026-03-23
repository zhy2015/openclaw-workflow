# TOOLS.md - Local Notes

## Skill Governance / Registry (核心基础设施)

### 新控制面

**契约位置**: `core/infra/skill_contracts.py`  
**总线位置**: `core/infra/skill_manager.py`  
**职责**: 统一 `ISkill` 契约、`ToolSchema` 聚合、`ExecutionResult` 归一化，以及控制面注册/分发。
**文档规则**: 以后调整 `AGENTS.md` / `TOOLS.md` / `MEMORY.md` 时，默认先检查是否仍满足：控制面归 `skill-governance`、记忆域归 `memory-master`、边界转换归 adapter。

### 旧兼容路径

**兼容位置**: `core/infra/registry/manager.py`  
**职责**: 旧式 manifest 扫描 + `skill://...` URI 执行。仅作为 legacy manifest executor 保留，不再视为新的全局控制面。

**当前推荐用法**:
```python
from core.infra.skill_manager import SkillManager
from core.runtime.policies import PolicyContext
from core.runtime.types import RouteDecision

manager = SkillManager()
# register(...) 由治理层或 bridge 完成

result = manager.dispatch(
    "hidream-api-gen",
    "generate_images",
    {"prompt": "..."},
    policy_context=PolicyContext(route=RouteDecision(mode="fast", reason="manual_call")),
)
```

**兼容说明**:
- `core/infra/registry/manager.py` 仍保留给 legacy bridge
- 新代码不应直接依赖 `get_registry()` 或 `registry.execute(...)`

**当前注册技能** (21个，按分类):
- **media** (7): one-story-video, hidream-api-gen, audio-mixer, pixabay-media, komori-sfx, sfx-generator, cli-anything-drawio
- **network** (2): clash-vpn, clash-auto-switch
- **search** (3): firecrawler, playwright-scraper-skill, tikhub-api
- **data** (3): csv-data-explorer, data-report-generator, paddleocr-doc-parsing-v2
- **integration** (3): notion, qqmail, memory-to-notion
- **infrastructure** (1): tencentcloud-lighthouse-skill
- **automation** (1): qqbot-cron
- **test** (1): echo-skill

---

## Workspace 目录结构

```
/root/.openclaw/workspace/
├── AGENTS.md              # 代理运行规则
├── SOUL.md                # 身份定义
├── USER.md                # 宿主信息
├── TOOLS.md               # 本文件
├── MEMORY.md              # 记忆路由（实际在 memory/core/）
├── HEARTBEAT.md           # 定时任务清单
├── SESSION-STATE.md       # 会话状态
├── KILL_SWITCH.md         # 紧急停止
├── core/                  # 核心引擎
│   ├── infra/registry/    # 技能注册中心
│   └── ...
├── skills/                # 技能目录（平铺，manifest 带 category）
├── memory/                # 记忆系统
│   ├── core/MEMORY.md     # 长时记忆
│   ├── daily/             # 日志
│   └── metrics/           # 指标
├── scripts/               # 运维脚本
│   ├── ops/               # 运维操作
│   ├── memory/            # 记忆管理
│   ├── testing/           # 测试脚本
│   └── download/          # 下载工具
├── resources/             # 资源文件
│   └── game-assets/       # 游戏素材
├── output/                # 输出产物
│   └── [project-dirs]/
├── logs/                  # 日志
│   ├── wal/               # WAL 工作流日志
│   └── *.log
├── archive/               # 归档
│   ├── videos/            # 旧视频
│   └── workflows/         # 旧工作流
├── bin/                   # 二进制工具
│   ├── ffmpeg
│   └── ffprobe
├── projects/              # 项目代码
├── domain/                # 领域知识
└── metal-anchor-monorepo/ # 独立项目
```

---

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

## OpenClaw tool gotcha: edit is exact-match only

- `edit` 适合做**已确认存在**的小范围精确替换。
- 在 README、长文档、频繁变动文件上，**不要先猜片段再 edit**。
- 正确做法：先 `read` 目标片段，再 `edit`；如果结构变化大，直接 `write` 重写完整文件更稳。
- 看到 `Could not find the exact text` 这类报错时，不要重复盲试同一种 `edit`，应先重新读取文件当前内容。

---

Add whatever helps you do your job. This is your cheat sheet.
