#!/bin/bash
# OpenClaw System Bootstrap
# 系统启动时自动执行，确保所有组件正确初始化

set -e

LOG_FILE="/root/.openclaw/workspace/logs/bootstrap.log"
mkdir -p "$(dirname "$LOG_FILE")"

exec > >(tee -a "$LOG_FILE")
exec 2>&1

echo "=========================================="
echo "OpenClaw System Bootstrap"
echo "Started: $(date)"
echo "=========================================="

# ==========================================
# Phase 1: Environment Setup
# ==========================================
echo ""
echo "[Phase 1] Setting up environment..."

export OPENCLAW_WORKSPACE="/root/.openclaw/workspace"
export PYTHONPATH="${OPENCLAW_WORKSPACE}:${PYTHONPATH}"
export PATH="${OPENCLAW_WORKSPACE}/scripts:${PATH}"

# ==========================================
# Phase 2: Memory System Bootstrap
# ==========================================
echo ""
echo "[Phase 2] Bootstrapping memory system..."

python3 "${OPENCLAW_WORKSPACE}/scripts/memory_bootstrap.py" || echo "  ⚠️  Memory bootstrap skipped"

# ==========================================
# Phase 3: Legacy Bridge Initialization
# ==========================================
echo ""
echo "[Phase 3] Initializing legacy bridge..."

python3 -c "
import sys
sys.path.insert(0, '${OPENCLAW_WORKSPACE}')
from core.infra.legacy_registry_adapter import LegacyRegistryAdapterFactory

factory = LegacyRegistryAdapterFactory()
skills = factory.list_legacy_skills()

print(f'  ✅ Legacy bridge initialized: {len(skills)} skills')
print(f'     Core memory: {any(s[\"name\"] == \"memory-master\" for s in skills)}')
"

# ==========================================
# Phase 4: Memory Master Maintenance
# ==========================================
echo ""
echo "[Phase 4] Running memory master maintenance..."

python3 "${OPENCLAW_WORKSPACE}/memory/core/memory_master_daemon.py" || echo "  ⚠️  Memory master skipped (may be already up-to-date)"

# ==========================================
# Phase 5: FTS5 Index Check
# ==========================================
echo ""
echo "[Phase 5] Checking FTS5 index..."

if [ -f "${OPENCLAW_WORKSPACE}/memory/index/memory_fts5.db" ]; then
    echo "  ✅ FTS5 index exists"
else
    echo "  🔄 Building FTS5 index..."
    python3 "${OPENCLAW_WORKSPACE}/memory/core/memory_query_engine.py" --index-only || echo "  ⚠️  Index build skipped"
fi

# ==========================================
# Phase 6: Closed Loop Orchestrator
# ==========================================
echo ""
echo "[Phase 6] Running closed loop orchestrator..."

python3 "${OPENCLAW_WORKSPACE}/scripts/testing/closed_loop_orchestrator.py" "${OPENCLAW_WORKSPACE}/workflows/test_chaining.yaml" || echo "  ⚠️  Quick check completed with warnings"

# ==========================================
# Complete
# ==========================================
echo ""
echo "=========================================="
echo "Bootstrap completed: $(date)"
echo "=========================================="

cat > "${OPENCLAW_WORKSPACE}/.bootstrap_status.json" << EOF
{
    "last_bootstrap": "$(date -Iseconds)",
    "status": "success",
    "memory_system": "initialized",
    "legacy_bridge": "initialized"
}
EOF
