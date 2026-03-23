# WORKFLOW.md - 五阶段工作流架构文档

## 概述

本文档记录完整的 Agent 工作流架构，包含五大核心模块。每次会话重置后必须阅读此文档。

## 五大核心模块

### 1. WAL (Write-Ahead Logging)
- **文件**: `core/wal_engine.py`
- **功能**: 任务状态持久化、崩溃恢复、双写同步
- **关键方法**:
  - `log_task_start()` - 记录任务开始
  - `log_task_success()` - 记录成功并保存 payload
  - `hydrate()` - 状态水化恢复

### 2. ResourceManager (双模资源调度)
- **文件**: `core/resource_manager.py`
- **功能**: Token 配额管理、RPM 限流、熔断保护
- **模式**:
  - Eco Mode: 令牌桶限流 + 阻塞等待
  - Burn Mode: AIMD 动态并发控制

### 3. CircuitBreaker (熔断器)
- **文件**: `core/circuit_breaker.py`
- **功能**: 错误分类、熔断保护、Alert 上报
- **错误分类**:
  - Recoverable (429/502/504): 自适应退避重试
  - Logical (JSON解析): Correction Agent 修复
  - Fatal (401/402): 熔断 + 立即 Alert

### 4. WorkflowContext (内存沙箱)
- **文件**: `core/workflow_context.py`
- **功能**: 协程安全的内存键值存储
- **禁止**: 直接文件读写，所有数据必须通过此类流转

### 5. BaseAgent (全局基类)
- **文件**: `core/base_agent_v2.py`
- **功能**: 四大模块集成、模板方法模式
- **使用**: 所有业务 Agent 必须继承此类

## 快速启动

```python
import asyncio
from core.bootstrap import initialize_system
from core.base_agent_v2 import BaseAgent
from core.workflow_context import get_context

async def main():
    # 1. 初始化系统（加载四大模块）
    await initialize_system(mode="eco")
    
    # 2. 创建业务 Agent
    class MyAgent(BaseAgent):
        async def process(self, context):
            # 读取输入
            data = await self._get_from_context("input")
            
            # 调用 LLM（自动走 ResourceManager）
            result = await self._ask_llm(f"Process: {data}")
            
            # 写回输出
            await self._set_to_context("output", result)
            
            return {"status": "success"}
    
    # 3. 执行任务
    agent = MyAgent()
    ctx = get_context("my-workflow")
    await ctx.set("input", "Hello")
    
    result = await agent.execute_task(
        task_id="task-1",
        workflow_id="my-workflow",
        context=ctx
    )

asyncio.run(main())
```

## 文件清单

```
core/
├── resource_manager.py      # 双模资源调度引擎
├── resource_config.json     # 资源配置
├── circuit_breaker.py       # 熔断器与错误分类
├── notification.py          # 通知 Hook (Silent/Milestone/Alert)
├── workflow_context.py      # 内存上下文沙箱
├── wal_engine.py            # WAL 引擎与水化
├── base_agent_v2.py         # 全局基类 (物理牢笼)
├── bootstrap.py             # 系统初始化入口
└── test_*.py                # 单元测试
```

## 关键约束

1. **禁止直接 LLM 调用** - 必须使用 `self._ask_llm()`
2. **禁止文件读写** - 必须使用 `WorkflowContext`
3. **禁止绕过 WAL** - 状态自动记录
4. **禁止忽略异常** - CircuitBreaker 自动处理

## 版本

- Version: 1.0
- Created: 2026-03-15
- Stages: 5/5 Complete
