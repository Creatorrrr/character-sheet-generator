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
    / "create-video-scenario-image-pack"
    / "scripts"
    / "video_scenario_image_pack_runner.py"
)


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(RUNNER), *args],
        text=True,
        capture_output=True,
        check=True,
    )


def run_cli_raw(*args):
    return subprocess.run(
        [sys.executable, str(RUNNER), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def run_dir_from(stdout):
    for line in stdout.splitlines():
        if line.startswith("RUN_DIR: "):
            return Path(line.split(": ", 1)[1])
    raise AssertionError(f"RUN_DIR missing from output:\n{stdout}")


def base_item(item_id, filename, *, anchor="", deps=None, category="set_detail"):
    return {
        "id": item_id,
        "filename": filename,
        "scene_refs": ["S01"],
        "category": category,
        "contains_character": False,
        "purpose": f"Purpose for {filename}",
        "visual_brief": f"Empty sunset court source for {filename}",
        "spatial_group": "basketball-court-sunset",
        "continuity_anchor": anchor,
        "fixed_layout_notes": "Hoop far/right, gate and bench left, blank masonry wall, no people or vehicles.",
        "camera_view": "wide reference",
        "must_match": ["no people", "no cars", "no silhouettes"],
        "prompt": f"Photoreal empty no-character source for {filename}.",
        "negative_prompt": "",
        "dependencies": deps or [],
        "notes": "",
    }


def sample_plan():
    return {
        "scenario_title": "Noeul Court",
        "items": [
            base_item(
                "001-court-master",
                "001-court-master.png",
                category="location_master",
            ),
            base_item(
                "002-hoop-detail",
                "002-hoop-detail.png",
                anchor="001-court-master",
            ),
            base_item(
                "003-ball-prop",
                "003-ball-prop.png",
                deps=["001-court-master"],
                category="prop",
            ),
        ],
    }


class VideoScenarioImagePackRunnerTest(unittest.TestCase):
    def init_run(self, root):
        scenario = root / "scenario.md"
        scenario.write_text("# Noeul Court\n\nEmpty sunset basketball court.", encoding="utf-8")
        result = run_cli(
            "init",
            "--title",
            "Noeul Court",
            "--scenario",
            str(scenario),
            "--output-root",
            str(root / "output"),
        )
        return run_dir_from(result.stdout)

    def approve_plan(self, run_dir):
        plan_file = run_dir / "plan.json"
        plan_file.write_text(json.dumps(sample_plan()), encoding="utf-8")
        run_cli("approve-plan", "--run-dir", str(run_dir), "--plan-file", str(plan_file))
        return plan_file

    def import_item(self, run_dir, filename, content=b"generated"):
        generated = run_dir / f"generated-{filename}"
        generated.write_bytes(content)
        run_cli(
            "import",
            "--run-dir",
            str(run_dir),
            "--item",
            filename,
            "--generated",
            str(generated),
            "--worker-status",
            "pass",
            "--worker-note",
            "worker pass",
        )

    def inspect_pass(self, run_dir, filename, note="parent pass"):
        run_cli(
            "inspect-pass",
            "--run-dir",
            str(run_dir),
            "--item",
            filename,
            "--note",
            note,
        )

    def test_next_batch_blocks_until_plan_is_approved(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self.init_run(Path(tmp))

            result = run_cli_raw("next-batch", "--run-dir", str(run_dir), "--limit", "4")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Plan is not approved", result.stderr)

    def test_continuity_anchor_becomes_dependency_and_blocks_dependent_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self.init_run(Path(tmp))
            self.approve_plan(run_dir)

            state = json.loads((run_dir / "state.json").read_text())
            hoop = next(item for item in state["items"] if item["id"] == "002-hoop-detail")
            self.assertEqual(hoop["dependencies"], ["001-court-master"])

            batch = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4")
            self.assertIn("BATCH_ID: batch-001", batch.stdout)
            self.assertIn("ITEM: 001-court-master.png", batch.stdout)
            self.assertNotIn("002-hoop-detail.png", batch.stdout)

    def test_rerun_reserves_item_before_other_pending_dependents_and_adds_prompt_hints(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self.init_run(Path(tmp))
            self.approve_plan(run_dir)
            run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4")
            self.import_item(run_dir, "001-court-master.png")
            self.inspect_pass(run_dir, "001-court-master.png", "anchor pass")

            first_dependent = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "1")
            self.assertIn("ITEM: 002-hoop-detail.png", first_dependent.stdout)
            self.import_item(run_dir, "002-hoop-detail.png")
            run_cli(
                "rerun",
                "--run-dir",
                str(run_dir),
                "--item",
                "002-hoop-detail.png",
                "--note",
                "background silhouette and car visible",
            )

            rerun_batch = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "2")

            self.assertIn("ITEM: 002-hoop-detail.png", rerun_batch.stdout)
            self.assertNotIn("003-ball-prop.png", rerun_batch.stdout.split("ITEM: 002-hoop-detail.png", 1)[0])
            state = json.loads((run_dir / "state.json").read_text())
            hoop = next(item for item in state["items"] if item["id"] == "002-hoop-detail")
            self.assertIn("background silhouette and car visible", hoop["rerun_prompt_hints"])
            prompt_text = Path(hoop["prompt_file"]).read_text()
            self.assertIn("Rerun prompt hints", prompt_text)
            self.assertIn("background silhouette and car visible", prompt_text)

    def test_import_batch_and_inspect_batch_pass_apply_sequentially(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self.init_run(Path(tmp))
            self.approve_plan(run_dir)
            run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4")
            self.import_item(run_dir, "001-court-master.png")
            self.inspect_pass(run_dir, "001-court-master.png", "anchor pass")

            run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4")
            generated_a = run_dir / "generated-hoop.png"
            generated_b = run_dir / "generated-ball.png"
            generated_a.write_bytes(b"hoop")
            generated_b.write_bytes(b"ball")
            import_manifest = run_dir / "import-manifest.json"
            import_manifest.write_text(
                json.dumps(
                    {
                        "run_dir": str(run_dir),
                        "items": [
                            {
                                "item": "002-hoop-detail.png",
                                "generated": str(generated_a),
                                "worker_status": "pass",
                                "worker_note": "worker hoop pass",
                            },
                            {
                                "item": "003-ball-prop.png",
                                "generated": str(generated_b),
                                "worker_status": "pass",
                                "worker_note": "worker ball pass",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            import_result = run_cli("import-batch", "--manifest", str(import_manifest))

            self.assertIn("IMPORTED: 2", import_result.stdout)
            self.assertEqual((run_dir / "002-hoop-detail.png").read_bytes(), b"hoop")
            self.assertEqual((run_dir / "003-ball-prop.png").read_bytes(), b"ball")

            inspect_manifest = run_dir / "inspect-manifest.json"
            inspect_manifest.write_text(
                json.dumps(
                    {
                        "run_dir": str(run_dir),
                        "items": [
                            {"item": "002-hoop-detail.png", "note": "parent hoop pass"},
                            {"item": "003-ball-prop.png", "note": "parent ball pass"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            inspect_result = run_cli("inspect-batch-pass", "--manifest", str(inspect_manifest))

            self.assertIn("INSPECTED_PASS: 2", inspect_result.stdout)
            state = json.loads((run_dir / "state.json").read_text())
            self.assertTrue(all(item["status"] == "inspected_pass" for item in state["items"]))

    def test_batch_prompts_writes_ready_to_spawn_subagent_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self.init_run(Path(tmp))
            self.approve_plan(run_dir)
            batch = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4")
            batch_id = next(line.split(": ", 1)[1] for line in batch.stdout.splitlines() if line.startswith("BATCH_ID: "))

            prompts = run_cli("batch-prompts", "--run-dir", str(run_dir), "--batch-id", batch_id)

            self.assertIn("SUBAGENT_PROMPT:", prompts.stdout)
            state = json.loads((run_dir / "state.json").read_text())
            anchor = next(item for item in state["items"] if item["id"] == "001-court-master")
            self.assertTrue(Path(anchor["artifact_paths"]["subagent_prompt"]).exists())
            subagent_prompt = Path(anchor["artifact_paths"]["subagent_prompt"]).read_text()
            self.assertIn("You are generating exactly one image", subagent_prompt)
            self.assertIn("Do not edit state.json", subagent_prompt)

    def test_report_summarizes_completion_and_reruns_in_korean(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = self.init_run(Path(tmp))
            self.approve_plan(run_dir)
            run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4")
            self.import_item(run_dir, "001-court-master.png")
            run_cli(
                "rerun",
                "--run-dir",
                str(run_dir),
                "--item",
                "001-court-master.png",
                "--note",
                "tiny background silhouette",
            )

            report = run_cli("report", "--run-dir", str(run_dir))

            self.assertIn("[영상 시나리오 이미지 팩 진행 결과]", report.stdout)
            self.assertIn("승인된 이미지 수: 3", report.stdout)
            self.assertIn("rerun 필요/진행 항목: 1", report.stdout)
            self.assertIn("현재 차단 항목: 없음", report.stdout)


if __name__ == "__main__":
    unittest.main()
