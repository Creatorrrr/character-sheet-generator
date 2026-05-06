---
name: create-video-closeup-reference-pack
description: Manage a video-production character closeup reference pack made from an approved photoreal character sheet or master face reference. Use when the user wants multiple high-resolution images for video AI identity consistency, wants Codex to coordinate image-specific skills, wants a parallel image generation batch, or needs left/right view pairs generated together in one image to avoid same-direction mistakes.
---

# Create Video Closeup Reference Pack

## Overview

Coordinate a photoreal reference pack for video AI. The pack is not a single beauty image; it is a set of face, expression, hair, costume, prop, hand, full-body, and motion reference images used to keep character identity stable across generated video.

Do not hardcode named character examples or character-specific traits from source notes. Use only the user's supplied character sheet, approved master face, and any user-provided generic character detail block.

## Inputs

Require at least one:

- Approved photoreal character sheet.
- Approved master face reference.
- User-provided character detail block.

Ask for missing inputs only when identity cannot be inferred. If the user requests a full pack and no master face exists, create `01_face_front` first and use it as the identity anchor after approval or after the user explicitly asks for autonomous continuation.

## Image Skill Map

- `01_face_front.png`: `$create-face-front-closeup`
- `02_face_3q_left.png`: `$create-face-3q-left-closeup`
- `03_face_3q_right.png`: `$create-face-3q-right-closeup`
- `04_face_side_left.png`: `$create-face-side-left-profile`
- `05_face_side_right.png`: `$create-face-side-right-profile`
- `06_eye_macro.png`: `$create-eye-brow-macro-closeup`
- `07_expression_sheet.png`: `$create-expression-six-sheet`
- `08_mouth_speech_sheet.png`: `$create-mouth-speech-sheet`
- `09_hair_front_detail.png`: `$create-hair-front-detail-closeup`
- `10_hair_accessory_macro.png`: `$create-hair-accessory-macro`
- `11_upper_costume_closeup.png`: `$create-upper-costume-closeup`
- `12_hand_sleeve_closeup.png`: `$create-hand-sleeve-gesture-closeup`
- `13_belt_props_closeup.png`: `$create-belt-props-closeup`
- `14_shoes_closeup.png`: `$create-shoes-lower-outfit-closeup`
- `15_full_body_front.png`: `$create-full-body-front-reference`
- `16_full_body_back.png`: `$create-full-body-back-reference`
- `17_full_body_side.png`: `$create-full-body-side-reference`
- `18_character_pose_idle.png`: `$create-character-idle-pose`
- `face_turnaround_sheet.png`: `$create-face-turnaround-sheet`
- `hand_gesture_four_sheet.png`: `$create-hand-gesture-four-sheet`

If explicit skill invocation is unavailable, open the sibling `SKILL.md` and reuse its prompt directly.

## Parallel Generation Plan

Before generating, build a batch plan with:

```text
- output: ...
- skill: ...
- request_group: ...
- dependencies: ...
- notes: ...
```

Use these dependency rules:

- `01_face_front` blocks the rest only when no approved master face exists.
- After a master face exists, detail images can be requested in parallel.
- Costume, props, shoes, hands, expression, mouth, hair, and full-body views are independent enough to batch together.
- If an image generation tool supports parallel or batch requests, submit the independent requests at once. If the tool is serial-only, still prepare the full request list so the user can run them in parallel elsewhere.

## Left/Right Pair Rule

When both left and right versions of a view are requested, do not generate them as separate requests. Create one combined image with both directions in one request:

- For `02_face_3q_left` + `03_face_3q_right`, request `02_03_face_3q_pair.png`.
- For `04_face_side_left` + `05_face_side_right`, request `04_05_face_side_pair.png`.

Paired prompt rules:

- One image, two equal side-by-side panels.
- Same person, same lighting, same background, same crop, same clothing.
- Left panel: subject's nose and face direction point toward image-left.
- Right panel: subject's nose and face direction point toward image-right.
- No text labels. Use panel position, not written labels, to distinguish direction.

If only one direction is requested, use the individual direction skill.

## Common Negative Prompt

Append this to every image prompt unless a lower-level skill already includes it:

```text
Negative prompt:
anime, manga, cartoon, illustration, digital painting, semi-realistic art, 3D render, CGI, game asset, doll-like face, wax figure, plastic skin, glossy AI smoothness, overly perfect beauty retouching, over-sharpening, unreal symmetry, mannequin body, artificial lighting, random outfit changes, redesigned face, different age, inconsistent hairstyle, extra fingers, distorted hands, unreadable text, watermark, logo text, low resolution.
```

For a child or minor character, also append:

```text
child-safe, age-appropriate, non-glamour, non-sensual, no mature styling, no suggestive pose, no low-angle body framing.
```

## Reporting

After each batch, report in Korean:

```text
[영상 레퍼런스 팩 진행 결과]
- 기준 이미지: ...
- 생성 요청: ...
- 병렬 그룹: ...
- 좌우 묶음 처리: ...
- 검수 기준: ...
- 다음 결정: ...
```

Do not claim identity consistency, readable text, or correct left/right direction unless the output was inspected. If a paired image shows the same direction twice, rerun the paired request with stricter nose-direction wording.
