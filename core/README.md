# OpenClaw Core - 复杂工作流引擎

一个轻量级、高可靠的 AI Agent 工作流编排引擎，专为长流程、多步骤任务设计。

## 核心特性

| 特性 | 说明 |
|------|------|
| **WAL 双写日志** | 任务产物持久化，崩溃后可恢复内存上下文 |
| **DAG 工作流** | 支持依赖图编排，自动并行执行无依赖节点 |
| **资源限流** | 令牌桶算法控制 RPM 和 Token 消耗配额 |
| **熔断机制** | 连续失败自动熔断，防止级联故障 |
| **治理式技能平面** | 统一 skill dispatch，legacy manifest 通过 bridge 兼容 |
| **子代理隔离** | 复杂任务下沉到独立会话，保持主通道纯净 |

## 架构概览

```
core/
├── bootstrap.py              # 系统初始化入口
├── engine/                   # 工作流引擎层
│   ├── wal_engine.py         # WAL 双写日志引擎
│   ├── dag_engine.py         # DAG 执行引擎
│   ├── workflow_context.py   # 内存上下文沙箱
│   ├── task_verifier.py      # 任务验证器
│   └── workflow_registry.py  # 工作流注册表
├── infra/                    # 基础设施层
│   ├── resource_manager.py   # 资源管理器（限流/配额）
│   ├── circuit_breaker.py    # 熔断器
│   ├── notification.py       # 通知系统
│   ├── skill_manager.py      # 治理式技能总线
│   ├── skill_contracts.py    # ISkill / ToolSchema / ExecutionResult
│   ├── legacy_registry_adapter.py # legacy manifest bridge
│   └── registry/             # 旧 registry，仅兼容迁移期
└── agent/                    # Agent 基类
    ├── base_agent.py         # 物理牢笼基类
    └── base_agent_v2.py      # 增强版本
```

## 快速开始

```python
from core.bootstrap import initialize_system, get_rm
import asyncio

async def main():
    # 初始化系统（eco 模式 = 节能，burn 模式 = 高性能）
    await initialize_system(mode="eco")
    
    # 获取 ResourceManager
    rm = get_rm()
    
    # 请求 LLM（自动限流、配额检查）
    result = await rm.request_llm("Hello, World!")
    print(result)

asyncio.run(main())
```

## 工作流定义示例

```yaml
workflow_id: "video-production"
name: "视频生成流水线"

nodes:
  - id: "generate_script"
    skill_name: "llm"
    tool_name: "generate"
    inputs:
      prompt: "写一个30秒视频脚本"

  - id: "generate_images"
    skill_name: "hidream-api-gen"
    tool_name: "generate_images"
    inputs:
      prompt: "generate_script.output"
    next: ["compose_video"]

  - id: "compose_video"
    skill_name: "ffmpeg"
    tool_name: "compose"
```

> 兼容说明：旧 `skill://...` URI 仍可读取，但新定义应优先使用 `skill_name + tool_name`。

## 执行工作流

```python
from core.engine.runner import WorkflowRunner

runner = WorkflowRunner()
result = await runner.run_yaml("workflow.yaml")
```

## 资源管理配置

```json
{
  "mode": "eco",
  "token_quota_total": 100000,
  "token_quota_threshold": 0.8,
  "rpm_bucket_capacity": 60,
  "rpm_refill_rate": 1.0,
  "circuit_breaker_threshold": 3,
  "circuit_breaker_timeout": 300
}
```

| 模式 | 说明 |
|------|------|
| `eco` | 节能模式，严格限流，适合日常任务 |
| `burn` | 高性能模式，宽松配额，适合紧急任务 |

## 技能调用

```python
from core.infra.skill_manager import SkillManager
from core.runtime.policies import PolicyContext
from core.runtime.types import RouteDecision

manager = SkillManager()
# register(...) 由治理层或 bridge 完成

result = manager.dispatch(
    "hidream-api-gen",
    "generate_images",
    {"prompt": "a cat", "resolution": "1024*1024"},
    policy_context=PolicyContext(route=RouteDecision(mode="fast", reason="manual_call")),
)
```

> 兼容说明：legacy registry 仅作为迁移桥接器保留，不再是推荐入口。

## 关键设计原则

1. **崩溃恢复**: WAL 引擎保证任务产物不丢失，重启后可水化状态
2. **资源隔离**: 复杂任务下沉到子代理，主会话保持轻量
3. **防雪崩**: 熔断器连续 3 次失败后自动断开，避免资源耗尽
4. **配额管控**: 令牌桶限流 + 总配额控制，防止 Token 燃烧过快

## 依赖

- Python >= 3.9
- asyncio
- PyYAML (工作流定义)
- aiohttp (异步 HTTP)

## 许可证

MIT License

---

*设计用于 OpenClaw 生态，可独立使用*
