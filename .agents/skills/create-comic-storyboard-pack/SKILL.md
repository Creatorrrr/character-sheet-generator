---
name: create-comic-storyboard-pack
description: Use when a story outline, scenario, script, scene notes, or storyboard request needs approved Korean comic-book pages managed as a resumable page pack.
---

# Create Comic Storyboard Pack

## Overview

Convert a story outline, plot, or scenario into a resumable Korean comic-book page pack. This skill is the orchestrator: it extracts the page plan, asks for approval, owns runner state, reserves batches, imports worker outputs, performs parent inspection, routes reruns, performs stage finish review, and asks for user feedback before moving from sketch/ink to finish.

Actual image generation is delegated to stage skills:

- `$create-comic-storyboard-sketch-ink` for `storyboard_sketch_ink`
- `$create-comic-storyboard-finish` for `finish`

Use Codex built-in `image_gen` only through one subagent per reserved page. Do not generate any image before the user approves the exact page plan.

## Default Locations

If the user does not specify a save folder, create `output/<slug>-comic-storyboard-pack-YYYYMMDD-HHMMSS/` under `/Users/chasoik/Projects/character-sheet-generator/output/`.

Save `scenario.md`, `state.json`, `approved_storyboard_plan.json`, `batch_plan.md`, prompt files, subagent prompt files, generated stage images, worker notes, parent inspection notes, and stage-review state under that run folder.

If the user does not specify source/reference paths, use `/Users/chasoik/Projects/character-sheet-generator/sources/`. Do not use `/Users/chasoik/Projects/character-sheet-generator/output/` or any `output/` subtree as source/reference data. Current-run generated images may be used only as prior-stage workflow references after parent inspection.

## Page Planning Rules

- Plan complete page images, not isolated panels.
- Default to 3-5 panels per page with measured cinematic Korean comic-book pacing.
- Use 1-2 panels for special staging such as silence, stillness, full-page emotion, a large reveal, or decisive action.
- Use six or more panels only for montage, comedy timing, quick action chains, or another explicit story reason.
- Use experimental freeform panel design by default when readable: diagonal panels, asymmetry, tall vertical panels, half/full-page panels, borderless or open panels, inset panels, partial overlaps, and wide negative space.
- Avoid generic uniform rectangular grids unless the user asks for them or the scene benefits from restraint.
- Include page-level layout notes and panel-level composition/viewpoint notes.
- Include detail density, visual emphasis, line-weight/black-ink rhythm, background simplification/emphasis, and planned speed/focus/impact/emotion lines.
- Include character blocking, action, setting, props, mood, continuity notes, source dialogue, adapted dialogue, SFX, captions, spatial logic, motion checks, and `must_match`.
- For action or staging where direction, cover, line of sight, object trajectory, or landmark continuity matters, include a structured `spatial_contract`. Use it to define stable entities, coordinate space, per-panel positions/vectors/visibility/occlusion, and machine-checkable constraints before generation.
- Use `spatial_contract.constraints` for relations such as `aims_at`, `trajectory_to`, `cover_between`, `behind_cover_from`, `line_of_sight_blocked`, `left_of`, `right_of`, and `same_landmark_relation_as`. Treat failures as generation blockers before approval and rerun causes after image inspection.
- Include character appearance/anatomy locks in `character_locks` or `must_match`: approved species/body structure, face structure, eye count and placement, hand/finger/arm/leg count, silhouette, body proportions, and posture.
- Unless the plan or source explicitly approves a one-eyed, asymmetric, non-human, or otherwise unusual structure, treat missing/extra/merged eyes, one-eyed appearance for a two-eyed character, missing/extra limbs or fingers, changed species/body type, broken joints, and broken body proportions as rerun causes.
- Preserve source scene references such as `S01`, `S02-S04`, or the user's own scene names.

## Text Policy

Generated page text is controlled by `text_policy`.

- `dialogue_sfx_captions`: approved adapted dialogue, SFX, and short captions may appear in the image.
- `sfx_only`: only approved SFX may appear. No speech balloons, dialogue, captions, narration, signage, environmental text, labels, page/panel numbers, random typography, or corner labels.
- `text_free`: no rendered text of any kind, including SFX, dialogue, speech balloons, captions, signage, labels, logos, page/panel numbers, environmental text, or random glyphs.

Record original lines as `source_dialogue` and comic lines as `adapted_dialogue` even when the active policy forbids rendering them. Use `visual_text_guard` for concrete text bans such as arbitrary lettering on buildings, flags, books, decorations, labels, or panel corners.

## Approval Gate

Before generation, present the proposed page list in Korean and wait for explicit approval.

Use this format:

```text
[만화 페이지 생성 승인 요청]
- 줄거리/시나리오: ...
- 저장 폴더: ...
- 기본 참고 폴더: /Users/chasoik/Projects/character-sheet-generator/sources/
- 참고 제외 폴더: /Users/chasoik/Projects/character-sheet-generator/output/
- 총 페이지 수: ...
- 페이지당 컷 구성 기준: ...
- 컷 형태/레이아웃 자유도: 실험적 자유형 컷 구성 허용
- 텍스트 정책(text_policy): dialogue_sfx_captions | sfx_only | text_free
- 캐릭터 고정 조건(character_locks): ...
- 캐릭터 외형/해부 고정 조건(appearance/anatomy): 종족/신체 구조, 얼굴 구조, 눈 개수/배치, 손/손가락/팔/다리 개수, 실루엣, 체형 비율, 자세. 예: 두 눈 캐릭터는 두 눈이 보이거나 각도상 자연스럽게 가려져야 하며, 외눈 캐릭터처럼 보이면 rerun.
- 이미지 내 문자 방지 조건(visual_text_guard): ...
- 구조화 공간 계약(spatial_contract): 총구/시선/투사체/엄폐/랜드마크 관계가 중요한 컷은 승인 전 벡터와 관계 검증을 통과해야 함

| id | 파일명 | 장면 | 페이지 구성 | 컷 수 | 컷 형태/여백 | 디테일/강약/효과선 연출 | 텍스트 정책/SFX | 캐릭터/외형/문자 고정 조건 | 공간/동선/spatial_contract 검수 포인트 |
| ... |

승인 후 진행 방식:
- 1단계: 콘티/스케치/펜선 storyboard_sketch_ink
- 각 페이지는 $create-comic-storyboard-sketch-ink subagent가 생성/1차 검수
- 부모 세션 최종 검수
- 모든 페이지 1단계 부모 검수 후 stage-review
- 1단계 stage-review 통과 후 사용자 피드백을 받고 다음 단계 진행 여부 확인
- 사용자 피드백 게이트 선택지: 그대로 finish 승인(`approve-next-stage`) | 수정 UI 열기 또는 에이전트 좌표 마킹 생성(`$review-image-overlays`) | 현재 단계에서 중단(`stop-after-stage`)
- approve-next-stage 전에는 finish 예약 금지
- 사용자가 중단하면 stop-after-stage로 1단계 산출물만 완료 처리
- 사용자 또는 에이전트가 수정을 요청하면 `$review-image-overlays`로 색상별 오버레이 PNG/TXT와 `revision_requests.json`을 저장하고, `request-revisions`로 해당 페이지를 rerun 처리
- 사용자가 승인하면 2단계: 톤/채색/마무리 finish
- 2단계는 $create-comic-storyboard-finish subagent가 생성/1차 검수
- 2단계는 parent-inspected storyboard_sketch_ink 이미지를 필수 입력으로 사용
```

Do not call `approve-plan` or `next-batch` until the user approves this list. If the user edits generated-page details or rendered text, update the plan and ask approval again.

## Plan JSON

Approved plans use `pages[].panels[]`. Legacy flat `panels` are accepted only for compatibility and are converted to single-panel pages.

```json
{
  "scenario_title": "short title",
  "style_brief": "Korean comic-book style, tone, palette, rendering direction",
  "reading_order": "top-to-bottom, left-to-right",
  "text_policy": "dialogue_sfx_captions",
  "character_locks": [
    "character: fixed visual marker or silhouette requirement",
    "two-eyed character: keep two-eye structure unless a natural angle, hair, or object occlusion hides one eye"
  ],
  "visual_text_guard": ["no arbitrary text on buildings, books, flags, labels, or panel corners"],
  "pages": [
    {
      "id": "001-gym-arrival",
      "filename": "001-gym-arrival.png",
      "page_no": 1,
      "scene_refs": ["S01"],
      "layout_brief": "Three-panel cinematic page with a wide establishing panel, diagonal action panel, and close reaction panel.",
      "reading_order": "top-to-bottom, left-to-right",
      "text_policy": "dialogue_sfx_captions",
      "pacing_notes": "3-5 panels by default; 1-2 panels only for special staging.",
      "panel_shape_notes": "Experimental freeform panel composition.",
      "negative_space_notes": "Leave breathing room around key faces, hands, action, balloons, and SFX.",
      "detail_density_notes": "Detail focal characters, props, hands, and faces; simplify low-priority background.",
      "visual_emphasis_notes": "Use stronger line weight and contrast on the focal beat.",
      "comic_effects_notes": "Use effect lines only where they clarify action, emotion, impact, speed, or eye guidance.",
      "spatial_logic_notes": "Hoop remains on far wall; ball moves toward the hoop.",
      "motion_checks": ["ball trajectory follows hand release toward target"],
      "must_match": [
        "three readable panels",
        "no impossible ball direction",
        "two-eyed characters must not look one-eyed unless explicitly approved"
      ],
      "spatial_contract": {
        "coordinate_space": {
          "type": "panel_screen_2d",
          "origin": "top_left",
          "x_axis": "right",
          "y_axis": "down",
          "units": "normalized 0..1 or consistent scene units"
        },
        "entities": [
          {"id": "protagonist", "type": "character", "role": "shooter"},
          {"id": "basketball", "type": "object", "role": "projectile"},
          {"id": "hoop", "type": "landmark", "role": "target"}
        ],
        "panel_snapshots": [
          {
            "panel": 1,
            "entities": [
              {"id": "protagonist", "position": [0.25, 0.68], "facing_vector": [1, -0.15]},
              {"id": "basketball", "position": [0.34, 0.55], "trajectory_vector": [1, -0.2]},
              {"id": "hoop", "position": [0.82, 0.36]}
            ]
          }
        ],
        "constraints": [
          {"type": "trajectory_to", "panel": 1, "object": "basketball", "target": "hoop"},
          {"type": "right_of", "panel": 1, "subject": "hoop", "anchor": "protagonist"}
        ]
      },
      "panels": [
        {
          "panel_no": 1,
          "beat": "The protagonist enters the empty gym.",
          "visual_brief": "Wide establishing panel of a quiet indoor court.",
          "characters": ["protagonist"],
          "action": "Standing near the entrance, looking toward the hoop.",
          "composition": "door frame foreground, hoop in distance",
          "source_dialogue": ["It's quiet in here."],
          "adapted_dialogue": ["...조용하네."],
          "sfx": ["끼익"],
          "caption": ["방과 후, 체육관."],
          "speech_balloon": "small balloon near protagonist, not covering face",
          "sfx_placement": "near opening door"
        }
      ],
      "references": [],
      "prompt": "A Korean comic-book page...",
      "negative_prompt": "watermark, random logo, garbled lettering...",
      "dependencies": []
    }
  ]
}
```

`references` and top-level `reference_paths` must point to user-provided files or relevant files under `sources/`. The runner rejects references under `output/`.

## Runner

Use `[스킬 경로]/scripts/comic_storyboard_runner.py`. `[스킬 경로]` means the directory that contains this `SKILL.md`.

```bash
SKILL_DIR=".agents/skills/create-comic-storyboard-pack"
RUNNER="$SKILL_DIR/scripts/comic_storyboard_runner.py"
```

Initialize and approve:

```bash
python3 "$RUNNER" init --title "<story/scenario title>" --scenario <story-or-scenario-file>
python3 "$RUNNER" status --run-dir <run-dir>
python3 "$RUNNER" spatial-check --plan-file <approved-plan.json>
python3 "$RUNNER" approve-plan --run-dir <run-dir> --plan-file <approved-plan.json>
```

`approve-plan` automatically runs `spatial-check` against every page with `spatial_contract`. Unknown entities, unsupported constraints, target-opposite aim vectors, impossible projectile trajectories, missing cover between actor/threat, and fixed-landmark relation drift fail before any generation is reserved. Legacy plans without `spatial_contract` remain valid and continue to use free-form `spatial_logic_notes`, `motion_checks`, and `must_match`.

Optional single-stage targets:

```bash
python3 "$RUNNER" approve-plan --run-dir <run-dir> --plan-file <approved-plan.json> --target-stage storyboard_sketch_ink
python3 "$RUNNER" approve-plan --run-dir <run-dir> --plan-file <approved-plan.json> --target-stage finish
```

Reserve and process a batch:

```bash
python3 "$RUNNER" next-batch --run-dir <run-dir> --limit 4
# Spawn one fork_context=true subagent per printed item.
# Use the printed SUBAGENT_PROMPT_FILE content as the subagent task.
python3 "$RUNNER" import --run-dir <run-dir> --item <page> --stage storyboard_sketch_ink --generated <generated-path> --worker-status pass --worker-note "<subagent note>"
python3 "$RUNNER" inspect-pass --run-dir <run-dir> --item <page> --stage storyboard_sketch_ink --note "<parent inspection note>" --spatial-verdict pass --spatial-note "<spatial contract visual inspection pass>"
python3 "$RUNNER" inspect-pass --run-dir <run-dir> --item <page> --stage storyboard_sketch_ink --note "<parent inspection note>" --spatial-verdict needs_rerun --spatial-note "<spatial contradiction found>"
python3 "$RUNNER" rerun --run-dir <run-dir> --item <page> --stage storyboard_sketch_ink --note "<reason>"
python3 "$RUNNER" batch-status --run-dir <run-dir> --batch-id <batch-id>
```

After every page in `storyboard_sketch_ink` passes parent inspection:

```bash
python3 "$RUNNER" stage-review --run-dir <run-dir> --stage storyboard_sketch_ink --status pass --note "<source consistency and continuity pass>"
```

This sets `stage_gates.storyboard_sketch_ink_to_finish.status` to `pending_user_feedback`. At that point report the first-stage outputs to the user and ask whether to continue.

Offer exactly these feedback choices:

- Approve next stage: continue to `finish` with `approve-next-stage`.
- Open revision UI or create agent markup: use `$review-image-overlays` to collect color-coded overlay requests.
- Stop after stage: keep only `storyboard_sketch_ink` with `stop-after-stage`.

If the user wants the revision UI:

```bash
REVIEW_SKILL_DIR=".agents/skills/review-image-overlays"
REVIEW_RUNNER="$REVIEW_SKILL_DIR/scripts/review_overlay_server.py"
python3 "$REVIEW_RUNNER" serve --run-dir <run-dir> --stage storyboard_sketch_ink
```

If a subagent self-check or parent inspection identifies a concrete fix without needing user painting, create a coordinate markup spec and save the same artifact format directly:

```bash
python3 "$REVIEW_RUNNER" create-markup --run-dir <run-dir> --stage storyboard_sketch_ink --spec <markup.json>
```

Use normalized coordinates by default. The markup spec supports `rect` boxes and `polygon` points, non-empty request text per mark, and optional `coordinate_space: "pixel"` for exact image pixel coordinates. The generated color-specific overlay PNG/TXT files are canonical, just like the browser UI output.

After the user saves in the browser or an agent creates markup, import the manifest back into this runner:

```bash
python3 "$RUNNER" request-revisions --run-dir <run-dir> --review-manifest <run-dir>/review_overlays/storyboard_sketch_ink/<review-id>/revision_requests.json
python3 "$RUNNER" next-batch --run-dir <run-dir> --limit 4
```

`request-revisions` resets the affected page stage to `pending`, records the color-specific overlay PNG/TXT paths and request text, resets stage-review and following gates, and injects a `User revision overlays` section into the next prompt/subagent prompt. Use the color-specific overlay files as canonical instructions; the combined overlay is only for quick visual review.

If the user approves finish:

```bash
python3 "$RUNNER" approve-next-stage --run-dir <run-dir> --from-stage storyboard_sketch_ink --to-stage finish --note "<user approved finish>"
python3 "$RUNNER" next-batch --run-dir <run-dir> --limit 4
```

If the user stops after sketch/ink:

```bash
python3 "$RUNNER" stop-after-stage --run-dir <run-dir> --stage storyboard_sketch_ink --note "<user stops before finish>"
```

For finish-only runs with an external sketch/ink image:

```bash
python3 "$RUNNER" import-prior-stage --run-dir <run-dir> --item <page> --stage storyboard_sketch_ink --generated <sketch-ink-image> --note "<external prior reference>"
python3 "$RUNNER" stage-review --run-dir <run-dir> --stage storyboard_sketch_ink --status pass --note "<external prior stage accepted>"
python3 "$RUNNER" approve-next-stage --run-dir <run-dir> --from-stage storyboard_sketch_ink --to-stage finish --note "<user approved finish>"
python3 "$RUNNER" next-batch --run-dir <run-dir> --limit 4
```

## State Rules

- `approve-plan` is the only transition from approval-gated planning into generation-ready state.
- `target_stages` defaults to `["storyboard_sketch_ink", "finish"]`.
- `storyboard_sketch_ink` must finish parent inspection and stage-review before `finish`.
- `finish` also requires `approve-next-stage`; stage-review pass alone is not enough.
- `stop-after-stage` changes the completion target to the requested completed stage.
- `finish` requires a parent-inspected or imported prior `storyboard_sketch_ink` image.
- `next-batch --limit 4` reserves at most four eligible pages and writes both `prompts/<stage>/...prompt.txt` and `subagent_prompts/<stage>/...subagent.txt`.
- `next-batch` injects `spatial_contract` summaries into the stage prompt and subagent prompt. Generated images must preserve the approved entity positions, vectors, visibility/occlusion, cover, line-of-sight, trajectory, and landmark-relation constraints.
- Do not reserve a new batch while any page stage is `generation_requested` or `imported`.
- Subagent inspection is advisory. Only the parent session may run `inspect-pass`.
- Parent `inspect-pass --spatial-verdict needs_rerun` never marks the page passed; it routes the page back to `pending` rerun and resets stage review / following gates.
- `request-revisions --review-manifest <revision_requests.json>` imports `$review-image-overlays` feedback, marks affected page stages `pending`/`rerun_pending`, resets stage-review and following gates, and adds overlay PNG/TXT paths plus request text to the next rerun prompt.
- `$review-image-overlays create-markup` is valid for subagent self-verification and parent comprehensive verification when the issue can be localized with rect/polygon coordinates; it must still flow through `request-revisions`.
- If a subagent returns `completed:null`, no final message, or no generated path, do not invent an import path. Route the page to `rerun`.
- Rerun resets the relevant stage review and any following stage gate.

## Parent Verification

Inspect every imported page before marking it passed. Check page id, stage, panel count, reading order, layout brief, text policy, character locks, character appearance/anatomy locks, visual text guard, source consistency, structured `spatial_contract` compliance, spatial continuity, motion plausibility, visual emphasis, effect-line direction, technical quality, and output filename mapping.

When a page has `spatial_contract`, inspect against every entity, panel snapshot, vector, visibility/occlusion, and constraint. Reject target-opposite aim vectors, projectile paths that do not move toward the target, cover that is not between actor and threat, exposed characters that were specified as hidden behind cover, broken line-of-sight blocking, left/right relation flips, and fixed landmark relation drift. Record the result with `--spatial-verdict` and `--spatial-note`.

Character appearance/anatomy is an independent reject criterion, not just a technical-quality note. Unless explicitly approved by the plan or source, rerun pages with missing/extra/merged eyes, one-eyed appearance for a two-eyed character, one-eyed face unless explicitly approved, missing/extra limbs or fingers, changed species/body type, broken joints, or broken body proportions.

For `finish`, verify that tone/color/final polish preserved the inspected `storyboard_sketch_ink` layout, panel shapes, negative space, text placement or required text absence, line-weight rhythm, visual emphasis, effect lines, character/object blocking, structured spatial contract, eye/face/hand/limb/silhouette/body proportion/posture structure, movement direction, and action logic.

Do not claim page coverage, text quality, continuity, spatial logic, or stage quality unless the image was inspected.

## Reporting

After each batch or gate, report in Korean:

```text
[만화 콘티 팩 진행 결과]
- 줄거리/시나리오: ...
- 저장 폴더: ...
- 상태 파일: ...
- 대상 단계(target_stages): ...
- 현재 단계: storyboard_sketch_ink | finish | complete
- 승인된 페이지 수: ...
- 이번 병렬 그룹: ...
- worker 검수 결과: ...
- 부모 검수 결과: ...
- 텍스트 정책 검수: ...
- 캐릭터 고정 조건 검수: ...
- 캐릭터 외형/해부 검수: ...
- 이미지 내 문자 방지 검수: ...
- 공간/동선 검수: ...
- 단계 마무리 검수 결과: ...
- 다음 단계 사용자 피드백 게이트: pending_user_feedback | approved | stopped
- 보완 대상 페이지: ...
- 다음 결정: approve-next-stage로 finish 진행 | $review-image-overlays로 수정 UI 열기/에이전트 마킹 생성 | stop-after-stage로 종료
```
