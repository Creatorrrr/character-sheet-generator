---
name: create-comic-storyboard-pack
description: "Turn a story outline, plot, scenario, script, scene notes, or storyboard request into an approved comic storyboard panel plan, then coordinate Codex image_gen creation through three verified stages: storyboard thumbnails, sketch/ink line art, and tone/color/final finish. Use when the user wants manga, webtoon, comic, or visual-novel style panels generated from a story or scenario with an approval gate, four-subagent parallel batches, worker inspection, and parent inspection."
---

# Create Comic Storyboard Pack

## Overview

Convert a story outline, plot, or scenario into a resumable comic storyboard pack. First extract and report the panel plan in Korean for user approval. After approval, generate the panels in three ordered image stages: `storyboard`, `sketch_ink`, then `finish`.

Use Codex built-in `image_gen`; do not call external image APIs. Do not generate any image before the user approves the exact panel plan.

## Default Output Location

If the user does not specify where to save files, create a new run folder under `/Users/chasoik/Projects/character-sheet-generator/output/`.

- Use `output/<slug>-comic-storyboard-pack-YYYYMMDD-HHMMSS/`.
- Build `<slug>` from the scenario title, scenario filename stem, or concise scenario name. Normalize it to lowercase ASCII letters, numbers, and hyphens. If empty, use `comic-storyboard-pack`.
- If the user is resuming from an existing run folder, keep using that folder.
- Save `scenario.md`, `state.json`, `approved_storyboard_plan.json`, `batch_plan.md`, prompt files, generated stage images, worker notes, and parent inspection notes under the selected run folder.

## Inputs

Accept any of these:

- A pasted story outline, plot summary, scenario, script, scene notes, or storyboard request.
- A screenplay, shot list, or scene brief when the source happens to be written in that format.
- A story or scenario file path.
- Existing character, location, style, or panel-layout references.
- A resumed run folder from this skill.

Ask for missing inputs only when the story outline or scenario cannot define story beats or when a visual dependency would be risky to infer.

## Panel Extraction Rules

Extract comic panels that serve the story outline or scenario, not every moment or minor beat.

- Merge repeated beats when one panel can clearly cover the action.
- Split panels when the reader needs a new beat, reaction, reveal, action change, location change, time shift, or important insert.
- Preserve scene references such as `S01`, `S02-S04`, or the user's own scene names.
- Include composition/viewpoint notes: wide, closeup, over-shoulder, low angle, top view, insert, reaction, or establishing.
- Include character blocking, action, setting, props, mood, continuity notes, dialogue, SFX, and narration as metadata.
- Keep panel images text-free by default. Dialogue, SFX, captions, and panel numbers stay in the plan and prompt notes unless the user explicitly approves visible text inside images.
- Use concise stable filenames with a numeric prefix.

## Approval Gate

Before generation, present the proposed panel list in Korean and wait for explicit approval.

Use this approval format:

```text
[만화 콘티 생성 승인 요청]
- 줄거리/시나리오: ...
- 저장 폴더: ...
- 총 패널 수: ...
- 구성 기준: ...

| id | 파일명 | 장면 | 패널 목적 | 구도/카메라 | 등장 요소 | 대사/SFX 메모 |
| ... |

텍스트 정책:
- 기본값: 이미지 내부 말풍선/자막/패널 번호/효과음 글자 미포함
- 대사/SFX/캡션: 승인 계획과 배치 노트에만 기록
- 이미지 내부 텍스트 포함 항목: 명시 승인된 항목만

승인 후 진행 방식:
- 1단계: 콘티 storyboard
- 2단계: 스케치/펜선 sketch_ink
- 3단계: 톤/채색/마무리 finish
- 각 단계 최대 4개씩 서브에이전트 병렬 생성
- 각 서브에이전트 1차 검수
- 부모 세션 최종 검수
- 실패 항목 rerun 후 다음 배치 진행
```

Do not call `approve-plan` or `next-batch` until the user approves this list. If the user edits the list, update the plan first and ask approval again when the change affects generated outputs.

## Plan JSON

After approval, write an approved plan and import it with the runner:

```json
{
  "scenario_title": "short title",
  "style_brief": "comic style, tone, palette, rendering direction",
  "reading_order": "left-to-right",
  "panels": [
    {
      "id": "001-arrival-wide",
      "filename": "001-arrival-wide.png",
      "panel_no": 1,
      "scene_refs": ["S01"],
      "beat": "The protagonist arrives at the empty gym.",
      "visual_brief": "Wide establishing panel of a quiet indoor court at dusk.",
      "setting": "Indoor basketball court",
      "characters": ["protagonist"],
      "action": "Standing near the entrance, looking toward the hoop.",
      "camera": "wide establishing view from behind the entrance",
      "composition": "door frame in foreground, hoop in distance, protagonist small in frame",
      "mood": "quiet, anticipatory",
      "dialogue": [],
      "sfx": [],
      "narration": ["After practice, the court was finally silent."],
      "continuity_notes": "Hoop remains on the far wall; entrance remains foreground-left.",
      "references": [],
      "prompt": "A cinematic comic storyboard panel...",
      "negative_prompt": "watermark, caption text, speech bubble text...",
      "dependencies": [],
      "notes": "Keep image text-free."
    }
  ]
}
```

Write image prompts in English unless the story outline or scenario explicitly requires visible text. Keep Korean dialogue and captions in metadata, not the generated image, unless visible text was explicitly approved.

## Resumable Runner Contract

Use `scripts/comic_storyboard_runner.py`. The runner keeps state because `image_gen` may end a turn and because subagent results must be mapped back to exact panel and stage outputs.

Initialize or resume:

```bash
python3 scripts/comic_storyboard_runner.py init --title "<story/scenario title>" --scenario <story-or-scenario-file>
python3 scripts/comic_storyboard_runner.py status --run-dir <run-dir>
```

Approve the user-approved plan:

```bash
python3 scripts/comic_storyboard_runner.py approve-plan --run-dir <run-dir> --plan-file <approved-plan.json>
```

Reserve the next batch:

```bash
python3 scripts/comic_storyboard_runner.py next-batch --run-dir <run-dir> --limit 4
```

Import each worker result:

```bash
python3 scripts/comic_storyboard_runner.py import --run-dir <run-dir> --item <filename-or-id> --stage storyboard --generated <generated-path> --worker-status pass --worker-note "<subagent note>"
```

Parent inspection:

```bash
python3 scripts/comic_storyboard_runner.py inspect-pass --run-dir <run-dir> --item <filename-or-id> --stage storyboard --note "<parent inspection note>"
python3 scripts/comic_storyboard_runner.py rerun --run-dir <run-dir> --item <filename-or-id> --stage storyboard --note "<reason>"
python3 scripts/comic_storyboard_runner.py batch-status --run-dir <run-dir> --batch-id <batch-id>
```

Use the same commands with `--stage sketch_ink` and `--stage finish` as the workflow advances.

State rules:

- `approve-plan` is the only transition from approval-gated planning into generation-ready state.
- Stages must run in order: `storyboard`, then `sketch_ink`, then `finish`.
- `next-batch --limit 4` reserves at most four eligible panels from the current stage and writes one prompt file per panel under `prompts/<stage>/`.
- Do not reserve a new batch while any panel stage is still `generation_requested` or `imported`.
- A later stage is eligible only after every panel in the previous stage is parent-inspected as `inspected_pass` or marked `complete`.
- Panel dependencies, when present, must pass in the current stage before the dependent panel can be reserved.
- Subagent inspection is advisory. Store it through `import`, but only the parent session may run `inspect-pass`.
- If a generated image fails parent inspection, run `rerun`; the rerun is prioritized before new pending panels in that same stage.
- Treat the pack as complete only when every panel is `inspected_pass` or `complete` in all three stages.

## Three Stage Rules

1. `storyboard`
   Generate rough but readable comic thumbnails focused on beat clarity, shot composition, camera angle, panel framing, and action blocking.

2. `sketch_ink`
   Use the parent-inspected storyboard image as the structure reference. Generate clean sketch and ink line art while preserving composition, camera, blocking, props, and continuity.

3. `finish`
   Use the parent-inspected sketch/ink image as the structure reference. Add tone, color, lighting, shadows, material treatment, and final cleanup without changing the beat or composition.

## Parallel Generation Rules

After approval, all image generation must happen through subagents:

- Use one `fork_context=true` subagent per batch item.
- Use a maximum of four subagents per batch.
- Each subagent generates exactly one assigned panel stage.
- Do not use serial parent-session `image_gen` as a fallback.
- If subagents are unavailable, stop and report that generation is blocked by missing subagent support.
- Do not start the next four images until the parent has inspected every imported image from the current batch and routed failures to `rerun` or passes to `inspect-pass`.

## Subagent Batch Contract

When spawning subagents for `next-batch`, pass explicit task context:

```text
You are generating exactly one image for create-comic-storyboard-pack.
Do not edit state.json.
Run folder: <run-dir>
Story/scenario file: <run-dir>/scenario.md
Approved plan: <run-dir>/approved_storyboard_plan.json
Assigned panel: <filename-or-id>
Stage: <storyboard|sketch_ink|finish>
Prompt file: <prompt-file>
Batch id: <batch-id>
Prior-stage reference: <path or none>
Relevant references: <paths or "none">
Image text policy: no speech bubbles, subtitles, panel numbers, captions, labels, or random typography unless explicitly approved.

Use image_gen with the assigned prompt and visual references. After generation, inspect the output for stage fit, panel/story fit, composition continuity, text policy, technical quality, and obvious defects. Return only:
- generated file path
- worker_status: pass or needs_rerun
- worker_note: concise inspection note
```

The parent session imports the result, visually inspects it, and decides `inspect-pass` or `rerun`.

## Parent Verification

Inspect every imported image before marking it passed. Check:

- The image matches the approved panel, not a nearby scene or invented beat.
- The image matches the current stage: rough storyboard, sketch/ink, or finished tone/color.
- Composition, camera, character blocking, props, setting, and continuity match the plan.
- `sketch_ink` preserves the inspected storyboard structure.
- `finish` preserves the inspected sketch/ink structure.
- Dialogue, SFX, captions, panel numbers, labels, watermarks, and random typography are absent unless explicitly approved.
- Characters, hands, faces, props, perspective, and key action do not contain obvious defects.
- The generated output is mapped to the correct panel filename and stage.

Do not claim story coverage, continuity, text policy, or stage quality unless the image was inspected.

## Reporting

After each batch, report in Korean:

```text
[만화 콘티 팩 진행 결과]
- 줄거리/시나리오: ...
- 저장 폴더: ...
- 상태 파일: ...
- 현재 단계: storyboard | sketch_ink | finish
- 승인된 패널 수: ...
- 이번 병렬 그룹: ...
- worker 검수 결과: ...
- 부모 검수 결과: ...
- rerun 필요 항목: ...
- 다음 결정: ...
```

Keep reporting factual. If any item is still `generation_requested` or `imported`, say it is not parent-inspected yet.
