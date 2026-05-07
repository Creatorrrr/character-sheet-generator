#!/usr/bin/env python3
from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> int:
    skill_script = Path(__file__).resolve()
    repo_root = skill_script.parents[4]
    root_runner = repo_root / "scripts" / "video_scenario_image_pack_runner.py"
    if not root_runner.exists():
        print(f"Missing root runner: {root_runner}", file=sys.stderr)
        return 1
    sys.argv[0] = str(root_runner)
    runpy.run_path(str(root_runner), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
