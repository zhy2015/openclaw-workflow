# Constitution Runtime 成熟度矩阵

## 当前能力矩阵

| 维度 | 当前状态 | 说明 |
|---|---|---|
| 统一入口 | 已建立 | `ConstitutionRuntime` 已作为 fast/slow path 统一入口 |
| Fast Path | 可运行 | 通过 governed dispatch 执行 |
| Slow Path | 可运行 | 已支持单节点、链式多节点、多依赖汇聚 DAG |
| Memory Gate | 已落地 | recall-required 任务已可前置拦截 |
| Capability Enforcement | 已落地 | `slow_only` / `requires_memory` / `deprecated` 已可强校验 |
| Legacy Bridge | 已落地 | legacy manifest skill 已通过 adapter bridge 接入 |
| Agent Entry | 初步收口 | `BaseAgent` 已具备 constitution 调用入口 |
| Script Entry | 部分收口 | 关键脚本已迁移，仍需继续扩大覆盖 |
| Workflow Runtime | 初步成型 | `WorkflowRunner + DAGEngine + governed dispatcher` 已打通 |
| Audit Log | 已有基础 | `logs/constitution.log` 已可记录关键事件 |
| Boundary Check | 已落地 | `check_constitution_boundaries.py` 已可用 |
| Regression Tests | 已落地 | 当前关键测试已覆盖 fast path / memory gate / slow path / failure path |

## 当前风险矩阵

| 风险项 | 当前级别 | 说明 |
|---|---|---|
| 残余旧入口文档/说明 | 中 | `TOOLS.md`、部分 skill-governance 文档仍保留旧 registry 叙述 |
| 上层脚本覆盖不足 | 中 | 关键入口已迁移，但不是全仓 fully enforced |
| Slow Path 编排深度 | 中 | 已支持基础 DAG，但更复杂恢复/分支/重试策略仍待增强 |
| CI 集成不足 | 中 | 主仓尚未形成默认自动执行的治理检查 |
| Legacy Bridge 长期存在 | 中 | 已受控，但仍需规划最终去可见化策略 |
| Fully Enforced Constitution | 低到中 | 主干骨架已成，但还没做到所有上层路径天然只走这一条 |

## 剩余旧入口清单（当前扫描）

### 代码层仍保留但属受控/兼容
- `core/infra/legacy_registry_adapter.py`
- `core/runtime/dispatch.py`（URI parser 兼容）
- `core/engine/dag_engine.py`（`skill_uri` 兼容字段）

### 文档/样例层仍提到旧入口
- `TOOLS.md`
- `projects/skill-governance/SKILL.md`
- `skill-governance/README.md`
- `skill-governance/MAINTAINERS.md`
- `workflows/test_chaining.yaml`
- `workflows/test_chaos_core.yaml`

### 结论

当前系统已经达到：

> **Governed-by-default, legacy-compatible, not-yet-fully-enforced**

也就是：
- 新路径已成默认主线
- 旧路径已基本收进桥接层
- 但上层文档、样例与部分周边资产仍需继续去旧化
