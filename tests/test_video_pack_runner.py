import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "scripts" / "video_pack_runner.py"


def run_cli(*args, cwd):
    return subprocess.run(
        [sys.executable, str(RUNNER), *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
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
            self.assertTrue((root / first.stdout.strip() / "batch_plan.md").exists())

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
