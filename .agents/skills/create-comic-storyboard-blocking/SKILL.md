---
name: create-comic-storyboard-blocking
description: Use when an approved comic storyboard page needs a rough comic-page blocking image and matching spatial validation description from a create-comic-storyboard-pack runner prompt.
---

# Create Comic Storyboard Blocking

## Overview

Generate exactly one approved comic page for the `storyboard_blocking` stage. This is not final art. It is a rough comic-page blocking pass that preserves the approved page composition, scene rhythm, and reader eye flow first, then adds enough spatial validation marks to inspect positions, directions, cover, visibility, occlusion, object trajectories, landmarks, and temporal state continuity before sketch/ink work begins.

The pack runner owns `state.json`, import, parent inspection, rerun, and stage-review. Do not edit runner state files.

## Inputs

Use the assigned subagent prompt from the pack runner. It provides:

- Run folder, approved plan, assigned page, stage, prompt file, output path, description path, and batch id.
- Relevant references, text policy, character locks, visual text guard, narrative-first page design, structured `spatial_contract`, rerun correction, and overlay notes.
- The required `*_desc.md` path beside the generated blocking image.

Read the prompt file before generation.

## Generation Rules

- Use Codex built-in `image_gen` exactly once for the blocking page image.
- Generate one complete page image with the approved panel count and reading order.
- Preserve the approved page/panel composition, scenario beat, action rhythm, emotional rhythm, reader eye flow, and comic readability before adding validation marks.
- Draw each important character, object, and environment element as a quick rough pen sketch, roughly the level of detail possible in about 3 seconds per entity.
- Make the rough form recognizable enough to identify the entity category and action: e.g. crouching person, standing person, gun, ball, hoop, low cover, wall, doorway, vehicle, tree, table, or landmark.
- Keep the drawing loose and schematic: simple gesture poses, blocky object contours, rough environmental silhouettes, shadow masses, and minimal landmark outlines are enough.
- Simplify or omit unimportant props/background elements when they are not needed for story readability, action readability, cover/occlusion, landmark continuity, or page composition.
- Add clear lines, arrows, vector marks, relation lines, sight/aim lines, trajectory arrows, and occlusion/cover markers only where needed so positions, directions, and spatial relationships remain inspectable.
- Do not render detailed faces, anatomy, costume detail, texture, dialogue, SFX, captions, labels, typography, polished ink, tone/color, or final art.
- Do not turn the page into a pure tactical diagram unless the approved page design explicitly calls for a diagram-like page.
- Semantic labels must not be drawn into the image. Put meanings in the sibling `*_desc.md`.
- Make positions, facing/gaze/aim vectors, trajectories, cover relationships, line of sight, visibility, occlusion, and location anchors easy to inspect.
- Preserve every `spatial_contract` entity id, panel snapshot, vector, visibility/occlusion state, and constraint as a validation overlay, not as the driver of composition.
- Preserve temporal fields from the prompt: `pose`, `cover`, `visibility`, `occlusion`, `location_anchor`, `held_props`, and `state_tags`, unless an approved `allowed_transition` and cause reference permit a change.

## Description File

Write the Markdown description file exactly at the assigned description path. It must include:

```markdown
# <page_stem>_desc

## Symbol Legend

## Panel Spatial Map

## Constraint Check

## Temporal Continuity Check
```

Keep the required heading text exactly as shown above. Write all body text under those headings in Korean, while preserving every entity id and constraint id verbatim. The description must mention every active `spatial_contract.entities[].id` and every named constraint id. Use plain Korean text to explain each rough mark or symbol's meaning, each panel's spatial map, every constraint result, and temporal continuity status.

## Worker Inspection

After generation and description writing, inspect both files before returning. Mark `needs_rerun` when the blocking image or description fails the prompt, omits required entities/constraints, contradicts a vector/cover/visibility/occlusion relation, introduces unsupported temporal drift, becomes a tactical diagram instead of a rough comic page, or contains detailed/final-art rendering.

Return only:

```text
generated file path: <absolute path>
description path: <absolute path>
worker_status: pass | needs_rerun
worker_note: <concise inspection note>
```
