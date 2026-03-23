#!/bin/bash
# OpenClaw Memory System Initialization Script
# 在 OpenClaw 启动时执行，确保记忆系统正确加载

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🧠 Initializing Memory System..."

# 加载配置
MEMORY_CONF="/root/.config/openclaw/memory.conf"
if [ -f "$MEMORY_CONF" ]; then
    source "$MEMORY_CONF"
    echo "  Config loaded from $MEMORY_CONF"
else
    echo "  ⚠️  Memory config not found, using defaults"
fi

# 确保目录结构存在
mkdir -p "$MEMORY_DAILY_PATH"
mkdir -p "$MEMORY_ARCHIVE_PATH"
mkdir -p "$MEMORY_INDEX_PATH"

# 检查核心记忆文件
if [ -f "$MEMORY_CORE_PATH" ]; then
    echo "  ✅ Core memory found: $MEMORY_CORE_PATH"
    echo "     Size: $(wc -c < "$MEMORY_CORE_PATH") bytes"
else
    echo "  ⚠️  Core memory not found at $MEMORY_CORE_PATH"
fi

# 检查 FTS5 索引
if [ -f "$MEMORY_FTS5_DB" ]; then
    echo "  ✅ FTS5 index found: $MEMORY_FTS5_DB"
else
    echo "  🔄 Building FTS5 index..."
    python3 "$MEMORY_QUERY_ENGINE" --index-only 2>/dev/null || echo "     (Will be built on first query)"
fi

# 运行 memory-master 整理（如果有过期日志）
echo "  🔄 Running memory master maintenance..."
python3 "$MEMORY_MASTER_DAEMON" 2>/dev/null || echo "     (Skipped)"

# 创建环境变量导出（供 Python 使用）
cat > /tmp/memory_env.sh << EOF
export MEMORY_CORE_PATH="${MEMORY_CORE_PATH}"
export MEMORY_DAILY_PATH="${MEMORY_DAILY_PATH}"
export MEMORY_INDEX_PATH="${MEMORY_INDEX_PATH}"
export MEMORY_ARCHIVE_PATH="${MEMORY_ARCHIVE_PATH}"
export MEMORY_FTS5_DB="${MEMORY_FTS5_DB}"
export MEMORY_QUERY_ENGINE="${MEMORY_QUERY_ENGINE}"
export MEMORY_MASTER_DAEMON="${MEMORY_MASTER_DAEMON}"
EOF

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Memory System initialized"
echo ""
echo "Memory locations:"
echo "  Core:    $MEMORY_CORE_PATH"
echo "  Daily:   $MEMORY_DAILY_PATH"
echo "  Archive: $MEMORY_ARCHIVE_PATH"
echo "  Index:   $MEMORY_INDEX_PATH"
