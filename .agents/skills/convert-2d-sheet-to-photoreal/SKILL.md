---
name: convert-2d-sheet-to-photoreal
description: Use when the user wants staged 2D to photoreal live-action character sheet conversion with autonomous continuation, self-verification, final-only feedback, a layout-locked text-free final sheet, a text-restored final sheet, or coordination across the photoreal base, intensify, layout restore, and text repair stage skills.
---

# Convert 2D Sheet to Photoreal

## Overview

Manage a staged image workflow that first creates a photoreal text-free sheet with the same structure as the original 2D character sheet, then restores the original sheet annotation text onto that text-free final. In this workflow, `text-free` means sheet-annotation-free: remove labels, captions, titles, and description text from the sheet UI, but preserve typography or logo-like marks that are part of the character image, costume, props, accessories, patches, embroidery, or engravings. Use the sibling stage skills in order. Always continue through self-verification and regeneration gates without asking for user feedback until the final report.

## Default Output Location

If the user does not specify where to save files, create a new run folder under `/Users/chasoik/Projects/character-sheet-generator/output/`.

- Use `output/<slug>-photoreal-sheet-YYYYMMDD-HHMMSS/` for this workflow.
- Build `<slug>` from the character name, then the input image filename stem, then `photoreal-sheet`. Normalize it to lowercase ASCII letters, numbers, and hyphens. If the normalized value is empty, use `photoreal-sheet`.
- If the user is resuming from an existing run folder, keep using that folder instead of creating a new one.
- Save Stage 1-4 outputs, self-approved intermediates, `final-photoreal-text-free-sheet.png`, `final-photoreal-character-sheet.png`, repair outputs, notes, and optional state or resume artifacts under the selected run folder.
- Keep `structure-inventory.md`, `workflow-state.json`, and a short `verification-notes.md` in the run folder so the next resumed turn knows the original structure/content contract, Character Appearance Lock, current stage, attempt counts, latest accepted image, latest rejected image, and next intended action.
- When reporting artifacts, include the selected run folder and write output paths under that folder.

## Stage Skills

Use these sibling skills from the same `.agents/skills` skill root:

1. `$create-photoreal-character-base` for a text-free live-action sheet that preserves the original canvas, panel layout, view positions, non-text graphics, and in-image costume/prop typography.
2. `$intensify-photoreal-character` when the base still feels anime, 3D, CGI, plastic, or overly AI-smoothed.
3. `$restore-photoreal-sheet-layout` to restore original sheet annotation text onto the self-approved `final-photoreal-text-free-sheet.png` without changing layout, character content, or the approved photoreal image set.
4. `$repair-photoreal-sheet-text` only when the final character and approved photoreal image set are good but sheet annotation text or labels need cleanup.

If explicit skill invocation is unavailable, open the matching sibling `SKILL.md` and follow it directly.

## Intake

Before generating or editing, identify:

- Original 2D character sheet image.
- Current stage image, if the user is resuming.
- Original structure/content inventory, if the user is resuming.
- Required sheet annotation text preservation level for the final text-inclusive sheet: exact, approximate, translated, or omit until later.
- Any explicit final-output preference or constraint.

The text removal scope for the text-free sheet is full removal of sheet annotation text: title, section numbers, labels, descriptions, captions, UI logo text, model name, version marks, and other readable text that belongs to the sheet layout must be removed while non-text structure remains.

Do not remove typography that is part of the character image itself. Preserve original printed, embroidered, engraved, patched, or logo-like text on clothing, props, accessories, weapons, bags, shoes, or other image-slot content as costume/prop design detail. If that in-image typography is too small or blurry to verify exactly, preserve its visible placement, scale, color, and design character without claiming exact text fidelity.

If no source image is available, ask for it. If the user provides an existing intermediate image, resume from the matching stage instead of restarting.

## Structure/Content Inventory

Before Stage 1, inspect the original 2D sheet and create `structure-inventory.md` in the run folder. This inventory is the acceptance contract for every later stage.

Inventory requirements:

- Derive the inventory from the current source image. Do not hard-code section names or known problem areas from prior runs.
- Record every visible section, panel group, image slot, text slot, callout target, color chip group, and repeated view/detail cell.
- For each image slot, record its relative location, role, expected view or crop type, direction or expression when applicable, and the mandatory visual content that must stay distinct.
- For each image slot that contains costume, prop, accessory, or object typography, record it as mandatory visual content or costume/prop typography, not as a removable text slot.
- For each text slot, record only sheet annotation text: its relative location, hierarchy, and whether it should be removed in the text-free stages or restored in the text-inclusive stages.
- Add a `Character Appearance Lock` section derived only from visible source evidence. Record apparent age/maturity, height/stature impression, body type and body proportions, head-to-body ratio, silhouette, posture, face shape, cheek/jaw/chin softness, eye shape, brow shape, nose/mouth/lip traits, skin tone/visible marks, hair silhouette, expression intensity, and emotional/personality impression.
- Treat slot count and slot meaning as locked. Two source slots must not be merged into one output slot, one source slot must not be omitted, and a slot must not change into a different expression, direction, detail target, prop, outfit area, or body part.
- Treat the Character Appearance Lock as an identity contract, not a biological measurement. Do not infer exact biological age, exact height, race, or ethnicity; record only visible visual impressions needed to keep the same character after photoreal conversion.
- Record any source text or tiny details that are not legible enough to verify exactly; do not later claim exact restoration for those areas.

Use `structure-inventory.md` during prompt construction and self-verification. If it is missing or lacks the Character Appearance Lock on resume, rebuild it from the source image before approving any stage.

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

- `workflow-state.json`: `stage`, `attemptsByStage`, `sourceImage`, `structureInventory`, `appearanceLock`, `latestAcceptedImage`, `latestRejectedImage`, `nextAction`, and `terminalReason`. `appearanceLock` should point to the `Character Appearance Lock` section in `structure-inventory.md`, not to a separate file.
- `structure-inventory.md`: original section/panel/slot contract, Character Appearance Lock, and any source details that cannot be verified exactly.
- `verification-notes.md`: chronological notes with each generated artifact, pass/fail decision, visible defects, and why the next stage or retry was chosen.

Attempt limits:

- Stage 1: maximum 2 attempts.
- Stage 2: maximum 2 attempts.
- Stage 3: maximum 2 attempts.
- Stage 4: maximum 2 attempts.
- If a stage still fails after its limit, do not keep regenerating. Finish with a final report that names the failed stage and the human follow-up needed.

Autonomous decisions:

- If Stage 1 is convincingly live-action, preserves the original sheet structure/content inventory, preserves the Character Appearance Lock, removes all sheet annotation text, and preserves any original in-image costume/prop typography, self-approve it as `final-photoreal-text-free-sheet.png` and proceed to Stage 3.
- If Stage 1 preserves the structure/content inventory and Character Appearance Lock, removes sheet annotation text, preserves in-image costume/prop typography, but still has anime, 3D, CGI, waxy skin, plastic skin, or overly clean AI traits, proceed to Stage 2.
- If Stage 1 changes the original layout, omits major panels/views, merges image slots, changes a slot's meaning, replaces a detail/expression/direction with another, changes the Character Appearance Lock, leaves readable/fake sheet annotation text, or removes original in-image costume/prop typography, retry Stage 1 if attempts remain.
- If Stage 2 passes the live-action threshold while preserving the text-free sheet layout/content inventory, Character Appearance Lock, and adding no new sheet annotation text, self-approve it as `final-photoreal-text-free-sheet.png` and proceed to Stage 3.
- If Stage 2 adds new sheet annotation/fake text, changes or removes original in-image costume/prop typography, changes layout, merges/omits slots, changes slot meaning, or changes the Character Appearance Lock, retry Stage 2 until the attempt limit, then fall back to Stage 1 if allowed.
- If Stage 2 still fails the live-action threshold after its limit, regenerate Stage 1 once if Stage 1 attempts remain; otherwise finish with a failure report.
- If Stage 3 restores readable original sheet annotation text while preserving the text-free sheet's character, Character Appearance Lock, panels, layout, non-text graphics, in-image costume/prop typography, and the full approved photoreal image set, self-approve it as `final-photoreal-character-sheet.png` and finish.
- If Stage 3 preserves the approved photoreal image set, Character Appearance Lock, and layout but sheet annotation text is broken, blurry, misaligned, fake, or unreadable, proceed to Stage 4.
- If Stage 3 changes the character or Character Appearance Lock, pulls any image slot back toward illustration, redraws or replaces any image slot, changes the locked text-free layout, merges/omits slots, changes slot meaning, or changes image-slot content versus the text-free base, retry Stage 3 if attempts remain; otherwise finish with `수동 텍스트 오버레이 필요`.
- If Stage 4 improves sheet annotation text while preserving character, Character Appearance Lock, pose, outfit, lighting, layout, and the full approved photoreal image set, finish.
- If Stage 4 changes the character, Character Appearance Lock, structure/content, redraws or replaces any image slot, weakens the photoreal quality of any image slot, or still cannot produce verifiable readable sheet annotation text after its limit, finish with `수동 텍스트 오버레이 필요`.

Required final artifacts:

- `final-photoreal-text-free-sheet.png`: the latest self-approved text-free live-action sheet from Stage 1 or Stage 2. It must preserve the original canvas ratio, panel structure, view positions, slot count, slot meaning, Character Appearance Lock, non-text graphics, and original in-image costume/prop typography while removing all sheet annotation text.
- `final-photoreal-character-sheet.png`: the latest self-approved text-inclusive character sheet from Stage 3 or Stage 4. It must be built on top of `final-photoreal-text-free-sheet.png` by restoring original sheet annotation text without changing character, Character Appearance Lock, layout, non-text graphics, slot count, slot meaning, in-image costume/prop typography, or the approved photoreal image set. If no text-inclusive sheet passes, still save the best failed candidate and mark it as needing manual text overlay.

## Workflow

### Stage 1: Photoreal Base

Use `$create-photoreal-character-base`.

Goal:

- Remove all sheet annotation text while preserving text boxes, panels, callout lines, color chips, and other non-text structure.
- Preserve character identity, Character Appearance Lock, hair, outfit, in-image costume/prop typography, pose, expression, original canvas ratio, panel layout, and view positions.
- Preserve every image slot from `structure-inventory.md` as a distinct 1:1 slot with the same role, view, expression, crop target, prop, outfit area, and body part.
- Produce a text-free sheet that looks like real live-action reference photography, not illustration, 3D render, or cosplay poster.

Report:

- What source image was used.
- What identity and costume details were preserved.
- What 외형 동등성 details were preserved from the Character Appearance Lock and what risk remains.
- Whether all sheet annotation text was removed and any original in-image costume/prop typography was preserved.
- Whether the original layout and panel structure stayed aligned.
- Whether all inventory slots stayed distinct and semantically matched the source.
- Any remaining non-photoreal risk.

Self-verification gate:

- Self-approve as `final-photoreal-text-free-sheet.png` and proceed to Stage 3 only if the base is convincingly photoreal, matches the original structure, preserves the Character Appearance Lock, contains no readable or fake sheet annotation text, and preserves original in-image costume/prop typography.
- Proceed to Stage 2 if the image matches the original structure, preserves the Character Appearance Lock, contains no sheet annotation text, preserves in-image costume/prop typography, but still has anime, 3D, CGI, waxy skin, plastic skin, or overly clean AI traits.
- Retry Stage 1 if the base changes the original layout, omits major panels/views, merges slots, changes slot meaning, replaces a source detail/expression/direction with another, changes the Character Appearance Lock, leaves readable or fake sheet annotation text, removes original in-image costume/prop typography, or is structurally unusable.
- Finish with a final report if no valid next action remains within the attempt limits.

### Stage 2: Photoreal Intensification

Use `$intensify-photoreal-character` when needed.

Goal:

- Remove remaining 2D, 3D, CGI, game-render, plastic, or over-retouched qualities.
- Keep expression, emotion, pose, clothing, Character Appearance Lock, original in-image costume/prop typography, original text-free layout, empty sheet annotation areas, non-text graphics, and every inventory image slot stable.

Report:

- Which artifacts were targeted.
- What should remain unchanged.
- Whether 외형 동등성 stayed aligned with the Character Appearance Lock while realism improved.
- Whether the result now passes the live-action photo threshold.
- Whether the result still matches the source inventory and previous text-free input.

Self-verification gate:

- Self-approve as `final-photoreal-text-free-sheet.png` and proceed to Stage 3 only if the result passes the live-action photo threshold while preserving original structure/content inventory, Character Appearance Lock, and adding no sheet annotation text.
- Retry Stage 2 if it still fails the threshold, changes layout, merges/omits slots, changes slot meaning, changes the Character Appearance Lock, changes/removes original in-image costume/prop typography, or adds readable/fake sheet annotation text and Stage 2 attempts remain.
- Fall back to Stage 1 if Stage 2 fails after its limit and Stage 1 attempts remain.
- Finish with a final report if no valid next action remains within the attempt limits.

### Stage 3: Text Restoration On Text-Free Sheet

Use `$restore-photoreal-sheet-layout`.

Goal:

- Use `final-photoreal-text-free-sheet.png` as the locked visual base.
- Restore the original 2D sheet's readable sheet annotation text, labels, section numbers, captions, UI logo text, and descriptions at the corresponding original positions.
- Keep character, Character Appearance Lock, panels, view positions, image-slot content, in-image costume/prop typography, text boxes, callout lines, color chips, and other non-text graphics unchanged.
- Treat the full image set inside `final-photoreal-text-free-sheet.png` as locked: every image slot must keep the same location, count, role, content, view, crop target, detail target, and photoreal live-action style.
- Make text readable without pulling the character back into illustration.

Report:

- Which sheet annotation text areas, labels, section numbers, captions, or descriptions were restored.
- How text readability was handled.
- Whether character realism stayed intact.
- Whether 외형 동등성 and the Character Appearance Lock stayed intact.
- Whether the locked text-free layout stayed unchanged.
- Whether every non-text slot, image slot, and in-image costume/prop typography still matches the locked text-free sheet and source inventory.
- Whether any image slot was redrawn, replaced, or shifted away from the approved photoreal image set.

Self-verification gate:

- Self-approve as `final-photoreal-character-sheet.png` and finish only when restored text is acceptable and the locked photoreal image set and Character Appearance Lock remain unchanged and still look photographic.
- Proceed to Stage 4 only when the approved photoreal image set and non-text structure/content are good but sheet annotation text or labels are broken, blurry, misaligned, fake, or unreadable.
- Retry Stage 3 if sheet annotation text restoration changed layout, changed the character or Character Appearance Lock, failed to restore text at corresponding positions, merged/omitted slots, changed slot meaning, changed in-image costume/prop typography, changed image-slot content versus the text-free base, redrew or replaced any image slot, or pulled any image slot toward illustration, anime, line-art, CGI, 3D render, or semi-realistic painting and Stage 3 attempts remain.
- Finish with `수동 텍스트 오버레이 필요` if no valid Stage 3 retry remains and the image set cannot stay locked during generative text restoration.

### Stage 4: Text Repair

Use `$repair-photoreal-sheet-text` only for text and labels.

Goal:

- Preserve character, Character Appearance Lock, pose, outfit, lighting, and layout.
- Fix only broken, blurry, misaligned, or unreadable sheet annotation text and labels.
- Preserve every non-text image slot and in-image costume/prop typography from the Stage 3 input and `final-photoreal-text-free-sheet.png`.
- Treat image-slot preservation as a hard gate, not a preference: text repair must not redraw, repaint, restyle, crop, replace, or otherwise modify the approved photoreal image set.

Report:

- Which sheet annotation text areas were repaired.
- Whether any character or layout changes occurred.
- Whether 외형 동등성 and the Character Appearance Lock stayed intact.
- Whether any non-text slot content, image slot, or in-image costume/prop typography changed versus Stage 3 and the locked text-free base.
- Whether every image slot still looks like the approved live-action photoreal base after text repair.
- Remaining text risk, if any.

Self-verification gate:

- Finish only when repaired sheet annotation text can be verified and the character, Character Appearance Lock, layout, in-image costume/prop typography, non-text slot content, and approved photoreal image set remained stable.
- Retry Stage 4 if sheet annotation text repair changed the character, Character Appearance Lock, pose, outfit, in-image costume/prop typography, lighting, layout, slot count, slot meaning, any image-slot content, or the photoreal quality of any image slot and Stage 4 attempts remain.
- Finish with `수동 텍스트 오버레이 필요` if the model still cannot produce verifiable readable sheet annotation text without changing the approved photoreal image set after the Stage 4 attempt limit.

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
- 외형 동등성: ...
- 검수 결과: ...
- 다음 결정: ...
```

Keep reports factual. Do not claim sheet annotation text is readable unless it was inspected. Do not claim a stage passed if obvious visual artifacts remain.

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
- 외형 동등성: ...
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
- For Stage 3 and Stage 4, apply the same photorealism check to every image slot in the text-inclusive result. A text-inclusive sheet fails even if the text improved when any image slot regresses from the approved text-free photoreal image set into illustration, anime, line-art, CGI, 3D render, or semi-realistic painting.

Layout check:

- Pass the text-free sheet only when it keeps the original canvas ratio, panel grid, major view groups, detail-panel positions, empty sheet annotation areas, callout lines, boxes, color chips, non-text graphic structure, and original in-image costume/prop typography.
- Pass the text-inclusive sheet only when it preserves the self-approved text-free layout, preserves the approved photoreal image set, and adds sheet annotation text at corresponding original positions.
- Fail or regenerate when the layout loses the reference-sheet purpose, omits major view groups, crops core design details, changes non-text graphics, adds a new UI structure, or lets graphic elements overpower the character.

Structure/content equivalence check:

- Compare every generated candidate against `structure-inventory.md`; for Stage 3 and Stage 4, compare image slots against `final-photoreal-text-free-sheet.png` as the locked photoreal image-set source of truth, while using the original source only for sheet annotation text and placement.
- Pass only when every original image slot remains present, separate, and semantically equivalent: the same role, view/crop type, expression or direction when applicable, prop/outfit/body-part target, and mandatory visible content.
- For Stage 3 and Stage 4, pass only when every image slot also remains equivalent to the approved text-free photoreal base in location, count, role, content, view, crop target, detail target, and live-action photographic style.
- Fail if any candidate merges multiple source slots into one image, omits a source slot, duplicates one slot to cover another, swaps the meaning of a slot, replaces a detail target with a different target, changes a required expression/direction/pose, removes original in-image costume/prop typography, changes non-text content during a sheet annotation-only stage, redraws or replaces an image slot, or weakens any image slot from the approved photoreal base into illustration, anime, line-art, CGI, 3D render, or semi-realistic painting.
- Record the mismatch in `verification-notes.md` by source section/panel/slot type plus the observed symptom, such as changed content, changed view, changed crop, redrawn slot, lost photoreal style, or changed in-image typography. Do not hard-code recurring problem-item names into the skill.

Appearance/Likeness equivalence check:

- Compare every generated candidate against the `Character Appearance Lock` in `structure-inventory.md`. Treat 외형 동등성 as a hard gate alongside layout and slot meaning.
- Pass only when the photoreal person still reads like the same character after realistic human translation: same apparent age/maturity impression, height/stature impression, body type and body proportions, head-to-body ratio, silhouette, posture, face shape, cheek/jaw/chin softness, eye shape, brow shape, nose/mouth/lip traits, skin tone/visible marks, hair silhouette, expression intensity, and emotional/personality impression.
- Fail Stage 1 or Stage 2 if realism improvement looks like recasting the character: for example, a cute teenage-girl impression becomes a confident adult woman, a soft cute face becomes a strong mature face, a slight smile becomes neutral, a small delicate body becomes a tall adult-model body, or face shape/apparent age becomes inconsistent between closeup and full-body panels.
- Fail Stage 3 or Stage 4 even when sheet annotation text improves if text editing changes face, apparent age, expression intensity, body proportions, silhouette, posture, or the approved same-character impression from `final-photoreal-text-free-sheet.png`.
- Do not fail only because anime anatomy was translated into plausible human anatomy. Fail when that translation changes the source character's visible age impression, facial impression, body impression, expression tone, or personality impression into a different person.
- Record each mismatch in `verification-notes.md` as an appearance drift, naming the source panel or slot and the observed drift such as changed apparent age, changed body proportions, changed face shape, changed expression intensity, changed smile, changed silhouette, or inconsistent identity across panels.

Text check:

- For the text-free sheet, fail if any readable sheet annotation text, section number, label, caption, UI logo text, model/version mark, or fake annotation typography remains.
- Do not fail a text-free sheet only because original typography inside a character image slot remains on clothing, props, accessories, patches, embroidery, or engravings; that is required costume/prop visual content.
- Claim sheet annotation text is readable only for areas that were inspected and can actually be read.
- Treat broken sheet annotation text, fake annotation typography, hallucinated labels, blurry labels, or misaligned text boxes as Stage 4 input only when structure/content equivalence still passes.
- If sheet annotation text remains unreliable after Stage 4 limits, or if readable text cannot be achieved without changing the approved photoreal image set, stop and report `수동 텍스트 오버레이 필요` instead of continuing to regenerate.

## Operating Rules

- Do not use or include the compressed prompt variant.
- Prefer staged editing over one-shot generation.
- Preserve only the latest self-approved image as the next stage input.
- Advance only after self-verification, state update, and attempt-limit check. Ask for feedback only in the final report.
- Do not chain multiple image generation stages in one assistant turn. Run one generation per turn and resume on the next user message or temporary heartbeat.
- When using an image generation or editing tool, submit only the current stage prompt plus the required image inputs. Do not mix future-stage layout or sheet annotation text restoration instructions into Stage 1 or Stage 2.
- When a model struggles with sheet annotation text, keep the character image stable and isolate sheet annotation text repair in Stage 4.
- Do not claim sheet annotation text is readable, exact, repaired, or complete unless it was inspected and verified.
- Do not exceed the retry limits. A clear final report with `수동 보정 필요` is better than unbounded regeneration.
