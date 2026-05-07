# Pack Map

Use this file to choose outputs and dependencies for `$create-character-sheet-closeup-reference-pack`.

## Presets

### Core

Use `core` by default.

```text
01_face_front.png
02_03_face_3q_pair.png
04_05_face_side_pair.png
06_eye_detail.png
07_expression_sheet.png
08_hair_detail.png
09_upper_outfit_detail.png
10_lower_outfit_shoes.png
11_hand_gesture_sheet.png
12_signature_props.png
```

### Full

Use `full` when the user asks for a complete production, animation, video, or downstream-generation pack.

```text
13_face_turnaround_sheet.png
14_mouth_speech_sheet.png
15_back_hair_or_back_detail.png
16_material_texture_details.png
17_full_body_front.png
18_full_body_side_back_pair.png
19_idle_pose.png
20_palette_motif_reference.png
```

The `full` preset includes all `core` outputs unless the user asks to skip them.

## Output Definitions

- `01_face_front.png`: Primary front-facing face identity closeup. Blocks later outputs only when no approved face anchor exists.
- `02_03_face_3q_pair.png`: Paired left/right three-quarter face views in one image to prevent same-direction mistakes.
- `04_05_face_side_pair.png`: Paired left/right side profile face views in one image.
- `06_eye_detail.png`: Eye shape, iris motif, eyelashes, makeup, highlight style, or special eye effects.
- `07_expression_sheet.png`: Four to six expression closeups using the approved personality and acting range.
- `08_hair_detail.png`: Front hair silhouette, bangs, hair accessory, texture, color gradients, or tie shapes.
- `09_upper_outfit_detail.png`: Collar, neck accessory, jacket, shirt, sleeve, chest emblem, fabric, and top construction.
- `10_lower_outfit_shoes.png`: Lower outfit, socks, shoes, soles, straps, boots, or non-human lower-body detail.
- `11_hand_gesture_sheet.png`: Hand shape, gloves, sleeve interaction, signature gestures, or tool-holding poses.
- `12_signature_props.png`: Props, weapons, mascot items, bag, belt items, charms, or other signature accessories.
- `13_face_turnaround_sheet.png`: Front, three-quarter, side, and back-of-head face/hair reference in one sheet.
- `14_mouth_speech_sheet.png`: Speaking mouth shapes or emotion mouth variants while keeping face identity stable.
- `15_back_hair_or_back_detail.png`: Back hair silhouette, back outfit closure, hood, wings, tail, or rear accessory.
- `16_material_texture_details.png`: Fabric, metal, leather, plastic, holographic, fur, scales, or special surface details.
- `17_full_body_front.png`: Full-body front pose for identity and proportion confirmation.
- `18_full_body_side_back_pair.png`: Side/back or side-plus-back full-body views, preferably as one paired sheet.
- `19_idle_pose.png`: Neutral standing pose for downstream animation or video use.
- `20_palette_motif_reference.png`: Color swatches, motif icons, symbols, pattern fragments, or visual brand tokens.

## Dependency Rules

- Generate `01_face_front.png` through the runner and mark it `inspected_pass` before every dependent face or detail output.
- If a resumed run already has an inspected face anchor, continue from the next dependency-ready item instead of creating a new run.
- Generate paired left/right outputs as a single two-panel request.
- After identity anchor inspection passes, eye, hair, outfit, props, shoes, hands, expression, and material details are independent enough for parallel generation.
- Full-body side/back and face turnaround depend on either a clear source full-body sheet or `17_full_body_front.png` marked `inspected_pass`.
- Use existing photoreal child skills only as prompt-pattern inspiration. Do not invoke them by default because they force photoreal output.

## Batch Plan Groups

Recommended groups:

```text
Group A: identity_anchor
- 01_face_front.png

Group B: face_direction_pairs
- 02_03_face_3q_pair.png
- 04_05_face_side_pair.png

Group C: parallel_details
- 06_eye_detail.png
- 07_expression_sheet.png
- 08_hair_detail.png
- 09_upper_outfit_detail.png
- 10_lower_outfit_shoes.png
- 11_hand_gesture_sheet.png
- 12_signature_props.png

Group D: full_pack_extensions
- 13_face_turnaround_sheet.png
- 14_mouth_speech_sheet.png
- 15_back_hair_or_back_detail.png
- 16_material_texture_details.png
- 17_full_body_front.png
- 18_full_body_side_back_pair.png
- 19_idle_pose.png
- 20_palette_motif_reference.png
```
