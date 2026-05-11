---
name: convert-2d-sheet-to-sd-character
description: Use when the user wants staged 2D character sheet conversion into an SD, chibi, or super-deformed character sheet with autonomous continuation, self-verification, final-only feedback, a layout-locked text-free final sheet, or a text-restored SD final sheet.
---

# Convert 2D Sheet to SD Character

## Overview

Manage a staged image workflow that first creates a text-free SD character sheet with the same structure as the original 2D character sheet, then restores the original sheet annotation text onto that text-free final. In this workflow, `SD` means super-deformed/chibi character style, not Stable Diffusion. `text-free` means sheet-annotation-free: remove labels, captions, titles, and description text from the sheet UI, but preserve typography or logo-like marks that are part of the character image, costume, props, accessories, patches, embroidery, or engravings. Use the sibling stage skills in order. Always continue through self-verification and regeneration gates without asking for user feedback until the final report.

## Default Output Location

If the user does not specify where to save files, create a new run folder under `/Users/chasoik/Projects/character-sheet-generator/output/`.

- Use `output/<slug>-sd-character-sheet-YYYYMMDD-HHMMSS/` for this workflow.
- Build `<slug>` from the character name, then the input image filename stem, then `sd-character-sheet`. Normalize it to lowercase ASCII letters, numbers, and hyphens. If the normalized value is empty, use `sd-character-sheet`.
- If the user is resuming from an existing run folder, keep using that folder instead of creating a new one.
- Save Stage 1-4 outputs, self-approved intermediates, `final-sd-text-free-sheet.png`, `final-sd-character-sheet.png`, repair outputs, notes, and optional state or resume artifacts under the selected run folder.
- Keep `structure-inventory.md`, `workflow-state.json`, and a short `verification-notes.md` in the run folder so the next resumed turn knows the original structure/content contract, Character Identity Lock, current stage, attempt counts, latest accepted image, latest rejected image, and next intended action.
- When reporting artifacts, include the selected run folder and write output paths under that folder.

## Stage Skills

Use these sibling skills from the same `.agents/skills` skill root:

1. `$create-sd-character-base` for a text-free SD/chibi sheet that preserves the original canvas, panel layout, view positions, non-text graphics, identity, and in-image costume/prop typography.
2. `$intensify-sd-character` when the base is structurally usable but still too normal-proportioned, semi-real, photoreal, adult, generic mascot-like, inconsistent, or not clearly SD/chibi.
3. `$restore-sd-sheet-layout` to restore original sheet annotation text onto the self-approved `final-sd-text-free-sheet.png` without changing layout, character content, or the approved SD image set.
4. `$repair-sd-sheet-text` only when the final character and approved SD image set are good but sheet annotation text or labels need cleanup.

If explicit skill invocation is unavailable, open the matching sibling `SKILL.md` and follow it directly.

## Intake

Before generating or editing, identify:

- Original 2D character sheet image.
- Current stage image, if the user is resuming.
- Original structure/content inventory, if the user is resuming.
- Required sheet annotation text preservation level for the final text-inclusive sheet: exact, approximate, translated, or omit until later.
- Any explicit SD style preference or constraint, such as 2-head, 2.5-head, 3-head, cute mascot, game avatar, sticker-like, cel-shaded, flat-color, or clean anime SD.

If the user says only `SD character`, default to a clean 2D super-deformed/chibi character sheet, not photoreal, not a 3D toy render, and not a plush mascot suit. Use compact 2-3 head proportions unless the source or user asks otherwise.

The text removal scope for the text-free sheet is full removal of sheet annotation text: title, section numbers, labels, descriptions, captions, UI logo text, model name, version marks, and other readable text that belongs to the sheet layout must be removed while non-text structure remains.

Do not remove typography that is part of the character image itself. Preserve original printed, embroidered, engraved, patched, or logo-like text on clothing, props, accessories, weapons, bags, shoes, or other image-slot content as costume/prop design detail. If that in-image typography is too small or blurry to verify exactly after SD simplification, preserve its visible placement, scale, color, and design character without claiming exact text fidelity.

If no source image is available, ask for it. If the user provides an existing intermediate image, resume from the matching stage instead of restarting.

## Structure/Content Inventory

Before Stage 1, inspect the original 2D sheet and create `structure-inventory.md` in the run folder. This inventory is the acceptance contract for every later stage.

Inventory requirements:

- Derive the inventory from the current source image. Do not hard-code section names or known problem areas from prior runs.
- Record every visible section, panel group, image slot, text slot, callout target, color chip group, and repeated view/detail cell.
- For each image slot, record its relative location, role, expected view or crop type, direction or expression when applicable, and the mandatory visual content that must stay distinct.
- For each image slot that contains costume, prop, accessory, or object typography, record it as mandatory visual content or costume/prop typography, not as a removable text slot.
- For each text slot, record only sheet annotation text: its relative location, hierarchy, and whether it should be removed in the text-free stages or restored in the text-inclusive stages.
- Add a `Character Identity Lock` section derived only from visible source evidence. Record apparent age/maturity impression, personality/emotional impression, face and eye impression, hair silhouette, signature outfit pieces, key props, palette, motifs, posture, expression intensity, and any non-negotiable marks or accessories.
- Add an `SD Proportion Target` section. Record the requested or inferred SD target: 2-head, 2.5-head, 3-head, or source-matched SD. If the user did not specify, default to compact 2-3 head proportions with a large head, simplified torso, short limbs, and readable hands/feet.
- Treat slot count and slot meaning as locked. Two source slots must not be merged into one output slot, one source slot must not be omitted, and a slot must not change into a different expression, direction, detail target, prop, outfit area, or body part.
- Treat the Character Identity Lock as an identity contract, not a biological measurement. Do not infer exact biological age, exact height, race, or ethnicity; record only visible visual impressions needed to keep the same character after SD conversion.
- Do not treat original realistic or normal anime body proportions as locked. SD conversion intentionally changes body proportions. Fail only when the SD simplification changes the character's visible identity, age/maturity impression, face/personality impression, core outfit, pose meaning, or signature details.
- Record any source text or tiny details that are not legible enough to verify exactly; do not later claim exact restoration for those areas.

Use `structure-inventory.md` during prompt construction and self-verification. If it is missing or lacks the Character Identity Lock or SD Proportion Target on resume, rebuild it from the source image before approving any stage.

## Turn Protocol for Image Generation

Direct image generation calls in the parent Codex session can end the visible assistant turn and hide the follow-up report. Because of that, when subagents are available, the parent workflow manager must delegate every Stage 1-4 image generation or image editing call to a context-forked generation subagent instead of calling the image tool directly.

Required parent/subagent split:

1. The parent session owns intake, inventory creation, `workflow-state.json`, `verification-notes.md`, Korean progress reports, self-verification, retry decisions, and final reporting.
2. The generation subagent owns only one image generation or image editing call for the current stage. It must not decide pass/fail, update workflow state, write verification notes, advance stages, ask the user for feedback, or produce a final workflow report.
3. Spawn the generation subagent only after the parent has sent the Korean `[N단계 실행 예정]` report and updated `workflow-state.json`. Use `fork_context=true` so the subagent receives the current conversation, source image context, structure inventory, stage goal, and constraints.
4. The parent must give the subagent a narrow handoff: current stage number, run folder, current input image path(s), `structure-inventory.md` path, the sibling stage skill/prompt to follow, the exact text-free or text-restoration goal, and an instruction to submit only the current stage image prompt plus required image inputs.
5. The subagent must treat the image generation or editing tool call as its final action. It must not append a result report, quality claim, next-step question, or stage decision after the image tool call.
6. After the subagent completes, the parent locates the generated artifact, copies or references it under the run folder when possible, inspects it, then sends the Korean `[N단계 결과]` or `[N단계 자체 검수]` report in the parent session.
7. The parent decides the next action from the self-verification rules, records the decision in `verification-notes.md`, updates `workflow-state.json`, and either spawns a new generation subagent for the next retry/stage or finishes with the final report.
8. If subagent spawning is unavailable in the current runtime, explicitly note the fallback in the Korean execution report, then use the direct one-generation-per-turn protocol: update state, call the image tool as the last action, and resume from the next user message or heartbeat.
9. Delete or pause the temporary heartbeat when the workflow reaches a terminal final report.

## Autonomous Continuation

Always use autonomous continuation. Keep stage reports factual, but treat them as progress logs rather than user gates.

Required state:

- `workflow-state.json`: `stage`, `attemptsByStage`, `sourceImage`, `structureInventory`, `characterIdentityLock`, `sdProportionTarget`, `latestAcceptedImage`, `latestRejectedImage`, `nextAction`, and `terminalReason`. `attemptsByStage` records the total attempt count per stage, including the initial attempt and retries. `characterIdentityLock` and `sdProportionTarget` should point to sections in `structure-inventory.md`, not to separate files.
- `structure-inventory.md`: original section/panel/slot contract, Character Identity Lock, SD Proportion Target, and any source details that cannot be verified exactly.
- `verification-notes.md`: chronological notes with each generated artifact, pass/fail decision, visible defects, and why the next stage or retry was chosen.

Attempt limits:

- Stage 1: maximum 3 total attempts: initial attempt + up to 2 retries.
- Stage 2: maximum 3 total attempts: initial attempt + up to 2 retries.
- Stage 3: maximum 3 total attempts: initial attempt + up to 2 retries.
- Stage 4: maximum 3 total attempts: initial attempt + up to 2 retries.
- If a stage still fails after its limit, do not keep regenerating. Finish with a final report that names the failed stage and the human follow-up needed.

Autonomous decisions:

- If Stage 1 is convincingly SD/chibi, preserves the original sheet structure/content inventory, preserves the Character Identity Lock, follows the SD Proportion Target, removes all sheet annotation text, and preserves any original in-image costume/prop typography as stylized design detail, self-approve it as `final-sd-text-free-sheet.png` and proceed to Stage 3.
- If Stage 1 preserves the structure/content inventory and Character Identity Lock, removes sheet annotation text, preserves in-image costume/prop typography, but still looks too normal-proportioned, semi-real, photoreal, adult, generic mascot-like, inconsistent, over-detailed, or not clearly SD/chibi, proceed to Stage 2.
- If Stage 1 changes the original layout, omits major panels/views, merges image slots, changes a slot's meaning, replaces a detail/expression/direction with another, changes the Character Identity Lock, ignores the SD Proportion Target, leaves readable/fake sheet annotation text, or removes original in-image costume/prop typography, retry Stage 1 if attempts remain.
- If Stage 2 passes the SD/chibi threshold while preserving the text-free sheet layout/content inventory, Character Identity Lock, SD Proportion Target, and adding no new sheet annotation text, self-approve it as `final-sd-text-free-sheet.png` and proceed to Stage 3.
- If Stage 2 adds new sheet annotation/fake text, changes or removes original in-image costume/prop typography, changes layout, merges/omits slots, changes slot meaning, changes the Character Identity Lock, or drifts from the SD Proportion Target, retry Stage 2 until the attempt limit, then fall back to Stage 1 if allowed.
- If Stage 2 still fails the SD/chibi threshold after its limit, regenerate Stage 1 once if Stage 1 attempts remain; otherwise finish with a failure report.
- If Stage 3 restores readable original sheet annotation text while preserving the text-free sheet's character, Character Identity Lock, SD Proportion Target, panels, layout, non-text graphics, in-image costume/prop typography, and the full approved SD image set, self-approve it as `final-sd-character-sheet.png` and finish.
- If Stage 3 preserves the approved SD image set, Character Identity Lock, SD Proportion Target, and layout but sheet annotation text is broken, blurry, misaligned, fake, or unreadable, proceed to Stage 4.
- If Stage 3 changes the character or Character Identity Lock, redraws or replaces any image slot, changes the locked text-free layout, merges/omits slots, changes slot meaning, changes image-slot content versus the text-free base, or weakens the SD/chibi style, retry Stage 3 if attempts remain; otherwise finish with `수동 텍스트 오버레이 필요`.
- If Stage 4 improves sheet annotation text while preserving character, Character Identity Lock, SD Proportion Target, pose, outfit, style, layout, and the full approved SD image set, finish.
- If Stage 4 changes the character, Character Identity Lock, structure/content, redraws or replaces any image slot, weakens the approved SD style of any image slot, or still cannot produce verifiable readable sheet annotation text after its limit, finish with `수동 텍스트 오버레이 필요`.

Required final artifacts:

- `final-sd-text-free-sheet.png`: the latest self-approved text-free SD/chibi sheet from Stage 1 or Stage 2. It must preserve the original canvas ratio, panel structure, view positions, slot count, slot meaning, Character Identity Lock, SD Proportion Target, non-text graphics, and original in-image costume/prop typography while removing all sheet annotation text.
- `final-sd-character-sheet.png`: the latest self-approved text-inclusive SD/chibi character sheet from Stage 3 or Stage 4. It must be built on top of `final-sd-text-free-sheet.png` by restoring original sheet annotation text without changing character, Character Identity Lock, SD Proportion Target, layout, non-text graphics, slot count, slot meaning, in-image costume/prop typography, or the approved SD image set. If no text-inclusive sheet passes, still save the best failed candidate and mark it as needing manual text overlay.

## Workflow

### Stage 1: SD Character Base

Use `$create-sd-character-base`.

Goal:

- Remove all sheet annotation text while preserving text boxes, panels, callout lines, color chips, and other non-text structure.
- Convert every character image slot into the same coherent SD/chibi style, with large head, compact body, simplified readable anatomy, short limbs, and expressive face.
- Preserve character identity, Character Identity Lock, hair, outfit, props, in-image costume/prop typography, pose, expression, original canvas ratio, panel layout, and view positions.
- Preserve every image slot from `structure-inventory.md` as a distinct 1:1 slot with the same role, view, expression, crop target, prop, outfit area, and body part.

Self-verification gate:

- Self-approve as `final-sd-text-free-sheet.png` and proceed to Stage 3 only if the base is clearly SD/chibi, matches the original structure, preserves the Character Identity Lock, follows the SD Proportion Target, contains no readable or fake sheet annotation text, and preserves original in-image costume/prop typography.
- Proceed to Stage 2 if the image matches the original structure, preserves the Character Identity Lock, contains no sheet annotation text, preserves in-image costume/prop typography, but still needs stronger SD/chibi styling.
- Retry Stage 1 if the base changes the original layout, omits major panels/views, merges slots, changes slot meaning, changes identity, ignores the SD Proportion Target, leaves readable or fake sheet annotation text, removes original in-image costume/prop typography, or is structurally unusable.

### Stage 2: SD Style Intensification

Use `$intensify-sd-character` when needed.

Goal:

- Strengthen SD/chibi readability and consistency across all image slots.
- Keep expression, emotion, pose, clothing, Character Identity Lock, SD Proportion Target, original in-image costume/prop typography, original text-free layout, empty sheet annotation areas, non-text graphics, and every inventory image slot stable.

Self-verification gate:

- Self-approve as `final-sd-text-free-sheet.png` and proceed to Stage 3 only if the result passes the SD/chibi style threshold while preserving original structure/content inventory, Character Identity Lock, SD Proportion Target, and adding no sheet annotation text.
- Retry Stage 2 if it still fails the style threshold, changes layout, merges/omits slots, changes slot meaning, changes the Character Identity Lock, changes/removes original in-image costume/prop typography, or adds readable/fake sheet annotation text and Stage 2 attempts remain.
- Fall back to Stage 1 if Stage 2 fails after its limit and Stage 1 attempts remain.

### Stage 3: Text Restoration On Text-Free Sheet

Use `$restore-sd-sheet-layout`.

Goal:

- Use `final-sd-text-free-sheet.png` as the locked visual base.
- Restore the original 2D sheet's readable sheet annotation text, labels, section numbers, captions, UI logo text, and descriptions at the corresponding original positions.
- Keep character, Character Identity Lock, SD Proportion Target, panels, view positions, image-slot content, in-image costume/prop typography, text boxes, callout lines, color chips, and other non-text graphics unchanged.
- Treat the full image set inside `final-sd-text-free-sheet.png` as locked: every image slot must keep the same location, count, role, content, view, crop target, detail target, and SD/chibi style.

Self-verification gate:

- Self-approve as `final-sd-character-sheet.png` and finish only when restored text is acceptable and the locked SD image set, Character Identity Lock, and SD Proportion Target remain unchanged.
- Proceed to Stage 4 only when the approved SD image set and non-text structure/content are good but sheet annotation text or labels are broken, blurry, misaligned, fake, or unreadable.
- Retry Stage 3 if sheet annotation text restoration changed layout, changed the character or Character Identity Lock, failed to restore text at corresponding positions, merged/omitted slots, changed slot meaning, changed in-image costume/prop typography, changed image-slot content versus the text-free base, redrew or replaced any image slot, or weakened the SD/chibi style and Stage 3 attempts remain.

### Stage 4: Text Repair

Use `$repair-sd-sheet-text` only for text and labels.

Goal:

- Preserve character, Character Identity Lock, SD Proportion Target, pose, outfit, style, and layout.
- Fix only broken, blurry, misaligned, or unreadable sheet annotation text and labels.
- Preserve every non-text image slot and in-image costume/prop typography from the Stage 3 input and `final-sd-text-free-sheet.png`.

Self-verification gate:

- Finish only when repaired sheet annotation text can be verified and the character, Character Identity Lock, SD Proportion Target, layout, in-image costume/prop typography, non-text slot content, and approved SD image set remained stable.
- Retry Stage 4 if sheet annotation text repair changed the character, Character Identity Lock, pose, outfit, in-image costume/prop typography, style, layout, slot count, slot meaning, or any image-slot content and Stage 4 attempts remain.
- Finish with `수동 텍스트 오버레이 필요` if the model still cannot produce verifiable readable sheet annotation text without changing the approved SD image set after the Stage 4 attempt limit.

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
- SD 동등성: ...
- 검수 결과: ...
- 다음 결정: ...
```

Keep reports factual. Do not claim sheet annotation text is readable unless it was inspected. Do not claim a stage passed if obvious visual artifacts remain.

Use the same report shape but label mid-stage checks as `[N단계 자체 검수]` when the next action is decided without user input. Include the chosen next action and the total stage attempt count. Only the final report includes feedback options.

Final report:

```text
[최종 결과]
- 저장 폴더: ...
- 무텍스트 SD 시트: ...
- 텍스트 포함 SD 캐릭터 시트: ...
- 자체 재시도 이력: ...
- 통과/실패 기준: ...
- 구조/내용 동등성: ...
- SD/캐릭터 동등성: ...
- 남은 리스크: ...
- 다음 선택:
  1. 완료
  2. 텍스트만 추가 보정
  3. SD 스타일만 추가 강화
  4. 전체 재생성
  5. 중단
```

Do not present numbered feedback options before the final report.

## Self-Verification Rules

SD style check:

- Pass only when every character image slot clearly reads as super-deformed/chibi: large expressive head, compact simplified body, short limbs, readable silhouette, simplified hands/feet, and a coherent cute stylized design language.
- Fail or intensify when the image looks normal-proportioned, photoreal, semi-real, adult fashion illustration, generic mascot, toy render, plush suit, inconsistent across panels, overly detailed in a way that breaks SD readability, or too close to the original non-SD proportions.
- Do not force a toddler/baby impression unless the source or user explicitly asks for it. SD proportions should preserve the source character's age/maturity and personality impression in stylized form.

Layout check:

- Pass the text-free sheet only when it keeps the original canvas ratio, panel grid, major view groups, detail-panel positions, empty sheet annotation areas, callout lines, boxes, color chips, non-text graphic structure, and original in-image costume/prop typography.
- Pass the text-inclusive sheet only when it preserves the self-approved text-free layout, preserves the approved SD image set, and adds sheet annotation text at corresponding original positions.
- Fail or regenerate when the layout loses the reference-sheet purpose, omits major view groups, crops core design details, changes non-text graphics, adds a new UI structure, or lets graphic elements overpower the character.

Structure/content equivalence check:

- Compare every generated candidate against `structure-inventory.md`; for Stage 3 and Stage 4, compare image slots against `final-sd-text-free-sheet.png` as the locked SD image-set source of truth, while using the original source only for sheet annotation text and placement.
- Pass only when every original image slot remains present, separate, and semantically equivalent: the same role, view/crop type, expression or direction when applicable, prop/outfit/body-part target, and mandatory visible content.
- For Stage 3 and Stage 4, pass only when every image slot also remains equivalent to the approved text-free SD base in location, count, role, content, view, crop target, detail target, and SD/chibi style.
- Fail if any candidate merges multiple source slots into one image, omits a source slot, duplicates one slot to cover another, swaps the meaning of a slot, replaces a detail target with a different target, changes a required expression/direction/pose, removes original in-image costume/prop typography, changes non-text content during a sheet annotation-only stage, redraws or replaces an image slot, or weakens any image slot from the approved SD base into another style.
- Record the mismatch in `verification-notes.md` by source section/panel/slot type plus the observed symptom, such as changed content, changed view, changed crop, redrawn slot, lost SD style, or changed in-image typography. Do not hard-code recurring problem-item names into the skill.

Character/SD equivalence check:

- Compare every generated candidate against the `Character Identity Lock` and `SD Proportion Target` in `structure-inventory.md`.
- Pass only when the SD character still reads as the same character after stylization: same face/personality impression, age/maturity impression, hair silhouette, eye/face cues, signature outfit, palette, motifs, props, expression intensity, and emotional impression.
- Pass SD proportion changes when they are intentional and consistent with the SD Proportion Target. Do not fail only because normal anime anatomy was simplified into a large-head, short-limb SD body.
- Fail Stage 1 or Stage 2 if SD stylization recasts the character: for example, a soft teenage impression becomes a toddler mascot, a calm character becomes hyperactive, a shy smile becomes a huge unrelated grin, a signature outfit is replaced by a generic outfit, or the face/hair reads like a different character.
- Fail Stage 3 or Stage 4 even when sheet annotation text improves if text editing changes face, age/maturity impression, expression intensity, silhouette, outfit, props, or the approved same-character impression from `final-sd-text-free-sheet.png`.
- Record each mismatch in `verification-notes.md` as identity or SD drift, naming the source panel or slot and the observed drift such as changed age/maturity impression, changed face shape, changed expression intensity, changed smile, changed silhouette, inconsistent SD proportion, or inconsistent identity across panels.

Text check:

- For the text-free sheet, fail if any readable sheet annotation text, section number, label, caption, UI logo text, model/version mark, or fake annotation typography remains.
- Do not fail a text-free sheet only because original typography inside a character image slot remains on clothing, props, accessories, patches, embroidery, or engravings; that is required costume/prop visual content.
- Claim sheet annotation text is readable only for areas that were inspected and can actually be read.
- Treat broken sheet annotation text, fake annotation typography, hallucinated labels, blurry labels, or misaligned text boxes as Stage 4 input only when structure/content equivalence still passes.
- If sheet annotation text remains unreliable after Stage 4 limits, or if readable text cannot be achieved without changing the approved SD image set, stop and report `수동 텍스트 오버레이 필요` instead of continuing to regenerate.

## Operating Rules

- Do not use or include a compressed prompt variant.
- Prefer staged editing over one-shot generation.
- Preserve only the latest self-approved image as the next stage input.
- Advance only after self-verification, state update, and attempt-limit check. Ask for feedback only in the final report.
- Do not chain multiple image generation stages in one assistant turn. Run one generation per turn and resume on the next user message or temporary heartbeat.
- When subagents are available, do not call the image generation or image editing tool directly from the parent session. Use a context-forked generation subagent for each generation attempt so the parent session remains available for result reporting, inspection, state updates, and final feedback.
- Keep generation subagents narrowly scoped: one stage, one attempt, one image tool call, no workflow-state edits, no verification decision, and no user-facing final report.
- When using an image generation or editing tool, submit only the current stage prompt plus the required image inputs. Do not mix future-stage layout or sheet annotation text restoration instructions into Stage 1 or Stage 2.
- When a model struggles with sheet annotation text, keep the character image stable and isolate sheet annotation text repair in Stage 4.
- Do not claim sheet annotation text is readable, exact, repaired, or complete unless it was inspected and verified.
- Do not exceed the retry limits. A clear final report with `수동 보정 필요` is better than unbounded regeneration.
