---
name: create-comic-storyboard-pack
description: "Turn a story outline, plot, scenario, script, scene notes, or storyboard request into approved Korean comic-book pages, then coordinate Codex image_gen creation through two verified stages: combined page storyboard/sketch/ink and tone/color/final finish. Use when the user wants manga, Korean comic, webtoon-page, comic-book, or visual-novel style pages generated from a story or scenario with 3-5 panel page layouts by default, 1-2 panel special staging, experimental freeform panel shapes, comic visual direction, text_policy handling, visual text guards, character locks, approval gate, four-subagent parallel batches, worker inspection, parent inspection, stage finish review, source consistency checks, and panel continuity checks."
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
- Also save stage finish review state and notes in `state.json` and `batch_plan.md`.

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

- Default output is one complete page image containing 3-5 panels by default, gutters or open borders, varied panel sizes, and rendered text only as allowed by the approved `text_policy`.
- Follow a measured cinematic Korean comic-book composition: clear reading flow, readable balloon placement, meaningful pauses, and balanced black/white or tone/color finish.
- Use 1-2 panels for special staging such as a full-page emotional beat, silence, stillness, large reveal, or decisive action moment; do not treat approved 1-2 panel special staging as a failure.
- Use experimental freeform panel design by default: diagonal panels, asymmetry, tall vertical panels, half/full-page panels, borderless or open panels, inset panels, partial overlaps, and wide negative space are allowed when reading order and continuity stay clear.
- Avoid a generic uniform rectangular grid unless the user asks for it or the scene clearly benefits from a restrained regular layout.
- Use six or more panels only for montage, comedy timing, quick action chains, or another clear story reason, and state that reason in the approval report.
- Merge repeated beats when one page or panel can clearly cover the action, but do not over-compress pages; split pages when emotional turns, action setup/result, gaze shifts, or quiet pauses need breathing room.
- Split pages when the reader needs a new location, time shift, major action sequence, emotional turn, reveal, or scene boundary.
- Split panels within a page when the reader needs a new beat, reaction, reveal, action change, object insert, or timing pause.
- Preserve scene references such as `S01`, `S02-S04`, or the user's own scene names.
- Include page-level layout notes and panel-level composition/viewpoint notes: wide, closeup, over-shoulder, low angle, top view, insert, reaction, or establishing.
- Include comic visual direction notes: detail density, focal point, visual emphasis, closeup intensity, line-weight/black-ink emphasis, background detail omission or emphasis, and planned speed/focus/impact/emotion lines.
- Use comic effect lines selectively. Do not add them as decoration to every panel; use them when they clarify action, emotion, impact, speed, or eye guidance.
- Include character blocking, action, setting, props, mood, continuity notes, source dialogue, adapted dialogue, SFX, captions, spatial logic, motion checks, and comic visual direction as metadata.
- Include `text_policy`, `character_locks`, and `visual_text_guard` in the approved plan when the user gives restrictions such as "대사 없이 효과음만", "텍스트 없음", fixed character markings, forbidden symbols, or forbidden environmental lettering.
- Use concise stable page filenames with a numeric prefix.

## Dialogue and Text Rules

Generated page text is controlled by `text_policy`.

- Default `text_policy` is `dialogue_sfx_captions`: comic text is allowed, including approved `adapted_dialogue`, SFX, and short captions inside the generated page image.
- `sfx_only` means no spoken dialogue, no speech balloons, no captions, no narration, no signage, no environmental text, no labels, no page or panel numbers, no random typography, and no corner labels. Only approved SFX from the plan may appear.
- `text_free` means no rendered text of any kind, including SFX, dialogue, speech balloons, captions, signage, labels, page or panel numbers, logos, environmental text, random glyphs, or corner labels.
- Record original lines as `source_dialogue` and comic lines as `adapted_dialogue` even when the active text policy forbids rendering them; they remain planning metadata unless the policy allows them.
- For `dialogue_sfx_captions`, do not copy provided source dialogue verbatim by default. Rewrite dialogue to fit comic timing, panel rhythm, emotion, balloon space, and page mood.
- Keep any allowed lettering short, legible, and placed where it does not cover faces, hands, props, or key action.
- If the user explicitly asks for exact dialogue preservation, mark that in `page_dialogue_notes` and keep the quoted line unchanged.
- Use `visual_text_guard` for concrete bans such as "건물/깃발/책/장식/컷 모서리에 임의 문자 금지".

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
- 페이지 호흡/컷 밀도: 기본 3-5컷 권장, 1-2컷은 특수 연출에 권장
- 컷 형태/레이아웃 자유도: 실험적 자유형 컷 구성 허용
- 6컷 이상 사용 사유: 해당 페이지가 있으면 명시
- 텍스트 정책(text_policy): dialogue_sfx_captions | sfx_only | text_free 중 승인안에 반영
- 캐릭터 고정 조건(character_locks): 있으면 명시
- 이미지 내 문자 방지 조건(visual_text_guard): 있으면 명시

| id | 파일명 | 장면 | 페이지 구성 | 컷 수 | 컷 형태/여백 | 디테일/강약/효과선 연출 | 텍스트 정책/SFX | 캐릭터/문자 고정 조건 | 공간/동선 검수 포인트 |
| ... |

텍스트 정책:
- 승인된 text_policy: ...
- dialogue_sfx_captions: 승인된 각색 대사/효과음/짧은 캡션을 이미지 내부에 포함
- sfx_only: 말풍선/대사/캡션/간판/환경문자/컷번호/라벨 금지, 승인 SFX만 허용
- text_free: SFX를 포함한 모든 이미지 내 문자 금지
- 원문 대사/각색 대사는 정책과 별도로 계획 메타데이터로 기록

승인 후 진행 방식:
- 1단계: 콘티/스케치/펜선 storyboard_sketch_ink
- 2단계: 톤/채색/마무리 finish
- 각 단계 최대 4페이지씩 서브에이전트 병렬 생성
- 각 서브에이전트 1차 검수
- 부모 세션 최종 검수
- 각 단계의 모든 페이지 부모 검수 후 단계 마무리 검수 stage-review
- 단계 마무리 검수에서 소스 데이터 일관성과 컷/페이지 연속성 확인
- 문제가 있으면 보완 대상 페이지를 rerun으로 되돌린 뒤 같은 단계 재진행
- 모든 페이지의 1단계 부모 검수 통과 전에는 2단계를 시작하지 않음
- 모든 페이지의 1단계 단계 마무리 검수 통과 전에는 2단계를 시작하지 않음
- 2단계는 1단계 생성 이미지를 필수 입력/구조 참조로 사용
- 실패 페이지 rerun 후 다음 배치 진행
- rerun --note의 보정 문구는 다음 재생성 프롬프트의 Current rerun correction에 자동 포함
- subagent가 completed:null이거나 생성 파일 경로를 반환하지 않으면 import하지 말고 rerun으로 라우팅
```

Do not call `approve-plan` or `next-batch` until the user approves this list. If the user edits the list, update the plan first and ask approval again when the change affects generated pages or page text.

## Plan JSON

After approval, write an approved plan and import it with the runner:

```json
{
  "scenario_title": "short title",
  "style_brief": "Korean comic-book style, tone, palette, rendering direction",
  "reading_order": "right-to-left or top-to-bottom as approved",
  "text_policy": "dialogue_sfx_captions",
  "character_locks": [
    "character name: fixed visual marker or silhouette requirement; forbidden drift"
  ],
  "visual_text_guard": [
    "no arbitrary text on buildings, signs, books, flags, decorations, labels, or panel corners"
  ],
  "pages": [
    {
      "id": "001-gym-arrival",
      "filename": "001-gym-arrival.png",
      "page_no": 1,
      "scene_refs": ["S01"],
      "layout_brief": "Three-panel cinematic page: one wide borderless establishing panel, one diagonal action panel, one quiet close reaction panel with breathing room.",
      "reading_order": "top-to-bottom, left-to-right within each row",
      "text_policy": "dialogue_sfx_captions",
      "character_locks": [],
      "visual_text_guard": [],
      "pacing_notes": "3-5 panels by default; 1-2 panels are recommended for special staging such as silence, stillness, or a decisive action moment.",
      "panel_shape_notes": "Use experimental freeform composition: borderless wide opening panel, diagonal action panel, and asymmetrical closeup panel.",
      "negative_space_notes": "Leave quiet negative space around the protagonist's entrance and the final reaction.",
      "detail_density_notes": "Keep the protagonist, door hand, ball, and hoop more detailed; simplify empty bleachers and far background.",
      "visual_emphasis_notes": "Use stronger line weight and black-ink contrast on the protagonist's face, hand, ball, and the final reaction closeup.",
      "comic_effects_notes": "Use subtle door squeak lines, a short ball motion streak, and light focus lines toward the hoop only where the action calls for them.",
      "page_dialogue_notes": "Rewrite dialogue to sound tense and concise; do not copy source lines verbatim.",
      "spatial_logic_notes": "Hoop remains on the far wall; protagonist enters from foreground-left; basketball moves toward the hoop when shot.",
      "motion_checks": [
        "ball trajectory follows hand release toward the hoop",
        "character gaze and body direction point toward the action target"
      ],
      "must_match": [
        "three spacious panels on one page",
        "experimental freeform panel design remains readable",
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
          "detail_density_notes": "Door handle, hand, and protagonist silhouette are detailed; empty court background is simplified.",
          "visual_emphasis_notes": "Focal point is the protagonist entering; use thicker foreground lines and lighter background line weight.",
          "comic_effects_notes": "Small squeak effect lines near the door hinge; no decorative speed lines.",
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

`text_policy` is optional for backward compatibility. If omitted, the runner treats it as `dialogue_sfx_captions`. Use page-level `text_policy`, `character_locks`, or `visual_text_guard` only when a page intentionally differs from the top-level rule.

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

Stage finish review after every page in a stage passes parent inspection:

```bash
python3 "$RUNNER" stage-review --run-dir <run-dir> --stage storyboard_sketch_ink --status pass --note "<source consistency and panel continuity pass note>"
python3 "$RUNNER" stage-review --run-dir <run-dir> --stage storyboard_sketch_ink --status needs_rerun --rerun-item <page-filename-or-id> --issue "<source or continuity issue>" --note "<reason>"
```

Use the same commands with `--stage finish` after every `storyboard_sketch_ink` page passes parent inspection.

State rules:

- `approve-plan` is the only transition from approval-gated planning into generation-ready state.
- `approve-plan` rejects `references` and `reference_paths` under `output/`.
- Stages must run in order: `storyboard_sketch_ink`, then `finish`.
- `next-batch --limit 4` reserves at most four eligible pages from the current stage and writes one prompt file per page under `prompts/<stage>/`.
- Do not reserve a new batch while any page stage is still `generation_requested` or `imported`.
- A later stage is eligible only after every page in the previous stage is parent-inspected as `inspected_pass` or marked `complete`, and the previous stage's stage finish review is `passed`.
- Stage pipelining is not allowed: do not start `finish` for any page until every page has passed `storyboard_sketch_ink`.
- `finish` requires the parent-inspected `storyboard_sketch_ink` image as visual input and structure reference.
- `text_policy`, `character_locks`, and `visual_text_guard` are copied into every stage prompt and worker inspection checklist.
- `rerun --note` stores the correction in `rerun_history`; the next `next-batch` prompt for that page includes it under `Current rerun correction`.
- `import --generated` may point directly to the stage output path. The runner updates state without copying over the same file.
- After all pages in a stage pass parent inspection, run `stage-review` before reserving the next stage or declaring completion.
- `stage-review --status pass` requires every page in that stage to be parent-inspected pass or complete.
- `stage-review --status needs_rerun` requires one or more `--rerun-item` values and moves those page stages back to `pending` with `rerun_pending=true`.
- Page dependencies, when present, must pass in the current stage before the dependent page can be reserved.
- Subagent inspection is advisory. Store it through `import`, but only the parent session may run `inspect-pass`.
- If a generated page fails parent inspection, run `rerun`; the rerun is prioritized before new pending pages in that same stage.
- Treat the pack as complete only when every page is `inspected_pass` or `complete` in both stages.

## Two Stage Rules

1. `storyboard_sketch_ink`
   Generate the combined comic page storyboard, sketch, and ink pass. Prioritize 3-5 panel measured cinematic pacing, experimental freeform panel shapes, clear reading flow, text/SFX placement according to the approved `text_policy`, beat clarity, action blocking, spatial logic, clean sketch structure, ink line clarity, detail density, visual emphasis, and planned comic effect lines. Use 1-2 panels for special staging such as full-page emotion, silence, stillness, or decisive action moments. Draw speed lines, focus lines, impact bursts, emotion lines, motion streaks, line-weight contrast, and black-ink emphasis only where they serve the approved beat. Reject over-compressed pages, unjustified dense panel packing, unintentional uniform rectangular grids, pages whose allowed text/SFX lacks breathing room, missing planned effects, effect lines that contradict motion, or pages where every panel has the same flat visual intensity.
   Stage finish review must compare every panel against approved source data and allowed `sources/` references for character, prop, profile, setting, and page-layout consistency, then check same-page and adjacent-page continuity.

2. `finish`
   Use the parent-inspected `storyboard_sketch_ink` page as the required visual input and structure reference. Add tone, color if requested, lighting, shadows, final policy-approved lettering/SFX, and cleanup without changing page layout, panel count, freeform panel shapes, negative space, text placement or text absence, comic effect lines, visual emphasis, line-weight rhythm, character/object blocking, movement direction, or action logic.
   Stage finish review must verify that tone/color/final polish did not introduce source-data drift or break continuity from the inspected `storyboard_sketch_ink` images.

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
- After a batch item is imported and parent-routed, close completed subagents that are no longer needed before starting the next batch.
- If a subagent returns `completed:null`, no final message, or no usable generated file path, do not invent an import path. Mark the page for `rerun` with the missing-result reason.

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
Page text policy: <approved text_policy and exact rendered-text allowance/prohibitions from prompt file>
Character locks: <top-level and page-level character_locks, or "none">
Visual text guard: <top-level and page-level visual_text_guard, or "none">
Current rerun correction: <rerun_history[-1].note / parent_note if present, or "none">
Page pacing policy: use 3-5 panels by default with measured cinematic pacing; use 1-2 panels for special staging; six or more panels need explicit story justification.
Panel shape policy: experimental freeform panel shapes are allowed and should not be rejected when reading order and continuity are clear.
Comic visual direction policy: follow approved detail density, visual emphasis, line-weight/black-ink rhythm, and speed/focus/impact/emotion lines; use effect lines only when they serve the beat.
Spatial logic policy: reject impossible positions, object trajectories, or motion direction.
Source consistency policy: reject drift in character face/body/hair/outfit, props, profile details, setting, landmarks, or page-layout references compared with the approved plan and allowed sources/.
Panel continuity policy: reject discontinuity across panels or adjacent pages in positions, gaze, action direction, object movement, time flow, policy-approved text/SFX placement or required text absence, and cause-effect motion.
Source policy: when no explicit reference path is provided, use relevant files from the default source folder; never use output/ files as source data.

Use image_gen with the assigned prompt and visual references. After generation, inspect the output for stage fit, page/story fit, multi-panel layout, active text_policy compliance, character_locks, visual_text_guard, spatial continuity, motion plausibility, technical quality, and obvious defects. Return only:
- generated file path
- worker_status: pass or needs_rerun
- worker_note: concise inspection note
```

The parent session imports the result, visually inspects it, and decides `inspect-pass` or `rerun`.

## Parent Verification

Inspect every imported page before marking it passed. Check:

- The image is one complete comic-book page, not a single isolated panel unless the approved page has one panel.
- The page matches the approved page id, panel count, reading order, layout brief, and current stage.
- The page uses 3-5 panels by default with measured cinematic pacing.
- 1-2 panel pages are acceptable for approved special staging such as full-page emotion, silence, stillness, large reveal, or decisive action moments.
- Six or more panels require explicit story justification in the approved plan.
- Experimental freeform panels are acceptable when reading order and continuity are clear.
- Over-compressed pages, unjustified dense panel packing, unintentional uniform rectangular grids, or pages packed with dialogue/SFX without breathing room must be rejected.
- Planned focal points, detail density, closeup intensity, line-weight/black-ink emphasis, and background simplification/emphasis match the approved page and panel notes.
- Planned speed lines, focus lines, impact bursts, emotion lines, and motion streaks are present where needed and match action direction, impact, mood, or eye guidance.
- Missing planned visual effects, effect lines that contradict motion, and pages where every panel has the same flat visual intensity must be rejected.
- Active `text_policy` is followed exactly: `dialogue_sfx_captions` uses approved adapted text/SFX/captions, `sfx_only` allows only approved SFX, and `text_free` contains no rendered text at all.
- `visual_text_guard` is satisfied: no arbitrary text on buildings, flags, books, decorations, panel corners, labels, or other listed surfaces.
- Source dialogue was adapted for comic timing unless exact preservation was explicitly approved and the active text policy allows dialogue rendering.
- Source/reference data came from user-provided paths or `sources/`, not from `output/` generated artifacts.
- Character face, age impression, body shape, hair, outfit, accessories, props, profile details, setting, landmarks, and page-layout references stay consistent with the approved plan and allowed source data.
- `character_locks` are preserved, including fixed markings, silhouettes, forbidden accessories, or other drift guards.
- Same-page panels and adjacent pages preserve continuity for position, gaze, action direction, object movement, time flow, policy-approved text/SFX placement or required text absence, and cause-effect motion.
- Composition, character blocking, props, setting, and continuity match the plan.
- Character/object positions, motion direction, ball/projectile paths, gaze direction, and cause-effect movement are plausible.
- `storyboard_sketch_ink` contains the approved page layout, cut structure, lettering placement, sketch structure, and ink lines.
- `storyboard_sketch_ink` contains the approved comic visual direction: selective detail density, focal emphasis, line-weight/black-ink rhythm, and planned effect lines.
- `finish` uses and preserves the inspected `storyboard_sketch_ink` page structure.
- `finish` does not weaken, hide, or contradict the inspected visual emphasis, effect-line direction, or ink rhythm.
- Watermarks, random logos, unrelated captions, garbled lettering, and random typography are absent.
- Characters, hands, faces, props, perspective, and key action do not contain obvious defects.
- The generated output is mapped to the correct page filename and stage.

Do not claim page coverage, text quality, continuity, spatial logic, or stage quality unless the image was inspected.

## Stage Finish Review

After every page in the current stage has passed parent inspection, review the complete stage before moving on:

- Compare all pages and all panels against approved source data and allowed `sources/` references.
- Check character, prop, profile, setting, landmark, and page-layout consistency across the whole stage.
- Check continuity within each page and across adjacent pages.
- If everything passes, run `stage-review --status pass`.
- If any page needs correction, run `stage-review --status needs_rerun --rerun-item <page>` with an issue note, then regenerate and inspect the rerun page before repeating stage finish review.
- Do not start `finish` and do not claim the pack complete until the relevant stage finish review is `passed`.

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
- 텍스트 정책 검수: ...
- 캐릭터 고정 조건 검수: ...
- 이미지 내 문자 방지 검수: ...
- 공간/동선 검수: ...
- 단계 마무리 검수 결과: ...
- 소스 일관성 이슈: ...
- 컷 연속성 이슈: ...
- 보완 대상 페이지: ...
- rerun 필요 페이지: ...
- 다음 결정: ...
```

Keep reporting factual. If any item is still `generation_requested` or `imported`, say it is not parent-inspected yet.
