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
    / "create-video-closeup-reference-pack"
    / "scripts"
    / "video_pack_runner.py"
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


class VideoPackRunnerTest(unittest.TestCase):
    def test_init_creates_full_queue_and_reuses_incomplete_run_for_same_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.png"
            source.write_bytes(b"fake image")

            first = run_cli("init", "--source", str(source), cwd=root)
            first_state = json.loads((root / first.stdout.strip() / "state.json").read_text())

            self.assertEqual(first_state["workflow"], "create-video-closeup-reference-pack")
            self.assertEqual(first_state["anchor_policy"], "auto_if_pass")
            self.assertEqual(len(first_state["items"]), 18)
            self.assertEqual(first_state["items"][0]["output"], "01_face_front.png")
            self.assertEqual(first_state["items"][1]["output"], "02_03_face_3q_pair.png")
            self.assertEqual(first_state["items"][2]["output"], "04_05_face_side_pair.png")
            outputs = [item["output"] for item in first_state["items"]]
            self.assertIn("19_face_turnaround_sheet.png", outputs)
            self.assertIn("20_hand_gesture_four_sheet.png", outputs)
            self.assertNotIn("face_turnaround_sheet.png", outputs)
            self.assertNotIn("hand_gesture_four_sheet.png", outputs)
            self.assertTrue((root / first.stdout.strip() / "batch_plan.md").exists())
            batch_plan = (root / first.stdout.strip() / "batch_plan.md").read_text()
            self.assertIn("- output: 19_face_turnaround_sheet.png", batch_plan)
            self.assertIn("- output: 20_hand_gesture_four_sheet.png", batch_plan)

            second = run_cli("init", "--source", str(source), cwd=root)
            self.assertEqual(first.stdout.strip(), second.stdout.strip())

    def test_next_import_status_and_rerun_update_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.png"
            generated = root / "generated.png"
            source.write_bytes(b"fake image")
            generated.write_bytes(b"generated image")

            init = run_cli("init", "--source", str(source), cwd=root)
            run_dir = root / init.stdout.strip()

            next_result = run_cli("next", "--run-dir", str(run_dir), cwd=root)
            self.assertIn("01_face_front.png", next_result.stdout)
            state = json.loads((run_dir / "state.json").read_text())
            self.assertEqual(state["items"][0]["status"], "generation_requested")
            self.assertIsNotNone(state["items"][0]["requested_at"])

            import_result = run_cli(
                "import-latest",
                "--run-dir",
                str(run_dir),
                "--generated",
                str(generated),
                cwd=root,
            )
            self.assertIn("01_face_front.png", import_result.stdout)
            self.assertEqual((run_dir / "01_face_front.png").read_bytes(), b"generated image")
            state = json.loads((run_dir / "state.json").read_text())
            self.assertEqual(state["items"][0]["status"], "imported")
            self.assertEqual(state["items"][0]["generated_source"], str(generated.resolve()))

            inspect = run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "01_face_front.png",
                "--note",
                "visual inspection passed",
                cwd=root,
            )
            self.assertIn("01_face_front.png", inspect.stdout)
            state = json.loads((run_dir / "state.json").read_text())
            self.assertEqual(state["items"][0]["status"], "inspected_pass")
            self.assertEqual(state["items"][0]["inspection"]["note"], "visual inspection passed")

            status = run_cli("status", "--run-dir", str(run_dir), cwd=root)
            self.assertIn("generated: 1", status.stdout)
            self.assertIn("pending: 17", status.stdout)
            self.assertNotIn("complete: true", status.stdout)

            rerun = run_cli(
                "rerun",
                "--run-dir",
                str(run_dir),
                "--item",
                "01_face_front.png",
                cwd=root,
            )
            self.assertIn("01_face_front.png", rerun.stdout)
            state = json.loads((run_dir / "state.json").read_text())
            self.assertEqual(state["items"][0]["status"], "needs_rerun")

    def test_next_batch_blocks_dependents_until_anchor_passes_then_reserves_four(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.png"
            source.write_bytes(b"fake image")

            init = run_cli("init", "--source", str(source), cwd=root)
            run_dir = root / init.stdout.strip()

            first_batch = run_cli("next-batch", "--run-dir", str(run_dir), cwd=root)
            self.assertIn("items: 1", first_batch.stdout)
            self.assertIn("01_face_front.png", first_batch.stdout)
            self.assertNotIn("02_03_face_3q_pair.png", first_batch.stdout)
            state = json.loads((run_dir / "state.json").read_text())
            self.assertEqual(state["items"][0]["status"], "generation_requested")
            self.assertIsNotNone(state["items"][0]["batch_id"])
            self.assertIsNotNone(state["items"][0]["requested_at"])

            anchor = run_dir / "01_face_front.png"
            anchor.write_bytes(b"anchor")
            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "01_face_front.png",
                cwd=root,
            )

            second_batch = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            self.assertIn("items: 4", second_batch.stdout)
            self.assertIn("02_03_face_3q_pair.png", second_batch.stdout)
            self.assertIn("04_05_face_side_pair.png", second_batch.stdout)
            self.assertIn("06_eye_macro.png", second_batch.stdout)
            self.assertIn("07_expression_sheet.png", second_batch.stdout)

            state = json.loads((run_dir / "state.json").read_text())
            reserved = state["items"][1:5]
            self.assertTrue(all(item["status"] == "generation_requested" for item in reserved))
            self.assertEqual(len({item["batch_id"] for item in reserved}), 1)
            self.assertTrue(all(item["requested_at"] for item in reserved))
            self.assertEqual(state["items"][5]["status"], "pending")

    def test_next_rejects_dependent_serial_generation_after_anchor_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.png"
            source.write_bytes(b"fake image")

            init = run_cli("init", "--source", str(source), cwd=root)
            run_dir = root / init.stdout.strip()
            anchor = run_dir / "01_face_front.png"
            anchor.write_bytes(b"anchor")
            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "01_face_front.png",
                cwd=root,
            )

            next_result = run_cli_raw("next", "--run-dir", str(run_dir), cwd=root)
            self.assertNotEqual(next_result.returncode, 0)
            self.assertIn(
                "Anchor is approved; use next-batch --limit 4 and subagents for dependent items.",
                next_result.stderr,
            )

            state = json.loads((run_dir / "state.json").read_text())
            self.assertEqual(state["items"][1]["status"], "pending")
            self.assertIsNone(state["items"][1].get("requested_at"))

    def test_import_latest_rejects_dependent_serial_import_after_anchor_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.png"
            generated = root / "generated-dependent.png"
            source.write_bytes(b"fake image")
            generated.write_bytes(b"generated image")

            init = run_cli("init", "--source", str(source), cwd=root)
            run_dir = root / init.stdout.strip()
            state_path = run_dir / "state.json"
            state = json.loads(state_path.read_text())
            state["items"][0]["status"] = "inspected_pass"
            state["items"][1]["status"] = "generation_requested"
            state["items"][1]["requested_at"] = "2026-01-01T00:00:00+00:00"
            state_path.write_text(json.dumps(state, indent=2) + "\n")

            import_result = run_cli_raw(
                "import-latest",
                "--run-dir",
                str(run_dir),
                "--generated",
                str(generated),
                cwd=root,
            )
            self.assertNotEqual(import_result.returncode, 0)
            self.assertIn(
                "Anchor is approved; import dependent items with `import --item <filename> --generated <path>`.",
                import_result.stderr,
            )
            self.assertFalse((run_dir / "02_03_face_3q_pair.png").exists())

    def test_explicit_import_maps_parallel_outputs_and_parent_pass_controls_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.png"
            generated_a = root / "generated-a.png"
            generated_b = root / "generated-b.png"
            source.write_bytes(b"fake image")
            generated_a.write_bytes(b"generated image a")
            generated_b.write_bytes(b"generated image b")

            init = run_cli("init", "--source", str(source), cwd=root)
            run_dir = root / init.stdout.strip()
            state_path = run_dir / "state.json"
            state = json.loads(state_path.read_text())
            state["items"][0]["status"] = "inspected_pass"
            state_path.write_text(json.dumps(state, indent=2) + "\n")

            batch = run_cli("next-batch", "--run-dir", str(run_dir), "--limit", "4", cwd=root)
            batch_id = next(line.split(": ", 1)[1] for line in batch.stdout.splitlines() if line.startswith("batch_id: "))

            import_a = run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "02_03_face_3q_pair.png",
                "--generated",
                str(generated_a),
                "--worker-status",
                "pass",
                "--worker-note",
                "worker visual pass",
                cwd=root,
            )
            self.assertIn("worker_status: pass", import_a.stdout)

            run_cli(
                "import",
                "--run-dir",
                str(run_dir),
                "--item",
                "04_05_face_side_pair.png",
                "--generated",
                str(generated_b),
                "--worker-status",
                "needs_rerun",
                "--worker-note",
                "direction mismatch",
                cwd=root,
            )

            self.assertEqual((run_dir / "02_03_face_3q_pair.png").read_bytes(), b"generated image a")
            self.assertEqual((run_dir / "04_05_face_side_pair.png").read_bytes(), b"generated image b")
            state = json.loads(state_path.read_text())
            self.assertFalse(state["complete"])
            self.assertEqual(state["items"][1]["status"], "imported")
            self.assertEqual(state["items"][1]["worker_status"], "pass")
            self.assertEqual(state["items"][2]["worker_status"], "needs_rerun")

            status = run_cli("batch-status", "--run-dir", str(run_dir), "--batch-id", batch_id, cwd=root)
            self.assertIn("items: 4", status.stdout)
            self.assertIn("worker_pass: 1", status.stdout)
            self.assertIn("worker_needs_rerun: 1", status.stdout)

            run_cli(
                "rerun",
                "--run-dir",
                str(run_dir),
                "--item",
                "04_05_face_side_pair.png",
                "--note",
                "parent rejected direction",
                cwd=root,
            )
            status_after_rerun = run_cli("batch-status", "--run-dir", str(run_dir), "--batch-id", batch_id, cwd=root)
            self.assertIn("needs_rerun: 1", status_after_rerun.stdout)

            run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "02_03_face_3q_pair.png",
                "--note",
                "parent pass",
                cwd=root,
            )
            state = json.loads(state_path.read_text())
            self.assertEqual(state["items"][1]["status"], "inspected_pass")
            self.assertIsNotNone(state["items"][1]["parent_inspected_at"])
            self.assertFalse(state["complete"])

    def test_completion_status_and_next_when_all_items_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.png"
            source.write_bytes(b"fake image")

            init = run_cli("init", "--source", str(source), cwd=root)
            run_dir = root / init.stdout.strip()
            state_path = run_dir / "state.json"
            state = json.loads(state_path.read_text())
            for item in state["items"]:
                item["status"] = "complete"
            state_path.write_text(json.dumps(state, indent=2) + "\n")

            status = run_cli("status", "--run-dir", str(run_dir), cwd=root)
            self.assertIn("complete: true", status.stdout)

            next_result = run_cli("next", "--run-dir", str(run_dir), cwd=root)
            self.assertIn("No pending items", next_result.stdout)


if __name__ == "__main__":
    unittest.main()
