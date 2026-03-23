#!/usr/bin/env python3
"""
Skill Version Manager
版本管理

支持版本比较、升级、回滚
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class VersionInfo:
    """版本信息"""
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    
    @classmethod
    def parse(cls, version_str: str) -> "VersionInfo":
        """解析版本字符串"""
        # 处理 prerelease
        if "-" in version_str:
            version_part, prerelease = version_str.split("-", 1)
        else:
            version_part = version_str
            prerelease = None
        
        parts = version_part.split(".")
        if len(parts) < 3:
            parts.extend(["0"] * (3 - len(parts)))
        
        return cls(
            major=int(parts[0]),
            minor=int(parts[1]),
            patch=int(parts[2]),
            prerelease=prerelease
        )
    
    def __str__(self) -> str:
        v = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            v += f"-{self.prerelease}"
        return v
    
    def __lt__(self, other: "VersionInfo") -> bool:
        if (self.major, self.minor, self.patch) != (other.major, other.minor, other.patch):
            return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
        # prerelease 版本小于正式版本
        if self.prerelease and not other.prerelease:
            return True
        if not self.prerelease and other.prerelease:
            return False
        if self.prerelease and other.prerelease:
            return self.prerelease < other.prerelease
        return False
    
    def __le__(self, other: "VersionInfo") -> bool:
        return self == other or self < other
    
    def __gt__(self, other: "VersionInfo") -> bool:
        return not self <= other
    
    def __ge__(self, other: "VersionInfo") -> bool:
        return not self < other
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VersionInfo):
            return False
        return (self.major, self.minor, self.patch, self.prerelease) == \
               (other.major, other.minor, other.patch, other.prerelease)


class VersionManager:
    """版本管理器"""
    
    def __init__(self, registry):
        self.registry = registry
        self.versions_dir = Path(__file__).parent / ".versions"
        self.versions_dir.mkdir(exist_ok=True)
    
    def compare(self, v1: str, v2: str) -> int:
        """
        比较两个版本
        
        Returns:
            -1: v1 < v2
             0: v1 = v2
             1: v1 > v2
        """
        ver1 = VersionInfo.parse(v1)
        ver2 = VersionInfo.parse(v2)
        
        if ver1 < ver2:
            return -1
        elif ver1 > ver2:
            return 1
        return 0
    
    def satisfies(self, version: str, version_range: str) -> bool:
        """
        检查版本是否满足范围
        
        支持格式:
        - ^1.2.0 (兼容 1.x.x)
        - ~1.2.0 (兼容 1.2.x)
        - >=1.2.0
        - 1.2.0 - 2.0.0
        """
        ver = VersionInfo.parse(version)
        
        if version_range.startswith("^"):
            # 兼容版本
            base = VersionInfo.parse(version_range[1:])
            return base.major == ver.major and ver >= base
        
        elif version_range.startswith("~"):
            # 近似版本
            base = VersionInfo.parse(version_range[1:])
            return (base.major, base.minor) == (ver.major, ver.minor) and ver >= base
        
        elif version_range.startswith(">="):
            min_ver = VersionInfo.parse(version_range[2:])
            return ver >= min_ver
        
        elif " - " in version_range:
            # 范围
            min_str, max_str = version_range.split(" - ")
            min_ver = VersionInfo.parse(min_str)
            max_ver = VersionInfo.parse(max_str)
            return min_ver <= ver <= max_ver
        
        else:
            # 精确版本
            return ver == VersionInfo.parse(version_range)
    
    def get_latest(self, skill_name: str) -> Optional[str]:
        """获取 Skill 最新版本"""
        skill = self.registry.get_skill_info(skill_name)
        return skill.version if skill else None
    
    def can_upgrade(self, skill_name: str, target_version: str) -> bool:
        """检查是否可以升级"""
        current = self.get_latest(skill_name)
        if not current:
            return False
        return VersionInfo.parse(target_version) > VersionInfo.parse(current)
    
    def backup_version(self, skill_name: str) -> bool:
        """备份当前版本"""
        skill = self.registry.get_skill_info(skill_name)
        if not skill:
            return False
        
        backup_file = self.versions_dir / f"{skill_name}_{skill.version}.json"
        with open(backup_file, "w") as f:
            json.dump({
                "name": skill.name,
                "version": skill.version,
                "entrypoint": skill.entrypoint,
                "path": skill.path
            }, f, indent=2)
        
        return True
    
    def rollback(self, skill_name: str, version: str) -> bool:
        """回滚到指定版本"""
        backup_file = self.versions_dir / f"{skill_name}_{version}.json"
        if not backup_file.exists():
            return False
        
        with open(backup_file) as f:
            data = json.load(f)
        
        # 恢复版本
        from .manager import SkillMetadata
        skill = self.registry.get_skill_info(skill_name)
        if skill:
            skill.version = data["version"]
            skill.entrypoint = data["entrypoint"]
            self.registry._save_index()
        
        return True


# 便捷函数
def compare_versions(v1: str, v2: str) -> int:
    """比较版本"""
    vm = VersionManager(None)
    return vm.compare(v1, v2)


def check_version_satisfies(version: str, version_range: str) -> bool:
    """检查版本是否满足范围"""
    vm = VersionManager(None)
    return vm.satisfies(version, version_range)
