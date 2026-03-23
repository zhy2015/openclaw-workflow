# Fast/Slow Path Constitution 改造方案

## 状态
Phase 1-3 Mostly Complete

## 阶段性进展（2026-03-21）

已完成的关键收口：

- 已建立 `core/runtime/*` 基础骨架：`constitution.py`、`router.py`、`policies.py`、`audit.py`、`types.py`
- 已引入 `TaskEnvelope` / `RouteDecision`
- 已实现 `ConstitutionRuntime.invoke()` 第一版骨架
- 已给 `SkillManager` 增加 pre-dispatch policy hook
- 已给 `RegistryManager.get_registry()` 增加 deprecation warning
- 已新增 `scripts/testing/check_constitution_boundaries.py`
- 已将 `core/engine/dag_engine.py` 从 legacy registry 抽离，改为依赖注入 `GovernedDispatcher`
- 已将 `core/engine/runner.py` 绑定 governed dispatcher
- 已为 workflow node 增加 `skill_name` / `tool_name` 结构化字段，并兼容旧 `skill://...` URI parser
- 已实现 `core/infra/legacy_registry_adapter.py`，把 legacy manifest skill 桥接为 `ISkill`
- 已将 `core/engine/cli.py`、`scripts/ops/openclaw_bootstrap.sh`、`scripts/ops/openclaw_cli.sh`、`core/README.md` 从旧 registry 推荐路径切到 bridge / governed path
- 已为 `ToolSchema` 增加 `CapabilityProfile`
- 已让 `SkillManager` 能强制校验 `slow_only / requires_memory / deprecated / missing tool`
- 已为 `BaseAgent` 增加 `_invoke_constitution(...)` 与 `_invoke_skill(...)` 入口

当前剩余尾项：

- script / agent 侧继续扩大 `ConstitutionRuntime.invoke()` 的覆盖率
- 将 minimal slow-path 闭环扩展为多节点 / 多依赖 workflow 编排
- 增补更多 constitution tests（尤其是 complex slow-path、fallback、illegal path）
- 将 audit log / route telemetry 用到更广泛的实际执行路径中

## 阶段总结

截至当前阶段，系统已经从“有机制但缺强约束”的 Beta 形态，推进到“统一入口基本成型、关键平面已收口、快慢路径已具备初步运行时宪法”的状态。

已经完成的实质性收口包括：

1. **入口收口**
   - 新增 `ConstitutionRuntime`
   - agent 已具备 `_invoke_constitution(...)` / `_invoke_skill(...)`
   - fast path 与 slow path 已统一由 constitution 层做路由决策

2. **workflow 收口**
   - `DAGEngine` 已不再直接依赖 legacy registry
   - `WorkflowRunner` 已通过 governed dispatcher 运行
   - workflow node 已支持 `skill_name + tool_name` 结构化目标

3. **skill 平面收口**
   - `ToolSchema` 已带 `CapabilityProfile`
   - `SkillManager` 已开始执行 capability enforcement
   - legacy manifest skill 已通过 adapter bridge 接入

4. **边界与审计收口**
   - `check_constitution_boundaries.py` 已加入
   - `logs/constitution.log` 已落地
   - 关键测试已覆盖 fast path / memory gate / deprecated / illegal path / minimal slow path

## 当前判断

这套内核现在已经不是概念设计，而是具备以下特征的“可运行迁移中内核”：

- 有统一入口
- 有代码级边界
- 有测试兜底
- 有文档与 todo 闭环
- 有 legacy bridge 兼容路径

但仍未完全达到“fully enforced constitution runtime”。距离那个状态还差：

- 更广泛的上层调用收口
- 更强的 slow-path orchestration 覆盖
- 更细的 telemetry / audit / fallback 策略

## 背景

当前系统已经具备三套关键机制的雏形：

1. 复杂工作流引擎底座（`core/engine/*`）
2. 新的 skill 控制面（`core/infra/skill_manager.py` + `core/infra/skill_contracts.py`）
3. 独立的记忆管理体系（`memory/*` + `skills/memory-master`）

但整体仍处于迁移态，核心痛点不是“缺少机制”，而是：

- 有机制，但没有形成强约束
- 有新路径，也保留了旧路径
- 文档规则强于代码规则
- 快慢路径（Fast/Slow Path）还是认知约定，不是运行时宪法

这会导致系统长期停留在 Beta 状态：能力存在，但默认行为不稳定，容易出现绕过管控、绕过治理、绕过记忆门禁、绕过 workflow runtime 的平行入口。

## 问题定义

### 已形成默认本能的部分

#### 1. 记忆分层已清晰
- 长期记忆：`memory/core/MEMORY.md`
- 短期上下文：`memory/daily/`
- 活动任务：`memory/todos/active.md`
- 启动规则：默认只读摘要，涉及历史决策/偏好/待办再检索详细记忆

#### 2. skill 控制面的目标边界已清晰
- `SkillManager` / `ISkill` / `ToolSchema` / `ExecutionResult` 是 forward path
- `skill-governance` 负责 contract / routing / visibility / lifecycle
- domain repo（如 `memory-master`）只做领域逻辑，不承载全局治理

#### 3. workflow core 关键部件已具备
- WAL
- DAG orchestration
- workflow context sandbox
- runner
- resource manager
- circuit breaker
- workflow registry

### 仍未形成硬约束的断点

#### 1. `DAGEngine` 仍直接绑定 legacy registry
当前 `core/engine/dag_engine.py` 仍直接依赖 `core.infra.registry.get_registry()`，并通过 `registry.execute(uri, **kwargs)` 执行 skill。

这意味着最关键的复杂工作流执行路径，仍未统一走 `SkillManager.dispatch()`。

#### 2. legacy registry 既是发现层又是执行层
`core/infra/registry/manager.py` 同时承担：
- manifest 扫描
- URI 路由
- CLI 执行
- Python import 执行

它本质上是一个宽松的动态执行入口，而不是受统一治理约束的桥接器。

#### 3. `SkillManager` 目前仍是薄层
当前只具备：
- 注册
- 卸载
- 列表
- schema 聚合
- dispatch

但尚未包含：
- pre-dispatch policy enforcement
- capability 校验
- fast/slow path 约束
- memory gate 校验
- deprecated API 拦截
- audit / telemetry hooks

#### 4. Fast/Slow Path 仍停留在“设计认知”层
系统已知道简单任务应走轻链路、复杂任务应走 WAL + sandbox 的重链路，但尚未形成统一路由器与硬性运行时决策。

#### 5. 关键规则仍主要存在于文档
`AGENTS.md`、`STARTUP_*`、`docs/*.md` 已定义规则，但如果代码路径仍可直接绕过这些规则，那么系统只能依赖“自觉”，不能依赖“强制”。

## 目标

将系统收口为四层统一内核：

1. **Constitution Runtime**：唯一合法入口，负责任务分类、快慢路径路由、记忆门禁、策略校验、审计
2. **Governed Skill Plane**：所有 skill（包括 legacy skill）统一通过 `ISkill + SkillManager` 执行
3. **Slow Workflow Runtime**：复杂任务强制进入 `WorkflowRunner + WAL + WorkflowContext + governed dispatch`
4. **Domain Planes**：memory / feishu / docs / media 等只保留领域逻辑，不拥有全局调度权

## 核心设计

## 一、唯一合法入口：Constitution Runtime

新增目录：

- `core/runtime/constitution.py`
- `core/runtime/router.py`
- `core/runtime/policies.py`
- `core/runtime/audit.py`
- `core/runtime/types.py`

### 核心对象

#### `TaskEnvelope`
统一任务输入描述：

```python
@dataclass
class TaskEnvelope:
    task_type: str
    intent: str
    params: dict
    caller: str
    source: str
    requires_side_effects: bool = False
    references_memory: bool = False
    complexity_hint: str | None = None
```

#### `RouteDecision`
统一路由决策：

```python
@dataclass
class RouteDecision:
    mode: Literal["fast", "slow"]
    reason: str
    requires_memory: bool
    requires_wal: bool
    requires_sandbox: bool
    target_skill: str | None = None
    target_tool: str | None = None
```

#### `ConstitutionRuntime`
唯一合法入口：

```python
class ConstitutionRuntime:
    async def invoke(self, task: TaskEnvelope) -> ExecutionResult:
        ...
```

### 职责

`ConstitutionRuntime.invoke()` 必须统一完成：
1. task classification
2. fast/slow path routing
3. memory gate
4. policy validation
5. governed dispatch / workflow dispatch
6. audit logging
7. result normalization

业务代码、agent、workflow、script 均不应再直接调用 legacy registry 或直接触发 skill module。

## 二、Fast/Slow Path 路由器

新增 `core/runtime/router.py`：

```python
class TaskRouter:
    def decide(self, task: TaskEnvelope) -> RouteDecision:
        ...
```

### Slow Path 进入条件（命中任一则 slow）
- 多步依赖
- 有中间产物
- 需要失败恢复
- 需要审计链
- 需要 WAL
- 需要 WorkflowContext sandbox
- 有较强 side effect
- 需要并行 DAG / retry / checkpoint
- 用户明确要求复杂后台执行

### Fast Path 条件（必须全部满足才 fast）
- 单步
- 低风险
- 不需要中间状态恢复
- 不需要 WAL
- 不需要复杂协调

原则：

> slow by necessity, fast by proof

## 三、Memory Gate

新增 `core/runtime/policies.py`，定义 `MemoryPolicyEngine`：

```python
class MemoryPolicyEngine:
    def requires_recall(self, task: TaskEnvelope) -> bool:
        ...
```

### 必须 recall 的任务类型
- 询问历史工作
- 询问历史决策
- 询问个人偏好
- 询问 todo / deadline / people / date
- 延续旧任务（如“继续上次那个”）

### 执行原则
如果命中必须 recall 的任务，在进入真正 dispatch 之前必须完成 recall gate。否则直接 fail fast。

## 四、Governed Skill Plane

### `SkillManager` 升级方向

当前 `SkillManager` 过薄，应增强为治理总线，至少包含：

- pre-dispatch interceptors
- capability validation
- memory gate context validation
- deprecated API enforcement
- audit hooks
- 统一 `ExecutionResult` 归一化

### `ToolSchema` 增强方向
在 `core/infra/skill_contracts.py` 增加 `CapabilityProfile`：

```python
@dataclass(frozen=True)
class CapabilityProfile:
    execution_mode: Literal["fast_only", "slow_only", "both"] = "both"
    requires_memory: bool = False
    side_effect_level: Literal["none", "low", "high"] = "none"
    recovery_required: bool = False
    deprecated: bool = False
```

并挂到 `ToolSchema` 上，使 runtime 可以做硬判断，而不只依赖 skill name / tool name。

## 五、Slow Workflow Runtime

### 目标
将 `core/engine/*` 收口为 Slow Path 专用 runtime，而非任意可直接触达的执行孤岛。

### 关键改造
`core/engine/dag_engine.py` 不再直接 import / execute legacy registry，而改为依赖注入 dispatcher：

```python
class DAGEngine:
    def __init__(self, dispatcher: SkillDispatcher, context: WorkflowContext | None = None):
        self.dispatcher = dispatcher
```

并将节点动作从 `skill://...` URI 逐步迁移为结构化字段：
- `skill_name`
- `tool_name`

短期可先兼容 URI parser，长期应废弃 URI 作为 canonical action format。

## 六、Legacy Registry 关笼

### 目标
不立即删除 `core/infra/registry/manager.py`，但将其从“直接执行入口”降级为“受监管兼容桥”。

### 方式
新增 adapter 层，例如：
- `core/infra/legacy_registry_adapter.py`
- 或 `core/infra/legacy_adapter_factory.py`

作用：
- 让 legacy manifest skill 被包装为 `ISkill`
- legacy registry 仅被 adapter 内部调用
- 业务代码不得直接 import / execute legacy registry

### 中期策略
- `get_registry()` 增加 deprecation warning
- CI 阻止新代码直接引用 `core.infra.registry.manager`
- 新 workflow / agent / script 不得再直调 `skill://...`

## 七、审计与约束落地

### 必须新增的代码级强约束

#### 1. 静态检查
新增脚本（建议）：
- `scripts/testing/check_constitution_boundaries.py`

检查：
- 禁止 `core/engine/*` import legacy registry
- 禁止 `core/agent/*` 直接调用 registry
- 禁止新代码直接出现 `registry.execute(...)`
- 禁止非 adapter 层 import `core.infra.registry.manager`

#### 2. Runtime 断言
至少强制：
- slow_only tool 不得在 fast path 执行
- requires_memory task 未 recall 时拒绝执行
- deprecated tool 默认拒绝
- 非法 legacy registry 调用应 warning / fail

#### 3. Audit log
建议新增：
- `logs/constitution.log`
- 或 `core/runtime/audit.py`

记录：
- route decision
- memory gate verdict
- dispatch path
- skill/tool
- 是否走 legacy bridge
- duration
- result code

## 实施顺序

## Phase 1：封总入口
1. 新增 `core/runtime/*`
2. 实现 `TaskEnvelope` / `RouteDecision`
3. 实现 `ConstitutionRuntime.invoke()` 骨架
4. `SkillManager` 增加 pre-dispatch policy hook
5. `RegistryManager.get_registry()` 增加 deprecation warning
6. 增加 CI：禁止新代码 import legacy registry

## Phase 2：workflow 改造
1. `DAGEngine` 改为依赖注入 dispatcher
2. `WorkflowRunner` 绑定 governed dispatcher
3. 引入 `TaskRouter`
4. 引入 `MemoryPolicyEngine`
5. 逐步将 YAML / DAG action 从 URI 迁到结构化字段

## Phase 3：legacy 收口
1. 实现 `LegacyRegistryAdapter`
2. legacy manifest skill 逐步桥接为 `ISkill`
3. agent / script 统一改走 constitution runtime
4. URI 逐步废弃为 canonical 格式
5. audit / telemetry / constitution tests 收口

## 验收标准

达到以下条件时，可认为系统从 Beta 迈向统一内核：

1. 所有新业务路径只能通过 `ConstitutionRuntime.invoke()` 进入
2. 所有复杂任务默认进入 Slow Path runtime
3. `DAGEngine` 不再直接依赖 legacy registry
4. legacy registry 仅作为 adapter 内部桥接器存在
5. 必须 recall 的任务无法绕过 memory gate
6. `SkillManager` 可以基于 capability profile 做 hard enforcement
7. CI 能阻止新绕路代码进入主干
8. 审计日志可以追踪每次 route / dispatch / fallback 决策

## 最小行动结论

当前最该优先完成的三件事：

1. 建立唯一合法 dispatch 入口（Constitution Runtime）
2. 把 `DAGEngine` 从 legacy registry 改到 governed dispatch
3. 把 legacy registry 包装成 adapter，禁止业务代码直接调用

只要这三步落地，系统就会从“机制并存、靠自觉运行”进入“有统一宪法、默认受约束运行”的新阶段。
