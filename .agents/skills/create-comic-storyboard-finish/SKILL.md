---
name: create-comic-storyboard-finish
description: Use when an approved comic storyboard page needs tone, color, lettering, or final polish from a parent-inspected storyboard_sketch_ink image.
---

# Create Comic Storyboard Finish

## Overview

Generate exactly one approved comic page for the `finish` stage. This skill is stage-local: it adds tone, color when requested, lighting, final cleanup, and policy-approved lettering or text absence while preserving the parent-inspected `storyboard_sketch_ink` page.

The pack runner owns `state.json`, import, parent inspection, rerun, stage-review, and user approval for entering this stage.

## Inputs

Use the assigned subagent prompt from the pack runner. It provides:

- Run folder, approved plan, assigned page, stage, prompt file, output path, and batch id.
- Required prior-stage reference from `01_storyboard_sketch_ink/`.
- Default source folder and excluded output folder.
- Relevant references, text policy, character locks, visual text guard, and rerun correction.

Read the prompt file and use the prior-stage image as the required visual input and structure reference. Do not edit `state.json`, `batch_plan.md`, `approved_storyboard_plan.json`, or any runner state files.

## Generation Rules

- Use Codex built-in `image_gen`; do not call external image APIs.
- Preserve the inspected `storyboard_sketch_ink` page structure.
- Do not change page layout, panel count, panel shapes, reading order, gutters, negative space, text placement or required text absence, visual emphasis, line-weight rhythm, comic effect lines, character/object blocking, motion direction, or action logic.
- Add tone, color if requested, lighting, shadows, texture, cleanup, and final polish.
- Preserve the approved focal hierarchy and avoid flattening or hiding the ink rhythm.
- Preserve speed lines, focus lines, impact bursts, emotion lines, motion streaks, and their direction. Do not cover or contradict them with tone or color.
- Keep characters, props, setting, landmarks, profile details, and page-layout references consistent with the approved plan, allowed sources, and inspected sketch/ink image.

## Text And Continuity

- Enforce the active `text_policy` exactly.
- For `dialogue_sfx_captions`, render only approved adapted dialogue, SFX, and captions, with short legible lettering that avoids faces, hands, props, and key action.
- For `sfx_only`, render only approved SFX. Do not render speech balloons, dialogue, captions, narration, signage, environmental text, labels, page numbers, panel numbers, random typography, or corner labels.
- For `text_free`, render no text of any kind, including SFX, dialogue, balloons, captions, signage, labels, logos, page or panel numbers, environmental text, or random glyphs.
- Preserve all character locks and visual text guards from the prompt.
- Reject any source drift introduced during finishing, including changed faces, outfits, props, landmarks, text policy, panel continuity, or motion direction.

## Worker Inspection

After generation, inspect the output before returning. Mark `needs_rerun` when finishing changes the inspected sketch/ink structure or violates text policy, source consistency, character locks, visual text guard, spatial logic, motion direction, or technical quality.

Return only:

```text
generated file path: <absolute path>
worker_status: pass | needs_rerun
worker_note: <concise inspection note>
```
