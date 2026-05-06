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

Default to step-by-step approval unless the user explicitly asks for autonomous continuation.

If no source image is available, ask for it. If the user provides an existing intermediate image, resume from the matching stage instead of restarting.

## Turn Protocol for Image Generation

Image generation calls end the current assistant turn. Because of that, each stage must be split across turns:

1. Before generating or editing an image, send a Korean `[N단계 실행 예정]` report with the current input, run folder, stage goal, resume behavior, and feedback options.
2. Submit only the current stage prompt and required image inputs to the image generation or editing tool.
3. Treat the image generation call as the last action of that turn. Do not append a result report, quality claim, or next-step question after the tool call.
4. On the user's next message, resume from the generated image. Copy or reference the generated artifact under the run folder when possible, inspect the image if available, then send the Korean `[N단계 결과]` report.
5. Do not start the next stage until the user chooses one of the feedback-gate options for the completed stage. This also applies when the original request asks for the full workflow, because multi-stage image generation cannot be chained in one assistant turn.

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

- Stop after reporting the Stage 1 result and ask the user to choose one option.
- Allowed options: `Stage 3 진행`, `Stage 2로 실사감 강화`, `Stage 1 재생성`, `중단`.
- Recommend `Stage 2로 실사감 강화` if the image still has anime, 3D, CGI, waxy skin, plastic skin, or overly clean AI traits.
- Recommend `Stage 3 진행` only if the base is convincingly photoreal.

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

- Stop after reporting the Stage 2 result and ask the user to choose one option.
- Allowed options: `Stage 3 진행`, `Stage 2 재시도`, `Stage 1부터 재생성`, `중단`.
- Recommend `Stage 2 재시도` if it still fails the live-action photo threshold.
- Recommend `Stage 3 진행` only if the result passes the live-action photo threshold.

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

- Stop after reporting the Stage 3 result and ask the user to choose one option.
- Allowed options: `완료`, `Stage 4 텍스트 보정`, `Stage 3 재생성`, `Stage 2로 회귀`.
- Recommend `Stage 2로 회귀` if character quality regressed.
- Recommend `Stage 3 재생성` if layout restoration failed or pulled the character back toward illustration.
- Recommend `Stage 4 텍스트 보정` only when the character is good but text or labels are broken, blurry, misaligned, or unreadable.
- Recommend `완료` only when character realism, layout, and text are all acceptable.

### Stage 4: Text Repair

Use `$repair-photoreal-sheet-text` only for text and labels.

Goal:

- Preserve character, pose, outfit, lighting, and layout.
- Fix only broken, blurry, misaligned, or unreadable text and labels.

Report:

- Which text areas were repaired.
- Whether any character or layout changes occurred.
- Remaining manual text risk, if any.

Feedback gate:

- Stop after reporting the Stage 4 result and ask the user to choose one option.
- Allowed options: `완료`, `Stage 4 재시도`, `수동 보정 필요로 종료`.
- Recommend `Stage 4 재시도` if text repair changed the character, pose, outfit, lighting, or layout.
- Recommend `수동 보정 필요로 종료` if the model still cannot produce verifiable readable text after a focused repair.
- Recommend `완료` only when the repaired text can be verified and the character remained stable.

## Reporting Format

Before each stage, send a concise Korean execution report:

```text
[N단계 실행 예정]
- 입력: ...
- 저장 폴더: ...
- 단계 목표: ...
- 생성 후 재개: ...
- 피드백 옵션: ...
```

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
- Preserve only the latest user-approved image as the next stage input.
- Pause for user feedback at every gate. Do not advance to the next stage without an explicit user choice.
- Even when the user requests autonomous continuation, do not chain multiple image generation stages in one assistant turn. Run one stage per image generation turn and resume on the next user message.
- When using an image generation or editing tool, submit only the current stage prompt plus the required image inputs. Do not mix future-stage layout or text restoration instructions into Stage 1 or Stage 2.
- When a model struggles with text, keep the character image stable and isolate text repair in Stage 4.
- Do not claim text is readable, exact, repaired, or complete unless it was inspected and verified.
