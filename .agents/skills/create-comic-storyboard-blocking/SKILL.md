---
name: create-comic-storyboard-blocking
description: Use when an approved comic storyboard page needs an abstract spatial/temporal blocking image and matching description from a create-comic-storyboard-pack runner prompt.
---

# Create Comic Storyboard Blocking

## Overview

Generate exactly one approved comic page for the `storyboard_blocking` stage. This is not final art. It is a visual contract for positions, directions, cover, visibility, occlusion, object trajectories, landmarks, and temporal state continuity before sketch/ink work begins.

The pack runner owns `state.json`, import, parent inspection, rerun, and stage-review. Do not edit runner state files.

## Inputs

Use the assigned subagent prompt from the pack runner. It provides:

- Run folder, approved plan, assigned page, stage, prompt file, output path, description path, and batch id.
- Relevant references, text policy, character locks, visual text guard, structured `spatial_contract`, rerun correction, and overlay notes.
- The required `*_desc.md` path beside the generated blocking image.

Read the prompt file before generation.

## Generation Rules

- Use Codex built-in `image_gen` exactly once for the blocking page image.
- Generate one complete page image with the approved panel count and reading order.
- Use only simplified symbols: circles, squares, triangles, lines, arrows, silhouettes, shadows, and relation lines.
- Do not render detailed faces, anatomy, costume detail, dialogue, SFX, captions, labels, typography, polished ink, tone/color, or final art.
- Semantic labels must not be drawn into the image. Put meanings in the sibling `*_desc.md`.
- Make positions, facing/gaze/aim vectors, trajectories, cover relationships, line of sight, visibility, occlusion, and location anchors easy to inspect.
- Preserve every `spatial_contract` entity id, panel snapshot, vector, visibility/occlusion state, and constraint.
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

Keep the required heading text exactly as shown above. Write all body text under those headings in Korean, while preserving every entity id and constraint id verbatim. The description must mention every active `spatial_contract.entities[].id` and every named constraint id. Use plain Korean text to explain each symbol's meaning, each panel's spatial map, every constraint result, and temporal continuity status.

## Worker Inspection

After generation and description writing, inspect both files before returning. Mark `needs_rerun` when the blocking image or description fails the prompt, omits required entities/constraints, contradicts a vector/cover/visibility/occlusion relation, introduces unsupported temporal drift, or contains detailed/final-art rendering.

Return only:

```text
generated file path: <absolute path>
description path: <absolute path>
worker_status: pass | needs_rerun
worker_note: <concise inspection note>
```
