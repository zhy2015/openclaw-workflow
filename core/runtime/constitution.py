from __future__ import annotations

from pathlib import Path
import uuid
import yaml

from core.engine.runner import WorkflowRunner
from core.infra.skill_contracts import ExecutionResult
from core.infra.skill_manager import SkillManager
from core.runtime.dispatch import GovernedDispatcher

from .audit import AuditLogger
from .policies import MemoryPolicyEngine, PolicyContext, PolicyViolation
from .progress import ProgressCheckpoint, ProgressTracker
from .progress_policy import policy_from_dict
from .router import TaskRouter
from .types import TaskEnvelope


class ConstitutionRuntime:
    """Single legal entrypoint.

    Current implementation supports:
    - route decision
    - memory gate enforcement
    - audit logging
    - governed fast-path dispatch via SkillManager
    - slow-path workflow closure via WorkflowRunner
    """

    def __init__(
        self,
        skill_manager: SkillManager | None = None,
        router: TaskRouter | None = None,
        memory_policy: MemoryPolicyEngine | None = None,
        audit: AuditLogger | None = None,
        workflow_runner: WorkflowRunner | None = None,
        workspace_root: str | None = None,
    ):
        self.workspace_root = Path(workspace_root) if workspace_root else Path(__file__).resolve().parents[2]
        self.skill_manager = skill_manager or SkillManager()
        self.router = router or TaskRouter()
        self.memory_policy = memory_policy or MemoryPolicyEngine()
        self.audit = audit or AuditLogger(str(self.workspace_root / "logs" / "constitution.log"))
        self.progress = ProgressTracker(str(self.workspace_root / "logs" / "progress"))
        self.dispatcher = GovernedDispatcher(self.skill_manager)
        self.workflow_runner = workflow_runner or WorkflowRunner(workspace_root=str(self.workspace_root), dispatcher=self.dispatcher)

    def _build_slow_workflow(self, task: TaskEnvelope) -> str:
        workflow_id = f"constitution-{uuid.uuid4().hex[:10]}"

        if task.workflow_nodes:
            nodes = task.workflow_nodes
        else:
            if not task.target_skill or not task.target_tool:
                raise ValueError("Slow path requires target_skill and target_tool")
            nodes = [
                {
                    "id": "task",
                    "skill_name": task.target_skill,
                    "tool_name": task.target_tool,
                    "inputs": {k: v for k, v in task.params.items() if isinstance(v, str)},
                    "outputs": list(task.params.get("expected_outputs", [])) if isinstance(task.params.get("expected_outputs"), list) else [],
                }
            ]

        workflow = {
            "workflow_id": workflow_id,
            "name": f"Constitution slow task: {task.intent}",
            "nodes": nodes,
        }

        workflows_dir = self.workspace_root / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        workflow_file = workflows_dir / f"{workflow_id}.yaml"
        workflow_file.write_text(yaml.safe_dump(workflow, allow_unicode=True, sort_keys=False), encoding="utf-8")
        return workflow_file.name

    async def invoke(self, task: TaskEnvelope, *, recall_performed: bool = False) -> ExecutionResult:
        route = self.router.decide(task)
        policy_context = PolicyContext(route=route, recall_performed=recall_performed)
        progress_policy = policy_from_dict(task.progress_policy or ({"report_every_seconds": 600} if route.mode == "slow" else {}))
        checkpoint = ProgressCheckpoint(
            task_id=task.request_id,
            request_id=task.request_id,
            intent=task.intent,
            stage="route_decision",
            status="running",
            progress_hint=0.05,
            message=f"route={route.mode}",
            meta={"target_skill": route.target_skill, "target_tool": route.target_tool, "progress_policy": progress_policy.__dict__},
        )
        self.progress.save(checkpoint)

        try:
            self.memory_policy.validate(task, policy_context)
        except PolicyViolation as e:
            self.audit.log("policy_violation", {
                "task_type": task.task_type,
                "intent": task.intent,
                "caller": task.caller,
                "reason": str(e),
            })
            failed_checkpoint = ProgressCheckpoint(
                task_id=task.request_id,
                request_id=task.request_id,
                intent=task.intent,
                stage="policy_gate",
                status="failed",
                progress_hint=0.0,
                message=str(e),
                meta={"progress_policy": progress_policy.__dict__},
            )
            self.progress.save(failed_checkpoint)
            return ExecutionResult.failure(str(e), code="POLICY_VIOLATION")

        self.audit.log("route_decision", {
            "task_type": task.task_type,
            "intent": task.intent,
            "caller": task.caller,
            "mode": route.mode,
            "reason": route.reason,
            "target_skill": route.target_skill,
            "target_tool": route.target_tool,
            "workflow_nodes": len(task.workflow_nodes),
        })

        if route.mode == "slow":
            try:
                workflow_file = self._build_slow_workflow(task)
                self.progress.save(ProgressCheckpoint(
                    task_id=task.request_id,
                    request_id=task.request_id,
                    intent=task.intent,
                    stage="slow_workflow_dispatch",
                    status="running",
                    progress_hint=0.2,
                    message=workflow_file,
                ))
                workflow_result = await self.workflow_runner.run_yaml(workflow_file)
                result = ExecutionResult.success(workflow_result, route=route.mode, workflow_id=workflow_result.get("workflow_id"))
                self.audit.log("dispatch_result", {
                    "task_type": task.task_type,
                    "skill": route.target_skill,
                    "tool": route.target_tool,
                    "ok": result.ok,
                    "code": result.code,
                    "route": route.mode,
                    "workflow_nodes": len(task.workflow_nodes),
                })
                completed_checkpoint = ProgressCheckpoint(
                    task_id=task.request_id,
                    request_id=task.request_id,
                    intent=task.intent,
                    stage="completed",
                    status="done",
                    progress_hint=1.0,
                    message="slow workflow completed",
                    workflow_id=workflow_result.get("workflow_id"),
                    meta={"progress_policy": progress_policy.__dict__},
                )
                self.progress.save(completed_checkpoint)
                return result
            except Exception as e:
                self.audit.log("dispatch_result", {
                    "task_type": task.task_type,
                    "skill": route.target_skill,
                    "tool": route.target_tool,
                    "ok": False,
                    "code": "SLOW_PATH_ERROR",
                    "route": route.mode,
                    "workflow_nodes": len(task.workflow_nodes),
                    "error": str(e),
                })
                failed_checkpoint = ProgressCheckpoint(
                    task_id=task.request_id,
                    request_id=task.request_id,
                    intent=task.intent,
                    stage="slow_workflow_dispatch",
                    status="failed",
                    progress_hint=0.2,
                    message=str(e),
                    meta={"progress_policy": progress_policy.__dict__},
                )
                self.progress.save(failed_checkpoint)
                return ExecutionResult.failure(str(e), code="SLOW_PATH_ERROR", route=route.mode)

        if not route.target_skill or not route.target_tool:
            return ExecutionResult.failure(
                "Fast path requires target_skill and target_tool",
                code="INVALID_TASK_TARGET",
                route=route.mode,
            )

        result = self.skill_manager.dispatch(
            route.target_skill,
            route.target_tool,
            task.params,
            policy_context=policy_context,
        )
        self.audit.log("dispatch_result", {
            "task_type": task.task_type,
            "skill": route.target_skill,
            "tool": route.target_tool,
            "ok": result.ok,
            "code": result.code,
        })
        self.progress.save(ProgressCheckpoint(
            task_id=task.request_id,
            request_id=task.request_id,
            intent=task.intent,
            stage="fast_dispatch",
            status="done" if result.ok else "failed",
            progress_hint=1.0 if result.ok else 0.8,
            message=result.code,
            meta={"skill": route.target_skill, "tool": route.target_tool},
        ))
        return result
