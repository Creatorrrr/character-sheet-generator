# State Schema

Use this schema in conversation. Persist it beside generated assets only when the user asks for resumable work, when the pack spans multiple turns, or when the output needs handoff.

## State

```json
{
  "workflow_id": "closeup_pack_001",
  "source_character_sheet": "",
  "source_orchestrator_state": "",
  "style_mode": "preserve_source_style",
  "pack_preset": "core",
  "character_spec": {},
  "identity_lock": {
    "must_keep": [],
    "flexible": []
  },
  "identity_anchor": {
    "path_or_id": "",
    "approved": false,
    "notes": ""
  },
  "requested_outputs": [],
  "batch_plan": [],
  "generated_assets": {},
  "review_results": {},
  "approval_state": {
    "identity_anchor_approved": false,
    "batch_plan_approved": false,
    "final_pack_approved": false
  }
}
```

## Style Modes

- `preserve_source_style`: default. Preserve the approved character sheet's exact visual style.
- `photoreal_conversion`: use only when the user explicitly asks to convert to photoreal outputs.
- `custom_style_override`: use only when the user explicitly gives a new target style.

## Batch Plan Item

```json
{
  "output": "01_face_front.png",
  "purpose": "primary face identity anchor",
  "request_group": "identity_anchor",
  "dependencies": [],
  "prompt_template": "01 Face Front",
  "status": "planned | requested | generated | approved | needs_rerun",
  "notes": ""
}
```

## Review Result Item

```json
{
  "output": "",
  "passed": [],
  "issues": [],
  "recommended_action": "approve | partial_rerun | rerun | return_to_source_sheet",
  "notes": ""
}
```

## Approval Invariants

- Do not mark `identity_anchor_approved` true until the user approves the anchor or autonomous continuation is explicit.
- Do not mark `batch_plan_approved` true until outputs, preset, and dependencies are accepted or autonomous continuation is explicit.
- Do not mark `final_pack_approved` true until all requested outputs pass review or the user accepts known issues.
- If style drift appears in generated outputs, return to the same output prompt with stronger source-style preservation instead of changing the source character sheet.
