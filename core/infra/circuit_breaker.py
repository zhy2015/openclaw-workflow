#!/usr/bin/env python3
"""
CircuitBreaker + 自适应退避重试
L2-L3 防御层：熔断器 + 指数退避
"""

import asyncio
import random
import time
import httpx
from enum import Enum
from typing import Any, Callable, Dict, Optional


class ErrorCategory(Enum):
    """错误分类"""
    RETRYABLE = "retryable"      # 限流、网络超时、临时故障
    NON_RETRYABLE = "non_retryable"  # 认证失败、参数错误、余额不足
    SUCCESS = "success"


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreakerOpen(Exception):
    """熔断器开启异常"""
    pass


class CircuitBreaker:
    """
    熔断器 + 自适应退避
    
    状态机:
    CLOSED -> (失败计数达标) -> OPEN -> (超时) -> HALF_OPEN -> (成功) -> CLOSED
                              -> (失败) -> OPEN
    """
    
    def __init__(self, name: str = "default", max_failures: int = 3, 
                 reset_timeout: float = 60.0, half_open_max_calls: int = 1):
        self.name = name
        self.max_failures = max_failures
        self.reset_timeout = reset_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.half_open_calls = 0
        self.success_count = 0
        
        self._lock = asyncio.Lock()
    
    def classify_error(self, error: Exception) -> ErrorCategory:
        """智能错误分类"""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()
        
        # 限流错误
        if any(kw in error_str for kw in ["rate limit", "429", "too many requests"]):
            return ErrorCategory.RETRYABLE
        
        # 网络/连接错误
        if any(kw in error_str for kw in ["timeout", "connection", "network", "dns", "refused"]):
            return ErrorCategory.RETRYABLE
        
        # 服务器临时错误
        if any(kw in error_str for kw in ["503", "502", "504", "service unavailable", "gateway"]):
            return ErrorCategory.RETRYABLE
        
        # 认证错误（不可重试）
        if any(kw in error_str for kw in ["unauthorized", "401", "forbidden", "403"]):
            return ErrorCategory.NON_RETRYABLE
        
        # 余额/配额错误（不可重试）
        if any(kw in error_str for kw in ["credits", "quota", "billing", "payment", "2007"]):
            return ErrorCategory.NON_RETRYABLE
        
        # 参数错误（不可重试）
        if any(kw in error_str for kw in ["invalid", "bad request", "400", "validation"]):
            return ErrorCategory.NON_RETRYABLE
        
        # 默认可重试
        return ErrorCategory.RETRYABLE
    
    def _calculate_backoff(self, attempt: int, base_delay: float = 2.0, 
                          max_delay: float = 60.0) -> float:
        """指数退避 + 抖动"""
        # 指数退避: base * 2^attempt
        delay = base_delay * (2 ** attempt)
        # 添加随机抖动 (±25%)
        jitter = delay * 0.25 * (2 * random.random() - 1)
        delay += jitter
        # 上限
        return min(delay, max_delay)
    
    async def call(self, func: Callable, *args, 
                   max_retries: int = 3, 
                   base_delay: float = 2.0,
                   **kwargs) -> Any:
        """
        带熔断和退避的调用
        
        Args:
            func: 要执行的异步函数
            max_retries: 最大重试次数
            base_delay: 基础退避时间
        """
        async with self._lock:
            # 检查熔断器状态
            if self.state == "OPEN":
                elapsed = time.time() - self.last_failure_time
                if elapsed < self.reset_timeout:
                    raise Exception(
                        f"[CircuitBreaker:{self.name}] 熔断器已开启 (OPEN)，"
                        f"还需等待 {self.reset_timeout - elapsed:.1f}s"
                    )
                else:
                    # 超时，进入半开状态
                    self.state = "HALF_OPEN"
                    self.half_open_calls = 0
                    print(f"[CircuitBreaker:{self.name}] 超时恢复，状态变更为 HALF_OPEN")
        
        last_error = None
        
        for attempt in range(max_retries + 1):  # +1 for initial attempt
            try:
                # 在半开状态下限制调用次数
                if self.state == "HALF_OPEN":
                    async with self._lock:
                        if self.half_open_calls >= self.half_open_max_calls:
                            raise Exception(
                                f"[CircuitBreaker:{self.name}] HALF_OPEN 状态调用次数超限"
                            )
                        self.half_open_calls += 1
                
                # 执行实际调用
                result = await func(*args, **kwargs)
                
                # 成功处理
                async with self._lock:
                    if self.state == "HALF_OPEN":
                        self.success_count += 1
                        if self.success_count >= self.half_open_max_calls:
                            self.state = "CLOSED"
                            self.failure_count = 0
                            self.success_count = 0
                            print(f"[CircuitBreaker:{self.name}] 半开状态恢复成功，状态变更为 CLOSED")
                    else:
                        self.failure_count = 0
                
                return result
            
            except Exception as e:
                last_error = e
                category = self.classify_error(e)
                
                # 不可重试错误：立即失败
                if category == ErrorCategory.NON_RETRYABLE:
                    async with self._lock:
                        self.failure_count = self.max_failures  # 强制触发熔断
                    print(f"[CircuitBreaker:{self.name}] 遇到不可重试错误: {str(e)[:50]}")
                    raise
                
                # 可重试错误：记录失败并可能触发熔断
                async with self._lock:
                    self.failure_count += 1
                    self.last_failure_time = time.time()
                    
                    if self.state == "HALF_OPEN" or self.failure_count >= self.max_failures:
                        self.state = "OPEN"
                        print(f"[CircuitBreaker:{self.name}] 失败次数达标 ({self.failure_count}/{self.max_failures})，"
                              f"状态变更为 OPEN，熔断 {self.reset_timeout}s")
                        raise
                
                # 计算退避时间
                if attempt < max_retries:
                    backoff = self._calculate_backoff(attempt, base_delay)
                    print(f"[CircuitBreaker:{self.name}] 第 {attempt+1}/{max_retries} 次失败，"
                          f"{e.__class__.__name__}: {str(e)[:30]}... "
                          f"退避 {backoff:.1f}s...")
                    await asyncio.sleep(backoff)
        
        # 重试耗尽
        raise Exception(f"[CircuitBreaker:{self.name}] 重试耗尽 ({max_retries}次)，最后错误: {last_error}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取熔断器状态"""
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "max_failures": self.max_failures,
            "last_failure_time": self.last_failure_time,
            "reset_timeout": self.reset_timeout,
            "time_until_reset": max(0, self.reset_timeout - (time.time() - self.last_failure_time))
            if self.state == "OPEN" else 0
        }


class ResourceManager:
    """
    L1 防御层：信号量 + 令牌桶限流
    
    控制并发数和请求速率
    """
    
    def __init__(self, name: str = "default", max_concurrent: int = 3, 
                 rate_limit_per_minute: int = 20):
        self.name = name
        self.max_concurrent = max_concurrent
        self.rate_limit = rate_limit_per_minute
        
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.tokens = rate_limit_per_minute
        self.last_refill = time.time()
        self.token_lock = asyncio.Lock()
        
        self.total_requests = 0
        self.throttled_requests = 0
    
    async def _acquire_token(self):
        """令牌桶算法获取令牌"""
        async with self.token_lock:
            now = time.time()
            elapsed = now - self.last_refill
            
            # 每分钟补充令牌
            refill_tokens = int(elapsed / 60 * self.rate_limit)
            if refill_tokens > 0:
                self.tokens = min(self.rate_limit, self.tokens + refill_tokens)
                self.last_refill = now
            
            if self.tokens <= 0:
                wait_time = 60 / self.rate_limit
                print(f"[ResourceManager:{self.name}] 速率限制触发，等待 {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
                self.tokens = 1
            
            self.tokens -= 1
            self.total_requests += 1
    
    async def __aenter__(self):
        await self.semaphore.acquire()
        await self._acquire_token()
        return self
    
    async def __aexit__(self, *args):
        self.semaphore.release()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "name": self.name,
            "max_concurrent": self.max_concurrent,
            "rate_limit_per_minute": self.rate_limit,
            "available_tokens": self.tokens,
            "total_requests": self.total_requests,
            "throttled_requests": self.throttled_requests
        }


# 预定义的熔断器配置
CIRCUIT_BREAKER_CONFIG = {
    "kling_api": {
        "max_failures": 3,
        "reset_timeout": 60.0,
        "half_open_max_calls": 1
    },
    "seedream_api": {
        "max_failures": 3,
        "reset_timeout": 60.0,
        "half_open_max_calls": 1
    },
    "tts_api": {
        "max_failures": 5,
        "reset_timeout": 30.0,
        "half_open_max_calls": 2
    }
}

RESOURCE_MANAGER_CONFIG = {
    "video_gen": {
        "max_concurrent": 3,
        "rate_limit_per_minute": 15
    },
    "image_gen": {
        "max_concurrent": 2,
        "rate_limit_per_minute": 10
    }
}


def create_circuit_breaker(name: str) -> CircuitBreaker:
    """创建预配置的熔断器"""
    config = CIRCUIT_BREAKER_CONFIG.get(name, {})
    return CircuitBreaker(name=name, **config)


def create_resource_manager(name: str) -> ResourceManager:
    """创建预配置的资源管理器"""
    config = RESOURCE_MANAGER_CONFIG.get(name, {})
    return ResourceManager(name=name, **config)


class ErrorHandler:
    """
    统一错误处理器
    
    集成 CircuitBreaker 和 ErrorCategory，提供统一的错误处理策略
    """
    
    def __init__(self):
        self.circuit_breaker = create_circuit_breaker("global_handler")
    
    async def handle_error(
        self,
        error: Exception,
        workflow_id: str,
        node_id: str,
        http_code: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        处理错误并返回建议操作
        
        Returns:
            {
                "action": "retry" | "abort" | "fix",
                "delay": float,
                "message": str
            }
        """
        # 1. 优先检查 HTTP 状态码
        if http_code:
            if http_code in [401, 403]:
                return {
                    "action": "abort",
                    "message": f"Authentication failed (HTTP {http_code})"
                }
            if http_code == 429:
                return {
                    "action": "retry",
                    "delay": 5.0,
                    "message": "Rate limit exceeded"
                }
        
        # 2. 使用 CircuitBreaker 分类
        category = self.circuit_breaker.classify_error(error)
        
        if category == ErrorCategory.NON_RETRYABLE:
            return {
                "action": "abort",
                "message": str(error)
            }
        
        # 3. 检查熔断器状态
        if self.circuit_breaker.state == "OPEN":
             return {
                "action": "abort",
                "message": "Circuit breaker is OPEN"
            }
            
        # 4. 默认重试策略
        return {
            "action": "retry",
            "delay": 2.0,
            "message": "Retryable error"
        }

_error_handler = ErrorHandler()

def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器"""
    return _error_handler
