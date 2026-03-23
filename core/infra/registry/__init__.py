"""
Registry Facade - 单一入口暴露层

此模块为零逻辑暴露层，所有业务逻辑内聚于 manager.py。
新控制面抽象见 `core.infra.skill_manager` / `core.infra.skill_contracts`。
"""

# 核心接口（legacy manifest 路径）
from .manager import RegistryManager, LegacyManifestRegistry, get_registry

# 兼容旧接口 (Wrapper映射)
from .manager import (
    RegistryManager as SkillRegistry,  # 旧名兼容
    SkillNotFoundError,
    SkillLoadError,
)

__all__ = [
    'RegistryManager',    # 旧 manifest/URI 路径兼容
    'LegacyManifestRegistry',
    'get_registry',
    'SkillRegistry',
    'SkillNotFoundError',
    'SkillLoadError',
]
