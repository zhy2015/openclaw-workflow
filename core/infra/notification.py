"""
Notification Hook - 事件驱动汇报机制

三层汇报级别：
- Silent: 原子任务完成，只写 WAL 不汇报
- Milestone: DAG 叶子节点全部完成，聚合汇报
- Alert: 异常/熔断，立即汇报

包含 10 秒防抖聚合器（Debouncer）
"""

import asyncio
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable
from collections import defaultdict
import json


class NotificationLevel(Enum):
    SILENT = "silent"      # 静默，不汇报
    MILESTONE = "milestone"  # 里程碑，聚合汇报
    ALERT = "alert"        # 警报，立即汇报


@dataclass
class NotificationEvent:
    """通知事件"""
    level: NotificationLevel
    workflow_id: str
    node_id: Optional[str]
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    tokens_consumed: int = 0


class Debouncer:
    """
    防抖聚合器
    
    10 秒缓冲窗口，合并多条 Milestone 汇报为列表
    """
    
    def __init__(self, window_seconds: float = 10.0):
        self.window = window_seconds
        self._buffer: List[NotificationEvent] = []
        self._lock = asyncio.Lock()
        self._timer: Optional[asyncio.Task] = None
        self._callback: Optional[Callable] = None
    
    def set_callback(self, callback: Callable[[List[NotificationEvent]], None]):
        """设置缓冲满时的回调函数"""
        self._callback = callback
    
    async def add(self, event: NotificationEvent):
        """添加事件到缓冲"""
        async with self._lock:
            self._buffer.append(event)
            
            # 如果是 Alert 级别，立即触发
            if event.level == NotificationLevel.ALERT:
                # Need to release lock before flushing if flush also acquires lock?
                # _flush acquires lock. This is a deadlock.
                # But here we are inside `async with self._lock`.
                # Re-entrant lock? asyncio.Lock is not re-entrant.
                pass

        if event.level == NotificationLevel.ALERT:
             await self._flush()
             return

        async with self._lock:
            # 启动定时器（如果未启动）
            if self._timer is None or self._timer.done():
                self._timer = asyncio.create_task(self._delayed_flush())
    
    async def _delayed_flush(self):
        """延迟触发缓冲"""
        await asyncio.sleep(self.window)
        await self._flush()
    
    async def _flush(self):
        """触发缓冲回调"""
        async with self._lock:
            if not self._buffer:
                return
            
            events = self._buffer.copy()
            self._buffer.clear()
            
            if self._callback:
                try:
                    self._callback(events)
                except Exception as e:
                    print(f"[Notification] 回调执行失败: {e}")
    
    async def force_flush(self):
        """强制清空并发送所有缓冲消息"""
        await self._flush()
        # 取消定时器
        if self._timer and not self._timer.done():
            self._timer.cancel()
            try:
                await self._timer
            except asyncio.CancelledError:
                pass
            self._timer = None


class NotificationManager:
    """
    通知管理器 - 单例
    
    统一处理 Silent / Milestone / Alert 三级汇报
    """
    
    _instance: Optional["NotificationManager"] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.debouncer = Debouncer(window_seconds=10.0)
        self.debouncer.set_callback(self._on_debounced_events)
        
        self._alert_handlers: List[Callable] = []
        self._milestone_handlers: List[Callable] = []
        
        self._initialized = True
    
    def register_alert_handler(self, handler: Callable[[NotificationEvent], None]):
        """注册 Alert 处理器"""
        self._alert_handlers.append(handler)
    
    def register_milestone_handler(self, handler: Callable[[List[NotificationEvent]], None]):
        """注册 Milestone 处理器"""
        self._milestone_handlers.append(handler)
    
    async def notify(self, event: NotificationEvent):
        """
        发送通知
        
        - Silent: 直接返回，不处理
        - Milestone: 加入防抖缓冲
        - Alert: 立即触发
        """
        if event.level == NotificationLevel.SILENT:
            # 静默级别，不汇报
            return
        
        elif event.level == NotificationLevel.MILESTONE:
            # 里程碑级别，加入防抖缓冲
            await self.debouncer.add(event)
        
        elif event.level == NotificationLevel.ALERT:
            # 警报级别，立即触发
            await self.debouncer.add(event)
    
    def _on_debounced_events(self, events: List[NotificationEvent]):
        """防抖缓冲触发回调"""
        if not events:
            return
        
        # 分离 Alert 和 Milestone
        alerts = [e for e in events if e.level == NotificationLevel.ALERT]
        milestones = [e for e in events if e.level == NotificationLevel.MILESTONE]
        
        # 处理 Alerts（立即）
        for alert in alerts:
            self._dispatch_alert(alert)
        
        # 处理 Milestones（聚合）
        if milestones:
            self._dispatch_milestones(milestones)
    
    def _dispatch_alert(self, event: NotificationEvent):
        """分发 Alert"""
        print(f"\n[ALERT] {event.message}")
        print(f"  Workflow: {event.workflow_id}")
        print(f"  Data: {json.dumps(event.data, indent=2)}")
        
        for handler in self._alert_handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"[Notification] Alert handler error: {e}")
    
    def _dispatch_milestones(self, events: List[NotificationEvent]):
        """分发 Milestones（聚合）"""
        total_tokens = sum(e.tokens_consumed for e in events)
        
        print(f"\n[MILESTONE] 完成 {len(events)} 个任务")
        print(f"  总 Token 消耗: {total_tokens}")
        print("  任务列表:")
        for e in events:
            print(f"    - {e.workflow_id}/{e.node_id}: {e.message}")
        
        for handler in self._milestone_handlers:
            try:
                handler(events)
            except Exception as e:
                print(f"[Notification] Milestone handler error: {e}")
    
    async def flush(self):
        """立即刷新缓冲"""
        await self.debouncer.flush_now()


# 便捷函数
def get_notification_manager() -> NotificationManager:
    """获取 NotificationManager 单例"""
    return NotificationManager()


async def notify_silent(workflow_id: str, node_id: str, message: str = ""):
    """静默通知（不汇报）"""
    pass  # Silent 级别什么都不做


async def notify_milestone(
    workflow_id: str,
    node_id: Optional[str],
    message: str,
    data: Dict[str, Any] = None,
    tokens_consumed: int = 0
):
    """里程碑通知（聚合汇报）"""
    nm = get_notification_manager()
    event = NotificationEvent(
        level=NotificationLevel.MILESTONE,
        workflow_id=workflow_id,
        node_id=node_id,
        message=message,
        data=data or {},
        tokens_consumed=tokens_consumed
    )
    await nm.notify(event)


async def notify_alert(
    workflow_id: str,
    node_id: Optional[str],
    message: str,
    data: Dict[str, Any] = None
):
    """警报通知（立即汇报）"""
    nm = get_notification_manager()
    event = NotificationEvent(
        level=NotificationLevel.ALERT,
        workflow_id=workflow_id,
        node_id=node_id,
        message=message,
        data=data or {}
    )
    await nm.notify(event)


if __name__ == "__main__":
    async def test_notification():
        print("=== Notification System Test ===\n")
        
        nm = get_notification_manager()
        
        # 测试 Silent（应该无输出）
        print("1. Silent notification (no output expected)")
        await notify_silent("wf-1", "node-1", "Task completed")
        
        # 等待 10 秒聚合
        print("   Waiting 10s for debounce...")
        await asyncio.sleep(11)
        
        # 测试 Alert（立即）
        print("\n3. Alert notification (immediate)")
        await notify_alert("wf-1", "node-4", "System hibernated due to token limit")
        
        # 等待 Alert 处理
        await asyncio.sleep(1)
        
        print("\n=== Test Complete ===")
    
    asyncio.run(test_notification())
