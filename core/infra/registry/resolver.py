#!/usr/bin/env python3
"""
Skill URI Resolver
URI 解析器

将各种格式的 Skill 调用转换为标准格式
"""

import re
from typing import Tuple, Optional
from urllib.parse import urlparse


class SkillResolver:
    """Skill URI 解析器"""
    
    # 支持的 URI 模式
    PATTERNS = {
        # skill://skill-name/function
        'full': re.compile(r'^skill://(?P<skill>[a-z][a-z0-9-]*)(?:/(?P<function>[a-z][a-z0-9_]*))?$'),
        # skill-name/function
        'short': re.compile(r'^(?P<skill>[a-z][a-z0-9-]*)(?:/(?P<function>[a-z][a-z0-9_]*))?$'),
        # @skill-name/function (快捷语法)
        'at': re.compile(r'^@(?P<skill>[a-z][a-z0-9-]*)(?:/(?P<function>[a-z][a-z0-9_]*))?$'),
    }
    
    @classmethod
    def resolve(cls, uri: str) -> Tuple[str, str]:
        """
        解析 Skill URI
        
        Args:
            uri: 各种格式的 URI
        
        Returns:
            (skill_name, function_name)
        
        Raises:
            ValueError: URI 格式无效
        """
        uri = uri.strip()
        
        for pattern_name, pattern in cls.PATTERNS.items():
            match = pattern.match(uri)
            if match:
                skill = match.group('skill')
                function = match.group('function') or 'main'
                return skill, function
        
        raise ValueError(f"Invalid skill URI: {uri}. Expected format: skill://skill-name/function or skill-name/function")
    
    @classmethod
    def normalize(cls, uri: str) -> str:
        """
        标准化 URI
        
        Args:
            uri: 各种格式的 URI
        
        Returns:
            标准格式: skill://skill-name/function
        """
        skill, function = cls.resolve(uri)
        return f"skill://{skill}/{function}"
    
    @classmethod
    def is_valid(cls, uri: str) -> bool:
        """检查 URI 是否有效"""
        try:
            cls.resolve(uri)
            return True
        except ValueError:
            return False


# 便捷函数
def resolve_skill_uri(uri: str) -> Tuple[str, str]:
    """解析 Skill URI"""
    return SkillResolver.resolve(uri)


def normalize_skill_uri(uri: str) -> str:
    """标准化 Skill URI"""
    return SkillResolver.normalize(uri)
