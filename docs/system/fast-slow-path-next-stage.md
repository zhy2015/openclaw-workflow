# Fast/Slow Path Constitution 下一阶段路线图

## 目标

把当前“统一入口基本成型”的状态，推进到“默认强约束、上层广泛收口、复杂慢路径更成熟”的下一阶段。

## 下一阶段优先级

### P1. 扩大入口覆盖率
- 把更多 agent 调用改为默认经 `ConstitutionRuntime.invoke()`
- 把 scripts 中残余的旧式 skill 触发入口继续迁走
- 对新的业务调用点加 lint / review checklist

### P2. 强化 slow path runtime
- 从单节点临时 workflow，扩到多节点 / 多依赖 DAG
- 支持更明确的输入映射、输出收集与失败节点定位
- 给 slow path 增加更细粒度的 telemetry

### P3. 强化 audit / telemetry
- route decision 统一记录 request id / workflow id / caller
- 记录 fallback / bridge 使用率
- 记录 capability violation 统计

### P4. 完善 constitution tests
- slow path 多节点成功路径
- slow path 失败恢复路径
- illegal fast/slow mismatch
- bridge-only compatibility path
- agent-level constitution entry tests

## 建议里程碑

### Milestone A
- 所有 core / agent / workflow 入口默认走 constitution
- `check_constitution_boundaries.py` 纳入 CI

### Milestone B
- slow path 支持多节点真实 workflow
- route + audit 日志具备追踪价值

### Milestone C
- 旧 registry 在业务层完全不可见
- constitution runtime 成为事实上的唯一公共入口
