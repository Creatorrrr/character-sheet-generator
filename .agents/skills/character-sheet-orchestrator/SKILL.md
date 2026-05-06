---
name: character-sheet-orchestrator
description: Use when the user wants a full character sheet, master sheet, setting sheet, mascot sheet, anime character reference board, photoreal character reference board, or character design sheet from images and notes.
---

# Character Sheet Orchestrator

## Overview

Manage a two-phase character-sheet workflow. Gate character identity and layout decisions up front, then continue autonomously through image generation, text composition, self-review, repair, and final QA so the user only needs to review the completed deliverables.

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
- Pause for approval after the normalized character spec and the sheet blueprint. After both are approved, switch to `post_blueprint_autonomous` mode by default unless the user explicitly requests continued gating.
- In `post_blueprint_autonomous` mode, do not pause after anchors, draft image, draft review, final copy, final composition, or QA. Generate the textless image sheet and the text-included final sheet, self-review each stage, auto-regenerate or repair within the configured budget, then show the completed artifacts and QA notes at the end.
- Preserve the latest approved artifact as the source for the next stage.
- Use `assets/master-sheet-template.png` as the default master-sheet layout reference unless the user requests another layout. Default template usage is `template_locked`: preserve the template geometry, top header, project metadata box, numbered section headers, profile/lower panels, footer boxes, and blue technical wireframe rhythm; replace only mannequin bodies, face placeholders, plus icons, and empty placeholder drawings with character content.
- Use the built-in `image_gen` tool by default for raster character art generation: anchor images, panel art, no-dense-body-copy draft sheets, and visual regenerations. Use CLI/API image generation only when the user explicitly asks for that path or when a required capability is unavailable in built-in `image_gen` and the user approves the fallback.
- Prefer no-dense-body-copy image generation for the art draft, then programmatic text overlay for the final sheet. In draft images, preserve structural labels, section numbers, and large template headers when template fidelity matters; avoid dense profile copy and small body text. Use image-model text insertion only as a fallback.
- After each generated anchor or draft, inspect the result before using it or, in fully gated mode, showing it for approval. If the draft review recommends anything other than `approve`, regenerate with `image_gen` using only the approved spec/blueprint plus the concrete review issues. Auto-regenerate at most 2 times before reporting the best result and remaining blockers.
- If a bundled-template draft fails template fidelity once, do not keep repeating broad image prompts. Route to either a stricter `template_locked` regeneration or the fallback path: fixed template background, separately generated panel art, and programmatic composition.
- Report in Korean by default. Keep reports factual and do not claim readable text, identity consistency, or panel completeness unless the result was inspected.
- If a generated sheet has broken text but the character art is good, repair or recompose only text instead of regenerating the character.

## Workflow

1. Parse input.
   Extract source images, character name, visible traits, supplied lore, target language, sheet style, requested sections, and missing information.

2. Normalize the character spec.
   Lock identity-critical traits, structure appearance/personality/motifs/palette, define must-keep and flexible elements, and ask focused questions only for blocking gaps.

3. Plan the sheet blueprint.
   Start from the bundled master-sheet template when appropriate. Propose sections, panel count, layout hierarchy, draft text strategy, final text boxes, and output style. Get approval before image generation. After approval, set mode to `post_blueprint_autonomous` unless the user explicitly asks to keep approving every stage.

4. Prepare anchor assets when useful.
   Use existing clear reference images when they are enough. Generate front full-body, face closeup, side/back view, or outfit detail anchors with built-in `image_gen` when consistency risk is high.

5. Generate the no-dense-body-copy draft sheet.
   Use built-in `image_gen` and focus on character consistency, layout, sections, expressions, turnaround, detail panels, and whitespace. When using `template_locked`, layout fidelity outranks decorative polish. Allow structural labels, section numbers, and template headers; avoid dense body text.

6. Review the draft.
   Check template fidelity first when the bundled template was used, then identity consistency, missing panels, expression variety, text-space adequacy, outfit/detail fidelity, no-dense-body-copy compliance, watermark/random text, and whether regeneration or fallback composition is needed. Regenerate automatically with `image_gen` up to 2 times before asking for approval on a failed draft.

7. Write final sheet copy.
   Produce short, box-sized text: title, subtitle, profile, keywords, motifs, section labels, and any concise concept notes in the user's requested language.

8. Compose final text.
   Prefer SVG, HTML/CSS, Canvas, Pillow, Figma, or equivalent programmatic overlay so Korean and small labels stay readable.

9. Run final QA.
   Inspect text clipping, typos, section coverage, profile coverage, character consistency, and layout balance. Report pass/fail with concrete notes.

For template guidance, read `references/template-layout.md`. For stage-level procedures, read `references/stage-protocols.md`. For generation prompts and composition guidance, read `references/prompt-templates.md`. For persisted state and feedback routing, read `references/state-schema.md`.

## Autonomy After Blueprint Approval

Default behavior after the user approves the character spec and blueprint:

- Continue through anchor selection/generation, no-dense-body-copy draft generation, draft review, final copywriting, final text composition, and QA without asking for more feedback.
- Run the existing self-review checks at each stage. If a check fails, route the failure internally: regenerate visual drafts for art/layout issues, switch to fallback composition for repeated template-fidelity failures, and repair/recompose only text for clipping, typo, or Korean-readability issues.
- Keep the latest self-reviewed passing artifact as the source for the next stage. Do not discard a user-approved spec or blueprint during regeneration.
- Stop early only when the next step would require a major new identity/layout decision, overwrite an explicitly approved image, exceed the configured regeneration budget with unresolved blockers, or use an unapproved CLI/API fallback.
- At the end, show both the textless draft sheet and the final text-included sheet, plus concise QA notes and known remaining issues. The user's next message is treated as final-stage feedback and routed by the normal feedback prefixes.

## Feedback Routing

- `승인`: advance to the next stage.
- `수정: ...` or new character facts: return to spec normalization.
- `배치수정: ...`: return to blueprint planning.
- `재생성: ...` or art-quality feedback: rerun draft generation with accumulated fixes.
- Bundled-template geometry, headers, numbered sections, profile/lower panels, or footer boxes missing: return to blueprint or `template_locked` regeneration. If this already failed once, switch to panel asset generation plus programmatic composition.
- `부분수정: ...`: isolate the named panel or detail if the tool supports editing; otherwise rerun draft with a narrow correction.
- `문구수정: ...` or `톤변경: ...`: rerun copywriting and final composition only.
- Text clipping, typo, or broken Korean: rerun final composition or text repair only.
- In `post_blueprint_autonomous` mode, collect user feedback only after the final QA report unless an early-stop condition is reached.

## Report Format

Use this compact gate report for the spec and blueprint gates, or when the user explicitly requests fully gated operation:

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

When running `post_blueprint_autonomous`, do not emit approval choices for intermediate stages. Continue internally and finish with a final report that includes the textless draft path, final text-included sheet path, QA result, any self-repairs/regenerations performed, and remaining known issues.
