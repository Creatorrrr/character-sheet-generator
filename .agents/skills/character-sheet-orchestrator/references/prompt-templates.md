# Prompt Templates

Use these templates when the workflow needs image generation, image editing, or text composition prompts. Replace bracketed fields with approved state values.

## Image Generation Tool Policy

- Use built-in `image_gen` by default for anchor images, panel art, draft sheets, final text-included sheets, text repair, and visual regenerations.
- Label image inputs before calling `image_gen`: template layout reference, primary character identity reference, supporting outfit/prop/detail reference, or approved anchor.
- Save the selected `image_gen` output under the active run folder before reporting it or using it in later stages.
- Inspect each generated image before approval. If review fails, regenerate with `image_gen` using the same approved spec/blueprint and only the concrete review issues.
- Auto-regenerate at most 2 times. After that, stop and report the best result plus remaining blockers.
- Use built-in `image_gen` for final Korean/body text insertion. Do not use deterministic text overlay tools such as SVG, HTML/CSS, Canvas, Pillow, or Figma for final text placement.

## Anchor Image

Use built-in `image_gen` for this prompt.

```text
Create a clean character identity anchor image based on the provided reference images and approved character specification.

Goal:
- Establish a stable reference for later multi-panel character sheet generation.
- Preserve the exact face, hair silhouette, outfit structure, colors, accessories, and signature motif.
- Do not redesign the character.

Requested anchor:
- [front full-body / face closeup / side view / back view / outfit detail]

Input images for image_gen:
- Template reference: [none / optional, role if attached]
- Primary character identity reference: [path_or_id and role]
- Supporting references: [path_or_id and role list]

Character specification:
[approved character_spec]

Identity lock:
[identity_lock.must_keep]

Style:
- [target style]
- clean studio reference image
- neutral background
- no dense text, no logos, no watermark

Important:
- Keep this as an identity anchor, not a poster or scene illustration.
- Avoid random outfit changes, changed age, changed face shape, changed hairstyle, or extra accessories.
```

## Template-Locked Draft Sheet

Use this when `generation_mode` is `template_locked` or when the bundled `assets/master-sheet-template.png` must stay visually recognizable.

Use built-in `image_gen` for the first draft and for stricter template-locked regenerations.

```text
Create a character master sheet by filling the provided template image, not by redesigning the sheet.

Highest priority:
- Preserve the template layout almost exactly.
- If there is a conflict between making the sheet more beautiful and preserving the template geometry, preserve the template geometry.
- Keep the same vertical page structure, outer border, top title/header area, project metadata box, numbered section headers, panel positions, profile/lower panels, footer boxes, and blue technical wireframe style.
- Do not invent a new decorative frame, fantasy border, poster layout, art-book composition, ornate parchment board, or replacement UI.
- Treat `assets/master-sheet-template.png` as the layout base. Replace only the mannequin bodies, face placeholders, plus icons, empty placeholder drawings, and interior art placeholders with approved character artwork.

Approved character specification:
[approved character_spec]

Identity lock:
[identity_lock.must_keep]

Template and blueprint:
[approved blueprint panel_plan, generation_mode, and template usage]

Input images for image_gen:
- Template layout reference: `assets/master-sheet-template.png`. Preserve this geometry.
- Primary character identity reference: [path_or_id and role]
- Supporting outfit/prop/detail references: [path_or_id and role list]
- Approved anchors, if any: [path_or_id and role list]

Template preservation rules:
- Keep the top `CHARACTER MASTER SHEET` header and the right project metadata box.
- Keep section `01` as the large left Front View panel.
- Keep section `02` as the top-center Turnaround panel with front, side, and back views.
- Keep section `03` as the top-right 2x2 Expressions grid.
- Keep section `04` as the Eye Detail panel below expressions.
- Keep section `05` as the horizontal Details strip.
- Keep section `06` as the Shoes or lower-detail panel.
- Keep section `07` as the Profile card area with blank body fields or faint placeholder lines.
- Keep sections `08`, `09`, and `10` in their original lower positions.
- Keep footer boxes for Notes / Remarks, Checklist, and Creator in their original lower positions.
- Keep section numbers `01`-`10` visible and aligned to the original template rhythm.

Text policy:
- This is a no-dense-body-copy draft, not a structural-label-free redesign.
- Preserve structural labels such as the sheet title, section numbers, and short section headers.
- Do not add dense body copy, long paragraphs, tiny unreadable filler text, watermark, credits, or logo marks.
- Leave profile, concept, notes, checklist, creator, and other copy fields blank or as faint placeholder lines for later `image_gen` final text insertion.

Character content:
- Fill the template with the approved character.
- Keep the same face, hair, outfit, palette, accessories, and proportions across every panel.
- Fit character artwork inside the existing template boxes.
- Include the required expression, turnaround, detail, footwear/lower-detail, motif, and palette content from the blueprint.

Visual style:
- Official production reference sheet.
- Clean rendering appropriate to [approved target style].
- Layout fidelity is more important than decorative polish.
```

## Adapted Draft Sheet

Use this only when the user wants a custom or adapted layout, or when preserving the exact bundled template geometry is not a priority.

Use built-in `image_gen` for adapted draft generation.

```text
Create a high-resolution character design master sheet based on the provided character specification, reference images, anchors, and blueprint.

Goal:
- Produce a polished character master sheet with a clean organized layout.
- Focus on image structure and illustration quality only.
- Do NOT include dense readable body text.
- Use only large section titles, short labels, panel numbers, or placeholder lines where needed.

Approved character specification:
[approved character_spec]

Identity lock:
[identity_lock.must_keep]

Blueprint:
[approved blueprint panel_plan and layout_style]

Input images for image_gen:
- Layout/reference image, if any: [path_or_id and role]
- Primary character identity reference: [path_or_id and role]
- Supporting outfit/prop/detail references: [path_or_id and role list]
- Approved anchors, if any: [path_or_id and role list]

Layout reference:
- Use the bundled master-sheet template image as a structural reference when attached: assets/master-sheet-template.png.
- Follow the same overall page hierarchy: large front view column, central turnaround area, right expression and eye-detail stack, middle detail strip, lower shoes/profile/concept/keyword/motif areas, and footer metadata.
- Use the template for panel geometry, spacing, numbered section rhythm, and reserved text zones only.
- Do not copy the mannequin construction lines, blank face placeholders, plus icons, empty profile lines, or exact English wireframe copy as final content.
- If exact template fidelity is required, stop and use the Template-Locked Draft Sheet prompt instead.

Required sections:
[approved section list]

Visual style:
- official character design sheet
- clean background with disciplined UI framing
- high-detail [anime / photoreal / mascot / requested style] rendering
- consistent character across all panels
- professional layout
- information-dense but organized
- clear empty areas reserved for final `image_gen` text insertion

Important:
- Same face, hair, outfit, colors, and accessories across every panel.
- Include the required expression and turnaround panels.
- Replace all placeholder bodies and face circles with the approved character.
- Keep text minimal and avoid small body copy.
- No watermark, no random logo text, no unreadable paragraph blocks.
```

## Draft Regeneration

Use built-in `image_gen` for visual regeneration. Keep the approved identity lock, character spec, blueprint, panel plan, and template usage unchanged. The only new instruction should be the failed-review issues.

```text
Regenerate the no-dense-body-copy character sheet using the same approved character specification and blueprint.

Attempt:
- Current attempt index: [attempt_index]
- Max automatic regenerations: 2
- Regeneration reason: [draft_review.issues or user feedback]

Keep:
- [approved identity lock]
- [approved panel plan]
- [approved style]
- [approved template usage, if any]

Fix these issues:
- [issue list from review and user feedback]

Input images for image_gen:
- Previous failed draft, if available: [path_or_id and role]
- Template layout reference, if applicable: [path_or_id and role]
- Primary character identity reference: [path_or_id and role]
- Approved anchors/supporting references: [path_or_id and role list]

Do not introduce:
- new hairstyle
- new outfit structure
- new color palette
- missing panels
- dense body text
- copied mannequin placeholders from the template
- character redesign
```

For bundled-template geometry failures, prefer the Template-Locked Draft Sheet prompt for the first stricter regeneration. If template fidelity fails again for the same approved blueprint, switch to visual fallback composition only: keep the fixed template background and generate needed panel art with built-in `image_gen`. Final text placement must still be performed with built-in `image_gen`; do not use local text overlay for the final text-included sheet. Do not keep broad-regenerating the whole sheet after the automatic regeneration budget is exhausted.

## Copywriting Constraints

Write final sheet copy as structured JSON.

Rules:

- Match the user's requested language.
- Keep every field short enough for a compact visual sheet.
- Prefer labels, keyword lists, and one-line descriptions over paragraphs.
- Do not invent lore that conflicts with approved facts.
- Mark uncertain facts as optional or omit them.

Output shape:

```json
{
  "sheet_title": "",
  "subtitle": "",
  "profile": {
    "이름": "",
    "역할": "",
    "성격": "",
    "특징": ""
  },
  "keywords": [],
  "motifs": [],
  "palette_labels": [],
  "section_labels": {},
  "short_notes": {}
}
```

## Final Composition

Use built-in `image_gen` for final composition:

- Use the approved no-dense-body-copy draft as the base image.
- Add the approved copy into the blueprint text boxes through `image_gen`.
- If the bundled master-sheet template was used, place text in its intended zones while adapting labels to the user's language.
- Keep line lengths short, text blocks compact, and every text item large enough for image-model rendering.
- Export the selected final text-included image, plus the text JSON when useful.
- Do not use SVG, HTML/CSS, Canvas, Pillow, Figma, or any other programmatic text overlay path for final text placement.

Final image_gen text insertion prompt:

```text
Add the approved final text to the approved no-dense-body-copy character sheet using image generation/editing while preserving the character art and panel layout as closely as possible.

Text payload:
[approved final_text_payload]

Rules:
- Do not alter the character face, hair, outfit, pose, panels, or colors.
- Keep all Korean/requested-language text readable and correctly spelled.
- Use clean labels and short profile text only.
- Keep the template's panel structure readable, but remove or replace leftover wireframe placeholders.
- Avoid tiny dense paragraphs.
- If text cannot be rendered clearly after the configured repair budget, report the remaining text issues. Do not switch to programmatic text overlay.
```
