from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Protocol


class HiDreamAdapterError(RuntimeError):
    pass


class HiDreamAdapterValidationError(HiDreamAdapterError):
    pass


@dataclass(frozen=True)
class HiDreamRequest:
    model: str
    version: str
    prompt: str
    resolution: str = "2048*2048"
    img_count: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "version": self.version,
            "prompt": self.prompt,
            "resolution": self.resolution,
            "img_count": self.img_count,
        }


class HiDreamAdapter(Protocol):
    def build_request(self, payload: Dict[str, Any]) -> HiDreamRequest:
        ...

    def submit(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        ...


class SeedreamImageAdapter:
    def __init__(self, skills_root: str | Path):
        self.skills_root = Path(skills_root)
        self.seedream_path = self.skills_root / "hidream-api-gen" / "scripts" / "seedream.py"
        if not self.seedream_path.exists():
            raise HiDreamAdapterValidationError(f"seedream.py not found: {self.seedream_path}")
        self._module = self._load_module(self.seedream_path, "hidream_seedream_adapter")

    def _load_module(self, path: Path, module_name: str):
        spec = importlib.util.spec_from_file_location(module_name, path)
        if not spec or not spec.loader:
            raise HiDreamAdapterError(f"unable to load module from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def build_request(self, payload: Dict[str, Any]) -> HiDreamRequest:
        prompt = payload.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise HiDreamAdapterValidationError("prompt must be a non-empty string")
        version = str(payload.get("version", "M1"))
        resolution = str(payload.get("resolution", "2048*2048"))
        img_count = int(payload.get("img_count", 1))
        return HiDreamRequest(
            model="seedream",
            version=version,
            prompt=prompt.strip(),
            resolution=resolution,
            img_count=img_count,
        )

    def submit(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        request = self.build_request(payload)
        result = self._module.run(
            version=request.version,
            prompt=request.prompt,
            resolution=request.resolution,
            img_count=request.img_count,
            authorization=payload.get("authorization"),
        )
        return {
            "request": request.to_dict(),
            "result": result,
        }


def serialize_hidream_request(request: HiDreamRequest) -> str:
    return json.dumps(request.to_dict(), ensure_ascii=False, indent=2)
