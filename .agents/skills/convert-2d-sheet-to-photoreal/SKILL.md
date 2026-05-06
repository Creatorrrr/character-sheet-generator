---
name: convert-2d-sheet-to-photoreal
description: Use when the user wants staged 2D to photoreal live-action character sheet conversion with autonomous continuation, self-verification, final-only feedback, or coordination across the photoreal base, intensify, layout restore, and text repair stage skills.
---

# Convert 2D Sheet to Photoreal

## Overview

Manage a staged image workflow that separates photoreal character conversion from text and layout restoration. Use the sibling stage skills in order. Always continue through self-verification and regeneration gates without asking for user feedback until the final report.

## Default Output Location

If the user does not specify where to save files, create a new run folder under `/Users/chasoik/Projects/character-sheet-generator/output/`.

- Use `output/<slug>-photoreal-sheet-YYYYMMDD-HHMMSS/` for this workflow.
- Build `<slug>` from the character name, then the input image filename stem, then `photoreal-sheet`. Normalize it to lowercase ASCII letters, numbers, and hyphens. If the normalized value is empty, use `photoreal-sheet`.
- If the user is resuming from an existing run folder, keep using that folder instead of creating a new one.
- Save Stage 1-4 outputs, self-approved intermediates, repair outputs, notes, and optional state or resume artifacts under the selected run folder.
- Keep `workflow-state.json` and a short `verification-notes.md` in the run folder so the next resumed turn knows the current stage, attempt counts, latest accepted image, latest rejected image, and next intended action.
- When reporting artifacts, include the selected run folder and write output paths under that folder.

## Stage Skills

Use these sibling skills from the same `.agents/skills` skill root:

1. `$create-photoreal-character-base` for a text-free live-action base.
2. `$intensify-photoreal-character` when the base still feels anime, 3D, CGI, plastic, or overly AI-smoothed.
3. `$restore-photoreal-sheet-layout` to rebuild the original sheet structure and readable text around the self-approved photoreal base.
4. `$repair-photoreal-sheet-text` only when the final character is good but text or labels need cleanup.

If explicit skill invocation is unavailable, open the matching sibling `SKILL.md` and follow it directly.

## Intake

Before generating or editing, identify:

- Original 2D character sheet image.
- Current stage image, if the user is resuming.
- Required text preservation level: exact, approximate, translated, or omit until later.
- Any explicit final-output preference or constraint.

If no source image is available, ask for it. If the user provides an existing intermediate image, resume from the matching stage instead of restarting.

## Turn Protocol for Image Generation

Image generation calls end the current assistant turn. Because of that, each generation must be split across turns:

1. Before generating or editing an image, send a Korean `[N단계 실행 예정]` report with the current input, run folder, stage goal, resume behavior, and final-only feedback note.
2. Before the image tool call, update `workflow-state.json` and create or update a temporary thread heartbeat so this same thread wakes up shortly after the image generation turn ends.
3. Submit only the current stage prompt and required image inputs to the image generation or editing tool.
4. Treat the image generation call as the last action of that turn. Do not append a result report, quality claim, or next-step question after the tool call.
5. On the next user message or heartbeat resume, copy or reference the generated artifact under the run folder when possible, inspect the image if available, then send the Korean `[N단계 결과]` or `[N단계 자체 검수]` report.
6. Do not ask for mid-stage feedback. Decide the next action from the self-verification rules, record the decision in `verification-notes.md`, then either start the next generation or finish with the final report.
7. Delete or pause the temporary heartbeat when the workflow reaches a terminal final report.

## Autonomous Continuation

Always use autonomous continuation. Keep stage reports factual, but treat them as progress logs rather than user gates.

Required state:

- `workflow-state.json`: `stage`, `attemptsByStage`, `sourceImage`, `latestAcceptedImage`, `latestRejectedImage`, `nextAction`, and `terminalReason`.
- `verification-notes.md`: chronological notes with each generated artifact, pass/fail decision, visible defects, and why the next stage or retry was chosen.

Attempt limits:

- Stage 1: maximum 2 attempts.
- Stage 2: maximum 2 attempts.
- Stage 3: maximum 2 attempts.
- Stage 4: maximum 2 attempts.
- If a stage still fails after its limit, do not keep regenerating. Finish with a final report that names the failed stage and the human follow-up needed.

Autonomous decisions:

- If Stage 1 is convincingly live-action and photographic, self-approve it and proceed to Stage 3.
- If Stage 1 still has anime, 3D, CGI, waxy skin, plastic skin, or overly clean AI traits, proceed to Stage 2.
- If Stage 2 passes the live-action threshold, self-approve it and proceed to Stage 3.
- If Stage 2 still fails after its limit, regenerate Stage 1 once if Stage 1 attempts remain; otherwise finish with a failure report.
- If Stage 3 preserves character realism and layout but text is broken, blurry, misaligned, fake, or unreadable, proceed to Stage 4.
- If Stage 3 pulls the character back toward illustration or breaks the sheet layout, retry Stage 3 if attempts remain; otherwise return to Stage 2 if attempts remain.
- If Stage 4 improves text while preserving character, pose, outfit, lighting, and layout, finish.
- If Stage 4 changes the character or still cannot produce verifiable readable text after its limit, finish with `수동 보정 필요`.

Required final artifacts:

- `final-photoreal-reference.png`: the latest self-approved text-free live-action reference image from Stage 1 or Stage 2.
- `final-photoreal-character-sheet.png`: the latest self-approved layout and text-inclusive character sheet from Stage 3 or Stage 4, if one passed. If no text-inclusive sheet passes, still save the best failed candidate and mark it as needing human text correction.

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

Self-verification gate:

- Self-approve and proceed to Stage 3 only if the base is convincingly photoreal.
- Proceed to Stage 2 if the image still has anime, 3D, CGI, waxy skin, plastic skin, or overly clean AI traits.
- Retry Stage 1 if the base is structurally unusable and Stage 1 attempts remain.
- Finish with a final report if no valid next action remains within the attempt limits.

### Stage 2: Photoreal Intensification

Use `$intensify-photoreal-character` when needed.

Goal:

- Remove remaining 2D, 3D, CGI, game-render, plastic, or over-retouched qualities.
- Keep expression, emotion, pose, clothing, and layout stable.

Report:

- Which artifacts were targeted.
- What should remain unchanged.
- Whether the result now passes the live-action photo threshold.

Self-verification gate:

- Self-approve and proceed to Stage 3 only if the result passes the live-action photo threshold.
- Retry Stage 2 if it still fails the threshold and Stage 2 attempts remain.
- Fall back to Stage 1 if Stage 2 fails after its limit and Stage 1 attempts remain.
- Finish with a final report if no valid next action remains within the attempt limits.

### Stage 3: Layout and Text Restoration

Use `$restore-photoreal-sheet-layout`.

Goal:

- Keep the self-approved photoreal character unchanged.
- Restore the original 2D sheet's information structure, view layout, labels, and text boxes.
- Make text readable without pulling the character back into illustration.

Report:

- Which layout elements were restored.
- How text readability was handled.
- Whether character realism stayed intact.

Self-verification gate:

- Self-approve and finish when character realism, layout, and text are all acceptable.
- Proceed to Stage 4 when the character is good but text or labels are broken, blurry, misaligned, or unreadable.
- Retry Stage 3 if layout restoration failed or pulled the character back toward illustration and Stage 3 attempts remain.
- Return to Stage 2 if character quality regressed and Stage 2 attempts remain.
- Finish with a final report if no valid next action remains within the attempt limits.

### Stage 4: Text Repair

Use `$repair-photoreal-sheet-text` only for text and labels.

Goal:

- Preserve character, pose, outfit, lighting, and layout.
- Fix only broken, blurry, misaligned, or unreadable text and labels.

Report:

- Which text areas were repaired.
- Whether any character or layout changes occurred.
- Remaining text risk, if any.

Self-verification gate:

- Finish only when repaired text can be verified and the character remained stable.
- Retry Stage 4 if text repair changed the character, pose, outfit, lighting, or layout and Stage 4 attempts remain.
- Finish with `수동 보정 필요` if the model still cannot produce verifiable readable text after the Stage 4 attempt limit.

## Reporting Format

Before each stage, send a concise Korean execution report:

```text
[N단계 실행 예정]
- 입력: ...
- 저장 폴더: ...
- 단계 목표: ...
- 생성 후 재개: ...
- 피드백: 최종 결과 보고에서만 받음
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

Use the same report shape but label mid-stage checks as `[N단계 자체 검수]` when the next action is decided without user input. Include the chosen next action and the attempt count. Only the final report includes feedback options.

Final report:

```text
[최종 결과]
- 저장 폴더: ...
- 실사 레퍼런스: ...
- 텍스트 포함 캐릭터 시트: ...
- 자체 재시도 이력: ...
- 통과/실패 기준: ...
- 남은 리스크: ...
- 다음 선택:
  1. 완료
  2. 텍스트만 추가 보정
  3. 실사감만 추가 강화
  4. 전체 재생성
  5. 중단
```

Do not present numbered feedback options before the final report.

## Self-Verification Rules

Photorealism check:

- Pass only when skin, hair, clothing, lighting, and materials look like real photography.
- Fail or intensify when the image shows anime proportions, illustration lines, 3D/CGI rendering, waxy skin, plastic skin, glossy AI smoothness, mannequin anatomy, or over-retouched symmetry.

Layout check:

- Pass only when the final sheet keeps the original broad information structure: full-body reference, turnaround, face/eye detail, outfit detail, lower-body/accessory detail, and profile or key-point panels when present.
- Fail or regenerate when the layout loses the reference-sheet purpose, omits major view groups, crops core design details, or lets graphic elements overpower the character.

Text check:

- Claim text is readable only for areas that were inspected and can actually be read.
- Treat broken text, fake typography, hallucinated labels, blurry labels, or misaligned text boxes as Stage 4 input.
- If text remains unreliable after Stage 4 limits, stop and report human text correction as required instead of continuing to regenerate.

## Operating Rules

- Do not use or include the compressed prompt variant.
- Prefer staged editing over one-shot generation.
- Preserve only the latest self-approved image as the next stage input.
- Advance only after self-verification, state update, and attempt-limit check. Ask for feedback only in the final report.
- Do not chain multiple image generation stages in one assistant turn. Run one generation per turn and resume on the next user message or temporary heartbeat.
- When using an image generation or editing tool, submit only the current stage prompt plus the required image inputs. Do not mix future-stage layout or text restoration instructions into Stage 1 or Stage 2.
- When a model struggles with text, keep the character image stable and isolate text repair in Stage 4.
- Do not claim text is readable, exact, repaired, or complete unless it was inspected and verified.
- Do not exceed the retry limits. A clear final report with `수동 보정 필요` is better than unbounded regeneration.
