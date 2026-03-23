# Skill Governance - Local v1

本地技能治理层，吸收 `skill-governance` 仓库的核心原则，并结合当前工作区的实际状态落地。

## 核心原则

### 双契约模型
- `manifest.json` = **执行契约**
- `SKILL.md` = **触发契约**

不要只维护 manifest，不要只写说明文档。两者缺一不可。

### Registry 边界
Registry 只负责：
- scan
- validate
- register
- dispatch
- usage log

Registry 不负责：
- 高层语义判断
- 模型偏好决策
- 模糊场景的主观选择

### 任务节点优先于分类
优先按 task node 过滤技能，再按 category/tags 二次过滤。

推荐 task nodes：
- coding
- monitoring
- memory
- social
- media
- automation
- governance

### 技能不是默认可见
目录里有 skill，不等于主模型就该看见。

技能曝光应由以下因素共同决定：
- `status`
- `visibility`
- `task_nodes`
- 可选 allowlist

## Manifest 治理字段

每个 manifest 至少应支持：
- `version`
- `status` = `active | archived | experimental | deprecated`
- `visibility` = `public | internal | hidden`
- `task_nodes` = `[]`
- `owner`
- `last_verified_at`

## 生命周期规则

### active
满足：
- manifest 合法
- SKILL.md 可用
- 至少测试过一次
- 当前 workflow 仍在使用

### experimental
适用于：
- 边界未稳定
- 刚创建
- 暂不应进入主模型默认曝光面

### deprecated
适用于：
- 有替代品
- 仍可能存在兼容依赖
- 不应继续优先使用

### archived
适用于：
- 30 天以上无使用
- 已有更好替代
- 仅保留参考价值

## ROI 规则

技能成功调用后记录到：
- `memory/metrics/skill_usage.csv`
- 统一建议通过 `python3 /root/.openclaw/workspace/scripts/log_skill_usage.py <skill> <action> <status>` 追加，避免状态值混乱

定期审查：
- 30 天无使用 → 候选 archived
- 高重叠度 → 候选 consolidation
- experimental 长期未转正 → 候选 archived

## 当前落地方向

1. 让高频核心技能具备完整治理字段
2. 给全部 manifest 做审计，不强制一次性全量手改
3. 审计输出为报告，不直接暴力修改所有技能
4. 后续由 heartbeat / memory maintenance 触发周期审查

## 当前建议的默认可见面

默认优先暴露：
- active + public

谨慎暴露：
- experimental + public

默认不暴露：
- internal
- hidden
- archived
- deprecated

## 与记忆系统的关系

skill governance 不是独立孤岛，应和记忆系统联动：
- `MEMORY.md` 记录治理原则与长期经验
- `skill_usage.csv` 提供 ROI 证据
- heartbeat 周期性做治理审查
