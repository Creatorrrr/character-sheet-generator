---
name: create-comic-storyboard-sketch-ink
description: Use when an approved comic storyboard page needs a storyboard, sketch, and ink image stage from a create-comic-storyboard-pack runner prompt.
---

# Create Comic Storyboard Sketch Ink

## Overview

Generate exactly one approved comic page for the `storyboard_sketch_ink` stage. This skill is stage-local: it creates and first-pass inspects the image, but the pack runner owns `state.json`, import, parent inspection, rerun, and stage-review.

## Inputs

Use the assigned subagent prompt from the pack runner. It provides:

- Run folder, approved plan, assigned page, stage, prompt file, output path, and batch id.
- Default source folder and excluded output folder.
- Relevant references, text policy, character locks, character appearance/anatomy lock, visual text guard, rerun correction, and prior-stage reference.

Read the prompt file before generation. Do not edit `state.json`, `batch_plan.md`, `approved_storyboard_plan.json`, or any runner state files.

## Generation Rules

- Use Codex built-in `image_gen`; do not call external image APIs.
- Generate one complete Korean comic-book page image, not loose panels.
- Follow the approved page id, panel count, reading order, layout brief, panel beats, and comic visual direction.
- Use 3-5 panels by default with measured cinematic pacing.
- Accept 1-2 panels only when the approved page uses special staging such as silence, stillness, a large reveal, full-page emotion, or decisive action.
- Use six or more panels only when the approved page includes an explicit story reason.
- Use experimental freeform panel shapes when approved: diagonal panels, asymmetry, tall vertical panels, open or borderless panels, inset panels, partial overlaps, and wide negative space are valid if reading order is clear.
- Avoid unintentional uniform rectangular grids, overcrowded pages, and dialogue/SFX packed without breathing room.
- Draw the approved sketch structure and ink lines in this stage.
- Include approved visual emphasis: selective detail density, focal-point strength, closeup intensity, line-weight rhythm, black-ink weight, and background simplification or emphasis.
- Use speed lines, focus lines, impact bursts, emotion lines, and motion streaks only where they serve the approved beat. Effect-line direction must match action direction, impact, mood, or eye guidance.
- Preserve the approved character appearance/anatomy lock: species/body structure, face structure, eye count and placement, hand/finger/arm/leg count, silhouette, body proportions, and posture.

## Text And Continuity

- Enforce the active `text_policy` exactly.
- For `dialogue_sfx_captions`, render only approved adapted dialogue, SFX, and captions, with short legible lettering that avoids faces, hands, props, and key action.
- For `sfx_only`, render only approved SFX. Do not render speech balloons, dialogue, captions, narration, signage, environmental text, labels, page numbers, panel numbers, random typography, or corner labels.
- For `text_free`, render no text of any kind, including SFX, dialogue, balloons, captions, signage, labels, logos, page or panel numbers, environmental text, or random glyphs.
- Preserve all character locks and visual text guards from the prompt.
- Use `character_locks`, `must_match`, source references, and page/panel notes as the source of truth for approved anatomy or non-human exceptions.
- Unless explicitly approved by the plan or source, reject missing/extra/merged eyes, one-eyed appearance for a two-eyed character, one-eyed face unless explicitly approved, missing/extra limbs or fingers, changed species/body type, broken joints, and broken body proportions.
- Preserve character, prop, setting, landmark, gaze, position, object trajectory, time flow, and cause-effect continuity across panels and adjacent-page references.
- Reject impossible staging, such as a thrown, kicked, or shot object moving opposite the body pose or intended target.

## Worker Inspection

After generation, inspect the output before returning. Mark `needs_rerun` when any required page structure, text policy, character lock, character appearance/anatomy lock, visual text guard, source consistency, spatial logic, motion direction, or technical quality check fails.

Do not pass a two-eyed character that appears one-eyed unless the approved plan or source explicitly says the character is one-eyed, asymmetric, non-human in that way, or naturally occluded by angle, hair, prop, or framing.

Return only:

```text
generated file path: <absolute path>
worker_status: pass | needs_rerun
worker_note: <concise inspection note>
```
