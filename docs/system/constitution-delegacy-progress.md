# Constitution 去旧化进展

## 已处理

### 主仓
- `TOOLS.md`：推荐路径已切到 governed dispatch
- `core/README.md`：推荐路径已切到 governed dispatch / WorkflowRunner / structured workflow fields
- `scripts/ops/openclaw_bootstrap.sh`：已切到 legacy bridge 初始化
- `scripts/ops/openclaw_cli.sh`：已切到 bridged skills
- `workflows/test_chaining.yaml`：已迁到 `skill_name + tool_name`
- `workflows/test_chaos_core.yaml`：已迁到 `skill_name + tool_name`

### skill-governance 子仓认知层
- `README.md`：推荐执行路径已切到 governed dispatch first
- `SKILL.md`：已重写为 governance-first mental model
- `MAINTAINERS.md`：已改成 registry compatibility-only 叙述
- `scripts/print_skill_governance_summary.py`：已改成 governed-dispatch-by-default 叙述

## 仍保留的旧世界痕迹

### 合理保留（兼容层）
- `core/infra/legacy_registry_adapter.py`
- `core/runtime/dispatch.py` 中的 URI parser
- `core/engine/dag_engine.py` 中的 `skill_uri` 兼容字段
- `skill-governance/engine/*` 中的 registry 代码

### 历史/迁移文档
- `docs/skill-governance-migration.md`
- `docs/skill-governance-round4-notes.md`
- `skill-governance/references/*`

## 当前判断

当前主仓已经达到：
- 新路径为默认主线
- 旧路径被收进 bridge / compatibility 层
- 文档层大部分已不再教用户走旧入口

仍未完全完成的是：
- 彻底删除所有迁移期兼容痕迹
- 让子仓 engine 层也完成更深度的结构重塑

结论：

> 主仓已基本完成去旧化；子仓仍处于可控兼容态。
