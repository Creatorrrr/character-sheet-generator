# Prompt Templates

Use these prompts to generate closeup pack requests from an approved character sheet. Replace bracketed values with the approved state.

## Common Source Block

Include this block in every request:

```text
Source of truth:
- Approved character sheet: [source_character_sheet]
- Orchestrator state, if available: [source_orchestrator_state]
- Approved identity anchor, if available: [identity_anchor]

Style requirement:
- Preserve the exact approved source style: [anime / mascot / photoreal / semi-real / custom].
- Do not convert the character to photoreal unless the user explicitly requested photoreal conversion.
- Keep the same rendering language, proportions, line quality, surface treatment, lighting logic, and color design as the approved sheet.

Identity lock:
[identity_lock.must_keep]

Character spec:
[character_spec]

Do not copy:
- template placeholders
- mannequin construction lines
- plus icons
- blank wireframe boxes
- UI guide lines as character content
- random logo text or watermark
```

## 01 Face Front

```text
Create `01_face_front.png`, a front-facing face identity closeup derived from the approved character sheet.

Goal:
- Establish or confirm the master identity anchor for the closeup reference pack.
- Show the face, hairline, eyes, expression baseline, head shape, and upper shoulders clearly.

Composition:
- Front-facing head-and-shoulders closeup.
- Neutral or soft default expression matching the approved character personality.
- Simple clean background.
- No text labels.

Use the common source block and preserve source style exactly.
```

## 02 03 Face Three-Quarter Pair

```text
Create `02_03_face_3q_pair.png`, one image with two equal side-by-side panels.

Composition:
- Left panel: the character's face is in three-quarter view, nose pointing toward image-left.
- Right panel: the character's face is in three-quarter view, nose pointing toward image-right.
- Same crop, same style, same lighting, same clothing, same facial identity.
- No written labels unless explicitly requested.

Use the common source block and preserve source style exactly.
```

## 04 05 Face Side Pair

```text
Create `04_05_face_side_pair.png`, one image with two equal side-by-side panels.

Composition:
- Left panel: clean side profile, nose pointing toward image-left.
- Right panel: clean side profile, nose pointing toward image-right.
- Match hair silhouette, ears, accessories, neckline, and expression baseline.
- No written labels unless explicitly requested.

Use the common source block and preserve source style exactly.
```

## Detail Outputs

Use this template for `06_eye_detail.png`, `08_hair_detail.png`, `09_upper_outfit_detail.png`, `10_lower_outfit_shoes.png`, `12_signature_props.png`, `15_back_hair_or_back_detail.png`, and `16_material_texture_details.png`.

```text
Create `[output_name]`, a closeup reference image focused on `[detail_target]`.

Goal:
- Stabilize `[detail_target]` for downstream character generation.
- Make construction, shape, color, material, pattern, and motif details clear.

Composition:
- Close crop centered on the detail.
- Clean background.
- No unrelated pose or scene.
- No text labels unless explicitly requested.

Must preserve:
- approved source style
- approved color palette
- approved motif and accessory design
- approved outfit or anatomy structure

Use the common source block.
```

## Expression Sheet

```text
Create `07_expression_sheet.png`, a four-to-six panel expression closeup sheet.

Default expressions:
1. neutral
2. smile
3. surprised
4. thinking
5. playful or embarrassed
6. determined or confident

Rules:
- Same face identity, hair, outfit neckline, lighting, and source style in every panel.
- Expressions should match the approved character personality.
- No written labels unless explicitly requested.

Use the common source block.
```

## Hand Gesture Sheet

```text
Create `11_hand_gesture_sheet.png`, a compact hand and sleeve gesture reference sheet.

Default gestures:
- relaxed open hand
- pointing or presenting gesture
- holding signature prop if one exists
- character-specific gesture from the approved concept

Rules:
- Preserve hand shape, glove, sleeve, accessory, and source style.
- Keep gestures clear, non-sensual, and reference-oriented.
- No text labels unless explicitly requested.

Use the common source block.
```

## Full Body And Pose Outputs

Use this template for `17_full_body_front.png`, `18_full_body_side_back_pair.png`, and `19_idle_pose.png`.

```text
Create `[output_name]`, a full-body reference derived from the approved character sheet.

Goal:
- Clarify the character's full-body proportions, silhouette, outfit, and pose baseline.

Composition:
- Neutral clean reference pose.
- Full body visible from head to toe.
- Simple background.
- No text labels unless explicitly requested.

For side/back pairs:
- Use one image with equal panels.
- Preserve exact same outfit, body proportions, hairstyle, and accessories across views.

Use the common source block and preserve source style exactly.
```

## Palette Motif Reference

```text
Create `20_palette_motif_reference.png`, a clean reference image for color palette, motif icons, symbols, and pattern fragments.

Goal:
- Isolate approved colors, motifs, markings, and decorative shapes from the character sheet.

Rules:
- Use clean swatches and motif samples.
- Keep labels out unless readable text is explicitly requested.
- Do not invent new brand marks or symbols.
- Preserve the approved character palette and motifs only.

Use the common source block.
```

## Common Negative Guidance

Append when appropriate:

```text
Avoid: redesigned face, changed age, changed species/body type, changed hairstyle, changed outfit structure, changed palette, missing signature accessory, template mannequin lines, placeholder face circles, random labels, watermark, unreadable text, unrelated background scene, over-stylization that differs from the approved sheet.
```

For child or minor-coded characters, append:

```text
child-safe, age-appropriate, non-glamour, non-sensual, no mature styling, no suggestive pose, no low-angle body framing.
```
