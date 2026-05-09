import base64
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    Image = None


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    REPO_ROOT
    / ".agents"
    / "skills"
    / "review-image-overlays"
    / "scripts"
    / "review_overlay_server.py"
)
FIRST_STAGE = "storyboard_sketch_ink"
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)
PNG_DATA_URL = "data:image/png;base64," + base64.b64encode(PNG_BYTES).decode("ascii")


spec = importlib.util.spec_from_file_location("review_overlay_server", SCRIPT)
review_overlay_server = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(review_overlay_server)


def make_run(root, size=(1, 1)):
    run_dir = root / "run"
    stage_dir = run_dir / "01_storyboard_sketch_ink"
    stage_dir.mkdir(parents=True)
    image = stage_dir / "001-page-1.png"
    if Image:
        Image.new("RGBA", size, (255, 255, 255, 255)).save(image)
    else:
        image.write_bytes(PNG_BYTES)
    state = {
        "workflow": "create-comic-storyboard-pack",
        "pages": [
            {
                "id": "001-page-1",
                "filename": "001-page-1.png",
                "page_no": 1,
                "stages": {
                    FIRST_STAGE: {
                        "status": "inspected_pass",
                        "output_path": str(image),
                    }
                },
            }
        ],
    }
    (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
    return run_dir


class ReviewImageOverlayTest(unittest.TestCase):
    def test_save_review_payload_writes_color_specific_artifacts_and_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = make_run(root)
            payload = {
                "stage": FIRST_STAGE,
                "items": [
                    {
                        "filename": "001-page-1.png",
                        "overlays": [
                            {
                                "color_id": "red",
                                "color": "#ff3b30",
                                "request": "Make this hand smaller.",
                                "data_url": PNG_DATA_URL,
                            },
                            {
                                "color_id": "blue",
                                "color": "#1d4ed8",
                                "request": "Move the speech balloon up.",
                                "data_url": PNG_DATA_URL,
                            },
                        ],
                        "combined_data_url": PNG_DATA_URL,
                    }
                ],
            }

            manifest = review_overlay_server.save_review_payload(
                run_dir,
                FIRST_STAGE,
                payload,
                review_id="manual-review",
            )

            review_dir = run_dir / "review_overlays" / FIRST_STAGE / "manual-review"
            self.assertEqual(manifest["revision_count"], 2)
            self.assertTrue((review_dir / "001-page-1_overlay_red.png").exists())
            self.assertTrue((review_dir / "001-page-1_overlay_red.txt").exists())
            self.assertTrue((review_dir / "001-page-1_overlay_blue.png").exists())
            self.assertTrue((review_dir / "001-page-1_overlay_blue.txt").exists())
            self.assertTrue((review_dir / "001-page-1_overlay_combined.png").exists())
            self.assertTrue((review_dir / "revision_requests.json").exists())
            self.assertTrue((review_dir / "revision_requests.md").exists())
            self.assertEqual((review_dir / "001-page-1_overlay_red.txt").read_text().strip(), "Make this hand smaller.")

    def test_save_review_payload_rejects_painted_color_without_request_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = make_run(Path(tmp))
            payload = {
                "stage": FIRST_STAGE,
                "items": [
                    {
                        "filename": "001-page-1.png",
                        "overlays": [
                            {
                                "color_id": "red",
                                "color": "#ff3b30",
                                "request": " ",
                                "data_url": PNG_DATA_URL,
                            }
                        ],
                    }
                ],
            }

            with self.assertRaises(review_overlay_server.ReviewError) as caught:
                review_overlay_server.save_review_payload(run_dir, FIRST_STAGE, payload, review_id="bad-review")

            self.assertIn("request text", str(caught.exception))
            self.assertFalse((run_dir / "review_overlays" / FIRST_STAGE / "bad-review").exists())

    def test_save_review_payload_rejects_unknown_or_traversal_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = make_run(Path(tmp))
            payload = {
                "stage": FIRST_STAGE,
                "items": [
                    {
                        "filename": "../escape.png",
                        "overlays": [
                            {
                                "color_id": "red",
                                "color": "#ff3b30",
                                "request": "Change this unsafe target.",
                                "data_url": PNG_DATA_URL,
                            }
                        ],
                    }
                ],
            }

            with self.assertRaises(review_overlay_server.ReviewError) as caught:
                review_overlay_server.save_review_payload(run_dir, FIRST_STAGE, payload, review_id="unsafe-review")

            self.assertIn("Unknown or unsafe", str(caught.exception))

    @unittest.skipUnless(Image, "Pillow is required for create-markup tests")
    def test_create_markup_from_normalized_rect_and_polygon_writes_same_size_overlays(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = make_run(Path(tmp), size=(100, 80))
            markup_spec = {
                "stage": FIRST_STAGE,
                "review_id": "agent-markup",
                "coordinate_space": "normalized",
                "items": [
                    {
                        "filename": "001-page-1.png",
                        "marks": [
                            {
                                "color_id": "red",
                                "shape": "rect",
                                "box": [0.10, 0.20, 0.30, 0.25],
                                "request": "Make this hand smaller.",
                            },
                            {
                                "color_id": "blue",
                                "shape": "polygon",
                                "points": [[0.55, 0.18], [0.72, 0.20], [0.70, 0.32], [0.53, 0.30]],
                                "request": "Move the speech balloon up.",
                            },
                        ],
                    }
                ],
            }

            manifest = review_overlay_server.create_markup_manifest(run_dir, FIRST_STAGE, markup_spec)

            review_dir = run_dir / "review_overlays" / FIRST_STAGE / "agent-markup"
            red_path = review_dir / "001-page-1_overlay_red.png"
            blue_path = review_dir / "001-page-1_overlay_blue.png"
            combined_path = review_dir / "001-page-1_overlay_combined.png"
            self.assertEqual(manifest["revision_count"], 2)
            self.assertTrue(red_path.exists())
            self.assertTrue(blue_path.exists())
            self.assertTrue(combined_path.exists())
            with Image.open(red_path) as red:
                self.assertEqual(red.size, (100, 80))
                self.assertGreater(red.getpixel((20, 20))[3], 0)
                self.assertEqual(red.getpixel((5, 5))[3], 0)
            with Image.open(blue_path) as blue:
                self.assertEqual(blue.size, (100, 80))
                self.assertGreater(blue.getpixel((60, 20))[3], 0)
            with Image.open(combined_path) as combined:
                self.assertEqual(combined.size, (100, 80))
            manifest_data = json.loads((review_dir / "revision_requests.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest_data["items"][0]["overlays"][0]["request"], "Move the speech balloon up.")
            self.assertEqual(manifest_data["items"][0]["overlays"][1]["request"], "Make this hand smaller.")

    @unittest.skipUnless(Image, "Pillow is required for create-markup tests")
    def test_create_markup_accepts_pixel_coordinates(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = make_run(Path(tmp), size=(50, 40))
            markup_spec = {
                "stage": FIRST_STAGE,
                "review_id": "pixel-markup",
                "coordinate_space": "pixel",
                "items": [
                    {
                        "filename": "001-page-1.png",
                        "marks": [
                            {
                                "color_id": "green",
                                "shape": "rect",
                                "box": [10, 8, 20, 12],
                                "request": "Raise this prop slightly.",
                            }
                        ],
                    }
                ],
            }

            review_overlay_server.create_markup_manifest(run_dir, FIRST_STAGE, markup_spec)

            overlay_path = run_dir / "review_overlays" / FIRST_STAGE / "pixel-markup" / "001-page-1_overlay_green.png"
            with Image.open(overlay_path) as overlay:
                self.assertEqual(overlay.size, (50, 40))
                self.assertGreater(overlay.getpixel((15, 12))[3], 0)
                self.assertEqual(overlay.getpixel((40, 35))[3], 0)

    @unittest.skipUnless(Image, "Pillow is required for create-markup tests")
    def test_create_markup_cli_writes_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = make_run(root, size=(30, 20))
            spec_path = root / "markup.json"
            spec_path.write_text(
                json.dumps(
                    {
                        "stage": FIRST_STAGE,
                        "review_id": "cli-markup",
                        "items": [
                            {
                                "filename": "001-page-1.png",
                                "marks": [
                                    {
                                        "color_id": "purple",
                                        "shape": "rect",
                                        "box": [0.1, 0.1, 0.3, 0.3],
                                        "request": "Darken this expression area.",
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "python3",
                    "-B",
                    str(SCRIPT),
                    "create-markup",
                    "--run-dir",
                    str(run_dir),
                    "--stage",
                    FIRST_STAGE,
                    "--spec",
                    str(spec_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("MANIFEST:", result.stdout)
            self.assertTrue(
                (
                    run_dir
                    / "review_overlays"
                    / FIRST_STAGE
                    / "cli-markup"
                    / "revision_requests.json"
                ).exists()
            )

    @unittest.skipUnless(Image, "Pillow is required for create-markup tests")
    def test_create_markup_rejects_invalid_coordinates_and_empty_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = make_run(Path(tmp), size=(100, 80))
            invalid_coordinate_spec = {
                "stage": FIRST_STAGE,
                "items": [
                    {
                        "filename": "001-page-1.png",
                        "marks": [
                            {
                                "color_id": "red",
                                "shape": "rect",
                                "box": [0.9, 0.9, 0.2, 0.2],
                                "request": "This should fail.",
                            }
                        ],
                    }
                ],
            }

            with self.assertRaises(review_overlay_server.ReviewError) as coordinate_error:
                review_overlay_server.create_markup_manifest(
                    run_dir,
                    FIRST_STAGE,
                    invalid_coordinate_spec,
                    review_id="invalid-coordinate",
                )
            self.assertIn("normalized box", str(coordinate_error.exception))

            empty_request_spec = {
                "stage": FIRST_STAGE,
                "items": [
                    {
                        "filename": "001-page-1.png",
                        "marks": [
                            {
                                "color_id": "red",
                                "shape": "rect",
                                "box": [0.1, 0.1, 0.2, 0.2],
                                "request": " ",
                            }
                        ],
                    }
                ],
            }
            with self.assertRaises(review_overlay_server.ReviewError) as request_error:
                review_overlay_server.create_markup_manifest(
                    run_dir,
                    FIRST_STAGE,
                    empty_request_spec,
                    review_id="empty-request",
                )
            self.assertIn("non-empty request", str(request_error.exception))


if __name__ == "__main__":
    unittest.main()
