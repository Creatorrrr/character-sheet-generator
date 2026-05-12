---
name: create-comic-storyboard-sketch-ink
description: Use when an approved comic storyboard page needs the integrated conti, rough sketch, and light clean-line stage with a spatial description.
---

# Create Comic Storyboard Sketch Ink

## Overview

Generate exactly one approved comic page for the `storyboard_conti_sketch_ink` stage. This skill is stage-local: it creates the combined conti, rough sketch, and light clean-line pass from the approved page plan, writes the required `*_desc.md` spatial validation description, then first-pass inspects the result. The pack runner owns `state.json`, import, parent inspection, rerun, and stage-review.

## Inputs

Use the assigned subagent prompt from the pack runner. It provides:

- Run folder, approved plan, assigned page, stage, prompt file, output path, and batch id.
- Assigned description path for the required `*_desc.md`.
- `Required image attachments` / `Prior page continuity references`, including previous pages' inspected `storyboard_conti_sketch_ink` images when the pack runner provides them.
- `Stage level anchor reference`; if this is the first page, it defines the conti/sketch/light-ink level for later pages, and if prior pages exist it includes the passed anchor note to match.
- Default source folder and excluded output folder.
- Relevant references, text policy, character locks, character appearance/anatomy lock, visual text guard, rerun correction, and spatial/temporal validation requirements.

Read the prompt file before generation. Attach every listed required image path as a local image visual reference when calling `image_gen`. Do not edit `state.json`, `batch_plan.md`, `approved_storyboard_plan.json`, or any runner state files.

## Generation Rules

- Use Codex built-in `image_gen`; do not call external image APIs.
- Generate one complete Korean comic-book page image, not loose panels.
- Follow the approved page id, panel count, reading order, layout brief, panel beats, and comic visual direction.
- Use 3-5 panels by default with measured cinematic pacing.
- Accept 1-2 panels only when the approved page uses special staging such as silence, stillness, a large reveal, full-page emotion, or decisive action.
- Use six or more panels only when the approved page includes an explicit story reason.
- Use experimental freeform panel shapes when approved: diagonal panels, asymmetry, tall vertical panels, open or borderless panels, inset panels, partial overlaps, and wide negative space are valid if reading order is clear.
- Avoid unintentional uniform rectangular grids, overcrowded pages, and dialogue/SFX packed without breathing room.
- Do not require a prior-stage image for this stage. Build from the approved narrative page plan, source references, prior same-stage page references, and spatial contract.
- Preserve the approved page composition, story rhythm, reader eye flow, character/object placement, vectors, visibility, occlusion, location anchors, movement paths, and temporal state fields.
- Draw identifiable rough sketch forms for important characters, objects, background structures, landmarks, and occluding elements. Add light clean-line structure where it clarifies silhouettes, edges, object shapes, paths, and panel readability.
- Do not make a meaningless pure-symbol conti. Validation arrows and relation marks may be added only where they help verify spatial relationships, movement, occlusion, or cause-effect logic.
- Do not render final tone, color, lighting, texture, glossy polish, or fully finished inking in this stage.
- Include approved visual emphasis at the planning level: selective detail density, focal-point strength, closeup intensity, line-weight rhythm, black-ink rhythm, and background simplification or emphasis, while keeping it clearly pre-finish.
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
- Treat `spatial_contract` as a spatial validation overlay for the approved comic page design. Write the sibling `*_desc.md` with the required headings and Korean body text while preserving entity ids and constraint ids verbatim. Reject changed occluder type, exposed hidden characters, reversed direction/trajectory vectors, implausible object transfer, landmark drift, or temporal state drift unless an approved `allowed_transition` with a valid cause reference permits it.
- Reject impossible staging, such as a thrown, kicked, or shot object moving opposite the body pose or intended target.

## Worker Inspection

After generation, inspect the output before returning. Mark `needs_rerun` when any required page structure, text policy, character lock, character appearance/anatomy lock, visual text guard, source consistency, description file, spatial logic, temporal continuity, motion direction, or technical quality check fails.

If this page is marked as the stage-level anchor, self-inspect the conti/sketch/light-ink level especially strictly: it must be readable and structurally useful while avoiding tone/color/final polish.

Do not pass a two-eyed character that appears one-eyed unless the approved plan or source explicitly says the character is one-eyed, asymmetric, non-human in that way, or naturally occluded by angle, hair, prop, or framing.

Return only:

```text
generated file path: <absolute path>
description path: <absolute path>
worker_status: pass | needs_rerun
worker_note: <concise inspection note>
```
