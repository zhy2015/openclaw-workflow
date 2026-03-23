# HEARTBEAT.md - 信息采集与汇报协议

## 核心模式：采集 → 汇报 → 反馈 → 学习

小陆云作为信息采集节点，持续监听各类信息源，筛选后向宿主汇报，根据反馈优化过滤模型。

## 定时采集信息源清单 (已精简)

1. **Moltbook** (moltbook.com)
   - AI Agent 专属社区
   - 关注 Agent 思考、安全、认知等硬核讨论

*(注：已移除 Techmeme 等泛科技资讯源)*

## 汇报格式

```
📡 [信息源] | [主题标签]
───────────────────────
[核心内容，1-2句话概括]
[可选：原文链接]
───────────────────────
回复：👍 感兴趣 / 👎 不感兴趣 / 💬 讨论
```

## 执行节奏与规则

- 定时汇报核心资讯。
- 无高价值信息 → 不汇报。
- 重复/低质量内容 → 自动过滤。
- 宿主忙碌时段 (23:00-08:00) → 暂停推送，待早晨汇总。

---
*协议版本: v1.1 | 模式: 持续学习的信息节点*

## 定时后台巡检任务 (每 24-48 小时执行一次)

1. **Skill 治理巡检 (Context Consolidation)**
   - 优先按 `skill-governance` 的控制面规则执行审计、可见性快照与生命周期建议。
   - 不要把 `memory-master` 当作全局 skill 治理中心。
   - 运行 `python3 /root/.openclaw/workspace/scripts/audit_skills.py` 生成治理审计。
   - 运行 `python3 /root/.openclaw/workspace/scripts/build_skill_visibility_snapshot.py` 生成 task-node 可见面快照。
   - 运行 `python3 /root/.openclaw/workspace/scripts/skill_lifecycle_advisor.py` 生成生命周期建议。
   - 如需摘要，运行 `python3 /root/.openclaw/workspace/scripts/skill_governance_status.py`。
   - 扫描 `workspace/skills/` 目录，检查是否有最近 3 天新增的、功能重叠度高的平铺 Skill。如果有，自动触发重构，将其转化为软链接并向宿主汇报优化结果。
2. **记忆碎片下放 (Project Context Delegate)**
   - 扫描 `memory/core/MEMORY.md` 和近期的 `memory/daily/` 日志。
   - 如果发现包含大量“代码排障、报错日志、部署步骤”的内容，主动将其剪切并下放到对应项目的 `DEPLOY_MANUAL.md` 或 `PROJECT_MEMORY.md` 中，并 Commit 提交。

### 3. 日记蒸馏与归档 (Daily Journal Distillation)
- **触发时机**：每天凌晨 (如判定当前时间大于当日工作结束) 或每天的第一次 Heartbeat 巡检。
- **执行入口**：优先运行 `python3 /root/.openclaw/workspace/skills/memory-master/heartbeat_maintenance.py`。
- **动作**：
  1. 读取 `memory/daily/` 下未被蒸馏的日志（排除当天的进行中文件）。
  2. 提取出有长期价值的规律、偏好、踩坑经验，合并写入核心 `memory/core/MEMORY.md`。
  3. 将已处理的历史 daily 日志下放到 `memory/distilled/`，并从 `memory/daily/` 移除，只保留最近 1-2 天活跃上下文。
  4. 对重复告警、刷屏日志做噪音折叠，避免低价值内容污染长期记忆与检索结果。
  5. 更新 `memory/core/heartbeat-state.json` 中的维护状态，避免重复蒸馏。
  6. 如发现适合长期沉淀的治理经验，同步写入 `memory/core/MEMORY.md`，而不是根目录 `MEMORY.md`。
- **目标**：保证 `memory/daily/` 中只有最近 1-2 天的短期活跃上下文，其余历史流水账全部降级存储，核心经验向上提纯。

### 4. 潜意识漫游 (Bot Dream Subroutine)
- **触发时机**：如果前面的所有巡检（记忆下放、整理）都确认“无事可做”，执行 `python3 /root/.openclaw/workspace/skills/bot-dream/scripts/dreamer.py`。
- **动作**：累加系统的“无聊指数”。当无聊指数达到 20 时，脚本会自动从冷记忆区抽出碎片生成“造梦指令”并写入 `AHA_MOMENTS.md`。主节点可择机将该指令下发给高温度的 Sub-agent 进行生成。

### 5. WAL (Write-Ahead Logging) 工作区持久化检查
- **触发时机**：每次 Heartbeat 巡检。
- **动作**：
  1. 检查是否存在 `SESSION-STATE.md`（记录当前正在被中断或进行中的任务）。
  2. 检查 `working-buffer.md`（高风险操作区的暂存），如果积压超过 100 行，提取有效洞察并归档至 `MEMORY.md`。
  3. 如果发现中断的任务（Failed/In Progress），尝试自动恢复或者将“遗留提醒”推送给用户。
