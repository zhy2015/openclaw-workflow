#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.infra.comic_compiler import ComicScriptCompiler, build_hidream_payloads


def main() -> int:
    topic = sys.argv[1] if len(sys.argv) > 1 else "赛博朋克算命局"
    compiled = ComicScriptCompiler().compile(topic)
    payloads = build_hidream_payloads(compiled)
    print(json.dumps({
        "topic": topic,
        "compiled_storyboard": compiled,
        "hidream_payloads": payloads,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
