---
name: create-comic-storyboard-finish
description: Use when an approved comic storyboard page needs tone, color, lettering, or final polish from a parent-inspected storyboard_sketch_ink image while preserving the blocking spatial validation overlay.
---

# Create Comic Storyboard Finish

## Overview

Generate exactly one approved comic page for the `finish` stage. This skill is stage-local: it adds tone, color when requested, lighting, final cleanup, and policy-approved lettering or text absence while preserving the parent-inspected `storyboard_sketch_ink` page and the earlier blocking `*_desc.md` spatial validation overlay.

The pack runner owns `state.json`, import, parent inspection, rerun, stage-review, and user approval for entering this stage.

## Inputs

Use the assigned subagent prompt from the pack runner. It provides:

- Run folder, approved plan, assigned page, stage, prompt file, output path, and batch id.
- Required prior-stage reference from `02_storyboard_sketch_ink/` or a recorded legacy/imported sketch path.
- Blocking `*_desc.md` reference when available; keep it as the spatial validation overlay for the approved comic page design.
- `Required image attachments` / `Prior page continuity references`, including the current page's sketch/ink image and previous pages' inspected finish images when the pack runner provides them.
- `Stage level anchor reference`; if this is the first page, it may define the finish level for later pages, and if prior pages exist it includes the passed anchor note to match.
- Default source folder and excluded output folder.
- Relevant references, text policy, character locks, character appearance/anatomy lock, visual text guard, and rerun correction.

Read the prompt file and use the prior-stage image as the required visual input and structure reference. Attach every listed required image path as a local image visual reference when calling `image_gen`. Do not edit `state.json`, `batch_plan.md`, `approved_storyboard_plan.json`, or any runner state files.

## Generation Rules

- Use Codex built-in `image_gen`; do not call external image APIs.
- Preserve the inspected `storyboard_sketch_ink` page structure.
- Preserve the blocking-stage positions, vectors, cover, line of sight, visibility, occlusion, location anchors, and temporal state fields recorded in the blocking `*_desc.md` without redesigning the page layout around them.
- Do not change page layout, panel count, panel shapes, reading order, gutters, negative space, text placement or required text absence, visual emphasis, line-weight rhythm, comic effect lines, character/object blocking, motion direction, or action logic.
- Add tone, color if requested, lighting, shadows, texture, cleanup, and final polish.
- Preserve the approved focal hierarchy and avoid flattening or hiding the ink rhythm.
- Preserve speed lines, focus lines, impact bursts, emotion lines, motion streaks, and their direction. Do not cover or contradict them with tone or color.
- Keep characters, props, setting, landmarks, profile details, and page-layout references consistent with the approved plan, allowed sources, and inspected sketch/ink image.
- Preserve the inspected `storyboard_sketch_ink` eye, face, hand, limb, silhouette, body proportion, and posture structure. Tone/color/final cleanup must not turn a two-eyed character into a one-eyed appearance or change species/body type unless explicitly approved.

## Text And Continuity

- Enforce the active `text_policy` exactly.
- For `dialogue_sfx_captions`, render only approved adapted dialogue, SFX, and captions, with short legible lettering that avoids faces, hands, props, and key action.
- For `sfx_only`, render only approved SFX. Do not render speech balloons, dialogue, captions, narration, signage, environmental text, labels, page numbers, panel numbers, random typography, or corner labels.
- For `text_free`, render no text of any kind, including SFX, dialogue, balloons, captions, signage, labels, logos, page or panel numbers, environmental text, or random glyphs.
- Preserve all character locks and visual text guards from the prompt.
- Reject any source drift introduced during finishing, including changed faces, outfits, props, landmarks, text policy, panel continuity, cover/visibility/occlusion, temporal state, or motion direction.
- Use `character_locks`, `must_match`, source references, page/panel notes, and the parent-inspected sketch/ink image as the source of truth for approved anatomy or non-human exceptions.
- Unless explicitly approved by the plan or source, reject missing/extra/merged eyes, one-eyed appearance for a two-eyed character, one-eyed face unless explicitly approved, missing/extra limbs or fingers, changed species/body type, broken joints, and broken body proportions.

## Worker Inspection

After generation, inspect the output before returning. Mark `needs_rerun` when finishing changes the inspected sketch/ink structure or violates text policy, source consistency, character locks, character appearance/anatomy lock, visual text guard, blocking spatial validation overlay, spatial logic, motion direction, or technical quality.

If this page is marked as the stage-level anchor, self-inspect the finish level especially strictly: it must add tone/color/final polish while preserving sketch/ink structure, line rhythm, effect lines, and text policy.

Do not pass a finish output that changes a passed two-eye, face, hand, limb, silhouette, body-proportion, or posture structure from the sketch/ink stage unless that exception is explicitly approved in the plan or source.

Return only:

```text
generated file path: <absolute path>
worker_status: pass | needs_rerun
worker_note: <concise inspection note>
```
