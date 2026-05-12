---
name: review-image-overlays
description: "Use when generated images need visual revision markup: open a local gallery for user-painted color-coded overlays, or generate agent-driven rect/polygon overlays from a coordinate JSON spec, then save per-color overlay PNG/TXT files plus a revision_requests.json manifest for rerun workflows such as create-comic-storyboard-pack."
---

# Review Image Overlays

## Overview

Create visual correction overlays for generated image review. Use the browser gallery when the user wants to paint directly. Use `create-markup` when an agent has identified issues and can describe them with coordinates. Both paths save the same color-specific overlay PNG/TXT artifacts plus a manifest that downstream runners can consume.

## Quick Start

Use the bundled script:

```bash
SKILL_DIR=".agents/skills/review-image-overlays"
RUNNER="$SKILL_DIR/scripts/review_overlay_server.py"
python3 "$RUNNER" serve --run-dir <run-dir> --stage storyboard_conti_sketch_ink
```

The script binds to `127.0.0.1` on an empty port by default, opens the browser, and prints `REVIEW_OVERLAY_URL`.

For comic storyboard runs, valid review stages include `storyboard_conti_sketch_ink` and `finish`. User feedback is collected after `storyboard_conti_sketch_ink` before finish.

Use `--items <filename>` repeatedly to limit the gallery:

```bash
python3 "$RUNNER" serve --run-dir <run-dir> --stage storyboard_conti_sketch_ink --items 001-page-1.png --items 003-page-3.png
```

## Agent Markup

For subagent self-verification or parent inspection, prefer coordinate-driven markup over browser automation. Write a JSON spec with normalized `0..1` coordinates by default:

```json
{
  "stage": "storyboard_conti_sketch_ink",
  "review_id": "parent-review-001",
  "coordinate_space": "normalized",
  "items": [
    {
      "filename": "001-page-1.png",
      "marks": [
        {
          "color_id": "red",
          "shape": "rect",
          "box": [0.18, 0.22, 0.16, 0.12],
          "request": "손이 너무 커 보이므로 손 크기를 줄이고 손가락 수를 자연스럽게 정리."
        },
        {
          "color_id": "blue",
          "shape": "polygon",
          "points": [[0.55, 0.18], [0.72, 0.20], [0.70, 0.32], [0.53, 0.30]],
          "request": "말풍선이 얼굴을 가리므로 위쪽 여백으로 이동."
        }
      ]
    }
  ]
}
```

Generate overlays and the manifest:

```bash
python3 "$RUNNER" create-markup --run-dir <run-dir> --stage storyboard_conti_sketch_ink --spec <markup.json>
```

Use `coordinate_space: "pixel"` when exact image pixel coordinates are easier. Supported shapes are `rect` with `box: [x, y, width, height]` and `polygon` with at least three `[x, y]` points. Every mark must include non-empty `request` text. Multiple marks with the same `color_id` are merged into one color-specific overlay and one request TXT.

## Saved Artifacts

Saved files are written under:

```text
<run-dir>/review_overlays/<stage>/<review-id>/
```

For each reviewed image, the canonical artifacts are one overlay PNG and one request TXT per color:

```text
001-page-1_overlay_red.png
001-page-1_overlay_red.txt
001-page-1_overlay_blue.png
001-page-1_overlay_blue.txt
```

The script also writes:

```text
001-page-1_overlay_combined.png
revision_requests.json
revision_requests.md
```

Treat `revision_requests.json` as the machine-readable handoff. Treat the combined overlay as a visual convenience only; use the color-specific files as the source of truth.

## Comic Storyboard Pack Handoff

After saving overlays for a `$create-comic-storyboard-pack` run, feed the manifest back to the pack runner:

```bash
COMIC_RUNNER=".agents/skills/create-comic-storyboard-pack/scripts/comic_storyboard_runner.py"
python3 "$COMIC_RUNNER" request-revisions --run-dir <run-dir> --review-manifest <run-dir>/review_overlays/storyboard_conti_sketch_ink/<review-id>/revision_requests.json
python3 "$COMIC_RUNNER" next-batch --run-dir <run-dir> --limit 1
```

`request-revisions` marks the matching page stage as rerun-pending, resets the stage review and following gate, injects the overlay paths plus request text into the next subagent prompt, and may reset later same-stage pages if an earlier page's continuity reference became stale.

## Validation Rules

- Save only after every painted color has non-empty request text.
- For agent markup, reject unknown coordinate spaces, unsupported shapes, out-of-bounds coordinates, and empty request text.
- Keep all served images and saved files inside the run folder.
- Reject unknown filenames and path traversal attempts.
- Use color-specific overlay PNG/TXT files for correction instructions; do not rely on a single combined overlay.
- Leave the browser server running while the user edits; stop it with `Ctrl-C` after saving.
