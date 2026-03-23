"""
WorkflowContext - 内存上下文沙箱

特性：
- 协程安全（asyncio.Lock）
- 纯内存键值存储
- 支持快照与恢复
- 禁止直接文件读写，所有数据流转必须通过此类
"""

import asyncio
import json
import time
from typing import Any, Optional, Dict, List
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ContextSnapshot:
    """上下文快照"""
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    version: int = 1


class WorkflowContext:
    """
    工作流上下文 - 协程安全的内存沙箱
    
    使用方式：
        ctx = WorkflowContext()
        await ctx.set("scene_1", {...})
        data = await ctx.get("scene_1")
    """
    
    def __init__(self, workflow_id: str = "default"):
        self.workflow_id = workflow_id
        self._data: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self._version = 0
        self._history: List[ContextSnapshot] = []
        self._max_history = 10
    
    async def set(self, key: str, value: Any) -> None:
        """
        设置键值（协程安全）
        
        Args:
            key: 键
            value: 值（任意类型，会被 JSON 序列化）
        """
        async with self._lock:
            self._data[key] = value
            self._version += 1
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        获取键值（协程安全）
        
        Args:
            key: 键
            default: 默认值
        
        Returns:
            值或默认值
        """
        async with self._lock:
            return self._data.get(key, default)
    
    async def delete(self, key: str) -> bool:
        """删除键（协程安全）"""
        async with self._lock:
            if key in self._data:
                del self._data[key]
                self._version += 1
                return True
            return False
    
    async def keys(self) -> List[str]:
        """获取所有键（协程安全）"""
        async with self._lock:
            return list(self._data.keys())
    
    async def to_dict(self) -> Dict[str, Any]:
        """导出为字典（协程安全）"""
        async with self._lock:
            return self._data.copy()
    
    async def from_dict(self, data: Dict[str, Any]) -> None:
        """从字典导入（协程安全）"""
        async with self._lock:
            self._data = data.copy()
            self._version += 1
    
    async def snapshot(self) -> ContextSnapshot:
        """创建快照（协程安全）"""
        async with self._lock:
            snapshot = ContextSnapshot(
                data=self._data.copy(),
                timestamp=time.time(),
                version=self._version
            )
            self._history.append(snapshot)
            
            # 限制历史记录长度
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]
            
            return snapshot
    
    async def restore(self, snapshot: ContextSnapshot) -> None:
        """从快照恢复（协程安全）"""
        async with self._lock:
            self._data = snapshot.data.copy()
            self._version = snapshot.version
    
    async def clear(self) -> None:
        """清空所有数据（协程安全）"""
        async with self._lock:
            self._data.clear()
            self._version += 1
    
    def __repr__(self) -> str:
        return f"WorkflowContext(id={self.workflow_id}, keys={len(self._data)}, version={self._version})"


# 全局上下文管理器
_contexts: Dict[str, WorkflowContext] = {}


def get_context(workflow_id: str = "default") -> WorkflowContext:
    """获取或创建工作流上下文"""
    if workflow_id not in _contexts:
        _contexts[workflow_id] = WorkflowContext(workflow_id)
    return _contexts[workflow_id]


def clear_all_contexts():
    """清空所有上下文（用于测试）"""
    _contexts.clear()


if __name__ == "__main__":
    async def test_workflow_context():
        print("=== WorkflowContext Test ===\n")
        
        ctx = get_context("test-wf-1")
        
        # 测试 set/get
        print("1. Testing set/get")
        await ctx.set("scene_1", {"description": "A dark forest", "characters": ["Alice"]})
        await ctx.set("scene_2", {"description": "A castle", "characters": ["Bob"]})
        
        scene1 = await ctx.get("scene_1")
        print(f"   scene_1: {scene1}")
        
        # 测试并发安全
        print("\n2. Testing concurrent access")
        
        async def writer(n):
            for i in range(5):
                await ctx.set(f"key_{n}_{i}", f"value_{n}_{i}")
            print(f"   Writer {n} done")
        
        await asyncio.gather(writer(1), writer(2), writer(3))
        
        keys = await ctx.keys()
        print(f"   Total keys: {len(keys)}")
        
        # 测试快照
        print("\n3. Testing snapshot")
        snapshot = await ctx.snapshot()
        print(f"   Snapshot created: {snapshot}")
        
        # 测试导出
        print("\n4. Testing export")
        data = await ctx.to_dict()
        print(f"   Exported {len(data)} items")
        
        print("\n=== Test Complete ===")
    
    asyncio.run(test_workflow_context())
