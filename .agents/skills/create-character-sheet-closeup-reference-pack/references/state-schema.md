# State Schema

Use the runner-owned `state.json` schema below. The runner persists it beside generated assets for every run because `image_gen` may end the turn immediately after generation.

## State

```json
{
  "source_image": "source_character_sheet.png",
  "source_sha256": "",
  "workflow": "create-character-sheet-closeup-reference-pack",
  "run_dir": "",
  "anchor_policy": "auto_if_pass",
  "pack_preset": "core",
  "style_mode": "preserve_source_style",
  "source_original": "",
  "complete": false,
  "items": []
}
```

## Style Modes

- `preserve_source_style`: default. Preserve the approved character sheet's exact visual style.
- `photoreal_conversion`: use only when the user explicitly asks to convert to photoreal outputs.
- `custom_style_override`: use only when the user explicitly gives a new target style.

## Batch Plan Item

```json
{
  "output": "01_face_front.png",
  "purpose": "primary face identity anchor",
  "request_group": "identity_anchor",
  "prompt_template": "01 Face Front",
  "prompt_file": "prompts/01_face_front.prompt.txt",
  "dependencies": ["source_character_sheet.png"],
  "status": "pending",
  "requested_at": null,
  "generated_source": null,
  "inspection": {}
}
```

## Item Status Values

- `pending`: planned but not requested.
- `generation_requested`: `next` has printed the prompt for Codex built-in `image_gen`; the next import belongs to this item.
- `imported`: a generated image was copied into the run folder but has not passed inspection.
- `inspected_pass`: the output was visually inspected and passed.
- `needs_rerun`: inspection failed or the user requested a rerun.
- `complete`: accepted as already complete during a controlled resume or handoff.

Only `inspected_pass` and `complete` count toward pack completion.

## Prompt Metadata

```json
{
  "output": "02_03_face_3q_pair.png",
  "purpose": "paired left/right three-quarter face views",
  "request_group": "face_direction_pairs",
  "prompt_template": "02 03 Face Three-Quarter Pair",
  "notes": ""
}
```

## Review Result Item

```json
{
  "output": "",
  "status": "inspected_pass",
  "inspection": {
    "result": "pass",
    "note": "source style and identity pass",
    "inspected_at": ""
  }
}
```

## Approval Invariants

- Do not mark `01_face_front.png` as `inspected_pass` until the image was visually inspected.
- With `anchor_policy: "auto_if_pass"`, a passing `01_face_front.png` inspection allows dependent items to proceed without a separate approval question unless the user requested a gated workflow.
- Do not mark the pack complete until every requested output is `inspected_pass` or `complete`.
- `import-latest` is never approval. It only moves the item to `imported`.
- Crop-only or manually extracted source-sheet regions do not count as completed pack outputs.
- If style drift appears in generated outputs, return to the same output prompt with stronger source-style preservation instead of changing the source character sheet.
