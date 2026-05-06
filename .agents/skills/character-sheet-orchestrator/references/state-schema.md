# State Schema

Use this schema in conversation. Persist it to a JSON file only when the user asks for restartable work, when the workflow spans multiple turns, or when artifacts need reproducible handoff.

## State

```json
{
  "workflow_id": "character_sheet_001",
  "current_stage": "input_parser",
  "mode": "gated | autonomous",
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
  "template": {
    "asset": "assets/master-sheet-template.png",
    "usage": "default | adapted | custom | none",
    "kept_sections": [],
    "modified_sections": [],
    "omitted_sections": []
  },
  "anchor_assets": {},
  "draft_sheet": {
    "path_or_id": "",
    "generation_notes": ""
  },
  "draft_review": {},
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
- `qa`
- `complete`

## Feedback Routing

```text
approval only -> advance current_stage
new identity/spec facts -> spec_normalizer
section or layout feedback -> blueprint_planner
need more stable references -> anchor_generator
art quality, expression, view, outfit, palette issues -> draft_generator
panel-specific visual issue -> draft_generator with partial-edit request when possible
copy wording, tone, language, keyword changes -> copywriter
broken text, clipping, typo, Korean readability -> final_composer
final minor visual artifact -> final_composer or partial edit
major identity drift in final -> return to draft_generator using approved anchors
```

## Approval Invariants

- Do not mark `spec_approved` true until the user approves the normalized character spec or explicitly asks to continue autonomously.
- Do not mark `blueprint_approved` true until sections and rough layout are accepted.
- Do not mark `draft_approved` true when the reviewer recommends regeneration unless the user chooses to proceed anyway.
- Do not mark `text_approved` true until the copy payload is accepted or autonomous mode is active.
- Do not mark `final_approved` true until QA passes or the user accepts known issues.
