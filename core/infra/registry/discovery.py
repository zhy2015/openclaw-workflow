#!/usr/bin/env python3
"""
Skill Discovery
自动发现 Skills

自动扫描 skills/ 目录，发现并注册新 Skill
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional
import yaml

SKILLS_ROOT = Path(__file__).parent.parent.parent.parent / "skills"


class SkillDiscovery:
    """Skill 自动发现器"""
    
    def __init__(self):
        self.discovered = []
    
    def scan(self) -> List[Dict]:
        """
        扫描 skills/ 目录发现 Skill
        
        Returns:
            发现的 Skill 列表
        """
        skills = []
        
        if not SKILLS_ROOT.exists():
            return skills
        
        for skill_dir in SKILLS_ROOT.iterdir():
            if not skill_dir.is_dir():
                continue
            
            # 检查是否有 SKILL.md 或 manifest
            skill_info = self._parse_skill(skill_dir)
            if skill_info:
                skills.append(skill_info)
        
        return skills
    
    def _parse_skill(self, skill_dir: Path) -> Optional[Dict]:
        """解析单个 Skill 目录"""
        skill_name = skill_dir.name
        
        # 1. 检查 SKILL.md
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            return self._parse_skill_md(skill_md, skill_dir)
        
        # 2. 检查 manifest.yaml/json
        manifest_yaml = skill_dir / "manifest.yaml"
        manifest_json = skill_dir / "manifest.json"
        
        if manifest_yaml.exists():
            return self._parse_manifest(manifest_yaml, skill_dir)
        elif manifest_json.exists():
            return self._parse_manifest(manifest_json, skill_dir)
        
        return None
    
    def _parse_skill_md(self, skill_md: Path, skill_dir: Path) -> Dict:
        """从 SKILL.md 解析元数据"""
        content = skill_md.read_text(encoding="utf-8")
        
        # 提取标题
        name = skill_dir.name
        description = ""
        version = "1.0.0"
        
        lines = content.split("\n")
        for line in lines[:20]:  # 只看前20行
            if line.startswith("# "):
                description = line[2:].strip()
            elif "version" in line.lower():
                # 尝试提取版本
                import re
                match = re.search(r'version[:\s]+([\d.]+)', line, re.I)
                if match:
                    version = match.group(1)
        
        # 查找入口脚本
        entrypoint = self._find_entrypoint(skill_dir)
        
        return {
            "name": name,
            "version": version,
            "description": description,
            "entrypoint": entrypoint,
            "path": str(skill_dir.relative_to(SKILLS_ROOT)),
            "source": "SKILL.md"
        }
    
    def _parse_manifest(self, manifest_path: Path, skill_dir: Path) -> Dict:
        """从 manifest 解析元数据"""
        content = manifest_path.read_text(encoding="utf-8")
        
        if manifest_path.suffix == ".yaml":
            data = yaml.safe_load(content)
        else:
            data = json.loads(content)
        
        return {
            "name": data.get("name", skill_dir.name),
            "version": data.get("version", "1.0.0"),
            "description": data.get("description", ""),
            "entrypoint": data.get("entrypoint", self._find_entrypoint(skill_dir)),
            "path": str(skill_dir.relative_to(SKILLS_ROOT)),
            "source": "manifest"
        }
    
    def _find_entrypoint(self, skill_dir: Path) -> Dict:
        """查找入口脚本"""
        # 常见入口
        candidates = [
            "main.py", "index.py", "run.py",
            "main.js", "index.js",
            "main.sh", "run.sh",
            "SKILL.md"
        ]
        
        for candidate in candidates:
            entry = skill_dir / candidate
            if entry.exists():
                if candidate.endswith(".py"):
                    return {"script": candidate, "runtime": "python"}
                elif candidate.endswith(".js"):
                    return {"script": candidate, "runtime": "node"}
                elif candidate.endswith(".sh"):
                    return {"script": candidate, "runtime": "bash"}
                elif candidate == "SKILL.md":
                    return {"script": candidate, "runtime": "markdown"}
        
        return {"script": "", "runtime": "unknown"}
    
    def auto_register(self, registry) -> int:
        """
        自动注册发现的 Skills
        
        Args:
            registry: SkillRegistry 实例
        
        Returns:
            注册数量
        """
        from .manager import SkillMetadata
        
        skills = self.scan()
        registered = 0
        
        for skill_info in skills:
            # 检查是否已存在
            existing = registry.get_skill_info(skill_info["name"])
            if existing:
                continue
            
            # 创建元数据
            metadata = SkillMetadata(
                name=skill_info["name"],
                version=skill_info["version"],
                description=skill_info["description"],
                entrypoint=skill_info["entrypoint"],
                path=skill_info["path"]
            )
            
            if registry.register(metadata):
                registered += 1
        
        return registered


# 便捷函数
def discover_skills() -> List[Dict]:
    """发现所有 Skills"""
    discovery = SkillDiscovery()
    return discovery.scan()


def auto_register_skills(registry) -> int:
    """自动注册 Skills"""
    discovery = SkillDiscovery()
    return discovery.auto_register(registry)
