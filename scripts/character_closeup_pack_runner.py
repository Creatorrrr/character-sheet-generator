#!/usr/bin/env python3
from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    skill_runner = (
        repo_root
        / ".agents"
        / "skills"
        / "create-character-sheet-closeup-reference-pack"
        / "scripts"
        / "character_closeup_pack_runner.py"
    )
    if not skill_runner.exists():
        print(f"Missing skill-local runner: {skill_runner}", file=sys.stderr)
        return 1
    sys.argv[0] = str(skill_runner)
    runpy.run_path(str(skill_runner), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
