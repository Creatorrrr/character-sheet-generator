import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "scripts" / "character_closeup_pack_runner.py"


def run_cli(*args, cwd):
    return subprocess.run(
        [sys.executable, str(RUNNER), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
    )


class CharacterCloseupPackRunnerTest(unittest.TestCase):
    def test_init_creates_core_queue_and_reuses_same_source_preset_and_style(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.png"
            source.write_bytes(b"fake image")

            first = run_cli("init", "--source", str(source), "--preset", "core", cwd=root)
            run_dir = root / first.stdout.strip()
            first_state = json.loads((run_dir / "state.json").read_text())

            self.assertEqual(first_state["workflow"], "create-character-sheet-closeup-reference-pack")
            self.assertEqual(first_state["anchor_policy"], "auto_if_pass")
            self.assertEqual(first_state["style_mode"], "preserve_source_style")
            self.assertEqual(first_state["pack_preset"], "core")
            self.assertEqual(len(first_state["items"]), 10)
            self.assertEqual(first_state["items"][0]["output"], "01_face_front.png")
            self.assertEqual(first_state["items"][1]["output"], "02_03_face_3q_pair.png")
            self.assertEqual(first_state["items"][2]["output"], "04_05_face_side_pair.png")
            self.assertTrue((run_dir / "source_character_sheet.png").exists())
            self.assertTrue((run_dir / "batch_plan.md").exists())
            self.assertTrue((run_dir / "prompts" / "01_face_front.prompt.txt").exists())
            self.assertIn(
                "Use Codex built-in image_gen",
                (run_dir / "batch_plan.md").read_text(),
            )

            second = run_cli("init", "--source", str(source), "--preset", "core", cwd=root)
            self.assertEqual(first.stdout.strip(), second.stdout.strip())

    def test_init_full_preset_includes_core_and_full_extension_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.png"
            source.write_bytes(b"fake image")

            init = run_cli("init", "--source", str(source), "--preset", "full", cwd=root)
            run_dir = root / init.stdout.strip()
            state = json.loads((run_dir / "state.json").read_text())
            outputs = [item["output"] for item in state["items"]]

            self.assertEqual(state["pack_preset"], "full")
            self.assertEqual(len(outputs), 18)
            self.assertIn("01_face_front.png", outputs)
            self.assertIn("12_signature_props.png", outputs)
            self.assertIn("13_face_turnaround_sheet.png", outputs)
            self.assertIn("20_palette_motif_reference.png", outputs)

    def test_next_import_inspect_and_rerun_update_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.png"
            generated = root / "generated.png"
            source.write_bytes(b"fake image")
            generated.write_bytes(b"generated image")

            init = run_cli("init", "--source", str(source), "--preset", "core", cwd=root)
            run_dir = root / init.stdout.strip()

            next_result = run_cli("next", "--run-dir", str(run_dir), cwd=root)
            self.assertIn("01_face_front.png", next_result.stdout)
            self.assertIn("Codex built-in image_gen", next_result.stdout)
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

            status_before_inspection = run_cli("status", "--run-dir", str(run_dir), cwd=root)
            self.assertIn("generated: 0", status_before_inspection.stdout)
            self.assertIn("imported_uninspected: 1", status_before_inspection.stdout)

            blocked_next = run_cli("next", "--run-dir", str(run_dir), cwd=root)
            self.assertIn("Inspect or rerun the blocking item first", blocked_next.stdout)

            inspect = run_cli(
                "inspect-pass",
                "--run-dir",
                str(run_dir),
                "--item",
                "01_face_front.png",
                "--note",
                "style and identity pass",
                cwd=root,
            )
            self.assertIn("01_face_front.png", inspect.stdout)
            state = json.loads((run_dir / "state.json").read_text())
            self.assertEqual(state["items"][0]["status"], "inspected_pass")
            self.assertEqual(state["items"][0]["inspection"]["note"], "style and identity pass")

            status_after_inspection = run_cli("status", "--run-dir", str(run_dir), cwd=root)
            self.assertIn("generated: 1", status_after_inspection.stdout)
            self.assertIn("pending: 9", status_after_inspection.stdout)
            self.assertNotIn("complete: true", status_after_inspection.stdout)

            next_after_anchor = run_cli("next", "--run-dir", str(run_dir), cwd=root)
            self.assertIn("02_03_face_3q_pair.png", next_after_anchor.stdout)

            rerun = run_cli(
                "rerun",
                "--run-dir",
                str(run_dir),
                "--item",
                "01_face_front.png",
                "--note",
                "identity drift",
                cwd=root,
            )
            self.assertIn("01_face_front.png", rerun.stdout)
            state = json.loads((run_dir / "state.json").read_text())
            self.assertEqual(state["items"][0]["status"], "needs_rerun")
            self.assertEqual(state["items"][0]["inspection"]["note"], "identity drift")

    def test_completion_status_and_next_when_all_items_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.png"
            source.write_bytes(b"fake image")

            init = run_cli("init", "--source", str(source), "--preset", "core", cwd=root)
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
