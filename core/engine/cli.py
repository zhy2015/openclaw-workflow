#!/usr/bin/env python3
"""
Core engine CLI for listing legacy-bridged skills and running YAML workflows on the new runtime.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from core.infra.legacy_registry_adapter import LegacyRegistryAdapterFactory
from core.infra.builtin_smoke_skill import BuiltinSmokeSkill
from core.infra.builtin_comic_workflow_skill import BuiltinComicWorkflowSkill
from core.infra.real_comic_workflow_skill import RealComicWorkflowSkill
from core.infra.skill_manager import SkillManager
from core.runtime.dispatch import GovernedDispatcher
from core.engine.runner import WorkflowRunner


def cmd_skill_list() -> int:
    factory = LegacyRegistryAdapterFactory()
    skills = sorted(factory.list_legacy_skills(), key=lambda x: x["name"])
    print(f"{'Name':<30} {'Category':<18} {'Execution'}")
    print('-' * 70)
    for item in skills:
        print(f"{item['name']:<30} {item['category']:<18} {item['execution_type']}")
    print(f"\nTotal: {len(skills)}")
    return 0


async def cmd_workflow_run(workflow_file: str) -> int:
    manager = SkillManager(context=None)
    manager._context.config["workspace_root"] = str(WORKSPACE_ROOT)
    manager._context.config["skills_root"] = "/Users/hidream/.openclaw/workspace/skills"
    manager.register(BuiltinSmokeSkill())
    manager.register(BuiltinComicWorkflowSkill())
    manager.register(RealComicWorkflowSkill())
    dispatcher = GovernedDispatcher(manager)
    runner = WorkflowRunner(dispatcher=dispatcher)
    result = await runner.run_yaml(workflow_file)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog='openclaw-core', description='Core engine CLI')
    sub = parser.add_subparsers(dest='command')

    skill = sub.add_parser('skill', help='Skill operations')
    skill_sub = skill.add_subparsers(dest='skill_command')
    skill_sub.add_parser('list', help='List active legacy-bridged skills')

    workflow = sub.add_parser('workflow', help='Workflow operations')
    workflow_sub = workflow.add_subparsers(dest='workflow_command')
    run = workflow_sub.add_parser('run', help='Run YAML workflow')
    run.add_argument('workflow_file', help='Path to YAML workflow file')

    args = parser.parse_args()

    if args.command == 'skill' and args.skill_command == 'list':
        return cmd_skill_list()
    if args.command == 'workflow' and args.workflow_command == 'run':
        return asyncio.run(cmd_workflow_run(args.workflow_file))

    parser.print_help()
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
