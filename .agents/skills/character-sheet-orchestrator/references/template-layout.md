# Template Layout

Use `assets/master-sheet-template.png` as the default character master-sheet layout reference when the user does not provide a custom layout. The asset is a wireframe reference, not character content.

Default use is `template_locked`: preserve the template's geometry and structural labels, then replace placeholders with character artwork. Use looser adaptation only when the user asks for a custom or redesigned layout.

## Asset

- Path: `assets/master-sheet-template.png`
- Size: 1055 x 1491 PNG
- Best use: vertical master sheet, A-series poster ratio, concept-art or production-reference output.

## Default Panel Map

1. `01 Front View`
   Large left column for the primary full-body front illustration. Keep this as the dominant identity anchor.

2. `02 Turnaround`
   Top-center panel for front, side, and back views. Use three views by default; add 3/4 views only if the user requests a wider turnaround.

3. `03 Expressions`
   Top-right 2x2 expression grid by default. Expand to six expressions only when the user prioritizes acting range over the template's original spacing.

4. `04 Eye Detail`
   Right-side eye variants or one eye-detail strip. Use for eye shape, iris motif, highlight design, makeup, or special visual effect.

5. `05 Details`
   Middle horizontal strip for hair/accessory, top detail, bottom detail, sleeve/detail, props, or material callouts.

6. `06 Shoes`
   Lower-center shoe views: front, side, back. Reuse this as footgear, lower outfit, or mobility detail for non-human characters.

7. `07 Profile`
   Lower-right profile card. Translate or relabel fields to the user's language. Keep entries short.

8. `08 Character Concept`
   Lower-left concept summary or short design rationale. Use one or two short lines, not paragraphs.

9. `09 Keyword & Mood`
   Lower-middle keyword icons, mood tags, or tone strip.

10. `10 Design Motif`
   Lower-right motif symbols and color palette. Keep palette swatches clear and label only when text will remain readable.

Footer:

- `Notes / Remarks`: optional production notes.
- `Checklist`: optional deliverable checklist.
- `Creator`: optional creator/designer/reviewer metadata.

## Adaptation Rules

- In `template_locked` mode, do not redesign the sheet. Preserve the outer border, top title/header area, project metadata box, numbered section headers, panel positions, profile/lower panels, footer boxes, and blue technical-frame style.
- In `template_locked` mode, replace only mannequin construction bodies, blank face placeholders, plus icons, empty placeholder drawings, and interior art placeholders.
- In `template_locked` mode, keep structural labels such as `CHARACTER MASTER SHEET`, section numbers, and short section headers. Omit dense profile/body copy until final programmatic text composition.
- Keep the broad hierarchy: big identity panel left, structural views center, facial/eye details right, detail strips and profile lower down.
- Use looser recoloring or panel reinterpretation only in `adapted` or `custom` mode. Do not recolor or restyle the default template in `template_locked` mode unless the user explicitly asks.
- For mascot, chibi, animal, creature, robot, or non-human characters, reinterpret anatomy panels without forcing a human mannequin.
- For photoreal sheets, reduce decorative UI density and keep the template as a clean production board.
- For Korean final sheets, relabel sections in Korean or bilingual Korean/English only if space allows.
- If the user's character does not need a section, omit or merge it rather than leaving empty placeholder panels.

## Do Not Copy

- Do not copy the gray mannequin construction body as the character.
- Do not copy blank face circles, plus icons, empty dashed boxes, or placeholder profile lines into the final art.
- Do not preserve the exact English labels when the user requested Korean or another language.
- Do not let the template override the approved character spec, outfit, palette, motifs, or proportions.
- Do not claim the final text is readable just because the template has text zones; inspect the output.

## Template Fidelity QA

Pass when all are true:

- Top `CHARACTER MASTER SHEET` header and right project metadata box remain.
- Section numbers `01` through `10` remain in the original relative positions.
- Left front-view, center turnaround, right expression/eye, middle detail, lower profile/concept/keyword/motif, and footer areas keep the template hierarchy.
- Body text zones are blank, faint placeholder lines, or ready for programmatic overlay.

Fail when any are true:

- The result becomes a poster, art-book spread, ornate fantasy frame, or new layout.
- Numbered section headers, project box, lower panels, or footer boxes disappear.
- Profile or footer areas are replaced by unrelated decorative boxes.
- Character illustration quality is good but the template geometry is not recognizable.
