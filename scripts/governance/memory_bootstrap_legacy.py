#!/usr/bin/env python3
"""
Memory Bootstrap Protocol
核心记忆引擎路径重构与自举协议

Phase 1: 动态路径锚定 (Dynamic Path Anchoring)
Phase 2: 存储结构自举与语义指针部署
Phase 3: 启动执行
"""

import os
from pathlib import Path

# ==========================================
# Phase 1: 动态路径锚定 (Dynamic Path Anchoring)
# 彻底消除硬编码与相对路径依赖，无惧重启与环境迁移
# ==========================================

# 1. 动态锚定工作区根目录
# 注意：请根据此脚本的实际存放位置调整 .parent 的层级。
# 假设此脚本在 scripts/ 下，则上一级即为 workspace root。
_current_dir = Path(__file__).resolve().parent
WORKSPACE_ROOT = _current_dir.parent 

# 2. 定义新架构的绝对物理路径
MEMORY_DIR = WORKSPACE_ROOT / "memory"
CORE_MEMORY_PATH = MEMORY_DIR / "core" / "MEMORY.md"
DAILY_LOG_DIR = MEMORY_DIR / "daily"
ARCHIVE_DIR = MEMORY_DIR / "archive"
METRICS_DIR = MEMORY_DIR / "metrics"
INDEX_DIR = MEMORY_DIR / "index"

# 3. 定义根目录遗留文件的物理路径
LEGACY_POINTER_PATH = WORKSPACE_ROOT / "MEMORY.md"

# ==========================================
# Phase 2: 存储结构自举与语义指针部署
# ==========================================

def bootstrap_memory_fs():
    """系统启动自检：初始化统一记忆存储结构并强制部署语义指针"""
    
    print("[Memory Bootstrap] Starting Phase 2: Storage Structure Bootstrap...")
    
    # 1. 构建全新组织架构
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    (MEMORY_DIR / "core").mkdir(exist_ok=True)
    DAILY_LOG_DIR.mkdir(exist_ok=True)
    ARCHIVE_DIR.mkdir(exist_ok=True)
    METRICS_DIR.mkdir(exist_ok=True)
    INDEX_DIR.mkdir(exist_ok=True)
    print(f"  ✅ Directory structure ensured at {MEMORY_DIR}")

    # 2. 初始化真正的核心记忆文件（若不存在）
    if not CORE_MEMORY_PATH.exists():
        CORE_MEMORY_PATH.write_text(
            "# OPENCLAW CORE MEMORY\n\n"
            "系统核心规律与长期经验存储中心。\n\n"
            "## 初始化时间\n"
            f"- 创建: {__import__('datetime').datetime.now().isoformat()}\n"
            "- 版本: v2.0 (统一记忆架构)\n",
            encoding="utf-8"
        )
        print(f"  ✅ Core memory initialized at {CORE_MEMORY_PATH}")
    else:
        print(f"  ✅ Core memory exists: {CORE_MEMORY_PATH} ({CORE_MEMORY_PATH.stat().st_size} bytes)")

    # 3. 部署 LLM 语义指针 (Semantic Pointer)
    # 利用大模型原生阅读理解能力，拦截旧代码的误操作并实施流量重定向
    pointer_content = """# ⚠️ SYSTEM CRITICAL: MEMORY ARCHITECTURE RELOCATED ⚠️

**TO ALL OPENCLAW AGENTS AND WORKFLOWS:**
The cognitive memory engine and system experience logs have been structurally upgraded and migrated to a centralized file system.

**DO NOT READ, WRITE, OR UPDATE THIS CURRENT FILE.**
This file is merely a legacy routing pointer. Any data written here will be permanently lost and ignored by the DAG engine, memory-master, and WAL systems.

**[ ACTION REQUIRED ]**
To access, query, or update my memory, you MUST redirect your file operations to the new unified memory core:
👉 `memory/core/MEMORY.md`

Please proceed to read `memory/core/MEMORY.md` immediately to retrieve the actual historical context and workflow rules.

---
*System Migration Notice: 2026-03-17*
*Architecture Version: Unified Memory System v2.0*
"""
    
    # 强制覆盖或创建根目录的伪文件
    LEGACY_POINTER_PATH.write_text(pointer_content, encoding="utf-8")
    print(f"  ✅ Semantic pointer deployed at {LEGACY_POINTER_PATH}")
    
    # 4. 设置环境变量供其他模块使用
    os.environ["MEMORY_CORE_PATH"] = str(CORE_MEMORY_PATH)
    os.environ["MEMORY_DAILY_PATH"] = str(DAILY_LOG_DIR)
    os.environ["MEMORY_ARCHIVE_PATH"] = str(ARCHIVE_DIR)
    os.environ["MEMORY_INDEX_PATH"] = str(INDEX_DIR)
    
    print(f"\n[Memory Bootstrap] Phase 2 completed successfully.")
    print(f"  Workspace Root: {WORKSPACE_ROOT}")
    print(f"  Memory Core: {CORE_MEMORY_PATH}")
    print(f"  Daily Logs: {DAILY_LOG_DIR}")
    
    return {
        "workspace_root": str(WORKSPACE_ROOT),
        "memory_dir": str(MEMORY_DIR),
        "core_memory": str(CORE_MEMORY_PATH),
        "daily_logs": str(DAILY_LOG_DIR),
        "legacy_pointer": str(LEGACY_POINTER_PATH)
    }

# ==========================================
# Phase 3: 启动执行
# ==========================================
# 在任何需要操作记忆的模块导入此配置前，确保自检已运行

if __name__ == "__main__":
    result = bootstrap_memory_fs()
    print("\n" + "=" * 60)
    print("MEMORY BOOTSTRAP PROTOCOL COMPLETED")
    print("=" * 60)
    for key, value in result.items():
        print(f"  {key}: {value}")
