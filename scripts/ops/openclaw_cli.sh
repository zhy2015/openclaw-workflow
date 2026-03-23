#!/bin/bash
# OpenClaw CLI - Quick commands for system management (new core engine)

OPENCLAW_WORKSPACE="/root/.openclaw/workspace"

show_help() {
    cat << EOF
OpenClaw CLI - Available commands:

  openclaw bootstrap     - Run full system bootstrap
  openclaw status        - Check system status
  openclaw skills        - List active skills
  openclaw workflow      - Run a YAML workflow (usage: openclaw workflow <file>)
  openclaw logs          - View recent logs
  openclaw help          - Show this help
EOF
}

case "${1:-help}" in
    bootstrap)
        echo "Running OpenClaw bootstrap..."
        "${OPENCLAW_WORKSPACE}/scripts/ops/openclaw_bootstrap.sh"
        ;;

    status)
        echo "OpenClaw System Status"
        echo "======================"
        echo ""
        if [ -f "${OPENCLAW_WORKSPACE}/.bootstrap_status.json" ]; then
            echo "✅ Bootstrap completed: $(cat ${OPENCLAW_WORKSPACE}/.bootstrap_status.json | grep last_bootstrap | cut -d'"' -f4)"
        else
            echo "⚠️  Bootstrap not yet run"
        fi
        echo ""
        echo "Legacy bridge:"
        python3 -c "
import sys
sys.path.insert(0, '${OPENCLAW_WORKSPACE}')
from core.infra.legacy_registry_adapter import LegacyRegistryAdapterFactory
f = LegacyRegistryAdapterFactory()
print(f'  Skills: {len(f.list_legacy_skills())} bridged')
" 2>/dev/null || echo "  ⚠️  Legacy bridge not initialized"
        ;;

    skills)
        python3 "${OPENCLAW_WORKSPACE}/core/engine/cli.py" skill list
        ;;

    workflow)
        if [ -z "$2" ]; then
            echo "Usage: openclaw workflow <yaml-file>"
            exit 1
        fi
        python3 "${OPENCLAW_WORKSPACE}/core/engine/cli.py" workflow run "$2"
        ;;

    logs)
        echo "Recent logs:"
        ls -lt "${OPENCLAW_WORKSPACE}/logs/" 2>/dev/null | head -10 || echo "No logs found"
        ;;

    help|--help|-h)
        show_help
        ;;

    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
