#!/usr/bin/env python3
"""
Task Verifier - 原子任务产物验证器

每个任务类型有对应的验证逻辑，确保 WAL 状态与真实产物一致。
"""

import os
import json
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class VerificationResult(Enum):
    VALID = "valid"           # 产物存在且有效
    INVALID = "invalid"       # 产物存在但无效（如损坏）
    MISSING = "missing"       # 产物不存在
    UNKNOWN = "unknown"       # 无法验证


@dataclass
class VerificationReport:
    result: VerificationResult
    details: Dict[str, Any]
    suggestion: str  # 建议操作: retry | skip | manual_check


class TaskVerifier:
    """任务产物验证器"""
    
    def __init__(self):
        self._verifiers: Dict[str, Callable] = {
            "file_write": self._verify_file_write,
            "video_gen": self._verify_video_gen,
            "api_call": self._verify_api_call,
            "git_clone": self._verify_git_clone,
            "git_pull": self._verify_git_pull,
            "shell": self._verify_shell,
            "code_gen": self._verify_code_gen,
            "install_deps": self._verify_install_deps,
            "build": self._verify_build,
        }
    
    def verify(self, task_type: str, outputs: Dict[str, Any]) -> VerificationReport:
        """验证任务产物"""
        verifier = self._verifiers.get(task_type)
        if not verifier:
            return VerificationReport(
                result=VerificationResult.UNKNOWN,
                details={"reason": f"No verifier for type: {task_type}"},
                suggestion="manual_check"
            )
        return verifier(outputs)
    
    def _verify_file_write(self, outputs: Dict[str, Any]) -> VerificationReport:
        """验证文件写入任务"""
        file_path = outputs.get("file_path") or outputs.get("path")
        expected_size = outputs.get("size", 0)
        
        if not file_path:
            return VerificationReport(
                result=VerificationResult.MISSING,
                details={"error": "No file_path in outputs"},
                suggestion="retry"
            )
        
        if not os.path.exists(file_path):
            return VerificationReport(
                result=VerificationResult.MISSING,
                details={"file_path": file_path},
                suggestion="retry"
            )
        
        actual_size = os.path.getsize(file_path)
        if expected_size > 0 and actual_size != expected_size:
            return VerificationReport(
                result=VerificationResult.INVALID,
                details={"file_path": file_path, "expected_size": expected_size, "actual_size": actual_size},
                suggestion="retry"
            )
        
        if actual_size == 0:
            return VerificationReport(
                result=VerificationResult.INVALID,
                details={"file_path": file_path, "reason": "Empty file"},
                suggestion="retry"
            )
        
        return VerificationReport(
            result=VerificationResult.VALID,
            details={"file_path": file_path, "size": actual_size},
            suggestion="skip"  # 已验证成功，可跳过
        )
    
    def _verify_video_gen(self, outputs: Dict[str, Any]) -> VerificationReport:
        """验证视频生成任务"""
        video_path = outputs.get("video_path") or outputs.get("file_path")
        expected_duration = outputs.get("duration", 0)
        
        if not video_path or not os.path.exists(video_path):
            # 检查是否有渲染中的标记文件
            flag_file = outputs.get("flag_file")
            if flag_file and os.path.exists(flag_file):
                return VerificationReport(
                    result=VerificationResult.UNKNOWN,
                    details={"status": "rendering", "flag_file": flag_file},
                    suggestion="wait"  # 仍在渲染中，继续等待
                )
            return VerificationReport(
                result=VerificationResult.MISSING,
                details={"video_path": video_path},
                suggestion="retry"
            )
        
        # 检查文件大小（视频至少要有一定大小）
        size = os.path.getsize(video_path)
        if size < 1000:  # 小于 1KB 可能是损坏
            return VerificationReport(
                result=VerificationResult.INVALID,
                details={"video_path": video_path, "size": size, "reason": "File too small"},
                suggestion="retry"
            )
        
        # TODO: 可以用 ffprobe 检查视频时长和完整性
        
        return VerificationReport(
            result=VerificationResult.VALID,
            details={"video_path": video_path, "size": size},
            suggestion="skip"
        )
    
    def _verify_api_call(self, outputs: Dict[str, Any]) -> VerificationReport:
        """验证 API 调用任务"""
        status_code = outputs.get("status_code")
        response_data = outputs.get("response")
        
        if status_code is None:
            return VerificationReport(
                result=VerificationResult.UNKNOWN,
                details={"error": "No status_code in outputs"},
                suggestion="retry"
            )
        
        if status_code >= 200 and status_code < 300:
            return VerificationReport(
                result=VerificationResult.VALID,
                details={"status_code": status_code},
                suggestion="skip"
            )
        
        if status_code >= 500:  # 服务端错误，可重试
            return VerificationReport(
                result=VerificationResult.INVALID,
                details={"status_code": status_code, "response": response_data},
                suggestion="retry"
            )
        
        # 4xx 客户端错误，可能需要人工检查
        return VerificationReport(
            result=VerificationResult.INVALID,
            details={"status_code": status_code, "response": response_data},
            suggestion="manual_check"
        )
    
    def _verify_git_clone(self, outputs: Dict[str, Any]) -> VerificationReport:
        """验证 Git 克隆任务"""
        cloned_to = outputs.get("cloned_to")
        
        if not cloned_to or not os.path.exists(cloned_to):
            return VerificationReport(
                result=VerificationResult.MISSING,
                details={"cloned_to": cloned_to},
                suggestion="retry"
            )
        
        git_dir = os.path.join(cloned_to, ".git")
        if not os.path.exists(git_dir):
            return VerificationReport(
                result=VerificationResult.INVALID,
                details={"cloned_to": cloned_to, "reason": "No .git directory"},
                suggestion="retry"
            )
        
        return VerificationReport(
            result=VerificationResult.VALID,
            details={"cloned_to": cloned_to},
            suggestion="skip"
        )
    
    def _verify_git_pull(self, outputs: Dict[str, Any]) -> VerificationReport:
        """验证 Git 拉取任务"""
        # 拉取成功通常有输出信息
        output = outputs.get("output", "")
        
        if "Already up to date" in output or "Updating" in output or "Fast-forward" in output:
            return VerificationReport(
                result=VerificationResult.VALID,
                details={"output": output[:100]},
                suggestion="skip"
            )
        
        if "error" in output.lower() or "fatal" in output.lower():
            return VerificationReport(
                result=VerificationResult.INVALID,
                details={"output": output},
                suggestion="manual_check"
            )
        
        return VerificationReport(
            result=VerificationResult.UNKNOWN,
            details={"output": output},
            suggestion="retry"
        )
    
    def _verify_shell(self, outputs: Dict[str, Any]) -> VerificationReport:
        """验证 Shell 命令任务"""
        # Shell 命令通常通过返回码判断，但这里只看产物
        stdout = outputs.get("stdout", "")
        stderr = outputs.get("stderr", "")
        
        # 如果有明确的错误输出，标记为失败
        if stderr and "error" in stderr.lower():
            return VerificationReport(
                result=VerificationResult.INVALID,
                details={"stderr": stderr[:200]},
                suggestion="manual_check"
            )
        
        # 默认认为成功（因为 WAL 已经记录了成功状态）
        return VerificationReport(
            result=VerificationResult.VALID,
            details={"stdout_length": len(stdout)},
            suggestion="skip"
        )
    
    def _verify_code_gen(self, outputs: Dict[str, Any]) -> VerificationReport:
        """验证代码生成任务"""
        file_path = outputs.get("file_path")
        
        if not file_path or not os.path.exists(file_path):
            return VerificationReport(
                result=VerificationResult.MISSING,
                details={"file_path": file_path},
                suggestion="retry"
            )
        
        # 检查文件是否有内容
        with open(file_path, 'r') as f:
            content = f.read()
        
        if len(content) < 10:  # 代码太短可能有问题
            return VerificationReport(
                result=VerificationResult.INVALID,
                details={"file_path": file_path, "content_length": len(content)},
                suggestion="retry"
            )
        
        return VerificationReport(
            result=VerificationResult.VALID,
            details={"file_path": file_path, "lines": len(content.splitlines())},
            suggestion="skip"
        )
    
    def _verify_install_deps(self, outputs: Dict[str, Any]) -> VerificationReport:
        """验证依赖安装任务"""
        # 检查 node_modules 或类似目录是否存在
        node_modules = outputs.get("node_modules_path")
        if node_modules and os.path.exists(node_modules):
            return VerificationReport(
                result=VerificationResult.VALID,
                details={"node_modules": node_modules},
                suggestion="skip"
            )
        
        # 或者检查 lock 文件
        lock_file = outputs.get("lock_file")
        if lock_file and os.path.exists(lock_file):
            return VerificationReport(
                result=VerificationResult.VALID,
                details={"lock_file": lock_file},
                suggestion="skip"
            )
        
        return VerificationReport(
            result=VerificationResult.UNKNOWN,
            details={"outputs": outputs},
            suggestion="retry"
        )
    
    def _verify_build(self, outputs: Dict[str, Any]) -> VerificationReport:
        """验证构建任务"""
        dist_path = outputs.get("dist_path") or outputs.get("output_path")
        
        if not dist_path or not os.path.exists(dist_path):
            return VerificationReport(
                result=VerificationResult.MISSING,
                details={"dist_path": dist_path},
                suggestion="retry"
            )
        
        # 检查是否有产物文件
        files = os.listdir(dist_path) if os.path.isdir(dist_path) else [dist_path]
        if not files:
            return VerificationReport(
                result=VerificationResult.INVALID,
                details={"dist_path": dist_path, "reason": "Empty output"},
                suggestion="retry"
            )
        
        return VerificationReport(
            result=VerificationResult.VALID,
            details={"dist_path": dist_path, "files": len(files)},
            suggestion="skip"
        )


# 全局验证器实例
verifier = TaskVerifier()


def verify_task(task_type: str, outputs: Dict[str, Any]) -> VerificationReport:
    """便捷函数：验证任务产物"""
    return verifier.verify(task_type, outputs)