# 视频业务重构对比报告

**重构时间**: 2026-03-17T15:06  
**重构目标**: 将 video-production 从独立引擎降级为纯业务包

## 一、代码清理统计

### 归档的旧引擎代码
| 文件 | 行数 | 说明 |
|------|------|------|
| dag_engine.py | 442 | 旧 DAG 引擎 |
| dag_engine_resilient.py | 259 | 旧防御型引擎 |
| wal_task_engine.py | 389 | 旧 WAL 引擎 |
| workflow_resumer.py | 303 | 旧恢复引擎 |
| **合计** | **1,393** | **已归档至 .archived/** |

### 保留的业务代码
| 文件 | 行数 | 说明 |
|------|------|------|
| registry.py | 712 | 需要重构为 V2 |
| chaos_tests.py | 265 | 测试代码 |
| ffmpeg_*.py | 531 | FFmpeg 工具 |
| jsonpath_resolver.py | 292 | 工具代码 |
| skill_usage_hook.py | 120 | 监控代码 |
| **合计** | **1,920** | **保留** |

### 新增的全局兼容代码
| 文件 | 行数 | 说明 |
|------|------|------|
| registry_v2.py | 280 | 接入全局引擎 |
| video_agent.py | 160 | 继承物理牢笼 |
| **合计** | **440** | **新增** |

## 二、架构变更对比

### 重构前 (独立引擎)
```
video-production/
├── core/
│   ├── dag_engine.py          # 自建 DAG
│   ├── wal_threadsafe.py      # 自建 WAL
│   ├── circuit_breaker.py     # 自建熔断
│   └── registry.py            # 自建注册表
└── agents/
    └── base_agent_v2.py       # 自建 Agent 基类
```

### 重构后 (纯业务包)
```
video-production/
├── core/
│   ├── registry_v2.py         # 接入全局引擎
│   └── ...                    # 仅保留业务工具
└── agents/
    └── video_agent.py         # 继承全局 BaseAgent

~/.openclaw/workspace/core/     # 全局引擎
├── engine/
│   ├── wal_engine.py          # 全局 WAL
│   └── workflow_context.py    # 全局上下文
├── infra/
│   ├── circuit_breaker.py     # 全局熔断
│   └── resource_manager.py    # 全局资源管理
└── agent/
    └── base_agent.py          # 全局物理牢笼
```

## 三、关键变更点

### 1. 资源管理
**重构前**:
```python
# 自建资源控制
class ResourceManager:
    def request(self):
        # 自己实现限流
```

**重构后**:
```python
from core.bootstrap import get_rm

# 通过全局引擎申请
rm = get_rm()
result = await rm.request_llm(prompt)
```

### 2. 熔断机制
**重构前**:
```python
# 自建熔断
class CircuitBreaker:
    def call(self, cmd):
        # 自己实现熔断
```

**重构后**:
```python
from core.infra.circuit_breaker import CircuitBreaker

# 全局熔断器
cb = CircuitBreaker(name="video_gen", max_failures=3)
if cb.can_execute():
    result = await execute()
    cb.record_success()
```

### 3. WAL 记录
**重构前**:
```python
# 自建 WAL
wal = WALTaskEngine(log_dir="logs")
wal.start_task(task_id, ...)
```

**重构后**:
```python
from core.engine.wal_engine import WALEngine

# 全局 WAL
wal = WALEngine(wal_path="memory/daily/video.wal")
await wal.log_task_start(workflow_id, task_id, metadata)
```

### 4. Agent 基类
**重构前**:
```python
class BaseAgent:
    async def run(self):
        # 自己实现生命周期
```

**重构后**:
```python
from core.agent.base_agent import BaseAgent

class VideoProductionAgent(BaseAgent):
    async def process(self, context: WorkflowContext):
        # 必须实现抽象方法
        # 自动集成四大模块
```

## 四、测试验证

### 冒烟测试通过 ✓
```
[1/5] 初始化全局引擎... ✓
[2/5] 加载 Registry V2... ✓
[3/5] 加载 Video Production Agent... ✓
[4/5] 执行极简视频工作流... ✓
[5/5] 验证 WAL 记录... ✓
```

### 验证项
- ✓ Registry V2 接入全局引擎
- ✓ Video Agent 继承物理牢笼 (BaseAgent)
- ✓ 资源申请通过 ResourceManager
- ✓ 重试机制工作 (3次指数退避)
- ✓ 熔断器状态管理

## 五、DAG 提交流程示例

### 重构前
```python
from skills.video_production.core.dag_engine import DAGWorkflowEngine

engine = DAGWorkflowEngine(registry)
execution_id = engine.execute_workflow(workflow_def, inputs)
```

### 重构后
```python
from core.engine.workflow_registry import WorkflowRegistry
from skills.video_production.agents.video_agent import VideoProductionAgent

# 1. 创建全局工作流注册表
wr = WorkflowRegistry()

# 2. 注册视频 Agent
wr.register_agent("video_producer", VideoProductionAgent)

# 3. 提交工作流
workflow_def = {
    "agent": "video_producer",
    "inputs": {
        "script_text": "A serene landscape",
        "output_name": "test_video",
        "scenes": 1
    }
}

execution_id = await wr.submit_workflow(workflow_def)

# 4. 全局引擎自动处理
# - ResourceManager 分配 Token
# - CircuitBreaker 监控异常
# - WALEngine 记录状态
# - BaseAgent 执行任务
```

## 六、总结

### 移除代码
- **1,393 行** 旧引擎代码已归档
- 消除了与视频业务的耦合

### 架构收益
1. **单一职责**: video-production 仅保留业务逻辑
2. **全局管控**: 所有资源通过 core/infra/ 统一管理
3. **可复用性**: 其他技能可共享同一套引擎
4. **可维护性**: 引擎升级不影响业务代码

### 状态
- **阶段 1**: 物理剥离 ✅
- **阶段 2**: 底座替换 ✅
- **阶段 3**: 技能降维 ✅

**重构完成!**
