#!/usr/bin/env python3
"""
YAML workflow loader for core.engine.

Loads a declarative YAML DAG into DAGPipeline objects backed by core.engine.dag_engine.
Only supports the new core/engine runtime. Does not touch archived engines.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

from core.engine.dag_engine import DAGNode, DAGPipeline


@dataclass
class LoadedWorkflow:
    workflow_id: str
    name: str
    pipeline: DAGPipeline
    raw: Dict[str, Any]


class YAMLWorkflowError(Exception):
    pass


class YAMLWorkflowLoader:
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parents[2] / "workflows"

    def load_file(self, path: str | Path) -> LoadedWorkflow:
        file_path = Path(path)
        if not file_path.is_absolute():
            file_path = self.base_dir / file_path
        if not file_path.exists():
            raise YAMLWorkflowError(f"Workflow file not found: {file_path}")

        data = yaml.safe_load(file_path.read_text(encoding="utf-8")) or {}
        return self.load_dict(data)

    def load_dict(self, data: Dict[str, Any]) -> LoadedWorkflow:
        workflow_id = data.get("workflow_id") or data.get("id") or "wf-yaml"
        name = data.get("name") or workflow_id
        nodes_data = data.get("nodes")
        if not isinstance(nodes_data, list) or not nodes_data:
            raise YAMLWorkflowError("Workflow YAML must contain a non-empty 'nodes' list")

        pipeline = DAGPipeline(pipeline_id=workflow_id, name=name)

        for item in nodes_data:
            if not isinstance(item, dict):
                raise YAMLWorkflowError(f"Invalid node entry: {item!r}")
            node_id = item.get("id")
            skill_uri = item.get("skill")
            skill_name = item.get("skill_name")
            tool_name = item.get("tool_name")
            if not node_id or not (skill_uri or (skill_name and tool_name)):
                raise YAMLWorkflowError(f"Node missing id and dispatch target: {item!r}")

            node = DAGNode(
                node_id=node_id,
                skill_uri=skill_uri,
                skill_name=skill_name,
                tool_name=tool_name,
                inputs=item.get("inputs", {}) or {},
                outputs=item.get("outputs", []) or [],
                retries=item.get("retries", 3),
                timeout=item.get("timeout", 300),
            )
            pipeline.add_node(node)

        for item in nodes_data:
            from_id = item["id"]
            for to_id in item.get("next", []) or []:
                if to_id not in pipeline.nodes:
                    raise YAMLWorkflowError(f"Unknown downstream node: {to_id}")
                pipeline.add_edge(from_id, to_id)

        return LoadedWorkflow(
            workflow_id=workflow_id,
            name=name,
            pipeline=pipeline,
            raw=data,
        )
