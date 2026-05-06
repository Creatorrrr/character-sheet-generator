---
name: convert-2d-sheet-to-photoreal
description: Use when the user wants staged 2D to photoreal live-action character sheet conversion, step-by-step feedback gates, final-only autonomous continuation, self-verification, or coordination across the photoreal base, intensify, layout restore, and text repair stage skills.
---

# Convert 2D Sheet to Photoreal

## Overview

Manage a staged image workflow that separates photoreal character conversion from text and layout restoration. Use the sibling stage skills in order. The default is step-by-step approval, but when the user asks for autonomous continuation, continue through self-verification and regeneration gates without asking for user feedback until the final report.

## Default Output Location

If the user does not specify where to save files, create a new run folder under `/Users/chasoik/Projects/character-sheet-generator/output/`.

- Use `output/<slug>-photoreal-sheet-YYYYMMDD-HHMMSS/` for this workflow.
- Build `<slug>` from the character name, then the input image filename stem, then `photoreal-sheet`. Normalize it to lowercase ASCII letters, numbers, and hyphens. If the normalized value is empty, use `photoreal-sheet`.
- If the user is resuming from an existing run folder, keep using that folder instead of creating a new one.
- Save Stage 1-4 outputs, approved intermediates, repair outputs, notes, and optional state or resume artifacts under the selected run folder.
- In autonomous continuation mode, keep `workflow-state.json` and a short `verification-notes.md` in the run folder so the next resumed turn knows the current stage, attempt counts, latest accepted image, latest rejected image, and next intended action.
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
- Whether the user wants manual step-by-step approval or autonomous continuation.

Default to manual step-by-step approval unless the user explicitly asks for autonomous continuation, final-only feedback, self-verification, or no mid-stage feedback. In autonomous mode, the user gives feedback only after the final report.

If no source image is available, ask for it. If the user provides an existing intermediate image, resume from the matching stage instead of restarting.

## Turn Protocol for Image Generation

Image generation calls end the current assistant turn. Because of that, each generation must be split across turns:

1. Before generating or editing an image, send a Korean `[N단계 실행 예정]` report with the current input, run folder, stage goal, resume behavior, and either manual feedback options or the autonomous final-only feedback note.
2. In autonomous mode, before the image tool call, update `workflow-state.json` and create or update a temporary thread heartbeat so this same thread wakes up shortly after the image generation turn ends.
3. Submit only the current stage prompt and required image inputs to the image generation or editing tool.
4. Treat the image generation call as the last action of that turn. Do not append a result report, quality claim, or next-step question after the tool call.
5. On the next user message or heartbeat resume, copy or reference the generated artifact under the run folder when possible, inspect the image if available, then send the Korean `[N단계 결과]` or `[N단계 자체 검수]` report.
6. In manual mode, do not start the next stage until the user chooses one of the feedback-gate options for the completed stage.
7. In autonomous mode, do not ask for mid-stage feedback. Decide the next action from the self-verification rules, record the decision in `verification-notes.md`, then either start the next generation or finish with the final report. Delete or pause the temporary heartbeat when the workflow reaches a terminal final report.

## Autonomous Continuation Mode

Use this mode only when the user explicitly requests autonomous continuation, final-only feedback, self-verification, or no mid-stage feedback. Keep the step-by-step reports factual, but treat them as progress logs rather than user gates.

Required state:

- `workflow-state.json`: `mode`, `stage`, `attemptsByStage`, `sourceImage`, `latestAcceptedImage`, `latestRejectedImage`, `nextAction`, and `terminalReason`.
- `verification-notes.md`: chronological notes with each generated artifact, pass/fail decision, visible defects, and why the next stage or retry was chosen.

Attempt limits:

- Stage 1: maximum 2 attempts.
- Stage 2: maximum 2 attempts.
- Stage 3: maximum 2 attempts.
- Stage 4: maximum 2 attempts.
- If a stage still fails after its limit, do not keep regenerating. Finish with a final report that names the failed stage and the manual follow-up needed.

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
- `final-photoreal-character-sheet.png`: the latest self-approved layout and text-inclusive character sheet from Stage 3 or Stage 4, if one passed. If no text-inclusive sheet passes, still save the best failed candidate and mark it as needing manual correction.

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

- In manual mode, stop after reporting the Stage 1 result and ask the user to choose one option.
- Manual options: `Stage 3 진행`, `Stage 2로 실사감 강화`, `Stage 1 재생성`, `중단`.
- Recommend `Stage 2로 실사감 강화` if the image still has anime, 3D, CGI, waxy skin, plastic skin, or overly clean AI traits.
- Recommend `Stage 3 진행` only if the base is convincingly photoreal.
- In autonomous mode, self-approve and proceed to Stage 3 only if the base is convincingly photoreal; otherwise proceed to Stage 2, or retry Stage 1 if the base is structurally unusable.

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

- In manual mode, stop after reporting the Stage 2 result and ask the user to choose one option.
- Manual options: `Stage 3 진행`, `Stage 2 재시도`, `Stage 1부터 재생성`, `중단`.
- Recommend `Stage 2 재시도` if it still fails the live-action photo threshold.
- Recommend `Stage 3 진행` only if the result passes the live-action photo threshold.
- In autonomous mode, self-approve and proceed to Stage 3 only if the result passes the live-action photo threshold; otherwise retry Stage 2 until the attempt limit, then fall back to Stage 1 if allowed.

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

- In manual mode, stop after reporting the Stage 3 result and ask the user to choose one option.
- Manual options: `완료`, `Stage 4 텍스트 보정`, `Stage 3 재생성`, `Stage 2로 회귀`.
- Recommend `Stage 2로 회귀` if character quality regressed.
- Recommend `Stage 3 재생성` if layout restoration failed or pulled the character back toward illustration.
- Recommend `Stage 4 텍스트 보정` only when the character is good but text or labels are broken, blurry, misaligned, or unreadable.
- Recommend `완료` only when character realism, layout, and text are all acceptable.
- In autonomous mode, self-approve only when character realism, layout, and text are all acceptable; go to Stage 4 when only text needs repair; retry Stage 3 or return to Stage 2 when character realism or layout regressed.

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

- In manual mode, stop after reporting the Stage 4 result and ask the user to choose one option.
- Manual options: `완료`, `Stage 4 재시도`, `수동 보정 필요로 종료`.
- Recommend `Stage 4 재시도` if text repair changed the character, pose, outfit, lighting, or layout.
- Recommend `수동 보정 필요로 종료` if the model still cannot produce verifiable readable text after a focused repair.
- Recommend `완료` only when the repaired text can be verified and the character remained stable.
- In autonomous mode, finish only when repaired text can be verified and the character remained stable; otherwise retry Stage 4 until the attempt limit, then finish with `수동 보정 필요`.

## Reporting Format

Before each stage, send a concise Korean execution report:

```text
[N단계 실행 예정]
- 입력: ...
- 저장 폴더: ...
- 단계 목표: ...
- 생성 후 재개: ...
- 피드백: ...
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

In autonomous mode, use the same report shape but label mid-stage checks as `[N단계 자체 검수]` when the next action is decided without user input. Include the chosen next action and the attempt count. Only the final report includes feedback options.

Final autonomous report:

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

Do not present numbered feedback options before the final autonomous report.

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
- If text remains unreliable after Stage 4 limits, stop and report manual text correction as required instead of continuing to regenerate.

## Operating Rules

- Do not use or include the compressed prompt variant.
- Prefer staged editing over one-shot generation.
- Preserve only the latest user-approved image in manual mode, or the latest self-approved image in autonomous mode, as the next stage input.
- Pause for user feedback at every gate in manual mode. Do not advance to the next stage without an explicit user choice.
- In autonomous mode, advance only after self-verification, state update, and attempt-limit check. Ask for feedback only in the final report.
- Do not chain multiple image generation stages in one assistant turn. Run one generation per turn and resume on the next user message or temporary heartbeat.
- When using an image generation or editing tool, submit only the current stage prompt plus the required image inputs. Do not mix future-stage layout or text restoration instructions into Stage 1 or Stage 2.
- When a model struggles with text, keep the character image stable and isolate text repair in Stage 4.
- Do not claim text is readable, exact, repaired, or complete unless it was inspected and verified.
- In autonomous mode, do not exceed the retry limits. A clear final report with `수동 보정 필요` is better than unbounded regeneration.
