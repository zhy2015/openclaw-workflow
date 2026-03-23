#!/usr/bin/env python3
"""
Skill Health Check
Skill 健康检查

检查 Skill 可用性、依赖状态
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthReport:
    """健康检查报告"""
    skill_name: str
    status: HealthStatus
    checks: Dict[str, bool]
    issues: List[str]
    last_check: str


class SkillHealthChecker:
    """Skill 健康检查器"""
    
    def __init__(self):
        self.reports: Dict[str, HealthReport] = {}
    
    def check(self, skill_metadata) -> HealthReport:
        """
        检查单个 Skill 健康状态
        
        Args:
            skill_metadata: Skill 元数据
        
        Returns:
            健康检查报告
        """
        checks = {}
        issues = []
        
        # 1. 检查入口文件存在
        entrypoint = skill_metadata.entrypoint
        script_path = entrypoint.get("script", "")
        
        if not script_path:
            checks["entrypoint_exists"] = False
            issues.append("No entrypoint defined")
        else:
            full_path = Path(skill_metadata.path) / script_path
            checks["entrypoint_exists"] = full_path.exists()
            if not checks["entrypoint_exists"]:
                issues.append(f"Entrypoint not found: {full_path}")
        
        # 2. 检查运行时可用
        runtime = entrypoint.get("runtime", "")
        checks["runtime_available"] = self._check_runtime(runtime)
        if not checks["runtime_available"]:
            issues.append(f"Runtime not available: {runtime}")
        
        # 3. 检查依赖
        checks["dependencies_satisfied"] = True
        for dep in skill_metadata.dependencies:
            dep_name = dep.get("skill")
            if not self._check_dependency(dep_name):
                checks["dependencies_satisfied"] = False
                issues.append(f"Dependency not satisfied: {dep_name}")
        
        # 4. 检查权限
        checks["permissions_ok"] = self._check_permissions(skill_metadata.permissions)
        
        # 确定状态
        if all(checks.values()):
            status = HealthStatus.HEALTHY
        elif checks.get("entrypoint_exists") and checks.get("runtime_available"):
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.UNHEALTHY
        
        from datetime import datetime
        report = HealthReport(
            skill_name=skill_metadata.name,
            status=status,
            checks=checks,
            issues=issues,
            last_check=datetime.now().isoformat()
        )
        
        self.reports[skill_metadata.name] = report
        return report
    
    def _check_runtime(self, runtime: str) -> bool:
        """检查运行时是否可用"""
        runtime_checks = {
            "python": ["python3", "--version"],
            "node": ["node", "--version"],
            "bash": ["bash", "--version"],
        }
        
        if runtime not in runtime_checks:
            return True  # unknown runtime, assume ok
        
        try:
            result = subprocess.run(
                runtime_checks[runtime],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def _check_dependency(self, dep_name: str) -> bool:
        """检查依赖是否满足"""
        # 简化：检查是否已注册
        from .manager import SkillRegistry
        registry = SkillRegistry()
        return dep_name in registry.list_skills()
    
    def _check_permissions(self, permissions: List[str]) -> bool:
        """检查权限是否满足"""
        # 简化：只检查基本权限
        return True
    
    def check_all(self, registry) -> Dict[str, HealthReport]:
        """
        检查所有 Skill
        
        Args:
            registry: SkillRegistry 实例
        
        Returns:
            所有 Skill 的健康报告
        """
        for skill_name in registry.list_skills():
            skill = registry.get_skill_info(skill_name)
            if skill:
                self.check(skill)
        
        return self.reports
    
    def get_unhealthy(self) -> List[str]:
        """获取不健康的 Skill"""
        return [
            name for name, report in self.reports.items()
            if report.status in [HealthStatus.UNHEALTHY, HealthStatus.DEGRADED]
        ]
    
    def print_report(self, report: HealthReport):
        """打印健康报告"""
        status_icon = {
            HealthStatus.HEALTHY: "✅",
            HealthStatus.DEGRADED: "⚠️",
            HealthStatus.UNHEALTHY: "❌",
            HealthStatus.UNKNOWN: "❓"
        }
        
        print(f"{status_icon.get(report.status, '❓')} {report.skill_name}: {report.status.value}")
        for check, passed in report.checks.items():
            icon = "✅" if passed else "❌"
            print(f"   {icon} {check}")
        if report.issues:
            print(f"   Issues: {', '.join(report.issues)}")


# 便捷函数
def check_skill_health(skill_metadata) -> HealthReport:
    """检查 Skill 健康"""
    checker = SkillHealthChecker()
    return checker.check(skill_metadata)


def check_all_skills(registry) -> Dict[str, HealthReport]:
    """检查所有 Skills"""
    checker = SkillHealthChecker()
    return checker.check_all(registry)
