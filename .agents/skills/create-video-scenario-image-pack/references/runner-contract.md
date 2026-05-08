# Video Scenario Image Pack Runner Contract

## Plan JSON

Use `write-plan-template` for a starter file:

```bash
python3 scripts/video_scenario_image_pack_runner.py write-plan-template --run-dir <run-dir>
```

Approved plans use this shape:

```json
{
  "scenario_title": "Noeul Court",
  "items": [
    {
      "id": "001-sunset-street-court-master",
      "filename": "001-sunset-street-court-master.png",
      "scene_refs": ["S01"],
      "category": "location_master",
      "contains_character": false,
      "purpose": "Reusable establishing source.",
      "visual_brief": "Empty sunset court with fixed landmarks.",
      "spatial_group": "basketball-court-sunset",
      "continuity_anchor": "",
      "fixed_layout_notes": "Hoop far/right; gate and bench camera-left; blank masonry wall behind hoop.",
      "camera_view": "wide establishing view",
      "must_match": ["no people, cars, silhouettes, or readable text"],
      "prompt": "Photoreal cinematic production reference of an empty sunset basketball court...",
      "negative_prompt": "",
      "dependencies": [],
      "notes": ""
    }
  ]
}
```

The runner normalizes `continuity_anchor` into `dependencies`, validates dependency ids, and stores prompt, worker, parent, rerun, and artifact metadata in `state.json`.

## Batch Commands

Reserve work:

```bash
python3 scripts/video_scenario_image_pack_runner.py next-batch --run-dir <run-dir> --limit 4
python3 scripts/video_scenario_image_pack_runner.py batch-prompts --run-dir <run-dir> --batch-id <batch-id>
```

Each reserved item writes:

- `prompts/<item>.prompt.txt`
- `subagent_prompts/<item>.subagent.txt`

Use the subagent prompt as the spawn task text. Do not ask subagents to edit `state.json`.

If spawning with `fork_context=true`, omit subagent role fields such as `agent_type` or `role`. Do not pass `worker`, `default`, or `explorer` as a role/type field. Treat `worker_status` and `worker_note` only as import-result labels, and describe generation plus first-pass inspection behavior in the prompt text.

## Import Manifest

Use one manifest to avoid parallel `state.json` writes:

```json
{
  "run_dir": "/absolute/run/dir",
  "items": [
    {
      "item": "002-hoop-detail.png",
      "generated": "/absolute/generated.png",
      "worker_status": "pass",
      "worker_note": "Worker inspection passed."
    }
  ]
}
```

Run:

```bash
python3 scripts/video_scenario_image_pack_runner.py import-batch --manifest <manifest.json>
```

## Parent Inspection Manifest

```json
{
  "run_dir": "/absolute/run/dir",
  "items": [
    {
      "item": "002-hoop-detail.png",
      "note": "Parent inspected pass: no people, text, or layout drift."
    }
  ]
}
```

Run:

```bash
python3 scripts/video_scenario_image_pack_runner.py inspect-batch-pass --manifest <manifest.json>
```

Use `rerun` instead of passing if any strict no-character or spatial-continuity rule fails.

## Strict Negative Prompt

For non-character outputs, the runner adds:

```text
people, person, pedestrian, player, performer, character, body, hands, face, silhouette, crowd, cars, vehicles, bicycles, scooters, posters, signs, window figures, reflections, human-shaped marks, tiny vertical marks shaped like people, background street activity, low resolution, watermark, random logo, caption text, storyboard panel labels, unreadable text, accidental subtitles, distorted anatomy, extra fingers, duplicated limbs, broken reflections, over-smoothed AI texture, waxy skin, plastic objects, inconsistent location layout, moved landmarks, swapped building positions, wrong hoop side, wrong entrance side, wrong time of day, wrong weather, unrelated props, cropped key subject
```

## Rerun Hints

`rerun --note` appends the note to `rerun_prompt_hints`. The next reservation injects those hints into the prompt file. Make rerun notes concrete, for example:

- `tiny background silhouette near right fence`
- `visible parked car beyond fence`
- `frame tighter inside court`
- `use blank masonry wall and no street activity`
