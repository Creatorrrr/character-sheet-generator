---
name: character-sheet-orchestrator
description: Orchestrate staged creation of a character design sheet from user-provided character images and notes. Use when the user wants a full character sheet, master sheet, setting sheet, mascot sheet, anime or photoreal character reference board, or a workflow that parses input, normalizes character specs, plans a blueprint, optionally creates anchor images, generates a no-dense-body-copy draft, reviews it, writes final copy, composes readable text, and performs final QA.
---

# Character Sheet Orchestrator

## Overview

Manage a gated character-sheet workflow. Separate character identity decisions, layout decisions, image generation, text writing, text composition, and QA so each expensive regeneration has a clear cause.

## Default Output Location

If the user does not specify where to save files, create a new run folder under `/Users/chasoik/Projects/character-sheet-generator/output/`.

- Use `output/<slug>-character-sheet-YYYYMMDD-HHMMSS/` for this workflow.
- Build `<slug>` from the character name, then the input image filename stem, then `character-sheet`. Normalize it to lowercase ASCII letters, numbers, and hyphens. If the normalized value is empty, use `character-sheet`.
- If the user is resuming from an existing run folder, keep using that folder instead of creating a new one.
- Save all generated sheets, draft images, anchor assets, composed text outputs, QA notes, and optional state JSON under the selected run folder.
- When reporting artifacts, include the selected run folder and write output paths under that folder.

## Core Rules

- Require at least one uploaded/reference character image or enough written detail to define the character. Ask for missing inputs only when identity, style, or output language cannot be inferred.
- Keep an explicit working state in the conversation. If the user wants the job to be resumable, write the state JSON beside the output artifacts using the schema in `references/state-schema.md`.
- Pause for approval after spec, blueprint, draft, and final text unless the user explicitly asks for autonomous continuation.
- Preserve the latest approved artifact as the source for the next stage.
- Use `assets/master-sheet-template.png` as the default master-sheet layout reference unless the user requests another layout. Default template usage is `template_locked`: preserve the template geometry, top header, project metadata box, numbered section headers, profile/lower panels, footer boxes, and blue technical wireframe rhythm; replace only mannequin bodies, face placeholders, plus icons, and empty placeholder drawings with character content.
- Prefer no-dense-body-copy image generation for the art draft, then programmatic text overlay for the final sheet. In draft images, preserve structural labels, section numbers, and large template headers when template fidelity matters; avoid dense profile copy and small body text. Use image-model text insertion only as a fallback.
- If a bundled-template draft fails template fidelity once, do not keep repeating broad image prompts. Route to either a stricter `template_locked` regeneration or the fallback path: fixed template background, separately generated panel art, and programmatic composition.
- Report in Korean by default. Keep reports factual and do not claim readable text, identity consistency, or panel completeness unless the result was inspected.
- If a generated sheet has broken text but the character art is good, repair or recompose only text instead of regenerating the character.

## Workflow

1. Parse input.
   Extract source images, character name, visible traits, supplied lore, target language, sheet style, requested sections, and missing information.

2. Normalize the character spec.
   Lock identity-critical traits, structure appearance/personality/motifs/palette, define must-keep and flexible elements, and ask focused questions only for blocking gaps.

3. Plan the sheet blueprint.
   Start from the bundled master-sheet template when appropriate. Propose sections, panel count, layout hierarchy, draft text strategy, final text boxes, and output style. Get approval before image generation.

4. Prepare anchor assets when useful.
   Use existing clear reference images when they are enough. Generate or request a front full-body, face closeup, side/back view, or outfit detail anchor when consistency risk is high.

5. Generate the no-dense-body-copy draft sheet.
   Focus on character consistency, layout, sections, expressions, turnaround, detail panels, and whitespace. When using `template_locked`, layout fidelity outranks decorative polish. Allow structural labels, section numbers, and template headers; avoid dense body text.

6. Review the draft.
   Check template fidelity first when the bundled template was used, then identity consistency, missing panels, expression variety, text-space adequacy, outfit/detail fidelity, and whether regeneration or fallback composition is needed.

7. Write final sheet copy.
   Produce short, box-sized text: title, subtitle, profile, keywords, motifs, section labels, and any concise concept notes in the user's requested language.

8. Compose final text.
   Prefer SVG, HTML/CSS, Canvas, Pillow, Figma, or equivalent programmatic overlay so Korean and small labels stay readable.

9. Run final QA.
   Inspect text clipping, typos, section coverage, profile coverage, character consistency, and layout balance. Report pass/fail with concrete notes.

For template guidance, read `references/template-layout.md`. For stage-level procedures, read `references/stage-protocols.md`. For generation prompts and composition guidance, read `references/prompt-templates.md`. For persisted state and feedback routing, read `references/state-schema.md`.

## Feedback Routing

- `승인`: advance to the next stage.
- `수정: ...` or new character facts: return to spec normalization.
- `배치수정: ...`: return to blueprint planning.
- `재생성: ...` or art-quality feedback: rerun draft generation with accumulated fixes.
- Bundled-template geometry, headers, numbered sections, profile/lower panels, or footer boxes missing: return to blueprint or `template_locked` regeneration. If this already failed once, switch to panel asset generation plus programmatic composition.
- `부분수정: ...`: isolate the named panel or detail if the tool supports editing; otherwise rerun draft with a narrow correction.
- `문구수정: ...` or `톤변경: ...`: rerun copywriting and final composition only.
- Text clipping, typo, or broken Korean: rerun final composition or text repair only.

## Report Format

Use this compact gate report after each major stage:

```text
[단계 n/m] 단계명 완료

저장 폴더: ...

요약:
- ...
- ...

확인 요청:
1. 승인
2. 수정: ...
3. 재생성/재실행: ...
```

When running autonomously, replace the confirmation request with the next action and continue unless the next step would discard an approved image or require a major layout/spec decision.
