# Completed TODOs — 2026-03

## [TODO-20260320-MEM-001] 修复 OpenClaw memory 主配置漂移
**创建**: 2026-03-20
**优先级**: high
**来源**: user
**状态**: done

### 描述
本轮发现 memory/recall 失效不是单点 provider 问题，而是主配置漂移导致的组合故障：
- `agents.defaults.workspace` 被写成 `/`
- memory backend 掉回 `builtin`
- builtin 自动选了 `openai/text-embedding-3-small`
- 当前第三方 OpenAI 兼容网关仅支持 chat，不支持 embeddings，导致 404
- 结果是 `memory_search` 扫描 `/memory`，文件数为 0，语义 recall 全挂

### 验收标准
- [x] `openclaw memory status --deep --json` 中 `workspaceDir` 指向 `/root/.openclaw/workspace`
- [x] memory backend 不再错误回退到 `builtin + openai embeddings 404`
- [x] 能看到 workspace 下的 memory 文件，而不是 `/memory`
- [x] `memory_search` 恢复为可用状态（即使结果为空，也不能是 disabled/404）

### 上下文
- 当前主配置: `/root/.openclaw/openclaw.json`
- memory 路径辅助配置: `/root/.config/openclaw/memory.conf`
- 已发现历史可用链路: `provider=qmd, model=qmd`
- 当前已做动作: 备份 openclaw.json，并已写入一版本地恢复配置，但尚未完成完整验证

### 更新记录
- 2026-03-20: 通过 `openclaw memory status --deep --json` 实锤当前坏相：workspace=`/`、backend=`builtin`、provider=`openai`、embeddings=404、files=0
- 2026-03-20: 发现历史会话中 `memory_search` 曾正常走 `qmd`
- 2026-03-20: 已备份 `/root/.openclaw/openclaw.json`，并写入一版恢复配置（workspace->workspace 路径，memory->qmd，memorySearch->local），待进一步验证
- 2026-03-20: 复验通过：`openclaw memory status --deep --json` 显示 workspaceDir=`/root/.openclaw/workspace`、backend/provider=`qmd`、files=47、embeddingProbe.ok=true；`memory_search` 已恢复可用

---

## [TODO-20260320-MEM-002] 落地本地 recall 方案并与聊天模型解耦
**创建**: 2026-03-20
**优先级**: high
**来源**: user
**状态**: done

### 描述
按本地落地方向实现 recall：聊天模型链路保留，embedding / memory backend 独立，不再依赖当前只兼容 chat 的第三方 OpenAI 网关。

### 验收标准
- [x] 聊天 provider 保持现状可用，不因 recall 修复被破坏
- [x] recall 使用本地可运行链路（优先 QMD / local embeddings）
- [x] 明确记录 fallback 策略：若本地 recall 异常，如何退回
- [x] 形成可复用配置，不依赖临时会话手工修补

### 上下文
- 候选策略：QMD + local embeddings
- 本机已确认存在 `qmd` 可执行文件
- 若本地 embedding 模型拉取失败，可再评估单独 embedding provider，但不应先动 chat provider

### 更新记录
- 2026-03-20: 已确认方向为“聊天链路不动，embedding/recall 独立修复”
- 2026-03-20: 已将稳定方案与 fallback 策略写入 `docs/memory-recall-runbook.md`，并增强 `scripts/check_memory_config.py`，把 chat provider baseUrl 一并纳入保护性校验
- 2026-03-20: 复验通过：`openclaw memory status --deep --json` 仍为 workspaceDir=`/root/.openclaw/workspace`、backend/provider=`qmd`、embeddingProbe.ok=true、files=47；聊天链路 baseUrl 保持 `https://ai.td.ee/v1` 未改动

---

## [TODO-20260320-MEM-003] 固化启动期 workspace / memory 自检机制
**创建**: 2026-03-20
**优先级**: medium
**来源**: user
**状态**: done

### 描述
避免刷新/新会话后再次出现“启动在 `/`、读错根目录镜像、找不到真实 memory”的问题。把 workspace sanity check 与 memory backend 自检固化进可长期生效的位置。

### 验收标准
- [x] 新会话启动时优先识别 `/root/.openclaw/workspace` 为 canonical home
- [x] 若主配置异常指向 `/`，能尽早暴露而不是等到 recall 失效才发现
- [x] 至少有一个可执行检查命令/流程用于快速诊断

### 上下文
- 这次已经补过 `AGENTS.md` 层的规则
- 但根因还涉及主配置文件 `/root/.openclaw/openclaw.json`

### 更新记录
- 2026-03-20: 已将 workspace sanity check 教训写入 `AGENTS.md` 和 `memory/core/MEMORY.md`
- 2026-03-20: 发现仅靠提示词层不够，仍需配置层自检/固化
- 2026-03-20: 已把快速检查命令 `python3 /root/.openclaw/workspace/scripts/check_memory_config.py` 写入 `AGENTS.md`，并把启动期建议固化到 `docs/memory-recall-runbook.md`
- 2026-03-20: 复验通过：`openclaw memory status --deep --json` 仍显示 workspaceDir=`/root/.openclaw/workspace`、backend/provider=`qmd`、embeddingProbe.ok=true、files=48

---

## [TODO-001] 示例任务模板
**创建**: 2026-03-19
**优先级**: low
**来源**: system
**状态**: archived

### 描述
这是一个示例任务，展示TODO格式

### 更新记录
- 2026-03-19: 创建
- 2026-03-20: 归档清理；无实际执行意义，仅保留为历史痕迹
