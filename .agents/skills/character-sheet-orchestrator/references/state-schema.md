# State Schema

Use this schema in conversation. Persist it to a JSON file only when the user asks for restartable work, when the workflow spans multiple turns, or when artifacts need reproducible handoff.

## State

```json
{
  "workflow_id": "character_sheet_001",
  "current_stage": "input_parser",
  "mode": "gated | post_blueprint_autonomous | autonomous",
  "source_inputs": {
    "source_images": [],
    "user_notes": "",
    "primary_reference": "",
    "output_language": "ko"
  },
  "parsed_input": {},
  "identity_lock": {
    "must_keep": [],
    "flexible": []
  },
  "character_spec": {},
  "blueprint": {},
  "generation_mode": "template_locked | adapted | custom",
  "generation_tool": "built-in image_gen | user_requested_cli_api",
  "attempt_index": 0,
  "max_auto_regenerations": 2,
  "regeneration_reason": "",
  "template": {
    "asset": "assets/master-sheet-template.png",
    "usage": "default | template_locked | adapted | custom | none",
    "kept_sections": [],
    "modified_sections": [],
    "omitted_sections": []
  },
  "prompt": {
    "path_or_id": "",
    "template": "template_locked | adapted | regeneration | final_composition",
    "notes": ""
  },
  "anchor_assets": {},
  "draft_sheet": {
    "path_or_id": "",
    "generation_tool": "built-in image_gen",
    "attempt_index": 0,
    "generation_notes": ""
  },
  "draft_review": {
    "template_fidelity": "pass | fail | not_applicable",
    "recommended_action": "approve | partial_edit | regenerate | return_to_blueprint | fallback_composition",
    "passed": [],
    "issues": [],
    "regeneration_reason": ""
  },
  "review_history": [],
  "draft_feedback_history": [],
  "final_text_payload": {},
  "final_sheet": {
    "path_or_id": "",
    "composition_method": ""
  },
  "qa_report": {},
  "approvals": {
    "spec_approved": false,
    "blueprint_approved": false,
    "anchors_approved": false,
    "draft_approved": false,
    "text_approved": false,
    "final_approved": false
  }
}
```

## Current Stage Values

- `input_parser`
- `spec_normalizer`
- `blueprint_planner`
- `anchor_generator`
- `draft_generator`
- `draft_review`
- `copywriter`
- `final_composer`
- `fallback_composition`
- `qa`
- `complete`

## Feedback Routing

```text
approval only -> advance current_stage
new identity/spec facts -> spec_normalizer
section or layout feedback -> blueprint_planner
need more stable references -> anchor_generator
art quality, expression, view, outfit, palette issues -> draft_generator
template geometry, top header, numbered sections, profile/lower panels, or footer boxes missing -> draft_generator with template_locked prompt through built-in image_gen
same template fidelity failure already recorded -> fallback_composition with fixed template background and image_gen panel art
panel-specific visual issue -> draft_generator with partial-edit request when possible
copy wording, tone, language, keyword changes -> copywriter
broken text, clipping, typo, Korean readability -> final_composer with built-in image_gen text repair
final minor visual artifact -> final_composer or partial edit
major identity drift in final -> return to draft_generator using approved anchors
```

## Generation and Review Invariants

- Default `generation_tool` for anchor assets, panel art, draft sheets, final text-included sheets, text repair, and visual regenerations is `built-in image_gen`.
- Use CLI/API image generation only when the user explicitly asks for it or approves that fallback.
- After both `approvals.spec_approved` and `approvals.blueprint_approved` are true, set `mode` to `post_blueprint_autonomous` by default unless the user explicitly requests fully gated operation.
- In `post_blueprint_autonomous`, do not pause for anchor, draft, text, composition, or QA approvals. Continue through final delivery using self-review, regeneration, fallback composition, and `image_gen` text repair rules.
- Treat `attempt_index` as zero-based: `0` is the first draft, `1` and `2` are the two allowed automatic regenerations. Keep `max_auto_regenerations` at `2` unless the user explicitly changes it.
- Append every failed draft review to `review_history` before regenerating.
- Set `regeneration_reason` to the concrete failed-review issues. Do not use regeneration to change the approved spec, identity lock, blueprint, or panel plan.
- If `attempt_index` reaches `max_auto_regenerations` and review still does not recommend `approve`, stop automatic regeneration and report the best draft plus remaining blockers.
- If only text is broken or clipped, route to `image_gen` final composition/text repair instead of regenerating character art. Do not use programmatic text overlay.
- Stop early in `post_blueprint_autonomous` only for major identity/layout decisions, unapproved CLI/API fallback, configured regeneration budget exhaustion with unresolved blockers, or actions that would discard a user-approved artifact.

## Approval Invariants

- Do not mark `spec_approved` true until the user approves the normalized character spec or explicitly asks to continue autonomously.
- Do not mark `blueprint_approved` true until sections and rough layout are accepted.
- Do not mark `draft_approved` true until self-review recommends `approve` or the user explicitly chooses to proceed with known issues.
- Do not mark `draft_approved` true when the reviewer recommends regeneration unless the user chooses to proceed anyway.
- Do not mark `draft_approved` true when `generation_mode` is `template_locked` and `draft_review.template_fidelity` is `fail`, even if character identity looks good.
- In `post_blueprint_autonomous`, self-reviewed draft approval may advance to copywriting without user approval.
- Do not mark `text_approved` true until the copy payload is accepted or `post_blueprint_autonomous` / `autonomous` mode is active.
- Do not mark `final_approved` true until QA passes or the user accepts known issues.
