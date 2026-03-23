#!/bin/bash
# Demo CLI for OpenClaw Workflow System

echo "=========================================="
echo "OpenClaw Workflow System - Demo"
echo "=========================================="
echo ""

# Setup environment
export PYTHONPATH="/root/.openclaw/workspace/skills/video-production/core:$PYTHONPATH"

echo "1. List all registered skills"
echo "----------------------------------------"
cd /root/.openclaw/workspace/skills/video-production
python3 -c "
import sys
sys.path.insert(0, 'core')
from registry import Registry

registry = Registry(skills_root='/root/.openclaw/workspace/skills')
skills = registry.scan()

print(f'Total: {len(skills)} skills\\n')
for name in sorted(skills):
    manifest = registry._manifests.get(name)
    has_workflow = '✓' if manifest.workflow else '○'
    print(f'  [{has_workflow}] {name}')
"

echo ""
echo "2. Show skill schema (weather)"
echo "----------------------------------------"
python3 -c "
import sys
import json
sys.path.insert(0, 'core')
from registry import Registry

registry = Registry(skills_root='/root/.openclaw/workspace/skills')
registry.scan()

schema = registry.get_skill_schema('weather')
print(json.dumps(schema, indent=2, ensure_ascii=False))
"

echo ""
echo "3. WAL Status"
echo "----------------------------------------"
if [ -f /root/.openclaw/workspace/skills/workflows/logs/wal.jsonl ]; then
    echo "WAL file exists"
    echo "Entries: $(wc -l < /root/.openclaw/workspace/skills/workflows/logs/wal.jsonl)"
    echo ""
    echo "Recent entries:"
    tail -3 /root/.openclaw/workspace/skills/workflows/logs/wal.jsonl | python3 -m json.tool 2>/dev/null || cat /root/.openclaw/workspace/skills/workflows/logs/wal.jsonl | tail -3
else
    echo "WAL file not found"
fi

echo ""
echo "=========================================="
echo "Demo Complete"
echo "=========================================="
