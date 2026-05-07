import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = (
    REPO_ROOT
    / ".agents"
    / "skills"
    / "create-comic-storyboard-pack"
    / "scripts"
    / "comic_storyboard_runner.py"
)


def run_cli(*args, cwd):
    return subprocess.run(
        [sys.executable, str(RUNNER), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
    )


def run_cli_raw(*args, cwd):
    return subprocess.run(
        [sys.executable, str(RUNNER), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def run_dir_from_init(result):
    for line in result.stdout.splitlines():
        if line.startswith("RUN_DIR: "):
            return Path(line.split(": ", 1)[1])
    raise AssertionError(f"RUN_DIR not found in output: {result.stdout}")


def sample_plan(panel_count=5):
    panels = []
    for index in range(1, panel_count + 1):
        panels.append(
            {
                "id": f"{index:03d}-panel-{index}",
                "filename": f"{index:03d}-panel-{index}.png",
                "panel_no": index,
                "scene_refs": ["S01"],
                "beat": f"Story beat {index}",
                "visual_brief": f"Comic panel visual brief {index}",
                "setting": "school gym",
                "characters": ["main character"],
                "action": "looks toward the hoop",
                "camera": "wide shot",
                "composition": "subject in foreground with hoop in background",
                "dialogue": [f"line {index}"],
                "sfx": [],
                "narration": [],
                "continuity_notes": "hoop stays on the far wall",
                "prompt": f"Generate comic panel {index}",
            }
        )
    return {
        "scenario_title": "Gym Story",
        "style_brief": "clean cinematic comic style",
        "reading_order": "left-to-right",
        "panels": panels,
    }


def init_run(root):
    result = run_cli(
        "init",
        "--title",
        "Gym Story",
        "--scenario-summary",
        "A short gym scene.",
        "--output-root",
        str(root / "output"),
        cwd=root,
    )
    return run_dir_from_init(result)


def approve_plan(root, run_dir, panel_count=5):
    plan_path = root / "plan.json"
    plan_path.write_text(json.dumps(sample_plan(panel_count), indent=2), encoding="utf-8")
    return run_cli("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_path), cwd=root)


def generate_file(root, name="generated.png", data=b"generated image"):
    path = root / name
    path.write_bytes(data)
    return path


class ComicStoryboardRunnerTest(unittest.TestCase):
    def test_init_creates_approval_gated_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            state = json.loads((run_dir / "state.json").read_text())

            self.assertEqual(state["workflow"], "create-comic-storyboard-pack")
            self.assertFalse(state["plan_approved"])
            self.assertEqual(state["stage_order"], ["storyboard", "sketch_ink", "finish"])
            self.assertEqual(state["panels"], [])
            self.assertTrue((run_dir / "scenario.md").exists())
            self.assertTrue((run_dir / "prompts" / "storyboard").exists())
            self.assertTrue((run_dir / "01_storyboard").exists())

    def test_approve_plan_normalizes_panels_and_stage_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)

            result = approve_plan(root, run_dir, panel_count=2)
            self.assertIn("APPROVED_PANELS: 2", result.stdout)
            state = json.loads((run_dir / "state.json").read_text())

            self.assertTrue(state["plan_approved"])
            self.assertEqual(len(state["panels"]), 2)
            first = state["panels"][0]
            self.assertEqual(first["id"], "001-panel-1")
            self.assertEqual(first["filename"], "001-panel-1.png")
            self.assertEqual(set(first["stages"].keys()), {"storyboard", "sketch_ink", "finish"})
            self.assertEqual(first["stages"]["storyboard"]["status"], "pending")
            self.assertTrue((run_dir / "approved_storyboard_plan.json").exists())
            self.assertTrue((run_dir / "batch_plan.md").exists())

    def test_next_batch_requires_approved_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)

            result = run_cli_raw("next-batch", "--run-dir", str(run_dir), cwd=root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Plan is not approved", result.stderr)

    def test_next_batch_reserves_at_most_four_current_stage_panels(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, panel_count=5)

            result = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "10", cwd=root)
            self.assertIn("STAGE: storyboard", result.stdout)
            self.assertEqual(result.stdout.count("ITEM: "), 4)
            state = json.loads((run_dir / "state.json").read_text())
            reserved = [
                panel
                for panel in state["panels"]
                if panel["stages"]["storyboard"]["status"] == "generation_requested"
            ]
            self.assertEqual(len(reserved), 4)
            self.assertEqual({panel["stages"]["storyboard"]["batch_id"] for panel in reserved}, {"batch-001"})
            self.assertEqual(state["panels"][4]["stages"]["storyboard"]["status"], "pending")

    def test_imported_or_requested_items_block_next_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, panel_count=4)
            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            generated = generate_file(root)

            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-panel-1.png",
                "--stage",
                "storyboard",
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )

            result = run_cli_raw("next-batch", "--run-dir", str(run_dir), cwd=root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Resolve current batch before reserving another", result.stderr)

    def test_next_stage_waits_until_all_panels_pass_parent_inspection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, panel_count=5)
            generated = generate_file(root)

            run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            for index in range(1, 5):
                item = f"{index:03d}-panel-{index}.png"
                run_cli(
                    "import",
                    "--run-dir",
                    str(run_dir),
                    "--item",
                    item,
                    "--stage",
                    "storyboard",
                    "--generated",
                    str(generated),
                    "--worker-status",
                    "pass",
                    "--worker-note",
                    "worker pass",
                    cwd=root,
                )
                run_cli(
                    "inspect-pass",
                    "--run-dir",
                    str(run_dir),
                    "--item",
                    item,
                    "--stage",
                    "storyboard",
                    "--note",
                    "parent pass",
                    cwd=root,
                )

            remaining = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            self.assertIn("STAGE: storyboard", remaining.stdout)
            self.assertIn("005-panel-5.png", remaining.stdout)
            self.assertNotIn("STAGE: sketch_ink", remaining.stdout)

            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "005-panel-5.png",
                "--stage",
                "storyboard",
                "--generated",
                str(generated),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker pass",
                cwd=root,
            )
            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "005-panel-5.png",
                "--stage",
                "storyboard",
                "--note",
                "parent pass",
                cwd=root,
            )

            sketch = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            self.assertIn("STAGE: sketch_ink", sketch.stdout)
            self.assertEqual(sketch.stdout.count("ITEM: "), 4)

    def test_worker_needs_rerun_is_advisory_until_parent_decides(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, panel_count=1)
            generated = generate_file(root)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-panel-1.png",
                "--stage",
                "storyboard",
                "--generated",
                str(generated),
                "--worker-status",
                "needs_rerun",
                "--worker-note",
                "worker sees rough anatomy",
                cwd=root,
            )

            state = json.loads((run_dir / "state.json").read_text())
            first = state["panels"][0]["stages"]["storyboard"]
            self.assertEqual(first["status"], "imported")
            self.assertEqual(first["worker_status"], "needs_rerun")

            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-panel-1.png",
                "--stage",
                "storyboard",
                "--note",
                "parent accepts the rough storyboard",
                cwd=root,
            )
            state = json.loads((run_dir / "state.json").read_text())
            first = state["panels"][0]["stages"]["storyboard"]
            self.assertEqual(first["status"], "inspected_pass")
            self.assertEqual(first["worker_status"], "needs_rerun")

            run_cli(
                "rerun",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-panel-1.png",
                "--stage",
                "storyboard",
                "--note",
                "parent changed decision",
                cwd=root,
            )
            state = json.loads((run_dir / "state.json").read_text())
            first = state["panels"][0]["stages"]["storyboard"]
            self.assertEqual(first["status"], "pending")
            self.assertTrue(first["rerun_pending"])


if __name__ == "__main__":
    unittest.main()
