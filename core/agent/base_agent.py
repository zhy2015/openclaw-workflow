"""
BaseAgent V2 - 全局基类 (物理牢笼与四大模块集成)

四大核心模块集成：
- WAL: 前置/后置拦截，自动记录任务状态
- ResourceManager: 流量劫持，所有 LLM 请求必须经由此路
- CircuitBreaker: 异常防线，自动分类与 Alert 上报
- WorkflowContext: 内存沙箱，数据流转禁止直接文件读写

使用方式：
    class MyAgent(BaseAgent):
        async def process(self, context: WorkflowContext) -> Dict:
            # 专心拼接 Prompt 和解析 JSON
            result = await self._ask_llm("prompt")
            await context.set("output", result)
            return {"status": "success"}
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from core.infra.skill_contracts import ExecutionResult
from core.runtime.constitution import ConstitutionRuntime
from core.runtime.types import TaskEnvelope

# 四大核心模块导入
try:
    from core.engine.workflow_context import WorkflowContext, get_context
    from core.engine.wal_engine import WALEngine, get_wal_engine, TaskStatus
    from core.infra.resource_manager import ResourceManager, get_resource_manager, HibernateException
    from core.infra.circuit_breaker import get_error_handler, ErrorCategory, CircuitBreakerOpen
    from core.infra.notification import notify_alert
except ImportError:
    from core.engine.workflow_context import WorkflowContext, get_context
    from core.engine.wal_engine import WALEngine, get_wal_engine, TaskStatus
    from core.infra.resource_manager import ResourceManager, get_resource_manager, HibernateException
    from core.infra.circuit_breaker import get_error_handler, ErrorCategory, CircuitBreakerOpen
    from core.infra.notification import notify_alert


class BaseAgent(ABC):
    """
    BaseAgent 抽象基类 - 所有业务 Agent 的物理牢笼
    
    子类必须实现：
        async def process(self, context: WorkflowContext) -> Dict
    
    子类禁止：
        - 直接调用 LLM API (必须使用 self._ask_llm)
        - 直接读写文件 (必须使用 WorkflowContext)
        - 绕过 WAL 记录
    """
    
    def __init__(
        self,
        agent_id: str,
        agent_type: str = "base",
        keys_to_save: Optional[List[str]] = None
    ):
        """
        初始化 BaseAgent
        
        Args:
            agent_id: Agent 唯一标识
            agent_type: Agent 类型
            keys_to_save: 任务完成后自动保存到 WAL 的上下文 keys
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.keys_to_save = keys_to_save or []
        
        # 依赖注入的占位符（由 execute_task 注入）
        self._task_id: Optional[str] = None
        self._workflow_id: Optional[str] = None
        self._context: Optional[WorkflowContext] = None
        
        # 四大模块实例
        self._wal: Optional[WALEngine] = None
        self._rm: Optional[ResourceManager] = None
        self._constitution = ConstitutionRuntime()
        
        # 统计
        self._start_time: Optional[float] = None
        self._tokens_consumed = 0
        
        # 重试控制
        self._retry_count = 0
        self._max_retries = 3
    
    # ========================================================================
    # 核心路由方法（不可重写）
    # ========================================================================
    
    async def execute_task(
        self,
        task_id: str,
        workflow_id: str,
        context: WorkflowContext,
        **kwargs
    ) -> Dict[str, Any]:
        """
        任务执行入口 - 模板方法模式
        
        此方法不可重写！所有子类通过 process() 实现业务逻辑。
        
        流程：
        1. 依赖注入
        2. WAL 前置拦截（记录 RUNNING）
        3. CircuitBreaker 异常防线
        4. 执行业务逻辑（process）
        5. ResourceManager 流量劫持
        6. WAL 后置拦截（双写同步）
        7. 返回结果
        """
        # 1. 依赖注入
        self._task_id = task_id
        self._workflow_id = workflow_id
        self._context = context
        self._wal = get_wal_engine()
        self._rm = get_resource_manager()
        self._start_time = time.time()
        self._retry_count = 0  # 重置重试计数器
        
        print(f"\n[BaseAgent:{self.agent_id}] 开始执行任务 {task_id}")
        
        try:
            # 2. WAL 前置拦截 - 记录 RUNNING
            await self._wal.log_task_start(
                workflow_id=workflow_id,
                task_id=task_id,
                metadata={
                    "agent_id": self.agent_id,
                    "agent_type": self.agent_type,
                    "start_time": datetime.now().isoformat()
                }
            )
            
            # 3. CircuitBreaker 异常防线 + 业务逻辑执行
            result = await self._execute_with_protection(context, **kwargs)
            
            # 4. WAL 后置拦截 - 双写同步
            if result.get("success", False):
                await self._post_success(result)
            else:
                await self._post_failure(result.get("error", "Unknown error"))
            
            return result
            
        except Exception as e:
            # 异常处理
            return await self._handle_fatal_error(e)
    
    async def _execute_with_protection(
        self,
        context: WorkflowContext,
        **kwargs
    ) -> Dict[str, Any]:
        """
        受保护的业务逻辑执行
        
        使用 CircuitBreaker 包裹核心逻辑
        """
        try:
            # 执行业务逻辑（子类实现）
            process_result = await self.process(context, **kwargs)
            
            return {
                "success": True,
                "data": process_result,
                "agent_id": self.agent_id,
                "task_id": self._task_id,
                "duration": time.time() - self._start_time
            }
            
        except Exception as e:
            # CircuitBreaker 异常分类与处理
            return await self._handle_exception(e)
    
    async def _handle_exception(self, error: Exception) -> Dict[str, Any]:
        """
        异常处理 - CircuitBreaker 防线
        """
        handler = get_error_handler()
        
        # 提取 HTTP 状态码（如果存在）
        http_code = self._extract_http_code(error)
        
        # 交给 CircuitBreaker 分类处理
        result = await handler.handle_error(
            error=error,
            workflow_id=self._workflow_id,
            node_id=self._task_id,
            http_code=http_code
        )
        
        action = result.get("action")
        
        if action == "retry":
            # 检查重试次数限制
            if self._retry_count >= self._max_retries:
                error_msg = f"达到最大重试次数 ({self._max_retries})，放弃重试"
                print(f"[BaseAgent] {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "error_type": "max_retries_exceeded"
                }
            
            self._retry_count += 1
            # 可恢复错误，静默重试
            print(f"[BaseAgent] 可恢复错误，{result.get('delay', 0)}s 后重试 (尝试 {self._retry_count}/{self._max_retries})")
            await asyncio.sleep(result.get("delay", 1))
            return await self._execute_with_protection(self._context)
        
        elif action == "fix":
            # 业务逻辑错误，尝试修复
            print(f"[BaseAgent] 业务逻辑错误，尝试修复")
            # 这里可以调用 Correction Agent
            return await self._execute_with_protection(self._context)
        
        elif action == "abort":
            # 致命错误，任务中止
            print(f"[BaseAgent] 致命错误，任务中止: {result.get('message')}")
            return {
                "success": False,
                "error": result.get("message"),
                "error_type": "fatal",
                "circuit_state": handler.circuit_breaker.state.value
            }
        
        return {
            "success": False,
            "error": str(error),
            "error_type": "unknown"
        }
    
    async def _handle_fatal_error(self, error: Exception) -> Dict[str, Any]:
        """处理致命错误"""
        error_msg = f"{type(error).__name__}: {str(error)}"
        print(f"[BaseAgent] 未捕获异常: {error_msg}")
        
        # WAL 记录失败
        await self._wal.log_task_failure(
            workflow_id=self._workflow_id,
            task_id=self._task_id,
            error=error_msg
        )
        
        # Alert 上报
        await notify_alert(
            workflow_id=self._workflow_id,
            node_id=self._task_id,
            message=f"Agent {self.agent_id} 执行失败: {error_msg}",
            data={"agent_type": self.agent_type}
        )
        
        return {
            "success": False,
            "error": error_msg,
            "error_type": "uncaught_exception"
        }
    
    async def _post_success(self, result: Dict):
        """后置成功处理 - 双写同步"""
        # 提取需要保存的 keys
        payload = {}
        for key in self.keys_to_save:
            value = await self._context.get(key)
            if value is not None:
                payload[key] = value
        
        # 双写同步：WAL + WorkflowContext
        await self._wal.log_task_success(
            workflow_id=self._workflow_id,
            task_id=self._task_id,
            context=self._context,
            keys_to_save=self.keys_to_save,
            metadata={
                "agent_id": self.agent_id,
                "duration": result.get("duration"),
                "tokens_consumed": self._tokens_consumed
            }
        )
        
        print(f"[BaseAgent] 任务成功，已双写同步 ({len(payload)} keys)")
    
    async def _post_failure(self, error: str):
        """后置失败处理"""
        await self._wal.log_task_failure(
            workflow_id=self._workflow_id,
            task_id=self._task_id,
            error=error
        )
    
    def _extract_http_code(self, error: Exception) -> Optional[int]:
        """从异常中提取 HTTP 状态码"""
        error_str = str(error)
        # 简单提取 "HTTP 401" 或 "401" 格式
        import re
        match = re.search(r'\b(\d{3})\b', error_str)
        if match:
            code = int(match.group(1))
            if 400 <= code <= 599:
                return code
        return None
    
    # ========================================================================
    # 受保护方法（子类可用）
    # ========================================================================
    
    async def _ask_llm(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        受保护的 LLM 请求方法
        
        所有子类必须通过此方法发起 LLM 请求，严禁绕过！
        内部通过 ResourceManager 进行流量劫持和限流。
        """
        if self._rm is None:
            raise RuntimeError("Agent 未初始化，请先调用 execute_task")
        
        result = await self._rm.request_llm(
            prompt=prompt,
            model_params=kwargs
        )
        
        # 记录 Token 消耗
        if result.get("success"):
            metrics = result.get("metrics", {})
            if hasattr(metrics, "total_tokens"):
                self._tokens_consumed += metrics.total_tokens
        
        return result
    
    async def _invoke_constitution(
        self,
        task_type: str,
        intent: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        target_skill: Optional[str] = None,
        target_tool: Optional[str] = None,
        requires_side_effects: bool = False,
        references_memory: bool = False,
        complexity_hint: Optional[str] = None,
        recall_performed: bool = False,
    ) -> ExecutionResult:
        envelope = TaskEnvelope(
            task_type=task_type,
            intent=intent,
            params=params or {},
            caller=self.agent_id,
            source=f"agent:{self.agent_type}",
            requires_side_effects=requires_side_effects,
            references_memory=references_memory,
            complexity_hint=complexity_hint,
            target_skill=target_skill,
            target_tool=target_tool,
        )
        return await self._constitution.invoke(envelope, recall_performed=recall_performed)

    async def _invoke_skill(
        self,
        skill_name: str,
        tool_name: str,
        params: Optional[Dict[str, Any]] = None,
        *,
        references_memory: bool = False,
        complexity_hint: Optional[str] = None,
        recall_performed: bool = False,
    ) -> ExecutionResult:
        return await self._invoke_constitution(
            task_type="skill_call",
            intent=f"{skill_name}.{tool_name}",
            params=params or {},
            target_skill=skill_name,
            target_tool=tool_name,
            references_memory=references_memory,
            complexity_hint=complexity_hint,
            recall_performed=recall_performed,
        )

    async def _get_from_context(self, key: str, default=None) -> Any:
        """从 WorkflowContext 获取数据"""
        if self._context is None:
            return default
        return await self._context.get(key, default)
    
    async def _set_to_context(self, key: str, value: Any):
        """设置数据到 WorkflowContext"""
        if self._context is None:
            raise RuntimeError("Agent 未初始化，请先调用 execute_task")
        await self._context.set(key, value)
    
    # ========================================================================
    # 抽象方法（子类必须实现）
    # ========================================================================
    
    @abstractmethod
    async def process(self, context: WorkflowContext, **kwargs) -> Dict[str, Any]:
        """
        业务逻辑实现 - 子类必须重写
        
        子类只需：
        1. 从 context 读取输入数据
        2. 拼接 Prompt
        3. 调用 self._ask_llm() 获取结果
        4. 解析 JSON
        5. 将输出写回 context
        
        底层限流、重试、写日志、熔断全部由 BaseAgent 接管。
        
        Args:
            context: WorkflowContext 实例
            **kwargs: 额外参数
        
        Returns:
            业务结果字典
        """
        pass


# ========================================================================
# 示例实现
# ========================================================================

class StoryGeneratorAgent(BaseAgent):
    """故事生成 Agent 示例"""
    
    def __init__(self):
        super().__init__(
            agent_id="story_gen",
            agent_type="generator",
            keys_to_save=["story_outline", "characters"]
        )
    
    async def process(self, context: WorkflowContext, **kwargs) -> Dict[str, Any]:
        """实现业务逻辑"""
        # 1. 读取输入
        theme = await self._get_from_context("theme", "adventure")
        
        # 2. 拼接 Prompt
        prompt = f"Generate a {theme} story outline with 3 characters"
        
        # 3. 调用 LLM（自动走 ResourceManager）
        result = await self._ask_llm(prompt, temperature=0.8)
        
        if not result["success"]:
            return {"status": "failed", "error": result.get("error")}
        
        # 4. 解析结果
        story_text = result["data"]
        
        # 5. 写回 context
        await self._set_to_context("story_outline", story_text)
        await self._set_to_context("characters", ["Alice", "Bob", "Charlie"])
        
        return {"status": "success", "story_length": len(story_text)}


class ErrorTestAgent(BaseAgent):
    """测试异常处理的 Agent"""
    
    def __init__(self, error_type: str = "429"):
        super().__init__(
            agent_id=f"error_test_{error_type}",
            agent_type="test"
        )
        self.error_type = error_type
    
    async def process(self, context: WorkflowContext, **kwargs) -> Dict[str, Any]:
        """模拟各种错误"""
        if self.error_type == "429":
            raise Exception("HTTP 429: Too Many Requests")
        elif self.error_type == "401":
            raise Exception("HTTP 401: Unauthorized")
        elif self.error_type == "json":
            json.loads("invalid json")
        
        return {"status": "success"}


if __name__ == "__main__":
    async def test_base_agent():
        print("=" * 60)
        print("BaseAgent V2 集成测试")
        print("=" * 60)
        
        try:
            from core.bootstrap import initialize_system
            from core.engine.workflow_context import clear_all_contexts
        except ImportError:
            from core.bootstrap import initialize_system
            from core.engine.workflow_context import clear_all_contexts
        
        # 初始化系统
        await initialize_system(mode="eco")
        clear_all_contexts()
        
        # 测试 1: 正常流程
        print("\n[Test 1] 正常任务流程")
        ctx = get_context("wf-test-1")
        await ctx.set("theme", "sci-fi")
        
        agent = StoryGeneratorAgent()
        result = await agent.execute_task(
            task_id="task-1",
            workflow_id="wf-test-1",
            context=ctx
        )
        
        print(f"  Result: {result}")
        print(f"  Story in context: {(await ctx.get('story_outline'))[:50]}...")
        
        # 测试 2: 429 错误（可恢复）
        print("\n[Test 2] 429 错误处理")
        agent429 = ErrorTestAgent("429")
        result = await agent429.execute_task(
            task_id="task-429",
            workflow_id="wf-test-429",
            context=get_context("wf-test-429")
        )
        print(f"  Result: {result}")
        
        # 测试 3: 401 错误（熔断）
        print("\n[Test 3] 401 熔断处理")
        agent401 = ErrorTestAgent("401")
        result = await agent401.execute_task(
            task_id="task-401",
            workflow_id="wf-test-401",
            context=get_context("wf-test-401")
        )
        print(f"  Result: {result}")
        print(f"  Circuit state: {result.get('circuit_state')}")
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)
    
    asyncio.run(test_base_agent())
