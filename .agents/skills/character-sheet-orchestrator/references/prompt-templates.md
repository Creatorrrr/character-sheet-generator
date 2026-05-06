# Prompt Templates

Use these templates when the workflow needs image generation, image editing, or text composition prompts. Replace bracketed fields with approved state values.

## Anchor Image

```text
Create a clean character identity anchor image based on the provided reference images and approved character specification.

Goal:
- Establish a stable reference for later multi-panel character sheet generation.
- Preserve the exact face, hair silhouette, outfit structure, colors, accessories, and signature motif.
- Do not redesign the character.

Requested anchor:
- [front full-body / face closeup / side view / back view / outfit detail]

Character specification:
[approved character_spec]

Style:
- [target style]
- clean studio reference image
- neutral background
- no dense text, no logos, no watermark

Important:
- Keep this as an identity anchor, not a poster or scene illustration.
- Avoid random outfit changes, changed age, changed face shape, changed hairstyle, or extra accessories.
```

## Text-Free Draft Sheet

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

Layout reference:
- Use the bundled master-sheet template image as a structural reference when attached: assets/master-sheet-template.png.
- Follow the same overall page hierarchy: large front view column, central turnaround area, right expression and eye-detail stack, middle detail strip, lower shoes/profile/concept/keyword/motif areas, and footer metadata.
- Use the template for panel geometry, spacing, numbered section rhythm, and reserved text zones only.
- Do not copy the mannequin construction lines, blank face placeholders, plus icons, empty profile lines, or exact English wireframe copy as final content.

Required sections:
[approved section list]

Visual style:
- official character design sheet
- clean background with disciplined UI framing
- high-detail [anime / photoreal / mascot / requested style] rendering
- consistent character across all panels
- professional layout
- information-dense but organized
- clear empty areas reserved for final text insertion

Important:
- Same face, hair, outfit, colors, and accessories across every panel.
- Include the required expression and turnaround panels.
- Replace all placeholder bodies and face circles with the approved character.
- Keep text minimal and avoid small body copy.
- No watermark, no random logo text, no unreadable paragraph blocks.
```

## Draft Regeneration

```text
Regenerate the text-free character sheet using the same approved character specification and blueprint.

Keep:
- [approved identity lock]
- [approved panel plan]
- [approved style]
- [approved template usage, if any]

Fix these issues:
- [issue list from review and user feedback]

Do not introduce:
- new hairstyle
- new outfit structure
- new color palette
- missing panels
- dense body text
- copied mannequin placeholders from the template
- character redesign
```

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

Prefer deterministic rendering:

- Use the approved text-free draft as the base image.
- Place the approved copy into the blueprint text boxes.
- If the bundled master-sheet template was used, align text with its intended zones while adapting labels to the user's language.
- Use a font that supports the requested language.
- Keep line lengths short and use explicit wrapping.
- Leave enough padding around every text block.
- Export a final PNG or equivalent image, plus the text JSON when useful.

If using image editing instead:

```text
Add the approved final text to the approved text-free character sheet while preserving the character art and panel layout exactly.

Text payload:
[approved final_text_payload]

Rules:
- Do not alter the character face, hair, outfit, pose, panels, or colors.
- Keep all Korean/requested-language text readable and correctly spelled.
- Use clean labels and short profile text only.
- Keep the template's panel structure readable, but remove or replace leftover wireframe placeholders.
- Avoid tiny dense paragraphs.
- If text cannot be rendered clearly, leave the art unchanged and report that programmatic overlay is required.
```
