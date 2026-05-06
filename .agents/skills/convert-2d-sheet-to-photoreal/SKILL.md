---
name: convert-2d-sheet-to-photoreal
description: Use when the user wants staged 2D to photoreal live-action character sheet conversion with autonomous continuation, self-verification, final-only feedback, a layout-locked text-free final sheet, a text-restored final sheet, or coordination across the photoreal base, intensify, layout restore, and text repair stage skills.
---

# Convert 2D Sheet to Photoreal

## Overview

Manage a staged image workflow that first creates a photoreal text-free sheet with the same structure as the original 2D character sheet, then restores the original text onto that text-free final. Use the sibling stage skills in order. Always continue through self-verification and regeneration gates without asking for user feedback until the final report.

## Default Output Location

If the user does not specify where to save files, create a new run folder under `/Users/chasoik/Projects/character-sheet-generator/output/`.

- Use `output/<slug>-photoreal-sheet-YYYYMMDD-HHMMSS/` for this workflow.
- Build `<slug>` from the character name, then the input image filename stem, then `photoreal-sheet`. Normalize it to lowercase ASCII letters, numbers, and hyphens. If the normalized value is empty, use `photoreal-sheet`.
- If the user is resuming from an existing run folder, keep using that folder instead of creating a new one.
- Save Stage 1-4 outputs, self-approved intermediates, `final-photoreal-text-free-sheet.png`, `final-photoreal-character-sheet.png`, repair outputs, notes, and optional state or resume artifacts under the selected run folder.
- Keep `structure-inventory.md`, `workflow-state.json`, and a short `verification-notes.md` in the run folder so the next resumed turn knows the original structure/content contract, current stage, attempt counts, latest accepted image, latest rejected image, and next intended action.
- When reporting artifacts, include the selected run folder and write output paths under that folder.

## Stage Skills

Use these sibling skills from the same `.agents/skills` skill root:

1. `$create-photoreal-character-base` for a text-free live-action sheet that preserves the original canvas, panel layout, view positions, and non-text graphics.
2. `$intensify-photoreal-character` when the base still feels anime, 3D, CGI, plastic, or overly AI-smoothed.
3. `$restore-photoreal-sheet-layout` to restore original text onto the self-approved `final-photoreal-text-free-sheet.png` without changing layout or character content.
4. `$repair-photoreal-sheet-text` only when the final character is good but text or labels need cleanup.

If explicit skill invocation is unavailable, open the matching sibling `SKILL.md` and follow it directly.

## Intake

Before generating or editing, identify:

- Original 2D character sheet image.
- Current stage image, if the user is resuming.
- Original structure/content inventory, if the user is resuming.
- Required text preservation level: exact, approximate, translated, or omit until later.
- Any explicit final-output preference or constraint.

The text removal scope for the text-free sheet is always full removal: title, section numbers, labels, descriptions, captions, logo text, model name, and all other readable text must be removed while non-text structure remains.

If no source image is available, ask for it. If the user provides an existing intermediate image, resume from the matching stage instead of restarting.

## Structure/Content Inventory

Before Stage 1, inspect the original 2D sheet and create `structure-inventory.md` in the run folder. This inventory is the acceptance contract for every later stage.

Inventory requirements:

- Derive the inventory from the current source image. Do not hard-code section names or known problem areas from prior runs.
- Record every visible section, panel group, image slot, text slot, callout target, color chip group, and repeated view/detail cell.
- For each image slot, record its relative location, role, expected view or crop type, direction or expression when applicable, and the mandatory visual content that must stay distinct.
- For each text slot, record its relative location, hierarchy, and whether it should be removed in the text-free stages or restored in the text-inclusive stages.
- Treat slot count and slot meaning as locked. Two source slots must not be merged into one output slot, one source slot must not be omitted, and a slot must not change into a different expression, direction, detail target, prop, outfit area, or body part.
- Record any source text or tiny details that are not legible enough to verify exactly; do not later claim exact restoration for those areas.

Use `structure-inventory.md` during prompt construction and self-verification. If it is missing on resume, rebuild it from the source image before approving any stage.

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

- `workflow-state.json`: `stage`, `attemptsByStage`, `sourceImage`, `structureInventory`, `latestAcceptedImage`, `latestRejectedImage`, `nextAction`, and `terminalReason`.
- `structure-inventory.md`: original section/panel/slot contract and any source details that cannot be verified exactly.
- `verification-notes.md`: chronological notes with each generated artifact, pass/fail decision, visible defects, and why the next stage or retry was chosen.

Attempt limits:

- Stage 1: maximum 2 attempts.
- Stage 2: maximum 2 attempts.
- Stage 3: maximum 2 attempts.
- Stage 4: maximum 2 attempts.
- If a stage still fails after its limit, do not keep regenerating. Finish with a final report that names the failed stage and the human follow-up needed.

Autonomous decisions:

- If Stage 1 is convincingly live-action, preserves the original sheet structure/content inventory, and removes all readable text, self-approve it as `final-photoreal-text-free-sheet.png` and proceed to Stage 3.
- If Stage 1 preserves the structure/content inventory and removes text but still has anime, 3D, CGI, waxy skin, plastic skin, or overly clean AI traits, proceed to Stage 2.
- If Stage 1 changes the original layout, omits major panels/views, merges image slots, changes a slot's meaning, replaces a detail/expression/direction with another, or leaves readable/fake text, retry Stage 1 if attempts remain.
- If Stage 2 passes the live-action threshold while preserving the text-free sheet layout/content inventory and adding no text, self-approve it as `final-photoreal-text-free-sheet.png` and proceed to Stage 3.
- If Stage 2 adds text, changes layout, merges/omits slots, or changes slot meaning, retry Stage 2 until the attempt limit, then fall back to Stage 1 if allowed.
- If Stage 2 still fails the live-action threshold after its limit, regenerate Stage 1 once if Stage 1 attempts remain; otherwise finish with a failure report.
- If Stage 3 restores readable original text while preserving the text-free sheet's character, panels, layout, non-text graphics, and image-slot content, self-approve it as `final-photoreal-character-sheet.png` and finish.
- If Stage 3 preserves character realism and layout but text is broken, blurry, misaligned, fake, or unreadable, proceed to Stage 4.
- If Stage 3 changes the character, pulls the character back toward illustration, changes the locked text-free layout, merges/omits slots, or changes image-slot content, retry Stage 3 if attempts remain; otherwise return to Stage 2 if attempts remain.
- If Stage 4 improves text while preserving character, pose, outfit, lighting, layout, and image-slot content, finish.
- If Stage 4 changes the character/structure/content or still cannot produce verifiable readable text after its limit, finish with `수동 보정 필요`.

Required final artifacts:

- `final-photoreal-text-free-sheet.png`: the latest self-approved text-free live-action sheet from Stage 1 or Stage 2. It must preserve the original canvas ratio, panel structure, view positions, slot count, slot meaning, and non-text graphics while removing all readable text.
- `final-photoreal-character-sheet.png`: the latest self-approved text-inclusive character sheet from Stage 3 or Stage 4. It must be built on top of `final-photoreal-text-free-sheet.png` by restoring original text without changing character, layout, non-text graphics, slot count, or slot meaning. If no text-inclusive sheet passes, still save the best failed candidate and mark it as needing human text correction.

## Workflow

### Stage 1: Photoreal Base

Use `$create-photoreal-character-base`.

Goal:

- Remove all readable text while preserving text boxes, panels, callout lines, color chips, and other non-text structure.
- Preserve character identity, hair, outfit, pose, expression, original canvas ratio, panel layout, and view positions.
- Preserve every image slot from `structure-inventory.md` as a distinct 1:1 slot with the same role, view, expression, crop target, prop, outfit area, and body part.
- Produce a text-free sheet that looks like real live-action reference photography, not illustration, 3D render, or cosplay poster.

Report:

- What source image was used.
- What identity and costume details were preserved.
- Whether all readable text was removed.
- Whether the original layout and panel structure stayed aligned.
- Whether all inventory slots stayed distinct and semantically matched the source.
- Any remaining non-photoreal risk.

Self-verification gate:

- Self-approve as `final-photoreal-text-free-sheet.png` and proceed to Stage 3 only if the base is convincingly photoreal, matches the original structure, and contains no readable or fake text.
- Proceed to Stage 2 if the image matches the original structure and contains no text but still has anime, 3D, CGI, waxy skin, plastic skin, or overly clean AI traits.
- Retry Stage 1 if the base changes the original layout, omits major panels/views, merges slots, changes slot meaning, replaces a source detail/expression/direction with another, leaves readable or fake text, or is structurally unusable.
- Finish with a final report if no valid next action remains within the attempt limits.

### Stage 2: Photoreal Intensification

Use `$intensify-photoreal-character` when needed.

Goal:

- Remove remaining 2D, 3D, CGI, game-render, plastic, or over-retouched qualities.
- Keep expression, emotion, pose, clothing, original text-free layout, empty text areas, non-text graphics, and every inventory image slot stable.

Report:

- Which artifacts were targeted.
- What should remain unchanged.
- Whether the result now passes the live-action photo threshold.
- Whether the result still matches the source inventory and previous text-free input.

Self-verification gate:

- Self-approve as `final-photoreal-text-free-sheet.png` and proceed to Stage 3 only if the result passes the live-action photo threshold while preserving original structure/content inventory and adding no text.
- Retry Stage 2 if it still fails the threshold, changes layout, merges/omits slots, changes slot meaning, or adds readable/fake text and Stage 2 attempts remain.
- Fall back to Stage 1 if Stage 2 fails after its limit and Stage 1 attempts remain.
- Finish with a final report if no valid next action remains within the attempt limits.

### Stage 3: Text Restoration On Text-Free Sheet

Use `$restore-photoreal-sheet-layout`.

Goal:

- Use `final-photoreal-text-free-sheet.png` as the locked visual base.
- Restore the original 2D sheet's readable text, labels, section numbers, captions, logo text, and descriptions at the corresponding original positions.
- Keep character, panels, view positions, image-slot content, text boxes, callout lines, color chips, and other non-text graphics unchanged.
- Make text readable without pulling the character back into illustration.

Report:

- Which text areas, labels, section numbers, captions, or descriptions were restored.
- How text readability was handled.
- Whether character realism stayed intact.
- Whether the locked text-free layout stayed unchanged.
- Whether every non-text slot still matches the locked text-free sheet and source inventory.

Self-verification gate:

- Self-approve as `final-photoreal-character-sheet.png` and finish when character realism, locked layout/content, and restored text are all acceptable.
- Proceed to Stage 4 when the character and non-text structure/content are good but text or labels are broken, blurry, misaligned, fake, or unreadable.
- Retry Stage 3 if text restoration changed layout, changed the character, failed to restore text at corresponding positions, merged/omitted slots, changed slot meaning, changed image-slot content versus the text-free base, or pulled the character back toward illustration and Stage 3 attempts remain.
- Return to Stage 2 if character quality regressed and Stage 2 attempts remain.
- Finish with a final report if no valid next action remains within the attempt limits.

### Stage 4: Text Repair

Use `$repair-photoreal-sheet-text` only for text and labels.

Goal:

- Preserve character, pose, outfit, lighting, and layout.
- Fix only broken, blurry, misaligned, or unreadable text and labels.
- Preserve every non-text image slot from the Stage 3 input and `final-photoreal-text-free-sheet.png`.

Report:

- Which text areas were repaired.
- Whether any character or layout changes occurred.
- Whether any non-text slot content changed versus Stage 3 and the locked text-free base.
- Remaining text risk, if any.

Self-verification gate:

- Finish only when repaired text can be verified and the character, layout, and non-text slot content remained stable.
- Retry Stage 4 if text repair changed the character, pose, outfit, lighting, layout, slot count, or slot meaning and Stage 4 attempts remain.
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
- 무텍스트 실사 시트: ...
- 텍스트 포함 캐릭터 시트: ...
- 자체 재시도 이력: ...
- 통과/실패 기준: ...
- 구조/내용 동등성: ...
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

- Pass the text-free sheet only when it keeps the original canvas ratio, panel grid, major view groups, detail-panel positions, empty text areas, callout lines, boxes, color chips, and non-text graphic structure.
- Pass the text-inclusive sheet only when it preserves the self-approved text-free layout and adds text at corresponding original positions.
- Fail or regenerate when the layout loses the reference-sheet purpose, omits major view groups, crops core design details, changes non-text graphics, adds a new UI structure, or lets graphic elements overpower the character.

Structure/content equivalence check:

- Compare every generated candidate against `structure-inventory.md`; for Stage 3 and Stage 4, compare against both the original source inventory and `final-photoreal-text-free-sheet.png`.
- Pass only when every original image slot remains present, separate, and semantically equivalent: the same role, view/crop type, expression or direction when applicable, prop/outfit/body-part target, and mandatory visible content.
- Fail if any candidate merges multiple source slots into one image, omits a source slot, duplicates one slot to cover another, swaps the meaning of a slot, replaces a detail target with a different target, changes a required expression/direction/pose, or changes non-text content during a text-only stage.
- Record the mismatch in `verification-notes.md` by source section/panel/slot type without hard-coding recurring problem-item names into the skill.

Text check:

- For the text-free sheet, fail if any readable text, section number, label, caption, logo text, or fake typography remains.
- Claim text is readable only for areas that were inspected and can actually be read.
- Treat broken text, fake typography, hallucinated labels, blurry labels, or misaligned text boxes as Stage 4 input only when structure/content equivalence still passes.
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
