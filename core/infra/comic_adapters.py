from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


class AdapterError(RuntimeError):
    pass


class AdapterTimeout(AdapterError):
    pass


class AdapterValidationError(AdapterError):
    pass


@dataclass(frozen=True)
class ScriptGenerateInput:
    topic: str
    panels: int = 6

    @classmethod
    def from_params(cls, params: Dict[str, Any]) -> "ScriptGenerateInput":
        topic = params.get("topic")
        panels = params.get("panels", 6)
        if not isinstance(topic, str) or not topic.strip():
            raise AdapterValidationError("topic must be a non-empty string")
        if not isinstance(panels, int) or panels <= 0:
            raise AdapterValidationError("panels must be a positive integer")
        return cls(topic=topic.strip(), panels=panels)


@dataclass(frozen=True)
class AvatarGenerateInput:
    character_prompt: str
    style: str = "manga"
    mode: str = "max"

    @classmethod
    def from_params(cls, params: Dict[str, Any]) -> "AvatarGenerateInput":
        character_prompt = params.get("character_prompt")
        if not isinstance(character_prompt, str) or not character_prompt.strip():
            raise AdapterValidationError("character_prompt must be a non-empty string")
        return cls(
            character_prompt=character_prompt.strip(),
            style=str(params.get("style", "manga")),
            mode=str(params.get("mode", "max")),
        )


@dataclass(frozen=True)
class ComiCogRenderInput:
    story_prompt: str
    format: str = "page"
    chat_mode: str = "agent"

    @classmethod
    def from_params(cls, params: Dict[str, Any]) -> "ComiCogRenderInput":
        story_prompt = params.get("story_prompt")
        if not isinstance(story_prompt, str) or not story_prompt.strip():
            raise AdapterValidationError("story_prompt must be a non-empty string")
        return cls(
            story_prompt=story_prompt.strip(),
            format=str(params.get("format", "page")),
            chat_mode=str(params.get("chat_mode", "agent")),
        )


@dataclass(frozen=True)
class ScriptGenerateOutput:
    script_outline: str
    panels: int
    source_skill: str = "comic-script"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "script_outline": self.script_outline,
            "panels": self.panels,
            "source_skill": self.source_skill,
        }


@dataclass(frozen=True)
class AvatarGenerateOutput:
    avatar_prompt: str
    style: str
    mode: str
    source_skill: str = "anime-avatar-generation"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "avatar_prompt": self.avatar_prompt,
            "style": self.style,
            "mode": self.mode,
            "source_skill": self.source_skill,
        }


@dataclass(frozen=True)
class ComiCogRenderOutput:
    render_prompt: str
    format: str
    chat_mode: str
    source_skill: str = "comi-cog"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "render_prompt": self.render_prompt,
            "format": self.format,
            "chat_mode": self.chat_mode,
            "source_skill": self.source_skill,
        }


@dataclass(frozen=True)
class KnowledgeComicPlanInput:
    topic: str
    source_text: str
    art: str = "manga"
    tone: str = "neutral"
    layout: str = "standard"
    aspect: str = "3:4"
    lang: str = "zh"

    @classmethod
    def from_params(cls, params: Dict[str, Any]) -> "KnowledgeComicPlanInput":
        topic = params.get("topic")
        source_text = params.get("source_text")
        if not isinstance(topic, str) or not topic.strip():
            raise AdapterValidationError("topic must be a non-empty string")
        if not isinstance(source_text, str) or not source_text.strip():
            raise AdapterValidationError("source_text must be a non-empty string")
        return cls(
            topic=topic.strip(),
            source_text=source_text.strip(),
            art=str(params.get("art", "manga")),
            tone=str(params.get("tone", "neutral")),
            layout=str(params.get("layout", "standard")),
            aspect=str(params.get("aspect", "3:4")),
            lang=str(params.get("lang", "zh")),
        )


@dataclass(frozen=True)
class KnowledgeComicPlanOutput:
    topic: str
    command_preview: str
    output_dir: str
    source_skill: str = "baoyu-comic"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "command_preview": self.command_preview,
            "output_dir": self.output_dir,
            "source_skill": self.source_skill,
        }


class AdapterLogger:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: Dict[str, Any]) -> None:
        record = dict(event)
        record.setdefault("ts", time.time())
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


class BaseComicAdapter:
    def __init__(self, *, workspace_root: str | Path, skills_root: str | Path | None = None, timeout_seconds: int = 20, logger: Optional[AdapterLogger] = None):
        self.workspace_root = Path(workspace_root)
        configured_skills_root = skills_root or os.environ.get("OPENCLAW_SKILLS_ROOT")
        self.skills_root = Path(configured_skills_root) if configured_skills_root else self.workspace_root / "skills"
        self.timeout_seconds = timeout_seconds
        self.logger = logger or AdapterLogger(self.workspace_root / "workflows" / "logs" / "comic-adapters.jsonl")

    def _run_subprocess(self, argv: list[str], *, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
        started = time.time()
        self.logger.log({"stage": "subprocess.start", "argv": argv, "cwd": str(cwd or self.workspace_root)})
        try:
            proc = subprocess.run(
                argv,
                cwd=str(cwd or self.workspace_root),
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as e:
            self.logger.log({
                "stage": "subprocess.timeout",
                "argv": argv,
                "timeout_seconds": self.timeout_seconds,
                "elapsed_ms": int((time.time() - started) * 1000),
            })
            raise AdapterTimeout(f"subprocess timeout after {self.timeout_seconds}s") from e

        self.logger.log({
            "stage": "subprocess.finish",
            "argv": argv,
            "returncode": proc.returncode,
            "elapsed_ms": int((time.time() - started) * 1000),
            "stdout_preview": proc.stdout[:500],
            "stderr_preview": proc.stderr[:500],
        })
        if proc.returncode != 0:
            raise AdapterError(proc.stderr.strip() or proc.stdout.strip() or f"subprocess failed: {argv}")
        return proc


class ComicScriptAdapter(BaseComicAdapter):
    def __init__(self, *, workspace_root: str | Path, skills_root: str | Path | None = None):
        super().__init__(workspace_root=workspace_root, skills_root=skills_root)
        self.script_path = self.skills_root / "comic-script" / "scripts" / "comic.sh"

    def _fallback_storyboard(self, payload: ScriptGenerateInput, reason: str) -> str:
        lines = [
            f"Storyboard — {payload.topic} ({payload.panels} panels)",
            f"Fallback reason: {reason}",
        ]
        for i in range(1, payload.panels + 1):
            lines.extend([
                "",
                f"Panel {i}/{payload.panels}",
                "Shot: [wide/medium/close-up]",
                f"Dialogue: {payload.topic} - beat {i}",
                "SFX: ___",
                "Note: ___",
            ])
        return "\n".join(lines)

    def generate_script_scaffold(self, params: Dict[str, Any]) -> Dict[str, Any]:
        payload = ScriptGenerateInput.from_params(params)
        if not self.script_path.exists():
            raise AdapterValidationError(f"comic-script entry not found: {self.script_path}")
        proc = self._run_subprocess([
            "bash",
            str(self.script_path),
            "storyboard",
            str(payload.panels),
            payload.topic,
        ])
        stdout = proc.stdout.strip()
        if not stdout or "Comic Script Writer" in stdout or "Commands:" in stdout:
            self.logger.log({
                "stage": "comic-script.fallback",
                "reason": "help_like_or_empty_output",
                "topic": payload.topic,
                "panels": payload.panels,
            })
            stdout = self._fallback_storyboard(payload, "comic-script returned non-storyboard output")
        output = ScriptGenerateOutput(
            script_outline=stdout,
            panels=payload.panels,
        )
        return output.to_dict()


class AnimeAvatarAdapter(BaseComicAdapter):
    def build_avatar_prompt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        payload = AvatarGenerateInput.from_params(params)
        self.logger.log({
            "stage": "anime-avatar.prompt",
            "style": payload.style,
            "mode": payload.mode,
        })
        output = AvatarGenerateOutput(
            avatar_prompt=(
                f"Create an {payload.style} anime avatar: {payload.character_prompt}. "
                f"Use quality mode {payload.mode}."
            ),
            style=payload.style,
            mode=payload.mode,
        )
        return output.to_dict()


class ComiCogAdapter(BaseComicAdapter):
    def build_render_prompt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        payload = ComiCogRenderInput.from_params(params)
        self.logger.log({
            "stage": "comi-cog.prompt",
            "format": payload.format,
            "chat_mode": payload.chat_mode,
        })
        output = ComiCogRenderOutput(
            render_prompt=(
                f"Create a {payload.format} comic render with chat_mode={payload.chat_mode}: "
                f"{payload.story_prompt}"
            ),
            format=payload.format,
            chat_mode=payload.chat_mode,
        )
        return output.to_dict()


class BaoyuComicAdapter(BaseComicAdapter):
    def __init__(self, *, workspace_root: str | Path, skills_root: str | Path | None = None):
        super().__init__(workspace_root=workspace_root, skills_root=skills_root)
        self.skill_dir = self.skills_root / "baoyu-comic"

    def plan_knowledge_comic(self, params: Dict[str, Any]) -> Dict[str, Any]:
        payload = KnowledgeComicPlanInput.from_params(params)
        if not self.skill_dir.exists():
            raise AdapterValidationError(f"baoyu-comic skill dir not found: {self.skill_dir}")

        topic_slug = "-".join(payload.topic.lower().split()) or "comic-topic"
        command_preview = (
            f"/baoyu-comic source.md --art {payload.art} --tone {payload.tone} "
            f"--layout {payload.layout} --aspect {payload.aspect} --lang {payload.lang}"
        )
        output = KnowledgeComicPlanOutput(
            topic=payload.topic,
            command_preview=command_preview,
            output_dir=f"comic/{topic_slug}/",
        )
        self.logger.log({
            "stage": "baoyu.plan",
            "topic": payload.topic,
            "art": payload.art,
            "tone": payload.tone,
            "layout": payload.layout,
            "aspect": payload.aspect,
            "lang": payload.lang,
            "skills_root": str(self.skills_root),
        })
        return output.to_dict()
