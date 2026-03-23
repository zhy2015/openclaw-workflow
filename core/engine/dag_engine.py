"""
DAG Engine - 极简 Skill 流水线调度器

核心职责:
1. 依赖解析 (Topological Sort) - 确定执行顺序
2. 上下文流转 - 节点输出 → 下一节点输入
3. 纯触发器 - 通过 governed dispatcher 调用 skill

与 WAL Engine 解耦 - 如需崩溃恢复，通过事件驱动异步集成
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from collections import deque

from core.engine.workflow_context import get_context, WorkflowContext
from core.runtime.dispatch import GovernedDispatcher


class NodeStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class DAGNode:
    """DAG 节点"""
    node_id: str
    skill_uri: Optional[str] = None         # legacy compatibility: skill://name/action
    skill_name: Optional[str] = None        # canonical target skill name
    tool_name: Optional[str] = None         # canonical target tool name
    inputs: Dict[str, str] = field(default_factory=dict)   # {param: "from_node.output_key"}
    outputs: List[str] = field(default_factory=list)       # 输出键名列表
    retries: int = 3
    timeout: int = 300       # 秒

    # 运行时状态
    status: NodeStatus = NodeStatus.PENDING
    result: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def resolve_target(self) -> tuple[str, str]:
        if self.skill_name and self.tool_name:
            return self.skill_name, self.tool_name
        if self.skill_uri:
            target = GovernedDispatcher.parse_legacy_uri(self.skill_uri)
            return target.skill_name, target.tool_name
        raise ValueError(f"Node {self.node_id} missing dispatch target")


@dataclass
class DAGPipeline:
    """DAG 流水线定义"""
    pipeline_id: str
    name: str
    nodes: Dict[str, DAGNode] = field(default_factory=dict)
    edges: Dict[str, List[str]] = field(default_factory=dict)  # node_id -> [下游节点]

    def add_node(self, node: DAGNode) -> "DAGPipeline":
        self.nodes[node.node_id] = node
        return self

    def add_edge(self, from_node: str, to_node: str) -> "DAGPipeline":
        if from_node not in self.edges:
            self.edges[from_node] = []
        self.edges[from_node].append(to_node)
        return self


class DAGEngine:
    """
    DAG 执行引擎

    说明：
    - 旧 `skill://...` URI 仍可兼容读取
    - 实际执行已改为 governed dispatcher
    - 新格式优先使用 `skill_name` + `tool_name`
    """

    def __init__(self, dispatcher: Optional[GovernedDispatcher] = None, context: Optional[WorkflowContext] = None):
        self.dispatcher = dispatcher or GovernedDispatcher()
        self.context = context or get_context()
        self._callbacks: List[Callable] = []

    def on_node_complete(self, callback: Callable[[str, Dict], None]):
        """注册节点完成回调 (用于 WAL 集成)"""
        self._callbacks.append(callback)

    async def execute(self, pipeline: DAGPipeline) -> Dict[str, Any]:
        """执行 DAG 流水线"""
        execution_order = self._topological_sort(pipeline)

        for node_id in execution_order:
            node = pipeline.nodes[node_id]
            await self._execute_node(node, pipeline)

            for cb in self._callbacks:
                asyncio.create_task(cb(node_id, {
                    "status": node.status.value,
                    "outputs": node.result,
                    "error": node.error
                }))

            if node.status == NodeStatus.FAILED:
                raise RuntimeError(f"Pipeline failed at node: {node_id} - {node.error}")

        return {
            node_id: node.result
            for node_id, node in pipeline.nodes.items()
            if node.status == NodeStatus.SUCCESS
        }

    def _topological_sort(self, pipeline: DAGPipeline) -> List[str]:
        in_degree = {node_id: 0 for node_id in pipeline.nodes}
        for from_node, to_nodes in pipeline.edges.items():
            for to_node in to_nodes:
                in_degree[to_node] += 1

        queue = deque([n for n, d in in_degree.items() if d == 0])
        result = []

        while queue:
            node_id = queue.popleft()
            result.append(node_id)

            for next_node in pipeline.edges.get(node_id, []):
                in_degree[next_node] -= 1
                if in_degree[next_node] == 0:
                    queue.append(next_node)

        if len(result) != len(pipeline.nodes):
            raise ValueError("DAG contains cycles")

        return result

    async def _execute_node(self, node: DAGNode, pipeline: DAGPipeline):
        node.status = NodeStatus.RUNNING

        try:
            kwargs = await self._resolve_inputs(node, pipeline)
            skill_name, tool_name = node.resolve_target()
            result = await self._call_skill(skill_name, tool_name, kwargs)

            if not isinstance(result, dict):
                raise TypeError(f"Node {node.node_id} expected dict result, got {type(result).__name__}")

            for key in node.outputs:
                if key in result:
                    await self.context.set(f"{node.node_id}.{key}", result[key])

            node.result = result
            node.status = NodeStatus.SUCCESS

        except Exception as e:
            node.error = str(e)
            node.status = NodeStatus.FAILED

    async def _resolve_inputs(self, node: DAGNode, pipeline: DAGPipeline) -> Dict[str, Any]:
        kwargs = {}

        for param, source in node.inputs.items():
            if "." in source:
                source_node_id, output_key = source.split(".", 1)
                source_node = pipeline.nodes.get(source_node_id)

                if source_node and source_node.status == NodeStatus.SUCCESS:
                    kwargs[param] = source_node.result.get(output_key)
                else:
                    kwargs[param] = await self.context.get(f"{source_node_id}.{output_key}")
            else:
                kwargs[param] = source

        return kwargs

    async def _call_skill(self, skill_name: str, tool_name: str, kwargs: Dict[str, Any]) -> Any:
        loop = asyncio.get_event_loop()

        def _dispatch():
            result = self.dispatcher.dispatch(skill_name, tool_name, kwargs)
            if not result.ok:
                raise RuntimeError(result.error or f"Dispatch failed: {result.code}")
            return result.data

        return await loop.run_in_executor(None, _dispatch)


async def run_pipeline(pipeline: DAGPipeline, dispatcher: Optional[GovernedDispatcher] = None) -> Dict[str, Any]:
    """快捷执行流水线"""
    engine = DAGEngine(dispatcher=dispatcher)
    return await engine.execute(pipeline)
