---
name: validate-comic-storyboard-physical-causality
description: Use after a create-comic-storyboard-pack page image has been imported and before parent inspect-pass, to inspect generated storyboard output for physical cause-effect logic, temporal order, object motion, impact, transfer, and state-change plausibility.
---

# Validate Comic Storyboard Physical Causality

## Purpose

Validate one imported `create-comic-storyboard-pack` page/stage for physical cause and effect before the parent session runs `inspect-pass`. This skill creates a required `physical_causality` validation report.

## Inputs

Use the assigned run folder, page filename/id, and stage. Inspect:

- `<run-dir>/approved_storyboard_plan.json`
- the imported stage image recorded in `state.json`
- the `storyboard_conti_sketch_ink` `*_desc.md` when present
- prior inspected page images when continuity depends on earlier pages
- any `spatial_contract.transitions`, `allowed_transition`, and `requires_cause` entries

## Checks

- Reject uncaused state changes: opened/closed doors, damage, injuries, falls, dropped or grabbed props, object possession changes, disappearance, or sudden relocation without an approved cause.
- Check direction agreement between body pose, force/effect lines, trajectory, destination, impact, and result position.
- Check temporal order: contact, throw, push, hit, release, or collision should appear before the result it causes.
- Check physical continuity: characters and objects should not teleport or change ownership/state without a visible or approved transition.
- Allow comic ellipsis only when the omitted cause is explicit in `narrative_plan`, panel notes, `spatial_contract.transitions`, `allowed_transition`, or `requires_cause`.

## Report

Write a JSON report under:

```text
<run-dir>/validation_reports/<stage>/<page-stem>/physical_causality.json
```

Use this schema:

```json
{
  "validator": "physical_causality",
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

Allowed `verdict` values are `pass`, `needs_rerun`, and `reconciled`. Use `needs_rerun` for hard physical contradictions. Use `reconciled` only for non-hard ambiguities that are safely explained in the approved page design.

## Helper

For a deterministic starter report, run:

```bash
python3 .agents/skills/validate-comic-storyboard-physical-causality/scripts/validate_physical_causality.py --run-dir <run-dir> --item <page> --stage <stage>
```

Then register it with the pack runner:

```bash
python3 .agents/skills/create-comic-storyboard-pack/scripts/comic_storyboard_runner.py validate-physical-causality --run-dir <run-dir> --item <page> --stage <stage> --report <run-dir>/validation_reports/<stage>/<page-stem>/physical_causality.json
```
