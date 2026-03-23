---
name: memory-master
description: 记忆管理 skill：自动整理、归档、检索记忆日志，支持上下文整合、提炼、去重与写入
version: 1.2.0
category: knowledge
---

# Memory Master Skill

把本地记忆系统统一成一个轻量但可持续维护的入口，兼容当前 workspace 目录结构，并吸收上游 `memory-master` 的核心能力。

## 能力

| Action | 描述 |
|---|---|
| `write` | 写入当日日志 |
| `consolidate` | 从 `memory/daily/` 提取高价值内容，去重后合并进 `memory/core/MEMORY.md` |
| `archive` | 归档超过阈值的 daily 日志 |
| `index` | 建立 / 重建本地索引 |
| `search` | 统一搜索 `daily / archive / distilled / core` 内容（优先使用 FTS5） |
| `status` | 查看记忆系统状态 |

## 当前目录约定

```text
memory/
├── core/MEMORY.md
├── daily/
├── archive/
├── distilled/
└── index/
    ├── vector_index.db
    ├── memory_index.json
    └── processed_logs.json
```

## CLI 用法

```bash
python skills/memory-master/memory_master.py write "今天解决了部署问题"
python skills/memory-master/memory_master.py consolidate --dry-run
python skills/memory-master/memory_master.py consolidate
python skills/memory-master/memory_master.py archive 7
python skills/memory-master/memory_master.py index
python skills/memory-master/memory_master.py search "部署问题" 5
python skills/memory-master/memory_master.py status
```

## 提取规则

自动提取以下内容到核心记忆：

- `FAILED: xxx` → `failure_pattern`
- `SUCCESS(xxx)` → `success_pattern`
- `DECISION: xxx` → `decision`
- `LEARNED: xxx` → `learning`
- `Skills registered: N` / `Total skills: A → B` → `metric`

## 设计取向

- 尽量轻量，不强绑定更重的 OpenClaw runtime
- 保持 skill 化接口，方便 heartbeat / agent / workflow 复用
- 优先兼容现有工作区记忆结构，而不是强迫迁移
- 默认只做“提纯与索引”，不主动大规模改写历史内容
- 检索入口统一收口到 memory-master，减少双引擎分裂
