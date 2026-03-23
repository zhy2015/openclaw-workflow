"""
ResourceManager - 双模资源调度引擎与 Token 管理器

支持两种模式：
- Eco Mode (省流模式): 宁可慢，绝不报错；达到红线，主动休眠
- Burn Mode (燃烧模式): 压榨 API 最大吞吐量，动态探测并发边界

所有 LLM 请求必须通过 ResourceManager 转发，不得直接调用外部 API。
"""

import asyncio
import time
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable, Dict, Any, List
import json
import os


class ResourceMode(Enum):
    ECO = "eco"
    BURN = "burn"


class HibernateException(Exception):
    """当 Token 配额耗尽时触发"""
    pass


@dataclass
class RequestMetrics:
    """单次请求指标"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)
    success: bool = True
    error_type: Optional[str] = None


@dataclass
class ResourceConfig:
    """资源配置（全部可配置）"""
    # RPM 限流配置
    rpm_bucket_capacity: int = 60
    rpm_refill_rate: float = 1.0  # 每秒补充的令牌数
    
    # Token 配额配置
    token_quota_total: int = 100000
    token_warning_threshold: float = 0.95  # 95% 触发警告
    token_hibernate_threshold: float = 1.0  # 100% 触发休眠
    
    # Burn Mode 配置
    burn_initial_concurrency: int = 3
    burn_additive_increase: int = 1
    burn_multiplicative_decrease: float = 0.5
    burn_success_threshold: int = 5  # 连续成功多少次后增加并发
    burn_max_backoff_seconds: float = 32.0
    burn_base_backoff_seconds: float = 2.0
    
    # Eco Mode 配置
    eco_max_wait_seconds: float = 300.0  # 最大等待时间
    
    @classmethod
    def from_file(cls, path: str) -> "ResourceConfig":
        """从配置文件加载"""
        if not os.path.exists(path):
            return cls()
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(**data)
    
    def to_file(self, path: str):
        """保存到配置文件"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.__dict__, f, indent=2)


class RateLimiter(ABC):
    """限流器抽象基类"""
    
    @abstractmethod
    async def acquire(self) -> bool:
        """获取执行许可，返回是否成功"""
        pass
    
    @abstractmethod
    def report_result(self, success: bool, is_rate_limited: bool = False):
        """报告请求结果用于调整策略"""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        pass


class TokenBucket:
    """令牌桶算法实现"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = float(capacity)
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self._lock = threading.Lock()
    
    def _refill(self):
        """补充令牌"""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
    
    def try_consume(self, tokens: int = 1) -> bool:
        """尝试消费令牌"""
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """计算需要等待多久才能获得足够令牌"""
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                return 0.0
            needed = tokens - self.tokens
            return needed / self.refill_rate


class EcoModeLimiter(RateLimiter):
    """省流模式限流器：令牌桶 + 阻塞等待"""
    
    def __init__(self, config: ResourceConfig):
        self.config = config
        self.bucket = TokenBucket(
            capacity=config.rpm_bucket_capacity,
            refill_rate=config.rpm_refill_rate
        )
        self._consecutive_success = 0
    
    async def acquire(self) -> bool:
        """阻塞等待直到获得令牌"""
        start_time = time.time()
        
        while True:
            if self.bucket.try_consume(1):
                return True
            
            # 计算需要等待的时间
            wait_time = self.bucket.get_wait_time(1)
            elapsed = time.time() - start_time
            
            # 检查是否超过最大等待时间
            if elapsed + wait_time > self.config.eco_max_wait_seconds:
                return False
            
            # 等待后重试
            await asyncio.sleep(min(wait_time, 1.0))  # 最多等1秒就重新检查
    
    def report_result(self, success: bool, is_rate_limited: bool = False):
        if success:
            self._consecutive_success += 1
        else:
            self._consecutive_success = 0
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "mode": "eco",
            "bucket_tokens": self.bucket.tokens,
            "bucket_capacity": self.bucket.capacity,
            "consecutive_success": self._consecutive_success
        }


class BurnModeLimiter(RateLimiter):
    """燃烧模式限流器：AIMD 动态并发控制"""
    
    def __init__(self, config: ResourceConfig):
        self.config = config
        self.concurrency_limit = config.burn_initial_concurrency
        self.current_inflight = 0
        self._lock = asyncio.Lock()
        self._consecutive_success = 0
        self._backoff_level = 0  # 当前退避级别
    
    async def acquire(self) -> bool:
        """尝试获取并发槽位"""
        while True:
            async with self._lock:
                if self.current_inflight < self.concurrency_limit:
                    self.current_inflight += 1
                    return True
            
            # 等待有空闲槽位
            await asyncio.sleep(0.1)
    
    def release(self):
        """释放并发槽位"""
        self.current_inflight = max(0, self.current_inflight - 1)
    
    def report_result(self, success: bool, is_rate_limited: bool = False):
        """根据结果调整并发限制"""
        if success and not is_rate_limited:
            self._consecutive_success += 1
            self._backoff_level = 0  # 重置退避
            
            # AIMD: 连续成功达到阈值，加性增加
            if self._consecutive_success >= self.config.burn_success_threshold:
                self.concurrency_limit += self.config.burn_additive_increase
                self._consecutive_success = 0
        else:
            self._consecutive_success = 0
            
            if is_rate_limited:
                # AIMD: 触发限流，乘性减少
                self.concurrency_limit = max(
                    1,
                    int(self.concurrency_limit * self.config.burn_multiplicative_decrease)
                )
                self._backoff_level += 1
    
    def get_backoff_time(self) -> float:
        """获取当前退避时间"""
        if self._backoff_level == 0:
            return 0.0
        return min(
            self.config.burn_base_backoff_seconds * (2 ** (self._backoff_level - 1)),
            self.config.burn_max_backoff_seconds
        )
    
    def get_status(self) -> Dict[str, Any]:
        return {
            "mode": "burn",
            "concurrency_limit": self.concurrency_limit,
            "current_inflight": self.current_inflight,
            "consecutive_success": self._consecutive_success,
            "backoff_level": self._backoff_level,
            "backoff_time": self.get_backoff_time()
        }


class TokenQuotaManager:
    """Token 配额管理器"""
    
    def __init__(self, config: ResourceConfig):
        self.config = config
        self.total_consumed = 0
        self._hibernated = False
        self._lock = threading.Lock()
        self._history: List[RequestMetrics] = []
        self._max_history = 1000
    
    def consume(self, metrics: RequestMetrics) -> bool:
        """
        消费 Token，返回是否允许继续
        如果达到休眠阈值，抛出 HibernateException
        """
        with self._lock:
            if self._hibernated:
                raise HibernateException("系统已休眠，Token 配额耗尽")
            
            self.total_consumed += metrics.total_tokens
            self._history.append(metrics)
            
            # 限制历史记录长度
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]
            
            # 检查是否达到休眠阈值
            usage_ratio = self.total_consumed / self.config.token_quota_total
            
            if usage_ratio >= self.config.token_hibernate_threshold:
                self._hibernated = True
                raise HibernateException(
                    f"Token 配额已耗尽 ({self.total_consumed}/{self.config.token_quota_total})，系统进入休眠状态"
                )
            
            # 检查是否达到警告阈值
            if usage_ratio >= self.config.token_warning_threshold:
                return False  # 返回警告状态，但允许继续
            
            return True
    
    def is_hibernated(self) -> bool:
        """检查是否处于休眠状态"""
        return self._hibernated
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """获取使用统计"""
        with self._lock:
            usage_ratio = self.total_consumed / self.config.token_quota_total
            return {
                "total_consumed": self.total_consumed,
                "quota_total": self.config.token_quota_total,
                "usage_ratio": usage_ratio,
                "remaining": self.config.token_quota_total - self.total_consumed,
                "hibernated": self._hibernated,
                "warning_threshold": self.config.token_warning_threshold,
                "hibernate_threshold": self.config.token_hibernate_threshold,
                "request_count": len(self._history),
                "avg_tokens_per_request": (
                    sum(m.total_tokens for m in self._history) / len(self._history)
                    if self._history else 0
                )
            }
    
    def hibernate(self):
        """手动触发休眠"""
        with self._lock:
            self._hibernated = True
    
    def reset_quota(self, new_quota: Optional[int] = None):
        """重置配额，用于用户恢复"""
        with self._lock:
            self.total_consumed = 0
            self._hibernated = False
            self._history.clear()
            if new_quota is not None:
                self.config.token_quota_total = new_quota


class ResourceManager:
    """
    资源管理器主类 - 单例模式
    所有 LLM 请求必须通过此类转发
    """
    _instance: Optional["ResourceManager"] = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, mode: str = "eco", config_path: Optional[str] = None):
        if self._initialized:
            return
        
        # 加载配置
        if config_path and os.path.exists(config_path):
            self.config = ResourceConfig.from_file(config_path)
        else:
            self.config = ResourceConfig()
        
        self.mode = ResourceMode.ECO if mode == "eco" else ResourceMode.BURN
        
        # 初始化限流器
        if self.mode == ResourceMode.ECO:
            self.limiter: RateLimiter = EcoModeLimiter(self.config)
        else:
            self.limiter = BurnModeLimiter(self.config)
        
        # 初始化 Token 配额管理器
        self.quota_manager = TokenQuotaManager(self.config)
        
        # 请求统计
        self._request_count = 0
        self._success_count = 0
        self._failure_count = 0
        
        self._initialized = True
    
    async def request_llm(
        self,
        prompt: str,
        model_params: Optional[Dict[str, Any]] = None,
        request_fn: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        统一的 LLM 请求接口
        
        Args:
            prompt: 提示词
            model_params: 模型参数
            request_fn: 实际的请求函数，接收 prompt 和 model_params 返回响应
        
        Returns:
            包含结果和指标的字典
        """
        # 检查是否已休眠
        if self.quota_manager.is_hibernated():
            raise HibernateException("系统处于休眠状态，请先重置配额")
        
        # 获取限流许可
        if not await self.limiter.acquire():
            return {
                "success": False,
                "error": "无法获取限流许可",
                "error_type": "rate_limited"
            }
        
        start_time = time.time()
        metrics = RequestMetrics()
        
        try:
            # 执行实际请求
            if request_fn is None:
                # 默认模拟请求，实际使用时应传入真实请求函数
                response = await self._default_request(prompt, model_params)
            else:
                response = await request_fn(prompt, model_params)
            
            # 解析 Token 使用量（从响应头或响应体）
            metrics.prompt_tokens = response.get("prompt_tokens", 0)
            metrics.completion_tokens = response.get("completion_tokens", 0)
            metrics.total_tokens = response.get("total_tokens", metrics.prompt_tokens + metrics.completion_tokens)
            metrics.success = True
            metrics.latency_ms = (time.time() - start_time) * 1000
            
            self._success_count += 1
            
            # 报告成功
            self.limiter.report_result(success=True)
            
            # 消费 Token
            try:
                self.quota_manager.consume(metrics)
            except HibernateException:
                # Token 已耗尽，但请求已成功
                pass
            
            return {
                "success": True,
                "data": response.get("data"),
                "metrics": metrics
            }
            
        except Exception as e:
            metrics.success = False
            metrics.error_type = type(e).__name__
            metrics.latency_ms = (time.time() - start_time) * 1000
            
            self._failure_count += 1
            
            # 检查是否是限流错误
            is_rate_limited = "429" in str(e) or "Too Many Requests" in str(e)
            self.limiter.report_result(success=False, is_rate_limited=is_rate_limited)
            
            # Burn 模式下进行指数退避重试
            if self.mode == ResourceMode.BURN and is_rate_limited:
                backoff_time = self.limiter.get_backoff_time()
                if backoff_time > 0:
                    await asyncio.sleep(backoff_time)
                    # 递归重试
                    return await self.request_llm(prompt, model_params, request_fn)
            
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "metrics": metrics
            }
        finally:
            self._request_count += 1
            
            # Burn 模式下释放并发槽位
            if self.mode == ResourceMode.BURN and isinstance(self.limiter, BurnModeLimiter):
                self.limiter.release()
    
    async def _default_request(self, prompt: str, model_params: Optional[Dict] = None) -> Dict:
        """默认请求实现（示例）"""
        # 这里应该替换为实际的 LLM API 调用
        await asyncio.sleep(0.1)  # 模拟网络延迟
        return {
            "data": f"Response to: {prompt[:50]}...",
            "prompt_tokens": len(prompt) // 4,
            "completion_tokens": 50,
            "total_tokens": len(prompt) // 4 + 50
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            "mode": self.mode.value,
            "limiter_status": self.limiter.get_status(),
            "quota_status": self.quota_manager.get_usage_stats(),
            "request_count": self._request_count,
            "success_count": self._success_count,
            "failure_count": self._failure_count
        }
    
    def save_state(self, wal_path: str):
        """保存状态到 WAL 日志"""
        state = {
            "timestamp": time.time(),
            "mode": self.mode.value,
            "total_consumed": self.quota_manager.total_consumed,
            "hibernated": self.quota_manager.is_hibernated(),
            "request_count": self._request_count,
            "success_count": self._success_count,
            "failure_count": self._failure_count
        }
        
        # 追加写入 WAL 日志
        with open(wal_path, "a") as f:
            f.write(json.dumps(state) + "\n")
    
    def switch_mode(self, mode: str):
        """切换模式（需要重新初始化）"""
        self.mode = ResourceMode.ECO if mode == "eco" else ResourceMode.BURN
        
        if self.mode == ResourceMode.ECO:
            self.limiter = EcoModeLimiter(self.config)
        else:
            self.limiter = BurnModeLimiter(self.config)
    
    def reset(self, new_quota: Optional[int] = None):
        """重置系统状态"""
        self.quota_manager.reset_quota(new_quota)
        self._request_count = 0
        self._success_count = 0
        self._failure_count = 0


# 便捷函数：获取 ResourceManager 实例
def get_resource_manager(mode: str = "eco", config_path: Optional[str] = None) -> ResourceManager:
    """获取 ResourceManager 单例"""
    return ResourceManager(mode, config_path)


if __name__ == "__main__":
    # 使用示例
    
    async def demo_eco_mode():
        print("\n=== Eco Mode Demo ===")
        rm = get_resource_manager(mode="eco")
        
        # 模拟多个请求
        for i in range(5):
            result = await rm.request_llm(f"Prompt {i}")
            print(f"Request {i}: success={result['success']}")
        
        print(f"\nStatus: {json.dumps(rm.get_status(), indent=2)}")
    
    async def demo_burn_mode():
        print("\n=== Burn Mode Demo ===")
        rm = get_resource_manager(mode="burn")
        
        # 并发请求
        tasks = [rm.request_llm(f"Prompt {i}") for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        success_count = sum(1 for r in results if r["success"])
        print(f"Total: {len(results)}, Success: {success_count}")
        print(f"\nStatus: {json.dumps(rm.get_status(), indent=2)}")
    
    async def demo_hibernate():
        print("\n=== Hibernate Demo ===")
        
        # 创建小配额配置
        config = ResourceConfig()
        config.token_quota_total = 1000  # 很小的配额用于演示
        config.to_file("/tmp/test_config.json")
        
        rm = get_resource_manager(mode="eco", config_path="/tmp/test_config.json")
        
        try:
            while True:
                result = await rm.request_llm("Test prompt with some content" * 10)
                if not result["success"]:
                    print(f"Failed: {result.get('error')}")
                    break
                status = rm.get_status()
                print(f"Tokens: {status['quota_status']['total_consumed']}/{status['quota_status']['quota_total']}")
        except HibernateException as e:
            print(f"\nHibernated: {e}")
            print(f"Final Status: {json.dumps(rm.get_status(), indent=2)}")
            
            # 演示重置
            print("\nResetting quota...")
            rm.reset(new_quota=5000)
            print(f"After reset: {json.dumps(rm.get_status(), indent=2)}")
    
    # 运行演示
    asyncio.run(demo_eco_mode())
    asyncio.run(demo_burn_mode())
    asyncio.run(demo_hibernate())
