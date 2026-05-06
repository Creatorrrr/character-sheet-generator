---
name: convert-2d-sheet-to-photoreal
description: Manage the full workflow for converting a 2D character sheet into a photoreal live-action character sheet. Use when the user wants staged 2D to realistic character sheet conversion, wants progress reports or feedback gates between stages, or wants Codex to coordinate the stage skills create-photoreal-character-base, intensify-photoreal-character, restore-photoreal-sheet-layout, and repair-photoreal-sheet-text.
---

# Convert 2D Sheet to Photoreal

## Overview

Manage a staged image workflow that separates photoreal character conversion from text and layout restoration. Use the sibling stage skills in order, report each stage result, and ask for feedback when a quality gate is uncertain.

## Default Output Location

If the user does not specify where to save files, create a new run folder under `/Users/chasoik/Projects/character-sheet-generator/output/`.

- Use `output/<slug>-photoreal-sheet-YYYYMMDD-HHMMSS/` for this workflow.
- Build `<slug>` from the character name, then the input image filename stem, then `photoreal-sheet`. Normalize it to lowercase ASCII letters, numbers, and hyphens. If the normalized value is empty, use `photoreal-sheet`.
- If the user is resuming from an existing run folder, keep using that folder instead of creating a new one.
- Save Stage 1-4 outputs, approved intermediates, repair outputs, notes, and optional state or resume artifacts under the selected run folder.
- When reporting artifacts, include the selected run folder and write output paths under that folder.

## Stage Skills

Use these sibling skills from the same `.agents/skills` skill root:

1. `$create-photoreal-character-base` for a text-free live-action base.
2. `$intensify-photoreal-character` when the base still feels anime, 3D, CGI, plastic, or overly AI-smoothed.
3. `$restore-photoreal-sheet-layout` to rebuild the original sheet structure and readable text around the approved photoreal base.
4. `$repair-photoreal-sheet-text` only when the final character is good but text or labels need cleanup.

If explicit skill invocation is unavailable, open the matching sibling `SKILL.md` and follow it directly.

## Intake

Before generating or editing, identify:

- Original 2D character sheet image.
- Current stage image, if the user is resuming.
- Required text preservation level: exact, approximate, translated, or omit until later.
- Whether the user wants step-by-step approval or autonomous continuation.

If no source image is available, ask for it. If the user provides an existing intermediate image, resume from the matching stage instead of restarting.

## Workflow

### Stage 1: Photoreal Base

Use `$create-photoreal-character-base`.

Goal:

- Discard text temporarily.
- Preserve character identity, hair, outfit, pose, expression, and sheet composition.
- Produce a text-free image that looks like real live-action reference photography, not illustration, 3D render, or cosplay poster.

Report:

- What source image was used.
- What identity and costume details were preserved.
- Whether text was omitted.
- Any remaining non-photoreal risk.

Feedback gate:

- If the image still has anime, 3D, CGI, waxy skin, plastic skin, or overly clean AI traits, recommend Stage 2.
- If the base is convincingly photoreal, ask whether to proceed to Stage 3.

### Stage 2: Photoreal Intensification

Use `$intensify-photoreal-character` when needed.

Goal:

- Remove remaining 2D, 3D, CGI, game-render, plastic, or over-retouched qualities.
- Keep expression, emotion, pose, clothing, and layout stable.

Report:

- Which artifacts were targeted.
- What should remain unchanged.
- Whether the result now passes the live-action photo threshold.

Feedback gate:

- If it still fails the threshold, repeat Stage 2 with sharper diagnosis.
- If it passes, ask whether to proceed to Stage 3.

### Stage 3: Layout and Text Restoration

Use `$restore-photoreal-sheet-layout`.

Goal:

- Keep the approved photoreal character unchanged.
- Restore the original 2D sheet's information structure, view layout, labels, and text boxes.
- Make text readable without pulling the character back into illustration.

Report:

- Which layout elements were restored.
- How text readability was handled.
- Whether character realism stayed intact.

Feedback gate:

- If character quality regressed, go back to Stage 2 or regenerate Stage 3 with stricter preservation.
- If text is broken but the character is good, proceed to Stage 4.

### Stage 4: Text Repair

Use `$repair-photoreal-sheet-text` only for text and labels.

Goal:

- Preserve character, pose, outfit, lighting, and layout.
- Fix only broken, blurry, misaligned, or unreadable text and labels.

Report:

- Which text areas were repaired.
- Whether any character or layout changes occurred.
- Remaining manual text risk, if any.

## Reporting Format

After each stage, send a concise Korean status report:

```text
[N단계 결과]
- 입력: ...
- 저장 폴더: ...
- 산출물: ...
- 유지한 요소: ...
- 수정/강화한 요소: ...
- 검수 결과: ...
- 다음 결정: ...
```

Keep reports factual. Do not claim text is readable unless it was inspected. Do not claim a stage passed if obvious visual artifacts remain.

## Operating Rules

- Do not use or include the compressed prompt variant.
- Prefer staged editing over one-shot generation.
- Preserve the latest approved image as the next stage input.
- Pause for user feedback at each gate unless the user explicitly asked to run the full workflow autonomously.
- When using an image generation or editing tool, submit only the current stage prompt plus the required image inputs. Do not mix future-stage text restoration instructions into Stage 1 or Stage 2.
- When a model struggles with text, keep the character image stable and isolate text repair in Stage 4.
