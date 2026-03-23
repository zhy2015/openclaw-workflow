"""
系统主入口 - 全局初始化与 ResourceManager 接管

使用方式:
    from core.bootstrap import initialize_system, get_rm
    
    # 初始化系统
    await initialize_system(mode="eco", config_path="core/resource_config.json")
    
    # 获取 ResourceManager 实例
    rm = get_rm()
    result = await rm.request_llm("prompt")
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from core.infra.resource_manager import ResourceManager, ResourceConfig, ResourceMode, get_resource_manager
except ImportError:
    from core.infra.resource_manager import ResourceManager, ResourceConfig, ResourceMode, get_resource_manager


# 全局 ResourceManager 实例
_resource_manager: Optional[ResourceManager] = None


async def initialize_system(
    mode: str = "eco",
    config_path: Optional[str] = None,
    custom_config: Optional[dict] = None
) -> ResourceManager:
    """
    初始化系统，加载配置并创建 ResourceManager 单例
    
    Args:
        mode: "eco" 或 "burn"
        config_path: 配置文件路径，默认使用 core/resource_config.json
        custom_config: 可选的自定义配置字典，会覆盖配置文件
    
    Returns:
        ResourceManager 实例
    """
    global _resource_manager
    
    # 默认配置文件路径
    if config_path is None:
        config_path = str(PROJECT_ROOT / "core" / "resource_config.json")
    
    print(f"[Bootstrap] 正在初始化系统...")
    print(f"[Bootstrap] 模式: {mode}")
    print(f"[Bootstrap] 配置文件: {config_path}")
    
    # 加载配置
    if os.path.exists(config_path):
        config = ResourceConfig.from_file(config_path)
        print(f"[Bootstrap] 已加载配置文件")
    else:
        config = ResourceConfig()
        print(f"[Bootstrap] 配置文件不存在，使用默认配置")
    
    # 应用自定义配置
    if custom_config:
        for key, value in custom_config.items():
            if hasattr(config, key):
                setattr(config, key, value)
                print(f"[Bootstrap] 自定义配置: {key} = {value}")
    
    # 创建临时配置文件（用于自定义配置）
    if custom_config:
        temp_config_path = str(PROJECT_ROOT / "core" / "runtime_config.json")
        config.to_file(temp_config_path)
        config_path = temp_config_path
    
    # 初始化 ResourceManager 单例
    _resource_manager = get_resource_manager(mode=mode, config_path=config_path)
    
    print(f"[Bootstrap] ResourceManager 初始化完成")
    print(f"[Bootstrap] Token 配额: {config.token_quota_total}")
    print(f"[Bootstrap] RPM 限制: {config.rpm_bucket_capacity}")
    print(f"[Bootstrap] 系统就绪！\n")
    
    return _resource_manager


def get_rm() -> ResourceManager:
    """获取 ResourceManager 单例（快捷方式）"""
    if _resource_manager is None:
        raise RuntimeError("系统未初始化，请先调用 initialize_system()")
    return _resource_manager


def check_system_status() -> dict:
    """检查系统状态"""
    if _resource_manager is None:
        return {"initialized": False, "error": "系统未初始化"}
    
    return {
        "initialized": True,
        "status": _resource_manager.get_status()
    }


# 便捷函数：快速初始化并运行
async def quick_init(mode: str = "eco", **config_overrides) -> ResourceManager:
    """快速初始化系统，支持配置覆盖"""
    return await initialize_system(mode=mode, custom_config=config_overrides)


if __name__ == "__main__":
    # 测试初始化
    async def test_bootstrap():
        print("=== Bootstrap Test ===\n")
        
        # 使用默认配置初始化
        rm = await initialize_system(mode="eco")
        
        # 检查状态
        status = check_system_status()
        print(f"\n系统状态: {status}")
        
        # 测试请求
        result = await rm.request_llm("Hello, World!")
        print(f"\n测试结果: {result['success']}")
    
    asyncio.run(test_bootstrap())
