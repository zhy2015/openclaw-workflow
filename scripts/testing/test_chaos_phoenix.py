#!/usr/bin/env python3
"""
Phoenix chaos test on the new core/engine stack.
Runs a YAML workflow that intentionally fails after one successful node,
then inspects WAL output.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from core.engine.runner import WorkflowRunner


async def main_async():
    runner = WorkflowRunner(str(WORKSPACE_ROOT))
    report = {
        'mode': 'core_engine_chaos_test',
        'workflow': 'workflows/test_chaos_core.yaml'
    }
    try:
        await runner.run_yaml(str(WORKSPACE_ROOT / 'workflows' / 'test_chaos_core.yaml'))
        report['status'] = 'unexpected_success'
    except Exception as e:
        report['status'] = 'expected_failure'
        report['error'] = str(e)

    wal_path = WORKSPACE_ROOT / 'workflows' / 'logs' / 'test-chaos-core.wal.jsonl'
    entries = []
    if wal_path.exists():
        for line in wal_path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    report['wal_path'] = str(wal_path)
    report['wal_entries'] = entries

    out = WORKSPACE_ROOT / 'logs' / 'phoenix_test_report.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


def main():
    asyncio.run(main_async())


if __name__ == '__main__':
    main()
