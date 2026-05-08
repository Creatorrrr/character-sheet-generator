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
FIRST_STAGE = "storyboard_sketch_ink"
FINISH_STAGE = "finish"


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
                "detail_density_notes": "detail the hand, ball, hoop rim, and face; simplify the far wall",
                "visual_emphasis_notes": "use stronger line weight on the shooter and ball, lighter background lines",
                "comic_effects_notes": "speed lines follow the ball toward the hoop and focus lines guide the eye to the rim",
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
        "layout_brief": "Three-panel cinematic Korean comic page with one wide open top panel and two asymmetric lower panels.",
        "reading_order": "top-to-bottom, left-to-right within rows",
        "pacing_notes": "3-5 panels by default with measured cinematic pacing.",
        "panel_shape_notes": "Use experimental freeform panel design with diagonal, asymmetric, inset, or borderless panels.",
        "negative_space_notes": "Leave wide negative space around faces, ball motion, balloons, and quiet reaction beats.",
        "detail_density_notes": "Keep the shooter, ball, hoop, and hand details crisp; simplify distant bleachers.",
        "visual_emphasis_notes": "Strongest visual emphasis goes to the shot release and final reaction closeup.",
        "comic_effects_notes": "Use speed lines on the ball, subtle focus lines toward the hoop, and small impact lines on rim contact.",
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


def stage_record(status, output_path=""):
    return {
        "status": status,
        "attempts": 1 if status != "pending" else 0,
        "rerun_pending": False,
        "batch_id": "",
        "prompt_file": "",
        "output_path": output_path,
        "generated_source": "",
        "worker_status": "pass" if status != "pending" else "",
        "worker_note": "",
        "parent_note": "parent pass" if status != "pending" else "",
    }


class ComicStoryboardRunnerTest(unittest.TestCase):
    def test_init_creates_approval_gated_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            state = json.loads((run_dir / "state.json").read_text())

            self.assertEqual(state["workflow"], "create-comic-storyboard-pack")
            self.assertFalse(state["plan_approved"])
            self.assertEqual(state["stage_order"], [FIRST_STAGE, FINISH_STAGE])
            self.assertEqual(state["pages"], [])
            self.assertTrue((run_dir / "scenario.md").exists())
            self.assertTrue((run_dir / "prompts" / FIRST_STAGE).exists())
            self.assertTrue((run_dir / "prompts" / FINISH_STAGE).exists())
            self.assertTrue((run_dir / "01_storyboard_sketch_ink").exists())
            self.assertTrue((run_dir / "02_finish").exists())
            self.assertEqual(state["stage_reviews"][FIRST_STAGE]["status"], "pending")
            self.assertEqual(state["stage_reviews"][FINISH_STAGE]["status"], "pending")

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
            self.assertEqual(first["pacing_notes"], "3-5 panels by default with measured cinematic pacing.")
            self.assertIn("experimental freeform panel design", first["panel_shape_notes"])
            self.assertIn("wide negative space", first["negative_space_notes"])
            self.assertIn("shooter, ball, hoop", first["detail_density_notes"])
            self.assertIn("shot release", first["visual_emphasis_notes"])
            self.assertIn("speed lines", first["comic_effects_notes"])
            self.assertIn("hand, ball, hoop rim", first["panels"][0]["detail_density_notes"])
            self.assertIn("stronger line weight", first["panels"][0]["visual_emphasis_notes"])
            self.assertIn("focus lines", first["panels"][0]["comic_effects_notes"])
            self.assertEqual(state["source_root"], "/Users/chasoik/Projects/character-sheet-generator/sources")
            self.assertEqual(state["excluded_source_roots"], ["/Users/chasoik/Projects/character-sheet-generator/output"])
            self.assertEqual(set(first["stages"].keys()), {FIRST_STAGE, FINISH_STAGE})
            self.assertEqual(first["stages"][FIRST_STAGE]["status"], "pending")
            self.assertEqual(set(state["stage_reviews"].keys()), {FIRST_STAGE, FINISH_STAGE})
            self.assertEqual(state["stage_reviews"][FIRST_STAGE]["status"], "pending")
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
            self.assertIn(f"STAGE: {FIRST_STAGE}", result.stdout)
            self.assertEqual(result.stdout.count("ITEM: "), 4)
            state = json.loads((run_dir / "state.json").read_text())
            reserved = [
                page
                for page in state["pages"]
                if page["stages"][FIRST_STAGE]["status"] == "generation_requested"
            ]
            self.assertEqual(len(reserved), 4)
            self.assertEqual({page["stages"][FIRST_STAGE]["batch_id"] for page in reserved}, {"batch-001"})
            self.assertEqual(state["pages"][4]["stages"][FIRST_STAGE]["status"], "pending")

    def test_legacy_stage_names_are_not_cli_choices(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=1)
            generated = generate_file(root)
            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)

            result = run_cli_raw(
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

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid choice", result.stderr)
            self.assertIn(FIRST_STAGE, result.stderr)

    def test_prompt_contains_page_text_and_spatial_motion_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=1, panel_count=3)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            state = json.loads((run_dir / "state.json").read_text())
            prompt_path = Path(state["pages"][0]["stages"][FIRST_STAGE]["prompt_file"])
            prompt = prompt_path.read_text(encoding="utf-8")

            self.assertIn("one complete Korean comic-book page image with 3-5 panels by default", prompt)
            self.assertIn("measured cinematic pacing", prompt)
            self.assertIn("Use 1-2 panels for special staging", prompt)
            self.assertIn("Requires explicit story justification for six or more panels", prompt)
            self.assertIn("experimental freeform panel design", prompt)
            self.assertIn("Avoid a uniform rectangular grid", prompt)
            self.assertIn("unintentional uniform rectangular grids", prompt)
            self.assertIn("dialogue/SFX without breathing room", prompt)
            self.assertIn("Comic visual direction:", prompt)
            self.assertIn("detail density", prompt)
            self.assertIn("visual emphasis", prompt)
            self.assertIn("speed lines", prompt)
            self.assertIn("focus lines", prompt)
            self.assertIn("impact bursts", prompt)
            self.assertIn("emotion lines", prompt)
            self.assertIn("effect-line direction must match action direction", prompt)
            self.assertIn("same flat visual intensity", prompt)
            self.assertIn("Use adapted_dialogue", prompt)
            self.assertIn("각색 대사 1-1", prompt)
            self.assertIn("휙", prompt)
            self.assertIn("ball moves toward hoop after release", prompt)
            self.assertIn("basketball moves toward hoop, not behind shooter", prompt)
            self.assertIn("No examples of impossible staging", prompt)
            self.assertIn("Source consistency checklist:", prompt)
            self.assertIn("Panel and page continuity checklist:", prompt)

    def test_prompt_uses_sources_by_default_and_excludes_output_source_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=1, panel_count=2)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            state = json.loads((run_dir / "state.json").read_text())
            prompt_path = Path(state["pages"][0]["stages"][FIRST_STAGE]["prompt_file"])
            prompt = prompt_path.read_text(encoding="utf-8")
            batch_plan = (run_dir / "batch_plan.md").read_text(encoding="utf-8")

            self.assertIn("Default source data folder:", prompt)
            self.assertIn("/Users/chasoik/Projects/character-sheet-generator/sources", prompt)
            self.assertIn("Output source exclusion:", prompt)
            self.assertIn("Do not use /Users/chasoik/Projects/character-sheet-generator/output", prompt)
            self.assertIn("Only the current run's parent-inspected prior-stage reference", prompt)
            self.assertIn("default source data folder", batch_plan)
            self.assertIn("Do not use /Users/chasoik/Projects/character-sheet-generator/output", batch_plan)
            self.assertIn("Stage reviews:", batch_plan)
            self.assertIn("Stage finish review checks source consistency", batch_plan)
            self.assertIn("3-5 panels by default", batch_plan)
            self.assertIn("1-2 panels for special staging", batch_plan)
            self.assertIn("six or more panels", batch_plan)
            self.assertIn("experimental freeform panel design", batch_plan)
            self.assertIn("negative_space:", batch_plan)
            self.assertIn("comic visual direction", batch_plan)
            self.assertIn("detail_density:", batch_plan)
            self.assertIn("visual_emphasis:", batch_plan)
            self.assertIn("comic_effects:", batch_plan)

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
                FIRST_STAGE,
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
                    FIRST_STAGE,
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
                    FIRST_STAGE,
                    "--note",
                    "parent pass",
                    cwd=root,
                )

            remaining = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            self.assertIn(f"STAGE: {FIRST_STAGE}", remaining.stdout)
            self.assertIn("005-page-5.png", remaining.stdout)
            self.assertNotIn(f"STAGE: {FINISH_STAGE}", remaining.stdout)

            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "005-page-5.png",
                "--stage",
                FIRST_STAGE,
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
                FIRST_STAGE,
                "--note",
                "parent pass",
                cwd=root,
            )

            blocked = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            self.assertIn(f"STAGE_REVIEW_REQUIRED: {FIRST_STAGE}", blocked.stdout)
            self.assertNotIn(f"STAGE: {FINISH_STAGE}", blocked.stdout)

            run_cli(
                "stage-review",
                "--run-dir",
                str(run_dir),
                "--stage",
                FIRST_STAGE,
                "--status",
                "pass",
                "--note",
                "source consistency and panel continuity pass",
                cwd=root,
            )
            finish = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            self.assertIn(f"STAGE: {FINISH_STAGE}", finish.stdout)
            self.assertEqual(finish.stdout.count("ITEM: "), 4)

    def test_finish_prompt_uses_first_stage_image_as_required_input(self):
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
                FIRST_STAGE,
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
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--note",
                "parent pass",
                cwd=root,
            )
            run_cli(
                "stage-review",
                "--run-dir",
                str(run_dir),
                "--stage",
                FIRST_STAGE,
                "--status",
                "pass",
                "--note",
                "first stage final review pass",
                cwd=root,
            )

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            state = json.loads((run_dir / "state.json").read_text())
            prompt_path = Path(state["pages"][0]["stages"][FINISH_STAGE]["prompt_file"])
            prompt = prompt_path.read_text(encoding="utf-8")
            first_stage_output = run_dir / "01_storyboard_sketch_ink" / "001-page-1.png"

            self.assertTrue(first_stage_output.exists())
            self.assertIn(str(first_stage_output), prompt)
            self.assertIn("required visual input / structure reference", prompt)
            self.assertIn("Do not redraw the page from scratch", prompt)
            self.assertIn("preserve the inspected storyboard_sketch_ink visual emphasis", prompt)
            self.assertIn("effect-line direction", prompt)
            self.assertIn("ink rhythm", prompt)

    def test_stage_review_pass_requires_all_pages_parent_inspected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=2)
            generated = generate_file(root)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
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
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--note",
                "parent pass",
                cwd=root,
            )

            result = run_cli_raw(
                "stage-review",
                "--run-dir",
                str(run_dir),
                "--stage",
                FIRST_STAGE,
                "--status",
                "pass",
                "--note",
                "not ready",
                cwd=root,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Stage review requires every page", result.stderr)

    def test_stage_review_needs_rerun_marks_items_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            approve_plan(root, run_dir, page_count=2)
            generated = generate_file(root)

            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            for index in range(1, 3):
                item = f"{index:03d}-page-{index}.png"
                run_cli(
                    "import",
                    "--run-dir",
                    str(run_dir),
                    "--item",
                    item,
                    "--stage",
                    FIRST_STAGE,
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
                    FIRST_STAGE,
                    "--note",
                    "parent pass",
                    cwd=root,
                )

            run_cli(
                "stage-review",
                "--run-dir",
                str(run_dir),
                "--stage",
                FIRST_STAGE,
                "--status",
                "needs_rerun",
                "--note",
                "character source consistency drift on page 2",
                "--issue",
                "page 2 character hair and prop shape drift from sources",
                "--rerun-item",
                "002-page-2.png",
                cwd=root,
            )
            state = json.loads((run_dir / "state.json").read_text())
            second = state["pages"][1]["stages"][FIRST_STAGE]

            self.assertEqual(state["stage_reviews"][FIRST_STAGE]["status"], "needs_rerun")
            self.assertEqual(second["status"], "pending")
            self.assertTrue(second["rerun_pending"])
            self.assertIn("page 2 character hair", state["stage_reviews"][FIRST_STAGE]["issues"][0])

            next_batch = run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            self.assertIn("002-page-2.png", next_batch.stdout)
            self.assertNotIn(f"STAGE: {FINISH_STAGE}", next_batch.stdout)

    def test_finish_stage_review_required_before_workflow_complete(self):
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
                FIRST_STAGE,
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
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--note",
                "parent pass",
                cwd=root,
            )
            run_cli(
                "stage-review",
                "--run-dir",
                str(run_dir),
                "--stage",
                FIRST_STAGE,
                "--status",
                "pass",
                "--note",
                "first stage continuity pass",
                cwd=root,
            )
            run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FINISH_STAGE,
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
                "001-page-1.png",
                "--stage",
                FINISH_STAGE,
                "--note",
                "parent pass",
                cwd=root,
            )

            status_before = run_cli("status", "--run-dir", str(run_dir), cwd=root)
            self.assertIn(f"CURRENT_STAGE: {FINISH_STAGE}", status_before.stdout)
            self.assertIn("finish_review: pending", status_before.stdout)
            self.assertIn("COMPLETE: false", status_before.stdout)

            run_cli(
                "stage-review",
                "--run-dir",
                str(run_dir),
                "--stage",
                FINISH_STAGE,
                "--status",
                "pass",
                "--note",
                "final source consistency and continuity pass",
                cwd=root,
            )
            status_after = run_cli("status", "--run-dir", str(run_dir), cwd=root)
            self.assertIn("CURRENT_STAGE: complete", status_after.stdout)
            self.assertIn("finish_review: passed", status_after.stdout)
            self.assertIn("COMPLETE: true", status_after.stdout)

    def test_finish_batch_fails_when_first_stage_output_file_is_missing(self):
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
                FIRST_STAGE,
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
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--note",
                "parent pass",
                cwd=root,
            )
            run_cli(
                "stage-review",
                "--run-dir",
                str(run_dir),
                "--stage",
                FIRST_STAGE,
                "--status",
                "pass",
                "--note",
                "first stage final review pass",
                cwd=root,
            )
            first_stage_output = run_dir / "01_storyboard_sketch_ink" / "001-page-1.png"
            first_stage_output.unlink()

            result = run_cli_raw("next-batch", "--run-dir", str(run_dir), cwd=root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Finish stage requires the parent-inspected storyboard_sketch_ink image", result.stderr)
            self.assertIn(str(first_stage_output), result.stderr)

            state = json.loads((run_dir / "state.json").read_text())
            self.assertEqual(state["pages"][0]["stages"][FINISH_STAGE]["status"], "pending")

    def test_old_three_stage_state_is_migrated_conservatively(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = init_run(root)
            state = json.loads((run_dir / "state.json").read_text())
            page_one = sample_page(1)
            page_two = sample_page(2)
            page_one["stages"] = {
                "storyboard": stage_record("inspected_pass"),
                "sketch_ink": stage_record("inspected_pass"),
                "finish": stage_record("pending"),
            }
            page_two["stages"] = {
                "storyboard": stage_record("inspected_pass"),
                "sketch_ink": stage_record("pending"),
                "finish": stage_record("pending"),
            }
            state["plan_approved"] = True
            state["stage_order"] = ["storyboard", "sketch_ink", "finish"]
            state["pages"] = [page_one, page_two]
            (run_dir / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")

            result = run_cli("status", "--run-dir", str(run_dir), cwd=root)

            self.assertIn(f"CURRENT_STAGE: {FIRST_STAGE}", result.stdout)
            self.assertIn(f"{FIRST_STAGE}: inspected_pass=1, pending=1", result.stdout)
            self.assertIn(f"{FINISH_STAGE}: pending=2", result.stdout)

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
                FIRST_STAGE,
                "--generated",
                str(generated),
                "--worker-status",
                "needs_rerun",
                "--worker-note",
                "worker sees impossible ball trajectory",
                cwd=root,
            )

            state = json.loads((run_dir / "state.json").read_text())
            first = state["pages"][0]["stages"][FIRST_STAGE]
            self.assertEqual(first["status"], "imported")
            self.assertEqual(first["worker_status"], "needs_rerun")

            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--note",
                "parent accepts after inspection",
                cwd=root,
            )
            state = json.loads((run_dir / "state.json").read_text())
            first = state["pages"][0]["stages"][FIRST_STAGE]
            self.assertEqual(first["status"], "inspected_pass")
            self.assertEqual(first["worker_status"], "needs_rerun")

            run_cli(
                "rerun",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-page-1.png",
                "--stage",
                FIRST_STAGE,
                "--note",
                "parent changed decision",
                cwd=root,
            )
            state = json.loads((run_dir / "state.json").read_text())
            first = state["pages"][0]["stages"][FIRST_STAGE]
            self.assertEqual(first["status"], "pending")
            self.assertTrue(first["rerun_pending"])


if __name__ == "__main__":
    unittest.main()
