#!/usr/bin/env python3
"""
Echo Skill - 冒烟测试用极简技能
"""

import time
import json


def execute(action: str = "print_hello", prev_output: str = None, **kwargs) -> dict:
    """
    执行 Echo 操作
    
    Args:
        action: "print_hello" 或 "print_world"
        prev_output: 上一个节点的输出
    
    Returns:
        执行结果
    """
    if action == "print_hello":
        message = "Hello"
        print(f"[Echo Skill] Node A: {message}")
        time.sleep(0.5)  # 模拟执行时间
        return {
            "message": message,
            "status": "success",
            "node": "A"
        }
    
    elif action == "print_world":
        message = f"{prev_output} World" if prev_output else "World"
        print(f"[Echo Skill] Node B: {message}")
        time.sleep(0.5)  # 模拟执行时间
        return {
            "message": message,
            "status": "success", 
            "node": "B"
        }
    
    elif action == "force_fail":
        raise RuntimeError(f"Forced failure after: {prev_output}" if prev_output else "Forced failure")

    else:
        return {
            "message": "Unknown action",
            "status": "failed"
        }


if __name__ == "__main__":
    # 测试
    print("=== Echo Skill Test ===")
    result_a = execute(action="print_hello")
    print(f"Result A: {result_a}")
    
    result_b = execute(action="print_world", prev_output=result_a["message"])
    print(f"Result B: {result_b}")
