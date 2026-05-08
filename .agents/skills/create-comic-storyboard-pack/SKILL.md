---
name: create-comic-storyboard-pack
description: "Turn a story outline, plot, scenario, script, scene notes, or storyboard request into approved Korean comic-book pages, then coordinate Codex image_gen creation through two verified stages: combined page storyboard/sketch/ink and tone/color/final finish. Use when the user wants manga, Korean comic, webtoon-page, comic-book, or visual-novel style pages generated from a story or scenario with multi-panel page layouts, adapted dialogue, sound effects, approval gate, four-subagent parallel batches, worker inspection, and parent inspection."
---

# Create Comic Storyboard Pack

## Overview

Convert a story outline, plot, or scenario into a resumable Korean comic-book page pack. First extract and report a page plan in Korean for user approval. After approval, generate complete pages in two ordered image stages: `storyboard_sketch_ink`, then `finish`.

Use Codex built-in `image_gen`; do not call external image APIs. Do not generate any image before the user approves the exact page plan.

## Default Output Location

If the user does not specify where to save files, create a new run folder under `/Users/chasoik/Projects/character-sheet-generator/output/`.

- Use `output/<slug>-comic-storyboard-pack-YYYYMMDD-HHMMSS/`.
- Build `<slug>` from the scenario title, scenario filename stem, or concise scenario name. Normalize it to lowercase ASCII letters, numbers, and hyphens. If empty, use `comic-storyboard-pack`.
- If the user is resuming from an existing run folder, keep using that folder.
- Save `scenario.md`, `state.json`, `approved_storyboard_plan.json`, `batch_plan.md`, prompt files, generated stage images, worker notes, and parent inspection notes under the selected run folder.

## Default Source Data Location

If the user does not specify source or reference paths, use `/Users/chasoik/Projects/character-sheet-generator/sources/` as the default folder for source data.

- Search only for relevant story, character, location, style, object, and page-layout source files needed for the current request.
- Do not use `/Users/chasoik/Projects/character-sheet-generator/output/` or any `output/` subtree as source/reference data. It may contain unrelated generated files, rejected attempts, or failed cases from other runs.
- Current-run generated images under the selected run folder may be used only as prior-stage workflow structure references after parent inspection, not as general source data.
- Record user-provided or `sources/` reference paths in the approved plan. The runner rejects `references` or `reference_paths` that point under `output/`.

## Inputs

Accept any of these:

- A pasted story outline, plot summary, scenario, script, scene notes, or storyboard request.
- A screenplay, shot list, or scene brief when the source happens to be written in that format.
- A story or scenario file path.
- Existing character, location, style, or page-layout references.
- If no reference path is specified, relevant files from `/Users/chasoik/Projects/character-sheet-generator/sources/`.
- A resumed run folder from this skill.

Ask for missing inputs only when the story outline or scenario cannot define page beats or when a visual dependency would be risky to infer.

## Page Planning Rules

Extract comic-book pages that serve the story outline or scenario, not every moment or minor beat.

- Default output is one complete page image containing multiple panels, gutters, varied panel sizes, speech balloons, SFX lettering, and short captions when useful.
- Follow a general Korean comic-book page composition: multiple panels per page, clear reading flow, cinematic framing, readable balloon placement, and balanced black/white or tone/color finish.
- Merge repeated beats when one page or panel can clearly cover the action.
- Split pages when the reader needs a new location, time shift, major action sequence, emotional turn, reveal, or scene boundary.
- Split panels within a page when the reader needs a new beat, reaction, reveal, action change, object insert, or timing pause.
- Preserve scene references such as `S01`, `S02-S04`, or the user's own scene names.
- Include page-level layout notes and panel-level composition/viewpoint notes: wide, closeup, over-shoulder, low angle, top view, insert, reaction, or establishing.
- Include character blocking, action, setting, props, mood, continuity notes, source dialogue, adapted dialogue, SFX, captions, spatial logic, and motion checks as metadata.
- Use concise stable page filenames with a numeric prefix.

## Dialogue and Text Rules

Comic text is part of the generated page by default.

- Do not copy provided source dialogue verbatim by default.
- Rewrite dialogue to fit comic timing, panel rhythm, emotion, balloon space, and page mood.
- Record the original line as `source_dialogue` and the used comic line as `adapted_dialogue`.
- Include approved `adapted_dialogue`, SFX, and short captions inside the generated page image.
- Keep lettering short, legible, and placed where it does not cover faces, hands, props, or key action.
- If the user explicitly asks for exact dialogue preservation, mark that in `page_dialogue_notes` and keep the quoted line unchanged.

## Spatial and Motion Logic

Plan and inspect the page for physically plausible layout and movement.

- Characters, props, objects, vehicles, balls, weapons, doors, furniture, landmarks, and camera direction must keep plausible positions across panels.
- Movement must follow cause and effect: a basketball shot must send the ball toward the hoop, not behind the shooter; a thrown object must follow the arm direction; a collision must show believable contact and reaction.
- Use `spatial_logic_notes`, `motion_checks`, and `must_match` to capture critical constraints before generation.
- Parent inspection must reject pages where object trajectories, character positions, or spatial relationships contradict the approved action.

## Approval Gate

Before generation, present the proposed page list in Korean and wait for explicit approval.

Use this approval format:

```text
[만화 페이지 생성 승인 요청]
- 줄거리/시나리오: ...
- 저장 폴더: ...
- 기본 참고 폴더: /Users/chasoik/Projects/character-sheet-generator/sources/
- 참고 제외 폴더: /Users/chasoik/Projects/character-sheet-generator/output/
- 총 페이지 수: ...
- 페이지당 컷 구성 기준: ...

| id | 파일명 | 장면 | 페이지 구성 | 컷 수 | 주요 대사/SFX 각색 | 공간/동선 검수 포인트 |
| ... |

텍스트 정책:
- 기본값: 승인된 말풍선 대사/효과음/짧은 캡션을 이미지 내부에 포함
- 원문 대사: 보존 자료로 기록
- 사용 대사: 만화 타이밍과 분위기에 맞게 각색하여 기록

승인 후 진행 방식:
- 1단계: 콘티/스케치/펜선 storyboard_sketch_ink
- 2단계: 톤/채색/마무리 finish
- 각 단계 최대 4페이지씩 서브에이전트 병렬 생성
- 각 서브에이전트 1차 검수
- 부모 세션 최종 검수
- 모든 페이지의 1단계 부모 검수 통과 전에는 2단계를 시작하지 않음
- 2단계는 1단계 생성 이미지를 필수 입력/구조 참조로 사용
- 실패 페이지 rerun 후 다음 배치 진행
```

Do not call `approve-plan` or `next-batch` until the user approves this list. If the user edits the list, update the plan first and ask approval again when the change affects generated pages or page text.

## Plan JSON

After approval, write an approved plan and import it with the runner:

```json
{
  "scenario_title": "short title",
  "style_brief": "Korean comic-book style, tone, palette, rendering direction",
  "reading_order": "right-to-left or top-to-bottom as approved",
  "pages": [
    {
      "id": "001-gym-arrival",
      "filename": "001-gym-arrival.png",
      "page_no": 1,
      "scene_refs": ["S01"],
      "layout_brief": "Four-panel page: wide establishing panel, two medium action panels, one close reaction panel.",
      "reading_order": "top-to-bottom, left-to-right within each row",
      "page_dialogue_notes": "Rewrite dialogue to sound tense and concise; do not copy source lines verbatim.",
      "spatial_logic_notes": "Hoop remains on the far wall; protagonist enters from foreground-left; basketball moves toward the hoop when shot.",
      "motion_checks": [
        "ball trajectory follows hand release toward the hoop",
        "character gaze and body direction point toward the action target"
      ],
      "must_match": [
        "four panels on one page",
        "speech balloons and SFX remain readable",
        "no impossible ball direction"
      ],
      "panels": [
        {
          "panel_no": 1,
          "beat": "The protagonist enters the empty gym.",
          "visual_brief": "Wide establishing panel of a quiet indoor court at dusk.",
          "setting": "Indoor basketball court",
          "characters": ["protagonist"],
          "action": "Standing near the entrance, looking toward the hoop.",
          "composition": "door frame foreground, hoop in distance, protagonist small in frame",
          "source_dialogue": ["It's quiet in here."],
          "adapted_dialogue": ["...조용하네."],
          "sfx": ["끼익"],
          "caption": ["방과 후, 체육관."],
          "speech_balloon": "small balloon near protagonist, not covering face",
          "sfx_placement": "near opening door",
          "spatial_logic_notes": "door stays foreground-left; hoop stays far wall"
        }
      ],
      "references": [],
      "prompt": "A Korean comic-book page...",
      "negative_prompt": "watermark, random logo, garbled lettering...",
      "dependencies": [],
      "notes": "Generate as one page image."
    }
  ]
}
```

Legacy flat `panels` plans are accepted only for compatibility. The runner converts each panel into a single-panel page, but new plans should use `pages[].panels[]`.

`references` and top-level `reference_paths` must point to user-provided files or relevant files under `sources/`. Do not put files from `output/` in the approved plan.

## Resumable Runner Contract

Use `[스킬 경로]/scripts/comic_storyboard_runner.py`. `[스킬 경로]` means the directory that contains this `SKILL.md`, not the checkout root. The runner keeps state because `image_gen` may end a turn and because subagent results must be mapped back to exact page and stage outputs.

Set the skill directory before running examples:

```bash
SKILL_DIR=".agents/skills/create-comic-storyboard-pack"
RUNNER="$SKILL_DIR/scripts/comic_storyboard_runner.py"
```

Initialize or resume:

```bash
python3 "$RUNNER" init --title "<story/scenario title>" --scenario <story-or-scenario-file>
python3 "$RUNNER" status --run-dir <run-dir>
```

Approve the user-approved page plan:

```bash
python3 "$RUNNER" approve-plan --run-dir <run-dir> --plan-file <approved-plan.json>
```

Reserve the next batch:

```bash
python3 "$RUNNER" next-batch --run-dir <run-dir> --limit 4
```

Import each worker result:

```bash
python3 "$RUNNER" import --run-dir <run-dir> --item <page-filename-or-id> --stage storyboard_sketch_ink --generated <generated-path> --worker-status pass --worker-note "<subagent note>"
```

Parent inspection:

```bash
python3 "$RUNNER" inspect-pass --run-dir <run-dir> --item <page-filename-or-id> --stage storyboard_sketch_ink --note "<parent inspection note>"
python3 "$RUNNER" rerun --run-dir <run-dir> --item <page-filename-or-id> --stage storyboard_sketch_ink --note "<reason>"
python3 "$RUNNER" batch-status --run-dir <run-dir> --batch-id <batch-id>
```

Use the same commands with `--stage finish` after every `storyboard_sketch_ink` page passes parent inspection.

State rules:

- `approve-plan` is the only transition from approval-gated planning into generation-ready state.
- `approve-plan` rejects `references` and `reference_paths` under `output/`.
- Stages must run in order: `storyboard_sketch_ink`, then `finish`.
- `next-batch --limit 4` reserves at most four eligible pages from the current stage and writes one prompt file per page under `prompts/<stage>/`.
- Do not reserve a new batch while any page stage is still `generation_requested` or `imported`.
- A later stage is eligible only after every page in the previous stage is parent-inspected as `inspected_pass` or marked `complete`.
- Stage pipelining is not allowed: do not start `finish` for any page until every page has passed `storyboard_sketch_ink`.
- `finish` requires the parent-inspected `storyboard_sketch_ink` image as visual input and structure reference.
- Page dependencies, when present, must pass in the current stage before the dependent page can be reserved.
- Subagent inspection is advisory. Store it through `import`, but only the parent session may run `inspect-pass`.
- If a generated page fails parent inspection, run `rerun`; the rerun is prioritized before new pending pages in that same stage.
- Treat the pack as complete only when every page is `inspected_pass` or `complete` in both stages.

## Two Stage Rules

1. `storyboard_sketch_ink`
   Generate the combined comic page storyboard, sketch, and ink pass. Prioritize page layout, panel count, gutters, reading flow, speech/SFX placement, beat clarity, action blocking, spatial logic, clean sketch structure, and ink line clarity.

2. `finish`
   Use the parent-inspected `storyboard_sketch_ink` page as the required visual input and structure reference. Add tone, color if requested, lighting, shadows, final lettering, SFX, captions, and cleanup without changing page layout, panel count, text placement, character/object blocking, movement direction, or action logic.

## Parallel Generation Rules

After approval, all image generation must happen through subagents:

- Use one `fork_context=true` subagent per batch item.
- When `fork_context=true` is used, omit subagent role fields such as `agent_type` or `role`. Do not pass `worker`, `default`, or `explorer` as a role/type field.
- Treat `worker` only as the runner's inspection-result label (`worker_status`, `worker_note`), not as a subagent role type.
- Put the one-page generation and inspection behavior in the subagent prompt text instead of role metadata.
- Use a maximum of four subagents per batch.
- Each subagent generates exactly one assigned page stage.
- Do not use serial parent-session `image_gen` as a fallback.
- If subagents are unavailable, stop and report that generation is blocked by missing subagent support.
- Do not start the next four pages until the parent has inspected every imported page from the current batch and routed failures to `rerun` or passes to `inspect-pass`.

## Subagent Batch Contract

When spawning subagents for `next-batch`, use `fork_context=true` with no `agent_type` or `role`, then pass explicit task context:

```text
You are generating exactly one image for create-comic-storyboard-pack.
Act as the generation-and-inspection worker for this assigned page in the prompt only; do not require a worker role field.
Do not edit state.json.
Run folder: <run-dir>
Story/scenario file: <run-dir>/scenario.md
Approved plan: <run-dir>/approved_storyboard_plan.json
Assigned page: <filename-or-id>
Stage: <storyboard_sketch_ink|finish>
Prompt file: <prompt-file>
Batch id: <batch-id>
Default source folder: /Users/chasoik/Projects/character-sheet-generator/sources/
Excluded source folder: /Users/chasoik/Projects/character-sheet-generator/output/
Prior-stage reference: <path or none>
Relevant references: <paths or "none">
Page text policy: include approved adapted dialogue, SFX, and short captions inside speech balloons/caption areas/SFX lettering.
Spatial logic policy: reject impossible positions, object trajectories, or motion direction.
Source policy: when no explicit reference path is provided, use relevant files from the default source folder; never use output/ files as source data.

Use image_gen with the assigned prompt and visual references. After generation, inspect the output for stage fit, page/story fit, multi-panel layout, adapted text/SFX fit, text legibility, spatial continuity, motion plausibility, technical quality, and obvious defects. Return only:
- generated file path
- worker_status: pass or needs_rerun
- worker_note: concise inspection note
```

The parent session imports the result, visually inspects it, and decides `inspect-pass` or `rerun`.

## Parent Verification

Inspect every imported page before marking it passed. Check:

- The image is one complete comic-book page, not a single isolated panel unless the approved page has one panel.
- The page matches the approved page id, panel count, reading order, layout brief, and current stage.
- Speech balloons, SFX, and captions use approved adapted text and are legible.
- Source dialogue was adapted for comic timing unless exact preservation was explicitly approved.
- Source/reference data came from user-provided paths or `sources/`, not from `output/` generated artifacts.
- Composition, character blocking, props, setting, and continuity match the plan.
- Character/object positions, motion direction, ball/projectile paths, gaze direction, and cause-effect movement are plausible.
- `storyboard_sketch_ink` contains the approved page layout, cut structure, lettering placement, sketch structure, and ink lines.
- `finish` uses and preserves the inspected `storyboard_sketch_ink` page structure.
- Watermarks, random logos, unrelated captions, garbled lettering, and random typography are absent.
- Characters, hands, faces, props, perspective, and key action do not contain obvious defects.
- The generated output is mapped to the correct page filename and stage.

Do not claim page coverage, text quality, continuity, spatial logic, or stage quality unless the image was inspected.

## Reporting

After each batch, report in Korean:

```text
[만화 콘티 팩 진행 결과]
- 줄거리/시나리오: ...
- 저장 폴더: ...
- 기본 참고 폴더: ...
- 참고 제외 폴더: output/
- 상태 파일: ...
- 현재 단계: storyboard_sketch_ink | finish
- 승인된 페이지 수: ...
- 이번 병렬 그룹: ...
- worker 검수 결과: ...
- 부모 검수 결과: ...
- 대사/효과음 검수: ...
- 공간/동선 검수: ...
- rerun 필요 페이지: ...
- 다음 결정: ...
```

Keep reporting factual. If any item is still `generation_requested` or `imported`, say it is not parent-inspected yet.
