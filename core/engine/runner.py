#!/usr/bin/env python3
"""
Unified workflow runner for the new core/engine stack.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict

from core.engine.dag_engine import DAGEngine
from core.engine.wal_engine import WALEngine
from core.engine.workflow_context import get_context
from core.engine.yaml_workflow import YAMLWorkflowLoader
from core.engine.workflow_registry import WorkflowRegistry, WorkflowStatus, TaskStatus
from core.runtime.dispatch import GovernedDispatcher


class WorkflowRunner:
    def __init__(self, workspace_root: str | None = None, dispatcher: GovernedDispatcher | None = None):
        self.workspace_root = Path(workspace_root) if workspace_root else Path(__file__).resolve().parents[2]
        self.workflows_dir = self.workspace_root / "workflows"
        self.logs_dir = self.workflows_dir / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.registry = WorkflowRegistry(str(self.workflows_dir / "registry.json"))
        self.dispatcher = dispatcher or GovernedDispatcher()

    async def run_yaml(self, workflow_file: str) -> Dict[str, Any]:
        loader = YAMLWorkflowLoader(base_dir=str(self.workflows_dir))
        loaded = loader.load_file(workflow_file)
        workflow_id = loaded.workflow_id
        pipeline = loaded.pipeline
        ctx = get_context(workflow_id)
        await ctx.clear()

        wf = self.registry.create_workflow(workflow_id, loaded.name, f"Loaded from {workflow_file}")
        wf.status = WorkflowStatus.RUNNING.value
        for node_id, node in pipeline.nodes.items():
            task_target = node.skill_uri or f"{node.skill_name}/{node.tool_name}"
            self.registry.add_task(workflow_id, node_id, task_target)

        wal_path = self.logs_dir / f"{workflow_id}.wal.jsonl"
        wal = WALEngine(str(wal_path))
        engine = DAGEngine(dispatcher=self.dispatcher, context=ctx)

        async def wal_callback(node_id: str, payload: Dict[str, Any]):
            if payload.get("status") == "success":
                await wal.log_task_success(
                    workflow_id=workflow_id,
                    task_id=node_id,
                    context=ctx,
                    keys_to_save=[f"{node_id}.{k}" for k in payload.get("outputs", {}).keys()],
                    metadata={"node_id": node_id},
                )
                self.registry.update_task_status(workflow_id, node_id, TaskStatus.SUCCESS, outputs=payload.get("outputs", {}))
            else:
                await wal.log_task_failure(
                    workflow_id=workflow_id,
                    task_id=node_id,
                    error=payload.get("error") or "unknown error",
                    metadata={"node_id": node_id},
                )
                self.registry.update_task_status(workflow_id, node_id, TaskStatus.FAILED, outputs={"error": payload.get("error")})

        engine.on_node_complete(wal_callback)

        for node_id in pipeline.nodes:
            self.registry.update_task_status(workflow_id, node_id, TaskStatus.RUNNING)
            node = pipeline.nodes[node_id]
            await wal.log_task_start(
                workflow_id,
                node_id,
                metadata={
                    "skill_uri": node.skill_uri,
                    "skill_name": node.skill_name,
                    "tool_name": node.tool_name,
                },
            )

        try:
            results = await engine.execute(pipeline)
            self.registry._workflows[workflow_id].status = WorkflowStatus.SUCCESS.value
            self.registry._save()
        except Exception as e:
            msg = str(e)
            failed_node_id = None
            if 'Pipeline failed at node:' in msg:
                try:
                    failed_node_id = msg.split('Pipeline failed at node:')[1].split('-')[0].strip()
                except Exception:
                    failed_node_id = None
            if failed_node_id:
                await wal.log_task_failure(
                    workflow_id=workflow_id,
                    task_id=failed_node_id,
                    error=msg,
                    metadata={'node_id': failed_node_id, 'source': 'runner_exception_handler'},
                )
                self.registry.update_task_status(workflow_id, failed_node_id, TaskStatus.FAILED, outputs={'error': msg})
            self.registry._workflows[workflow_id].status = WorkflowStatus.FAILED.value
            self.registry._save()
            raise

        context_data = await ctx.to_dict()
        await asyncio.sleep(0.1)
        return {
            "workflow_id": workflow_id,
            "results": results,
            "context": context_data,
            "wal_path": str(wal_path),
            "registry_path": str(self.workflows_dir / 'registry.json'),
        }
