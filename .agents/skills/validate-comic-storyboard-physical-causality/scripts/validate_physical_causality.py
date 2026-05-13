#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path("/Users/chasoik/Projects/character-sheet-generator")
PACK_SCRIPT_DIR = REPO_ROOT / ".agents" / "skills" / "create-comic-storyboard-pack" / "scripts"
RUNNER = PACK_SCRIPT_DIR / "comic_storyboard_runner.py"
if str(PACK_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(PACK_SCRIPT_DIR))

from comic_storyboard_validators import build_physical_causality_report  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a physical_causality validation report.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--item", required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve(strict=False)
    report = build_physical_causality_report(
        runner_path=RUNNER,
        run_dir=run_dir,
        page_ref=args.item,
        stage_id=args.stage,
    )
    stem = Path(report["filename"]).stem
    output = Path(args.output) if args.output else run_dir / "validation_reports" / args.stage / stem / "physical_causality.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"VALIDATION_REPORT: {output}")
    print(f"VERDICT: {report['verdict']}")


if __name__ == "__main__":
    main()
