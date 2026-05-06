# Stage Protocols

Use these as logical subskills inside `character-sheet-orchestrator`. Load this file when executing the workflow or resuming from a middle stage.

## 1. Input Parser

Collect:

- Source character images and which image is the primary reference.
- Character name, role, world, style target, output language, audience, and use case.
- Visible traits: face, hair, eyes, body type, outfit, accessories, palette, props, and motifs.
- Requested sheet type: redesign sheet, anime setting sheet, mascot sheet, photoreal sheet, video reference board, or document-style profile.
- Requested panels and any hard exclusions.

Output:

```json
{
  "character_name": "",
  "source_images": [],
  "requested_style": "",
  "language": "ko",
  "known_traits": {},
  "requested_sections": [],
  "missing_info": []
}
```

Report:

```text
[단계 1/8] 입력 분석 완료

확인된 정보:
- 캐릭터명:
- 원하는 시트 스타일:
- 제공 자료:
- 누락 가능 정보:

이대로 정보 구체화 단계로 진행할까요?
```

## 2. Spec Normalizer

Normalize all later generation around a single character spec.

Define:

- `identity_lock.must_keep`: face shape, hair silhouette, eye design, main outfit structure, palette, signature accessories, and motif.
- `identity_lock.flexible`: pose, expression intensity, minor UI styling, optional props, panel order, and copy tone.
- `character_spec`: name, role, age appearance when appropriate, personality keywords, visual motifs, palette, hair, eyes, outfit, accessories, expressions, and target style.
- Blocking questions only when identity or output format would otherwise be guesswork.

Report:

```text
[단계 2/8] 캐릭터 정보 구체화 완료

정리된 캐릭터 스펙:
- 이름:
- 역할:
- 성격 키워드:
- 외형 핵심:
- 대표 색상:
- 상징 모티프:
- 반드시 유지할 요소:

확인 요청:
1. 승인하고 시트 설계안 생성
2. 일부 항목 수정
3. 빠진 정보 추가
```

## 3. Blueprint Planner

Default to the bundled template at `assets/master-sheet-template.png` when the user asks for a general character master sheet and has not specified a different layout. Read `references/template-layout.md` for the panel map and constraints.

Choose one layout family:

- Basic: Front View, Turnaround, Expressions, Outfit Details, Profile, Color Palette.
- Standard: Front View, Turnaround, Expressions, Eye Detail, Outfit Details, Shoes, Profile, Keywords and Mood, Design Motif and Palette.
- Advanced: Hero Full Body, Turnaround, Expression Sheet, Face and Eye Detail, Outfit Breakdown, Props, Profile Card, Personality or Quotes, Design Keywords, Motifs and Palette.

Choose one generation mode:

- `template_locked`: default for the bundled `master-sheet-template.png`. Preserve template geometry, structural labels, numbered headers, project/profile/lower/footer boxes, and blue technical-frame rhythm.
- `adapted`: keep the broad hierarchy but allow resizing, relabeling, recoloring, or section merging.
- `custom`: use a user-provided layout or a new layout family.

Output:

```json
{
  "sheet_type": "master_sheet",
  "layout_style": "",
  "generation_mode": "template_locked | adapted | custom",
  "panel_plan": [
    {"id": "01", "title": "Front View", "priority": "high"}
  ],
  "text_strategy": {
    "draft_stage": "titles only / placeholder lines",
    "final_stage": "short readable labels"
  }
}
```

Report the proposed left/center/right/top/bottom layout, included sections, and the approval choices. After the user approves the blueprint, switch to `post_blueprint_autonomous` by default unless the user explicitly asks for fully gated operation.

If using the bundled template, state whether the mode is `template_locked` or `adapted`. In `template_locked`, do not plan to resize, recolor, or reorder template structure unless the user asks. Do not present the wireframe mannequin, empty profile lines, or placeholder circles as character content.

## 4. Anchor Generator

Use this stage when the source image is not enough to keep identity stable across multiple panels.

Generation tool:

- Use built-in `image_gen` by default for anchor image generation.
- Treat every provided source image as an identity/style reference, not as an editable file path, unless the user explicitly asks for editing.
- Use CLI/API image generation only when the user explicitly requests it or approves a fallback because built-in `image_gen` cannot satisfy a required capability.

Recommended anchors:

- Front full-body reference.
- Face closeup reference.
- Side or back view if turnaround accuracy matters.
- Outfit/detail closeup for complex costumes.

Skip this stage when the user already supplied clear reference images or wants a fast one-shot result.

Output:

```json
{
  "generation_tool": "built-in image_gen",
  "anchor_assets": {
    "full_body_front": "",
    "face_closeup": "",
    "side_view": "",
    "outfit_detail": ""
  },
  "attempt_index": 0,
  "review_history": []
}
```

Inspect generated anchors before using them. If an anchor has identity drift, missing required traits, random text, watermark, or unusable framing, regenerate with `image_gen` using the same approved spec and only the concrete review issues. In `post_blueprint_autonomous`, record which anchors were generated or selected and continue without asking for approval.

## 5. Draft Generator

Generate a no-dense-body-copy sheet from the approved spec, blueprint, source images, and anchors.

Generation tool:

- Use built-in `image_gen` by default for draft sheet generation and visual regeneration.
- Attach or reference the approved template, character references, and anchors according to the current tool's available image-input flow.
- Do not replace `image_gen` with local collage/composition as the first draft path. Use fixed-template programmatic composition only as fallback after template fidelity failure or when the reviewer explicitly routes there.
- Record `generation_tool`, `attempt_index`, `max_auto_regenerations`, and `regeneration_reason` in state for each attempt.

Rules:

- If using the bundled template in `template_locked` mode, use it as a visual layout base together with the approved character references. Preserve the template's outer border, top title/header area, project metadata box, numbered section headers, panel positions, profile/lower panels, footer boxes, and blue technical wireframe rhythm.
- In `template_locked` mode, replace only mannequin bodies, blank face placeholders, plus icons, empty placeholder drawings, and interior art placeholders with the approved character content.
- In `template_locked` mode, keep structural labels such as the large sheet title, section numbers, and short section headers. Do not treat these as unwanted random text.
- If using the bundled template in `adapted` mode, follow the broad panel structure, border rhythm, scale areas, and text-space reservations, but report any intended resizing or merging.
- Replace all mannequin silhouettes, blank face circles, plus icons, and empty placeholder boxes with the approved character content or clean empty text/composition areas.
- Prioritize same person, same face, same hair, same outfit, same palette, and same accessories across all panels.
- Include all blueprint panels unless a tool limitation makes it impossible; report any omission.
- Use no dense body text. Allow structural labels, large section titles, small placeholder lines, or numbered panel tags.
- Leave clean text areas for final composition.
- Keep the sheet high-resolution, organized, and useful as a production reference.
- Do not change the approved spec, identity lock, blueprint, or panel plan during regeneration. Regeneration may only add the concrete failed-review issues as fixes.

Report only in fully gated mode:

```text
[단계 5/8] 텍스트 없는 캐릭터 시트 초안 생성 완료

현재 결과에서 확인해 주세요:
- 캐릭터 얼굴/의상 일관성
- 시트 레이아웃
- 포함된 섹션
- 표정 종류
- 턴어라운드 구성
- 디테일 패널 구성

선택:
1. 승인하고 최종 텍스트 구성 단계로 진행
2. 수정 요청 후 초안 재생성
3. 레이아웃부터 다시 조정
```

## 6. Draft Reviewer

Inspect before asking the user to approve.

Check:

- Template fidelity if `generation_mode` is `template_locked`: top header, project metadata box, section numbers `01`-`10`, original relative panel positions, lower profile/concept/keyword/motif areas, and footer boxes.
- Same-character consistency across views and expressions.
- Expression variety and required expression count.
- Missing or duplicated panels.
- Turnaround and detail-panel clarity.
- Profile/copy box space.
- Outfit, shoes, props, eye detail, and palette coverage.
- No-dense-body-copy compliance: no long paragraphs, no tiny fake profile text, and no image-model attempt to write final Korean body copy.
- Watermark/random text: no logos, credits, signatures, random letters, or unintended copyright marks.
- Whether only a partial edit is enough.

Output:

```json
{
  "review_summary": {
    "template_fidelity": "pass | fail | not_applicable",
    "passed": [],
    "issues": [],
    "recommended_action": "approve | partial_edit | regenerate | return_to_blueprint | fallback_composition",
    "generation_tool": "built-in image_gen",
    "attempt_index": 0,
    "max_auto_regenerations": 2,
    "regeneration_reason": ""
  },
  "review_history": []
}
```

Auto-regeneration policy:

- If `recommended_action` is `approve`, ask the user to approve the draft and advance only in fully gated mode. In `post_blueprint_autonomous`, mark the draft as self-reviewed and continue to copywriting.
- Treat `attempt_index` as zero-based: `0` is the first draft, `1` and `2` are the two allowed automatic regenerations.
- If `recommended_action` is not `approve` and `attempt_index` is less than `max_auto_regenerations`, do not ask the user yet. Append the review to `review_history`, set `regeneration_reason` to the concrete `issues`, increment `attempt_index`, and run Draft Generator again with built-in `image_gen`.
- Use only the approved spec, approved blueprint, and current review issues in the regeneration prompt. Do not invent new sections, redesign the character, or change the approved layout.
- If a `template_locked` draft has good character art but fails template fidelity, do not approve it. First route to stricter `template_locked` `image_gen` regeneration.
- If template fidelity fails again after a stricter regeneration, recommend `fallback_composition`: fixed template background, separately generated panel art with `image_gen`, and programmatic composition.
- If the only issue is broken text, clipping, typo, or Korean readability, do not regenerate the character art. Route to final composition or text repair.
- If `attempt_index` reaches `max_auto_regenerations` and the draft still fails, stop regeneration and report the best available draft, the review history, and remaining blockers.

## 7. Copywriter

Write short final text sized for the blueprint boxes.

Include:

- Sheet title and subtitle.
- Profile fields.
- Character concept summary.
- Personality keywords.
- Motifs and palette names.
- Section labels and optional short notes.

Keep text concise, readable, and in the requested language. Avoid long paragraphs.

Output:

```json
{
  "sheet_title": "",
  "subtitle": "",
  "profile": {},
  "keywords": [],
  "motifs": [],
  "section_labels": {}
}
```

## 8. Final Composer

Combine the approved no-dense-body-copy draft with the approved copy. In `post_blueprint_autonomous`, the copy payload is self-reviewed and approved for composition when it satisfies the box-size and factual-consistency constraints.

Preferred order:

1. Programmatic overlay with SVG, HTML/CSS, Canvas, Pillow, Figma, or another deterministic renderer.
2. Image editing only for labels or graphic placeholders.
3. Full image-model text insertion only when the user accepts the risk of broken small text.

Preserve the character and panel art. If only text is wrong, do not regenerate the character art.

When the bundled template is used, align final copy to its text zones: project metadata, profile card, concept notes, keywords, mood/tone, design motif, palette, checklist or remarks. Rename or omit lower-priority footer boxes if they do not help the user's final sheet.

## 9. QA

Check:

- Title, labels, and profile text are readable.
- Korean or requested-language text is not garbled.
- Text is not clipped or overlapping the art.
- Required sections are present.
- Character identity is consistent.
- Profile facts, motifs, palette, and keywords match the approved spec.
- Layout is balanced and delivery-ready.

Report:

```text
[단계 8/8] 최종 QA 완료

검수 결과:
- 텍스트 가독성:
- 프로필 반영:
- 캐릭터 일관성:
- 누락 섹션:
- 수정 필요:

선택:
1. 최종본 확정
2. 경미한 수정 요청
3. 특정 패널만 부분 수정
```

In `post_blueprint_autonomous`, this is the first normal user-facing report after blueprint approval. Include the textless draft sheet, final text-included sheet, self-review/QA notes, any regeneration or text repair performed, and remaining known issues. Ask for final-stage feedback only here.
