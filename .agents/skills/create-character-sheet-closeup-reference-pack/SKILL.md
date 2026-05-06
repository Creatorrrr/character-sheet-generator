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

Ask for missing inputs only when identity or source style cannot be inferred. If no clear face identity anchor exists, create `01_face_front.png` first and use it as the master identity anchor after approval, unless the user explicitly asks for autonomous continuation.

## Core Rules

- Preserve the source sheet's approved style. Do not convert anime, mascot, semi-real, or stylized sheets into photoreal output unless the user explicitly requests conversion.
- Treat the approved character sheet and orchestrator state as the source of truth. If they conflict, prefer the latest user-approved state or ask only when the conflict affects identity.
- Preserve `identity_lock`: face shape, hair silhouette, eye design, outfit structure, palette, motifs, accessories, age appearance, and species/body type.
- Generate a pack, not a beauty image. Each output must serve a specific reference purpose.
- Avoid labels unless a labeled sheet is requested and text readability is important.
- Do not copy template placeholders, mannequin construction lines, plus icons, empty boxes, or UI wireframe elements as character content.
- Keep reporting factual. Do not claim identity consistency, correct left/right direction, or style preservation unless the output was inspected.

## Workflow

1. Extract source truth.
   Identify source sheet, state JSON, approved anchors, style mode, identity lock, required motifs, outfit details, and any requested pack preset.

2. Choose pack preset.
   Default to `core`. Use `full` when the user asks for a complete production reference pack. Read `references/pack-map.md` for output definitions and dependencies.

3. Build a batch plan.
   Use this format:

```text
- output: output/<slug>-character-closeup-pack-YYYYMMDD-HHMMSS/<filename>.png
- purpose: ...
- request_group: anchor | face_pair | parallel_detail | full_body | optional
- dependencies: ...
- prompt_template: ...
- notes: ...
```

4. Resolve identity anchor.
   If a clear face anchor exists, proceed to parallel groups. If not, generate `01_face_front.png` first and ask for approval before the rest.

5. Generate requested assets.
   Use the style-preserving prompt templates in `references/prompt-templates.md`. If an image generation tool supports parallel or batch requests, group independent detail outputs together. If the tool is serial-only, still present the parallel plan.

6. Review and route fixes.
   Check source-style preservation, same-character consistency, left/right direction for paired views, outfit/detail fidelity, missing outputs, and text/template artifact leakage.

7. Report completion.
   Summarize generated assets, failed or questionable assets, rerun recommendations, and next decision.

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
- 생성 요청: ...
- 병렬 그룹: ...
- 좌우 묶음 처리: ...
- 검수 기준: ...
- 다음 결정: ...
```

Read `references/pack-map.md` for output presets, `references/prompt-templates.md` for reusable prompts, and `references/state-schema.md` when persisting or resuming the workflow.
