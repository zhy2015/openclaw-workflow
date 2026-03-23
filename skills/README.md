# Skills Directory Layout

## Active / visible skills
普通活跃技能保留在 `skills/<skill-name>/`。

## Archived skills
- `skills/.archived/` = 主归档区，保留参考价值的旧技能
- `skills/.archived/legacy-imports/` = 从旧归档体系镜像过来的历史内容
- `skills/.archived_skills/` = 旧兼容保留区，不再新增内容，后续可移除

## Governance helpers
- `skills/GOVERNANCE.md` = 技能治理规则
- `skills/skill_audit_report.json` = 审计报告
- `skills/skill_visibility_snapshot.json` = task-node 可见面快照
- `skills/skill_lifecycle_advice.json` = 生命周期建议
- `skills/skill_governance_status.json` = 汇总状态

## Cleanup rule
- 不直接因为“目录存在”就暴露给主模型
- 优先依据 manifest 的 `status` / `visibility` / `task_nodes`
- test/legacy/archive 内容尽量不要混入 active path
