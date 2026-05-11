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
- `Required image attachments` / `Prior page continuity references` for previous pages in the same stage when the pack runner provides them.
- `Stage level anchor reference`; if this is the first page, it may define the stage level for later pages, and if prior pages exist it includes the passed anchor note to match.
- Relevant references, text policy, character locks, visual text guard, narrative-first page design, structured `spatial_contract`, rerun correction, and overlay notes.
- The required `*_desc.md` path beside the generated blocking image.

Read the prompt file before generation. Attach every listed required image path as a local image visual reference when calling `image_gen`.

## Generation Rules

- Use Codex built-in `image_gen` exactly once for the blocking page image.
- Generate one complete page image with the approved panel count and reading order.
- Preserve the approved page/panel composition, scenario beat, action rhythm, emotional rhythm, reader eye flow, and comic readability before adding validation marks.
- Draw each important character, object, and environment element as a quick rough pen sketch, roughly the level of detail possible in about 3 seconds per entity.
- Make the rough form recognizable enough to identify the entity category and action: e.g. crouching person, standing person, gun, ball, hoop, low cover, wall, doorway, vehicle, tree, table, or landmark.
- Keep the drawing loose and schematic: simple gesture poses, blocky object contours, rough environmental silhouettes, shadow masses, and minimal landmark outlines are enough.
- Simplify or omit unimportant props/background elements when they are not needed for story readability, action readability, cover/occlusion, landmark continuity, or page composition.
- Add clear lines, arrows, vector marks, relation lines, sight/aim lines, trajectory arrows, and occlusion/cover markers only where needed so positions, directions, and spatial relationships remain inspectable.
- Draw relation lines only for actual approved aim, line of fire, line of sight, movement, or trajectory paths. Do not draw a dashed line, pressure line, projectile, sight line, or aim vector for a `no_line_of_fire` or `not_aims_at` constraint; show non-firing pressure through placement, cover silhouette, reaction, and blocked sight instead.
- Do not render detailed faces, anatomy, costume detail, texture, dialogue, SFX, captions, labels, typography, polished ink, tone/color, or final art.
- Do not turn the page into a pure tactical diagram unless the approved page design explicitly calls for a diagram-like page.
- Semantic labels must not be drawn into the image. Put meanings in the sibling `*_desc.md`.
- Make positions, facing/gaze/aim vectors, trajectories, cover relationships, line of sight, visibility, occlusion, and location anchors easy to inspect.
- Preserve every `spatial_contract` entity id, panel snapshot, vector, visibility/occlusion state, and constraint as a validation overlay, not as the driver of composition.
- For `behind_cover_from` and `line_of_sight_blocked`, place the actor behind the named cover from the `viewpoint_entity` or threat line of fire/line of sight. Reader-side "behind" is insufficient.
- Respect `allowed_exposure` and `forbidden_exposure`: only the allowed peek area may show, and listed forbidden exposure such as torso visibility, above-roofline exposure, or open-field exposure is a failure.
- Translate `allowed_exposure` into readable occlusion staging rather than drawing literal eyes, hands, or weapon tips on a wall/cover edge. Draw the cover as a separate foreground occluder and the hidden character as a distinct recessed silhouette or pocket behind it.
- Keep a clean border, shadow gap, or negative-space sliver between any hidden character and the wall, pillar, vehicle, furniture, or cover. Do not share contour, hatching, texture, or shadow masses between the character and the occluder.
- For tiny exposure such as `eyes_only`, `weapon_edge_only`, `eyes_and_weapon_edge_only`, `eyes_and_hand_only`, or `side_edge_peek_only`, full concealment is acceptable and preferred when the partial peek would become unclear or visually fused. If an approved action requires deliberate exposure, keep only that exposure visible and maintain silhouette separation.
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

After generation and description writing, inspect both files before returning. Mark `needs_rerun` when the blocking image or description fails the prompt, omits required entities/constraints, contradicts a vector/cover/visibility/occlusion relation, treats reader POV as enough for `behind_cover_from`, shows any listed `forbidden_exposure`, fuses a character with a wall/pillar/vehicle/furniture/cover through shared contour, hatching, texture, or shadow masses, pastes an eye/face/hand/weapon tip onto a cover edge, draws a line/projectile/aim vector that violates `no_line_of_fire` or `not_aims_at`, introduces unsupported temporal drift, becomes a tactical diagram instead of a rough comic page, or contains detailed/final-art rendering.

If this page is marked as the stage-level anchor, self-inspect the blocking level especially strictly: it must stay rough, readable, and non-final while setting a reliable reference level for later pages.

Return only:

```text
generated file path: <absolute path>
description path: <absolute path>
worker_status: pass | needs_rerun
worker_note: <concise inspection note>
```
