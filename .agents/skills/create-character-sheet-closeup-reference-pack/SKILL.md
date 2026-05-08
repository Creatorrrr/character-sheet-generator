---
name: create-character-sheet-closeup-reference-pack
description: Coordinate a style-preserving closeup reference pack from an approved character sheet created by character-sheet-orchestrator. Use when the user wants face, expression, eye, hair, outfit, prop, hand, shoes, full-body, pose, palette, or motif detail images derived from an approved character master sheet while preserving the sheet's approved anime, mascot, photoreal, semi-real, or custom style.
---

# Create Character Sheet Closeup Reference Pack

## Overview

Build a batch plan for closeup and detail reference images from an approved character sheet. This skill coordinates source-of-truth extraction, identity anchoring, output selection, dependency ordering, generation prompts, review, and reporting.

## Default Output Location

If the user does not specify where to save files, create a new run folder under `/Users/chasoik/Projects/character-sheet-generator/output/`.

- Use `output/<slug>-character-closeup-pack-YYYYMMDD-HHMMSS/` for this workflow.
- Build `<slug>` from the character name, then the input image filename stem, then `character-closeup-pack`. Normalize it to lowercase ASCII letters, numbers, and hyphens. If the normalized value is empty, use `character-closeup-pack`.
- If the user is resuming from an existing run folder, keep using that folder instead of creating a new one.
- Save every pack image, paired-view image, approved anchor, batch plan, notes, and optional state or resume artifacts under the selected run folder.
- Keep the pack filenames from `references/pack-map.md`, but place them inside the selected run folder.

## Inputs

Require at least one:

- Approved final sheet from `$character-sheet-orchestrator`.
- `$character-sheet-orchestrator` state JSON with `character_spec`, `identity_lock`, `blueprint`, or `anchor_assets`.
- Approved face, full-body, or identity anchor asset.
- User-provided character detail block sufficient to identify the character.

Ask for missing inputs only when identity or source style cannot be inferred. Create `01_face_front.png` through the runner first and use it as the master identity anchor after parent inspection passes, unless a resumed run already has an inspected anchor. Dependent items must wait until this anchor is `inspected_pass` or `complete`.

## Resumable Runner Contract

Use `scripts/character_closeup_pack_runner.py` for this workflow. The runner exists because Codex image generation may end the turn immediately after an `image_gen` call. Do not rely on the same turn continuing after image generation.

Default policy:

- Use Codex built-in `image_gen`; do not call an external image API.
- Use `anchor_policy: "auto_if_pass"` in `state.json`.
- Use the anchor command flow only for `01_face_front.png` before the master face anchor is approved.
- If `01_face_front.png` is visually inspected and passes, continue to the rest of the pack without asking for another approval unless the user explicitly requested a gated workflow.
- After the master face anchor is approved, dependent images must be generated through `next-batch --limit 4` and one `fork_context=true` subagent per batch item.
- When `fork_context=true` is used, omit subagent role fields such as `agent_type` or `role`. Do not pass `worker`, `default`, or `explorer` as a role/type field.
- Treat `worker` only as the runner's inspection-result label (`worker_status`, `worker_note`), not as a subagent role type.
- Put the assigned-output generation and first-pass inspection behavior in the subagent prompt text instead of role metadata.
- Do not use serial fallback for dependent images. Do not call parent-session `image_gen`, `next`, or `import-latest` for dependent images after the anchor is approved.
- If subagents are unavailable after the anchor is approved, stop and report that dependent generation is blocked by missing subagent support.
- If the anchor fails inspection, run `rerun` for `01_face_front.png` and do not generate dependent items yet.
- Do not treat crop-only or manually extracted source-sheet regions as completed pack outputs. Crops may be used only as source or anchor references when the user explicitly asks.

Anchor command flow:

```bash
python3 scripts/character_closeup_pack_runner.py init --source <source-image> --preset core
python3 scripts/character_closeup_pack_runner.py next --run-dir <run-dir>
# Use the printed prompt with parent-session image_gen only for 01_face_front.png. The turn may end here.
python3 scripts/character_closeup_pack_runner.py import-latest --run-dir <run-dir>
# Inspect the imported output before marking pass.
python3 scripts/character_closeup_pack_runner.py inspect-pass --run-dir <run-dir> --item 01_face_front.png --note "<short inspection note>"
```

Do not use this flow for dependent images after `01_face_front.png` is `inspected_pass` or `complete`.

Parallel command flow after the master face anchor is approved:

```bash
python3 scripts/character_closeup_pack_runner.py next-batch --run-dir <run-dir> --limit 4
# Spawn one subagent per printed item, with fork_context=true and no agent_type/role field.
# Put the worker behavior in the task prompt. Each subagent generates exactly one assigned output with image_gen and reports the generated file path plus a first-pass inspection note.
python3 scripts/character_closeup_pack_runner.py import --run-dir <run-dir> --item <filename> --generated <generated-path> --worker-status pass --worker-note "<subagent note>"
# Parent session inspects each imported image before marking final pass.
python3 scripts/character_closeup_pack_runner.py inspect-pass --run-dir <run-dir> --item <filename> --note "<parent inspection note>"
python3 scripts/character_closeup_pack_runner.py batch-status --run-dir <run-dir> --batch-id <batch-id>
```

If the anchor image is wrong:

```bash
python3 scripts/character_closeup_pack_runner.py rerun --run-dir <run-dir> --item 01_face_front.png --note "<reason>"
python3 scripts/character_closeup_pack_runner.py next --run-dir <run-dir>
```

If a dependent batch image is wrong after the anchor is approved:

```bash
python3 scripts/character_closeup_pack_runner.py rerun --run-dir <run-dir> --item <filename> --note "<reason>"
python3 scripts/character_closeup_pack_runner.py next-batch --run-dir <run-dir> --limit 4
```

State rules:

- Before the anchor `image_gen` call, run `next` so `01_face_front.png` is marked `generation_requested`.
- For dependent parallel batches, run `next-batch --limit 4` once, then assign one printed item to each subagent.
- After anchor `image_gen`, do not create a new run folder. Resume the same run and run `import-latest` only for `01_face_front.png`.
- After dependent subagent `image_gen`, do not use `import-latest`; use `import --item <filename> --generated <path>` so each generated file is mapped to the correct output.
- If the user provides no run folder, initialize by source image; the runner reuses an incomplete run with the same source image hash, preset, and style mode.
- Only `inspect-pass` may mark an item `inspected_pass`. `import-latest` only copies the file into the run folder and marks it `imported`.
- Subagent inspection is advisory only. Store it through `import --worker-status ... --worker-note ...`, but the parent session must visually inspect and run `inspect-pass` before the item counts as complete.
- Treat the pack as complete only when every item is `inspected_pass` or `complete`.

## Core Rules

- Preserve the source sheet's approved style. Do not convert anime, mascot, semi-real, or stylized sheets into photoreal output unless the user explicitly requests conversion.
- Treat the approved character sheet and orchestrator state as the source of truth. If they conflict, prefer the latest user-approved state or ask only when the conflict affects identity.
- Preserve `identity_lock`: face shape, hair silhouette, eye design, outfit structure, palette, motifs, accessories, age appearance, and species/body type.
- Generate a pack, not a beauty image. Each output must serve a specific reference purpose.
- Every pack output must be a new `image_gen` result imported into the run folder and inspected. Crop-only outputs do not count as complete.
- Avoid labels unless a labeled sheet is requested and text readability is important.
- Do not copy template placeholders, mannequin construction lines, plus icons, empty boxes, or UI wireframe elements as character content.
- Keep reporting factual. Do not claim identity consistency, correct left/right direction, or style preservation unless the output was inspected.

## Workflow

1. Extract source truth.
   Identify source sheet, state JSON, approved anchors, style mode, identity lock, required motifs, outfit details, and any requested pack preset.

2. Choose pack preset.
   Default to `core`. Use `full` when the user asks for a complete production reference pack. Read `references/pack-map.md` for output definitions and dependencies.

3. Initialize or resume the runner and build a batch plan.
   Use `scripts/character_closeup_pack_runner.py init --source <source-image> --preset core|full`. The runner writes `state.json`, `batch_plan.md`, and per-output prompts under the run folder.

4. Review the batch plan.
   Use this format:

```text
- output: output/<slug>-character-closeup-pack-YYYYMMDD-HHMMSS/<filename>.png
- purpose: ...
- request_group: anchor | face_pair | parallel_detail | full_body | optional
- dependencies: ...
- prompt_template: ...
- notes: ...
```

5. Resolve identity anchor.
   Run `next`, generate `01_face_front.png` with Codex built-in `image_gen`, import the generated image, inspect it, and mark it with `inspect-pass` only if it preserves identity and source style. With `anchor_policy: "auto_if_pass"`, continue automatically after a passing inspection unless the user requested a gated workflow.

6. Generate requested assets.
   After the anchor is approved, run `next-batch --limit 4`, spawn one `fork_context=true` subagent per printed item with no `agent_type` or `role`, and give each subagent exactly one output. Use the style-preserving prompt templates in `references/prompt-templates.md`; the runner embeds those requirements in each prompt. Import each generated result with explicit `import --item <filename> --generated <path>` mapping. If subagents are unavailable, stop instead of falling back to parent-session serial generation.

7. Review and route fixes.
   Check source-style preservation, same-character consistency, left/right direction for paired views, outfit/detail fidelity, missing outputs, and text/template artifact leakage. Mark passing outputs with `inspect-pass`; mark failures with `rerun`.

8. Report completion.
   Summarize generated assets, imported-but-uninspected assets, failed or questionable assets, rerun recommendations, and next decision.

## Pair Rules

When both left and right versions of a view are requested, generate them as one two-panel image:

- `02_face_3q_left.png` + `03_face_3q_right.png` -> `02_03_face_3q_pair.png`
- `04_face_side_left.png` + `05_face_side_right.png` -> `04_05_face_side_pair.png`
- `18_full_body_side.png` + `18_full_body_back.png` may become `18_full_body_side_back_pair.png` for the `full` preset.

Paired prompt rules:

- One image with equal side-by-side panels.
- Same character, same style, same lighting, same crop, same clothing, same palette.
- Left panel: subject's nose and body direction point toward image-left.
- Right panel: subject's nose and body direction point toward image-right.
- Use panel position, not written labels, to distinguish direction unless labels are explicitly requested.

## Reporting

After each batch, report in Korean:

```text
[캐릭터 시트 클로즈업 팩 진행 결과]
- 기준 자료: ...
- 스타일 모드: ...
- 저장 폴더: ...
- 상태 파일: ...
- 생성 요청: ...
- 병렬 그룹: ...
- 좌우 묶음 처리: ...
- 미검수 imported 항목: ...
- rerun 필요 항목: ...
- 검수 기준: ...
- 다음 결정: ...
```

Read `references/pack-map.md` for output presets, `references/prompt-templates.md` for reusable prompts, and `references/state-schema.md` when persisting or resuming the workflow.

## Subagent Batch Contract

When spawning subagents for `next-batch`, use `fork_context=true` with no `agent_type` or `role`, then pass explicit task context even though the session is forked:

```text
You are generating exactly one image for create-character-sheet-closeup-reference-pack.
Act as the generation-and-inspection worker for this assigned output in the prompt only; do not require a worker role field.
Do not edit state.json.
Run folder: <run-dir>
Source character sheet: <run-dir>/source_character_sheet.png
Approved identity anchor: <run-dir>/01_face_front.png
Assigned output: <filename>
Prompt file: <prompt-file>
Batch id: <batch-id>
Preset: <core|full>
Style mode: <preserve_source_style|photoreal_conversion|custom_style_override>

Use image_gen with the assigned prompt and visual references. Preserve the source sheet's approved style unless style_mode explicitly requests conversion or override. After generation, inspect the output for prompt fit, source-style preservation, identity consistency, direction/crop correctness where applicable, outfit/detail fidelity, and obvious artifacts. Return only:
- generated file path
- worker_status: pass or needs_rerun
- worker_note: concise inspection note
```

The parent session imports the result, performs final visual inspection, and decides `inspect-pass` or `rerun`.
