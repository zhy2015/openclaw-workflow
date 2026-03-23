#!/usr/bin/env python3
"""
Workflow Registry - 工作流任务注册表

管理所有工作流任务的生命周期，支持会话恢复时的状态验证。
"""

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

from core.engine.task_verifier import verify_task, VerificationResult, VerificationReport


class WorkflowStatus(Enum):
    """工作流状态"""
    PENDING = "pending"       # 待执行
    RUNNING = "running"       # 执行中
    SUCCESS = "success"       # 成功完成
    FAILED = "failed"         # 失败
    CRASHED = "crashed"       # 崩溃（需恢复）
    INTERRUPTED = "interrupted"  # 用户中断
    STALE = "stale"           # 心跳超时


class TaskStatus(Enum):
    """原子任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    VERIFIED = "verified"     # 已验证成功
    INVALID = "invalid"       # 验证失败（产物无效）


@dataclass
class AtomicTask:
    """原子任务"""
    task_id: str
    task_type: str
    depends_on: List[str] = field(default_factory=list)
    status: str = TaskStatus.PENDING.value
    outputs: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    verified_at: Optional[str] = None
    retry_count: int = 0


@dataclass
class Workflow:
    """工作流"""
    workflow_id: str
    name: str
    description: str
    status: str = WorkflowStatus.PENDING.value
    tasks: Dict[str, AtomicTask] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    session_id: Optional[str] = None
    last_heartbeat: Optional[str] = None
    completed_tasks: List[str] = field(default_factory=list)
    failed_tasks: List[str] = field(default_factory=list)
    wal_path: Optional[str] = None  # WAL 日志路径


class WorkflowRegistry:
    """
    工作流注册表
    
    职责:
    1. 记录所有工作流的状态
    2. 会话启动时验证任务产物
    3. 识别崩溃/中断的任务
    4. 支持恢复执行
    """
    
    def __init__(self, registry_path: Optional[str] = None):
        resolved_path = registry_path or str((__import__('pathlib').Path(__file__).resolve().parents[2] / 'workflows' / 'registry.json'))
        self.registry_path = resolved_path
        self.workflows_dir = os.path.dirname(resolved_path)
        self._workflows: Dict[str, Workflow] = {}
        self._heartbeat_timeout = 300  # 5分钟超时
        
        os.makedirs(self.workflows_dir, exist_ok=True)
        self._load()
    
    def _load(self):
        """加载注册表"""
        if os.path.exists(self.registry_path):
            with open(self.registry_path, 'r') as f:
                data = json.load(f)
                for wf_id, wf_data in data.get("workflows", {}).items():
                    # 转换 tasks 为 AtomicTask 对象
                    tasks = {}
                    for tid, tdata in wf_data.get("tasks", {}).items():
                        tasks[tid] = AtomicTask(**tdata)
                    wf_data["tasks"] = tasks
                    self._workflows[wf_id] = Workflow(**wf_data)
    
    def _save(self):
        """保存注册表"""
        data = {
            "updated_at": datetime.now().isoformat(),
            "workflows": {}
        }
        for wf_id, wf in self._workflows.items():
            wf_dict = asdict(wf)
            # 转换 tasks 为普通 dict
            wf_dict["tasks"] = {tid: asdict(t) for tid, t in wf.tasks.items()}
            data["workflows"][wf_id] = wf_dict
        
        with open(self.registry_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_workflow(self, workflow_id: str, name: str, description: str = "") -> Workflow:
        """创建新工作流"""
        workflow = Workflow(
            workflow_id=workflow_id,
            name=name,
            description=description,
            wal_path=os.path.join(self.workflows_dir, f"{workflow_id}.wal")
        )
        self._workflows[workflow_id] = workflow
        self._save()
        return workflow
    
    def add_task(self, workflow_id: str, task_id: str, task_type: str,
                 depends_on: Optional[List[str]] = None) -> AtomicTask:
        """向工作流添加原子任务"""
        if workflow_id not in self._workflows:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        task = AtomicTask(
            task_id=task_id,
            task_type=task_type,
            depends_on=depends_on or []
        )
        self._workflows[workflow_id].tasks[task_id] = task
        self._save()
        return task
    
    def update_task_status(self, workflow_id: str, task_id: str, status: TaskStatus,
                          outputs: Optional[Dict[str, Any]] = None):
        """更新任务状态"""
        if workflow_id not in self._workflows:
            return
        
        wf = self._workflows[workflow_id]
        if task_id not in wf.tasks:
            return
        
        task = wf.tasks[task_id]
        if isinstance(status, TaskStatus):
            task.status = status.value
        else:
            task.status = status
        
        if status == TaskStatus.RUNNING:
            task.started_at = datetime.now().isoformat()
        elif status in (TaskStatus.SUCCESS, TaskStatus.FAILED):
            task.completed_at = datetime.now().isoformat()
            if outputs:
                task.outputs = outputs
        
        wf.updated_at = datetime.now().isoformat()
        self._save()
    
    def heartbeat(self, workflow_id: str, session_id: str):
        """更新工作流心跳"""
        if workflow_id in self._workflows:
            wf = self._workflows[workflow_id]
            wf.session_id = session_id
            wf.last_heartbeat = datetime.now().isoformat()
            self._save()
    
    def verify_and_recover(self) -> Dict[str, Any]:
        """
        会话启动时调用：验证所有工作流状态
        
        Returns:
            恢复报告
        """
        report = {
            "checked": 0,
            "valid": [],
            "recovered": [],
            "crashed": [],
            "stale": [],
            "actions": []
        }
        
        for wf_id, wf in self._workflows.items():
            report["checked"] += 1
            
            # 1. 检查 RUNNING 状态的工作流
            if wf.status == WorkflowStatus.RUNNING.value:
                # 检查心跳是否超时
                if wf.last_heartbeat:
                    last_hb = datetime.fromisoformat(wf.last_heartbeat)
                    if datetime.now() - last_hb > timedelta(seconds=self._heartbeat_timeout):
                        wf.status = WorkflowStatus.STALE.value
                        report["stale"].append(wf_id)
                        report["actions"].append(f"Workflow {wf_id} marked as STALE (no heartbeat)")
                        continue
                
                # 2. 验证每个 RUNNING 的原子任务
                for task_id, task in wf.tasks.items():
                    if task.status == TaskStatus.RUNNING.value:
                        # 任务正在执行但会话已重启 → 标记为 CRASHED
                        task.status = TaskStatus.FAILED.value
                        wf.status = WorkflowStatus.CRASHED.value
                        report["crashed"].append(f"{wf_id}/{task_id}")
                        report["actions"].append(f"Task {task_id} in {wf_id} marked as CRASHED")
                
                # 如果所有任务都已验证，更新工作流状态
                self._verify_all_tasks(wf_id)
            
            # 3. 验证 SUCCESS 状态的任务（二次确认产物）
            elif wf.status == WorkflowStatus.SUCCESS.value:
                for task_id, task in wf.tasks.items():
                    if task.status == TaskStatus.SUCCESS.value and task.outputs:
                        verification = verify_task(task.task_type, task.outputs)
                        if verification.result == VerificationResult.VALID:
                            task.status = TaskStatus.VERIFIED.value
                            report["valid"].append(f"{wf_id}/{task_id}")
                        elif verification.result == VerificationResult.INVALID:
                            task.status = TaskStatus.INVALID.value
                            report["actions"].append(
                                f"Task {task_id} in {wf_id} INVALID: {verification.suggestion}"
                            )
        
        self._save()
        return report
    
    def _verify_all_tasks(self, workflow_id: str):
        """验证工作流中所有已完成的任务"""
        wf = self._workflows[workflow_id]
        all_verified = True
        
        for task_id, task in wf.tasks.items():
            if task.status == TaskStatus.SUCCESS.value and task.outputs:
                verification = verify_task(task.task_type, task.outputs)
                if verification.result == VerificationResult.VALID:
                    task.status = TaskStatus.VERIFIED.value
                    task.verified_at = datetime.now().isoformat()
                else:
                    all_verified = False
            elif task.status == TaskStatus.FAILED.value:
                all_verified = False
        
        if all_verified:
            wf.status = WorkflowStatus.SUCCESS.value
    
    def get_recoverable_workflows(self) -> List[Workflow]:
        """获取需要恢复的工作流"""
        recoverable = []
        for wf in self._workflows.values():
            if wf.status in (WorkflowStatus.CRASHED.value, WorkflowStatus.STALE.value, 
                           WorkflowStatus.INTERRUPTED.value):
                recoverable.append(wf)
        return recoverable
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """获取工作流"""
        return self._workflows.get(workflow_id)
    
    def list_workflows(self, status: Optional[str] = None) -> List[Workflow]:
        """列出工作流"""
        workflows = list(self._workflows.values())
        if status:
            workflows = [w for w in workflows if w.status == status]
        return workflows
    
    def archive_workflow(self, workflow_id: str):
        """归档已完成的工作流"""
        if workflow_id in self._workflows:
            wf = self._workflows[workflow_id]
            archive_path = os.path.join(self.workflows_dir, "archive", f"{workflow_id}.json")
            os.makedirs(os.path.dirname(archive_path), exist_ok=True)
            
            with open(archive_path, 'w') as f:
                json.dump(asdict(wf), f, indent=2)
            
            del self._workflows[workflow_id]
            self._save()
    
    def cleanup_old_workflows(self, days: int = 7):
        """清理旧的工作流"""
        cutoff = datetime.now() - timedelta(days=days)
        to_remove = []
        
        for wf_id, wf in self._workflows.items():
            if wf.status in (WorkflowStatus.SUCCESS.value, WorkflowStatus.FAILED.value):
                updated = datetime.fromisoformat(wf.updated_at)
                if updated < cutoff:
                    to_remove.append(wf_id)
        
        for wf_id in to_remove:
            self.archive_workflow(wf_id)
        
        return len(to_remove)


# 便捷函数
def get_registry() -> WorkflowRegistry:
    """获取全局注册表实例"""
    return WorkflowRegistry()


def on_session_start() -> Dict[str, Any]:
    """
    会话启动时调用
    
    自动验证并恢复工作流
    """
    registry = get_registry()
    report = registry.verify_and_recover()
    
    # 获取可恢复的工作流
    recoverable = registry.get_recoverable_workflows()
    
    return {
        "verification_report": report,
        "recoverable_count": len(recoverable),
        "recoverable_workflows": [w.workflow_id for w in recoverable]
    }


if __name__ == "__main__":
    # 测试
    result = on_session_start()
    print(json.dumps(result, indent=2))