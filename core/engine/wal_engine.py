"""
WAL Engine - 支持 Payload 双写与状态水化

特性：
- 任务成功时将产物数据作为 payload 写入 WAL
- 崩溃重启时从 WAL 恢复内存上下文
- 原子性保证
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

try:
    from core.engine.workflow_context import get_context, WorkflowContext
except ImportError:
    from core.engine.workflow_context import get_context, WorkflowContext


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class WALEngine:
    """
    WAL 引擎 - 支持双写同步与状态水化
    
    WAL 记录格式：
    {
        "timestamp": 1234567890.123,
        "workflow_id": "wf-1",
        "task_id": "task-1",
        "status": "success",
        "payload": {...},  # 任务产物数据
        "metadata": {...}
    }
    """
    
    def __init__(self, wal_path: str = ".workflow/wal.jsonl"):
        self.wal_path = Path(wal_path)
        self.wal_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
    
    async def log_task_start(self, workflow_id: str, task_id: str, metadata: Dict = None):
        """记录任务开始"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "workflow_id": workflow_id,
            "task_id": task_id,
            "status": TaskStatus.RUNNING.value,
            "metadata": metadata or {}
        }
        await self._append_record(record)
    
    async def log_task_success(
        self,
        workflow_id: str,
        task_id: str,
        context: WorkflowContext,
        keys_to_save: Optional[List[str]] = None,
        metadata: Dict = None
    ):
        """
        记录任务成功 - 双写同步
        
        将指定 keys 的数据从 WorkflowContext 提取并写入 WAL
        """
        # 提取 payload 数据
        if keys_to_save:
            payload = {}
            for key in keys_to_save:
                value = await context.get(key)
                if value is not None:
                    payload[key] = value
        else:
            # 保存所有数据
            payload = await context.to_dict()
        
        record = {
            "timestamp": datetime.now().isoformat(),
            "workflow_id": workflow_id,
            "task_id": task_id,
            "status": TaskStatus.SUCCESS.value,
            "payload": payload,
            "metadata": metadata or {}
        }
        
        await self._append_record(record)
    
    async def log_task_failure(
        self,
        workflow_id: str,
        task_id: str,
        error: str,
        metadata: Dict = None
    ):
        """记录任务失败"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "workflow_id": workflow_id,
            "task_id": task_id,
            "status": TaskStatus.FAILED.value,
            "error": error,
            "metadata": metadata or {}
        }
        await self._append_record(record)
    
    async def _append_record(self, record: Dict):
        """原子性追加记录"""
        async with self._lock:
            with open(self.wal_path, "a") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                f.flush()
                os.fsync(f.fileno())  # 确保写入磁盘
    
    async def hydrate(self, workflow_id: str) -> WorkflowContext:
        """
        状态水化 - 从 WAL 恢复内存上下文
        
        扫描 WAL，提取所有 SUCCESS 记录的 payload，恢复到 WorkflowContext
        """
        context = get_context(workflow_id)
        
        if not self.wal_path.exists():
            print(f"[Hydration] No WAL found for {workflow_id}")
            return context
        
        print(f"[Hydration] Scanning WAL for {workflow_id}...")
        
        restored_count = 0
        last_success_records: Dict[str, Dict] = {}  # task_id -> record
        
        # 读取 WAL
        with open(self.wal_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    record = json.loads(line)
                    
                    # 只处理指定 workflow 的 SUCCESS 记录
                    if record.get("workflow_id") != workflow_id:
                        continue
                    
                    if record.get("status") == TaskStatus.SUCCESS.value:
                        task_id = record.get("task_id")
                        # 保留每个任务的最新成功记录
                        last_success_records[task_id] = record
                
                except json.JSONDecodeError:
                    continue
        
        # 恢复数据到上下文
        for task_id, record in last_success_records.items():
            payload = record.get("payload", {})
            for key, value in payload.items():
                await context.set(key, value)
                restored_count += 1
            
            print(f"[Hydration] Restored task {task_id}: {len(payload)} keys")
        
        print(f"[Hydration] Complete! Restored {restored_count} items from {len(last_success_records)} tasks")
        
        return context
    
    async def get_task_status(self, workflow_id: str, task_id: str) -> Optional[TaskStatus]:
        """获取任务最新状态"""
        if not self.wal_path.exists():
            return None
        
        latest_status = None
        
        with open(self.wal_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    record = json.loads(line)
                    if (record.get("workflow_id") == workflow_id and
                        record.get("task_id") == task_id):
                        status_str = record.get("status")
                        if status_str:
                            latest_status = TaskStatus(status_str)
                except (json.JSONDecodeError, ValueError):
                    continue
        
        return latest_status
    
    async def get_workflow_tasks(self, workflow_id: str) -> Dict[str, TaskStatus]:
        """获取工作流所有任务状态"""
        tasks = {}
        
        if not self.wal_path.exists():
            return tasks
        
        with open(self.wal_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    record = json.loads(line)
                    if record.get("workflow_id") == workflow_id:
                        task_id = record.get("task_id")
                        status_str = record.get("status")
                        if task_id and status_str:
                            tasks[task_id] = TaskStatus(status_str)
                except (json.JSONDecodeError, ValueError):
                    continue
        
        return tasks


# 便捷函数
_wal_engine: Optional[WALEngine] = None


def get_wal_engine(wal_path: str = ".workflow/wal.jsonl") -> WALEngine:
    """获取 WAL 引擎单例"""
    global _wal_engine
    if _wal_engine is None:
        _wal_engine = WALEngine(wal_path)
    return _wal_engine


if __name__ == "__main__":
    async def test_wal_engine():
        print("=== WAL Engine Test ===\n")
        
        # 清理测试环境
        test_wal_path = ".workflow/test_wal.jsonl"
        if os.path.exists(test_wal_path):
            os.remove(test_wal_path)
        
        engine = WALEngine(test_wal_path)
        
        # 测试 1: 写入任务成功记录（带 payload）
        print("1. Writing task success with payload")
        ctx = get_context("wf-test-1")
        await ctx.set("scene_1", {"desc": "Dark forest", "chars": ["Alice", "Bob"]})
        await ctx.set("scene_2", {"desc": "Castle", "chars": ["King"]})
        
        await engine.log_task_success(
            workflow_id="wf-test-1",
            task_id="task-1",
            context=ctx,
            keys_to_save=["scene_1", "scene_2"]
        )
        print("   Written to WAL\n")
        
        # 测试 2: 模拟崩溃 - 清空内存
        print("2. Simulating crash - clearing memory")
        await ctx.clear()
        print(f"   Context after clear: {await ctx.keys()}")
        print()
        
        # 测试 3: 水化恢复
        print("3. Hydrating from WAL")
        restored_ctx = await engine.hydrate("wf-test-1")
        
        scene1 = await restored_ctx.get("scene_1")
        print(f"   Restored scene_1: {scene1}")
        print(f"   Total keys: {len(await restored_ctx.keys())}")
        print()
        
        # 测试 4: 验证状态查询
        print("4. Checking task status")
        status = await engine.get_task_status("wf-test-1", "task-1")
        print(f"   Task status: {status}")
        
        print("\n=== Test Complete ===")
    
    asyncio.run(test_wal_engine())
