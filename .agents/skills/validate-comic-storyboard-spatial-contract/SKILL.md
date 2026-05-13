---
name: validate-comic-storyboard-spatial-contract
description: Use after a create-comic-storyboard-pack page image has been imported and before parent inspect-pass, to inspect generated storyboard output against the approved spatial_contract, spatial_continuity_plan, scene_3d renders, and *_desc.md validation description.
---

# Validate Comic Storyboard Spatial Contract

## Purpose

Validate one imported `create-comic-storyboard-pack` page/stage before the parent session runs `inspect-pass`. This skill creates a required `spatial_contract` validation report; it does not edit runner state directly unless the parent asks it to run the report helper and then register the report through the pack runner.

## Inputs

Use the assigned run folder, page filename/id, and stage. Inspect:

- `<run-dir>/approved_storyboard_plan.json`
- the imported stage image recorded in `state.json`
- the `storyboard_conti_sketch_ink` `*_desc.md` when present
- `spatial-render-manifest` PNGs for `scene_3d` pages when the pack runner requires them
- prior same-stage inspected pages when the current page depends on them

## Checks

- Preserve the approved comic page design first; use `spatial_contract` only as a validation overlay.
- Check every active entity id, panel snapshot, position/vector, visibility, occlusion, held prop, state tag, and named constraint.
- Check `spatial_continuity_plan` before page-specific contract details: same `location_id` means the same physical set, fixed landmarks, entrances/exits, lighting, and allowed state changes.
- For `scene_3d`, treat hard locks as rerun criteria and soft/inferred geometry as reconciliation candidates only when hard invariants and page design remain intact.
- Reject target-opposite vectors, missing/incorrect occluders, reader-POV-only cover, line-of-sight failures, forbidden exposure, landmark drift, uncaused state drift, and generated-page contradictions with the `*_desc.md`.

## Report

Write a JSON report under:

```text
<run-dir>/validation_reports/<stage>/<page-stem>/spatial_contract.json
```

Use this schema:

```json
{
  "validator": "spatial_contract",
  "run_dir": "<absolute run dir>",
  "page_id": "<approved page id>",
  "filename": "<approved filename>",
  "stage": "storyboard_conti_sketch_ink",
  "verdict": "pass",
  "summary": "short inspection result",
  "issues": [],
  "checked_artifacts": ["<image path>", "<desc path>"],
  "reconciliation_note": ""
}
```

Allowed `verdict` values are `pass`, `needs_rerun`, and `reconciled`. Use `reconciled` only when hard invariants pass and the generated storyboard safely calibrates soft/inferred geometry; include `reconciliation_note`.

## Helper

For a deterministic starter report, run:

```bash
python3 .agents/skills/validate-comic-storyboard-spatial-contract/scripts/validate_spatial_contract.py --run-dir <run-dir> --item <page> --stage <stage>
```

Then register it with the pack runner:

```bash
python3 .agents/skills/create-comic-storyboard-pack/scripts/comic_storyboard_runner.py validate-spatial --run-dir <run-dir> --item <page> --stage <stage> --report <run-dir>/validation_reports/<stage>/<page-stem>/spatial_contract.json
```
