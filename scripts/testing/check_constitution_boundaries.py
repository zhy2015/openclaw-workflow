#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path("/root/.openclaw/workspace")
TARGET_DIRS = [ROOT / "core", ROOT / "scripts", ROOT / "projects"]
FORBIDDEN_PATTERNS = [
    "from core.infra.registry import get_registry",
    "from core.infra.registry.manager import get_registry",
    "registry.execute(",
]
ALLOWED_SUBSTRINGS = [
    "legacy_registry_adapter",
    "legacy_adapter_factory",
    "core/infra/registry/manager.py",
    "core/infra/registry/__init__.py",
    "scripts/testing/check_constitution_boundaries.py",
]


def is_allowed(path: Path) -> bool:
    s = str(path)
    return any(x in s for x in ALLOWED_SUBSTRINGS)


def main() -> int:
    violations: list[str] = []
    for base in TARGET_DIRS:
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if is_allowed(path):
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in FORBIDDEN_PATTERNS:
                if pattern in text:
                    violations.append(f"{path}: forbidden pattern -> {pattern}")
    if violations:
        print("Constitution boundary violations found:")
        for v in violations:
            print(v)
        return 1
    print("Constitution boundary check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
