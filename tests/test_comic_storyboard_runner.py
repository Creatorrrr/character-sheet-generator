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


def sample_page(page_index, panel_count=3):
    panels = []
    for panel_index in range(1, panel_count + 1):
        panels.append(
            {
                "id": f"{page_index:03d}-panel-{panel_index}",
                "panel_no": panel_index,
                "scene_refs": [f"S{page_index:02d}"],
                "beat": f"Story beat {page_index}-{panel_index}",
                "visual_brief": f"Comic panel visual brief {page_index}-{panel_index}",
                "setting": "school gym",
                "characters": ["main character"],
                "action": "shoots the basketball toward the hoop",
                "composition": "subject in foreground with hoop in background",
                "source_dialogue": [f"raw line {page_index}-{panel_index}"],
                "adapted_dialogue": [f"각색 대사 {page_index}-{panel_index}"],
                "sfx": ["휙"],
                "caption": ["방과 후 체육관"],
                "speech_balloon": "small balloon near the speaker",
                "sfx_placement": "near the moving basketball",
                "spatial_logic_notes": "ball travels from hand toward hoop",
                "motion_checks": ["basketball moves toward hoop, not behind shooter"],
                "must_match": ["hoop stays on far wall"],
                "prompt": f"Generate comic panel {page_index}-{panel_index}",
            }
        )
    return {
        "id": f"{page_index:03d}-page-{page_index}",
        "filename": f"{page_index:03d}-page-{page_index}.png",
        "page_no": page_index,
        "scene_refs": [f"S{page_index:02d}"],
        "layout_brief": "Three-panel Korean comic page with one wide top panel and two lower panels.",
        "reading_order": "top-to-bottom, left-to-right within rows",
        "page_dialogue_notes": "Adapt dialogue for comic timing; do not copy source lines verbatim.",
        "spatial_logic_notes": "Hoop remains on far wall; ball moves toward hoop after release.",
        "motion_checks": ["basketball shot trajectory follows the hand release toward the hoop"],
        "must_match": ["multi-panel comic page", "legible balloons and SFX"],
        "panels": panels,
        "references": [],
        "prompt": f"Generate complete comic page {page_index}",
    }


def sample_plan(page_count=5, panel_count=3):
    return {
        "scenario_title": "Gym Story",
        "style_brief": "clean cinematic Korean comic style",
        "reading_order": "top-to-bottom, left-to-right within rows",
        "pages": [sample_page(index, panel_count=panel_count) for index in range(1, page_count + 1)],
    }


def legacy_panel_plan(panel_count=2):
    panels = []
    for index in range(1, panel_count + 1):
        panels.append(
            {
                "id": f"{index:03d}-legacy-panel",
                "filename": f"{index:03d}-legacy-panel.png",
                "panel_no": index,
                "visual_brief": f"Legacy panel brief {index}",
                "prompt": f"Generate legacy panel {index}",
            }
        )
    return {"scenario_title": "Legacy Story", "panels": panels}


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


def approve_plan(root, run_dir, page_count=5, panel_count=3):
    plan_path = root / "plan.json"
    plan_path.write_text(json.dumps(sample_plan(page_count, panel_count), indent=2), encoding="utf-8")
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
            self.assertEqual(state["pages"], [])
            self.assertTrue((run_dir / "scenario.md").exists())
            self.assertTrue((run_dir / "prompts" / "storyboard").exists())
            self.assertTrue((run_dir / "01_storyboard").exists())

    def test_approve_plan_normalizes_pages_and_nested_panels(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)

            result = approve_plan(root, run_dir, page_count=2, panel_count=3)
            self.assertIn("APPROVED_PAGES: 2", result.stdout)
            state = json.loads((run_dir / "state.json").read_text())

            self.assertTrue(state["plan_approved"])
            self.assertEqual(len(state["pages"]), 2)
            first = state["pages"][0]
            self.assertEqual(first["id"], "001-page-1")
            self.assertEqual(first["filename"], "001-page-1.png")
            self.assertEqual(len(first["panels"]), 3)
            self.assertEqual(first["panels"][0]["adapted_dialogue"], ["각색 대사 1-1"])
            self.assertEqual(state["source_root"], "/Users/chasoik/Projects/character-sheet-generator/sources")
            self.assertEqual(state["excluded_source_roots"], ["/Users/chasoik/Projects/character-sheet-generator/output"])
            self.assertEqual(set(first["stages"].keys()), {"storyboard", "sketch_ink", "finish"})
            self.assertEqual(first["stages"]["storyboard"]["status"], "pending")
            self.assertTrue((run_dir / "approved_storyboard_plan.json").exists())
            self.assertTrue((run_dir / "batch_plan.md").exists())

    def test_approve_plan_rejects_output_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            plan = sample_plan(page_count=1)
            plan["pages"][0]["references"] = [
                "/Users/chasoik/Projects/character-sheet-generator/output/failed-page.png"
            ]
            plan_path = root / "plan-output-ref.json"
            plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

            result = run_cli_raw("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_path), cwd=root)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Reference path is under output/", result.stderr)
            self.assertIn("cannot be used as source data", result.stderr)

    def test_legacy_flat_panels_are_converted_to_single_panel_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            plan_path = root / "legacy-plan.json"
            plan_path.write_text(json.dumps(legacy_panel_plan(), indent=2), encoding="utf-8")

            run_cli("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_path), cwd=root)
            state = json.loads((run_dir / "state.json").read_text())

            self.assertEqual(len(state["pages"]), 2)
            self.assertEqual(len(state["pages"][0]["panels"]), 1)
            self.assertNotIn("panels", state)

    def test_next_batch_requires_approved_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)

            result = run_cli_raw("next-batch", "--run-dir", str(run_dir), cwd=root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Plan is not approved", result.stderr)

    def test_next_batch_reserves_at_most_four_current_stage_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=5)

            result = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "10", cwd=root)
            self.assertIn("STAGE: storyboard", result.stdout)
            self.assertEqual(result.stdout.count("ITEM: "), 4)
            state = json.loads((run_dir / "state.json").read_text())
            reserved = [
                page
                for page in state["pages"]
                if page["stages"]["storyboard"]["status"] == "generation_requested"
            ]
            self.assertEqual(len(reserved), 4)
            self.assertEqual({page["stages"]["storyboard"]["batch_id"] for page in reserved}, {"batch-001"})
            self.assertEqual(state["pages"][4]["stages"]["storyboard"]["status"], "pending")

    def test_prompt_contains_page_text_and_spatial_motion_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=1, panel_count=3)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            state = json.loads((run_dir / "state.json").read_text())
            prompt_path = Path(state["pages"][0]["stages"]["storyboard"]["prompt_file"])
            prompt = prompt_path.read_text(encoding="utf-8")

            self.assertIn("one complete Korean comic-book page image with multiple panels", prompt)
            self.assertIn("Use adapted_dialogue", prompt)
            self.assertIn("각색 대사 1-1", prompt)
            self.assertIn("휙", prompt)
            self.assertIn("ball moves toward hoop after release", prompt)
            self.assertIn("basketball moves toward hoop, not behind shooter", prompt)
            self.assertIn("No examples of impossible staging", prompt)

    def test_prompt_uses_sources_by_default_and_excludes_output_source_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=1, panel_count=2)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            state = json.loads((run_dir / "state.json").read_text())
            prompt_path = Path(state["pages"][0]["stages"]["storyboard"]["prompt_file"])
            prompt = prompt_path.read_text(encoding="utf-8")
            batch_plan = (run_dir / "batch_plan.md").read_text(encoding="utf-8")

            self.assertIn("Default source data folder:", prompt)
            self.assertIn("/Users/chasoik/Projects/character-sheet-generator/sources", prompt)
            self.assertIn("Output source exclusion:", prompt)
            self.assertIn("Do not use /Users/chasoik/Projects/character-sheet-generator/output", prompt)
            self.assertIn("Only the current run's parent-inspected prior-stage reference", prompt)
            self.assertIn("default source data folder", batch_plan)
            self.assertIn("Do not use /Users/chasoik/Projects/character-sheet-generator/output", batch_plan)

    def test_imported_or_requested_pages_block_next_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=4)
            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            generated = generate_file(root)

            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
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

    def test_next_stage_waits_until_all_pages_pass_parent_inspection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=5)
            generated = generate_file(root)

            run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            for index in range(1, 5):
                item = f"{index:03d}-page-{index}.png"
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
            self.assertIn("005-page-5.png", remaining.stdout)
            self.assertNotIn("STAGE: sketch_ink", remaining.stdout)

            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "005-page-5.png",
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
                "005-page-5.png",
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
            approve_plan(root, run_dir, page_count=1)
            generated = generate_file(root)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                "storyboard",
                "--generated",
                str(generated),
                "--worker-status",
                "needs_rerun",
                "--worker-note",
                "worker sees impossible ball trajectory",
                cwd=root,
            )

            state = json.loads((run_dir / "state.json").read_text())
            first = state["pages"][0]["stages"]["storyboard"]
            self.assertEqual(first["status"], "imported")
            self.assertEqual(first["worker_status"], "needs_rerun")

            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                "storyboard",
                "--note",
                "parent accepts after inspection",
                cwd=root,
            )
            state = json.loads((run_dir / "state.json").read_text())
            first = state["pages"][0]["stages"]["storyboard"]
            self.assertEqual(first["status"], "inspected_pass")
            self.assertEqual(first["worker_status"], "needs_rerun")

            run_cli(
                "rerun",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                "storyboard",
                "--note",
                "parent changed decision",
                cwd=root,
            )
            state = json.loads((run_dir / "state.json").read_text())
            first = state["pages"][0]["stages"]["storyboard"]
            self.assertEqual(first["status"], "pending")
            self.assertTrue(first["rerun_pending"])


if __name__ == "__main__":
    unittest.main()
