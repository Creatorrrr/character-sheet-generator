---
name: create-comic-storyboard-pack
description: Use when a story outline, scenario, script, scene notes, or storyboard request needs approved Korean comic-book pages managed as a resumable page pack.
---

# Create Comic Storyboard Pack

## Overview

Convert a story outline, plot, or scenario into a resumable Korean comic-book page pack. This skill is the orchestrator: it extracts the page plan, asks for approval, owns runner state, reserves batches, imports worker outputs, performs parent inspection, routes reruns, performs stage finish review, and asks for user feedback before moving from sketch/ink to finish.

Actual image generation is delegated to stage skills:

- `$create-comic-storyboard-blocking` for `storyboard_blocking`
- `$create-comic-storyboard-sketch-ink` for `storyboard_sketch_ink`
- `$create-comic-storyboard-finish` for `finish`

Use Codex built-in `image_gen` only through one subagent per reserved page. Do not generate any image before the user approves the exact page plan.

## Default Locations

If the user does not specify a save folder, create `output/<slug>-comic-storyboard-pack-YYYYMMDD-HHMMSS/` under `/Users/chasoik/Projects/character-sheet-generator/output/`.

Save `scenario.md`, `state.json`, `proposed_storyboard_plan.json`, `approved_storyboard_plan.json`, proposed/approved spatial-preview HTML files, `batch_plan.md`, prompt files, subagent prompt files, generated stage images, blocking `*_desc.md` files, worker notes, parent inspection notes, and stage-review state under that run folder.

If the user does not specify source/reference paths, use `/Users/chasoik/Projects/character-sheet-generator/sources/`. Do not use `/Users/chasoik/Projects/character-sheet-generator/output/` or any `output/` subtree as source/reference data. Current-run generated images may be used only as prior-stage workflow references after parent inspection.

## Page Planning Rules

- Plan complete page images, not isolated panels.
- Default to 3-5 panels per page with measured cinematic Korean comic-book pacing.
- Use 1-2 panels for special staging such as silence, stillness, full-page emotion, a large reveal, or decisive action.
- Use six or more panels only for montage, comedy timing, quick action chains, or another explicit story reason.
- Use experimental freeform panel design by default when readable: diagonal panels, asymmetry, tall vertical panels, half/full-page panels, borderless or open panels, inset panels, partial overlaps, and wide negative space.
- Avoid generic uniform rectangular grids unless the user asks for them or the scene benefits from restraint.
- Before individual page composition, create a pre-page `spatial_continuity_plan` whenever pages share or revisit a location, move through connected spaces, or depend on landmark continuity. This is the location bible: decide the physical set, `location_id`s, entrances/exits, walls, doors, windows, furniture, props, fixed landmarks, camera/world axes, lighting sources, offscreen zones, movement path, allowed state changes, and page-to-page location transitions before planning individual pages. Same `location_id` means the same physical space unless a page records an explicit transition or allowed change.
- Each page under an active `spatial_continuity_plan` must include `location_id` plus `location_continuity` fields such as `zone`, `camera_axis`, `fixed_landmarks_visible`, `offscreen_landmarks`, `must_preserve`, `changes_from_previous_page`, and `location_transition` when the location changes. Do not let a later page silently invent a different room, corridor, street, furniture layout, entrance/exit placement, or landmark arrangement for the same `location_id`.
- Use a three-pass page planning flow. First, define the pre-page location/landmark continuity plan when applicable. Second, design each page and panel from the scenario, emotional beats, action rhythm, reader eye flow, panel density, negative space, detail density, visual emphasis, line-weight/black-ink rhythm, background simplification/emphasis, and planned speed/focus/impact/emotion lines while respecting that location plan.
- After the narrative-first page/panel design is chosen, extract only the spatial relations needed for validation into `spatial_contract`. `spatial_contract` is a validation overlay, not a page or composition driver.
- Do not design panels just to make `spatial_contract` easy to draw. Do not turn action pages into tactical diagrams or place character/object coordinates at the center of page design unless the story itself calls for a diagram-like page.
- For spatially important scenes such as multi-floor interiors, stairwells, balconies, rooms/corridors seen from changing cameras, or recurring connected sets, `spatial_continuity_plan` should include `scene_3d_scenes[]` by default. Treat each `scene_3d` as a provisional validation model, not an absolute floor plan or composition driver.
- For spatially important panels, default `spatial_contract.coordinate_space.type` to `"scene_3d"` unless an exception is explicitly justified. Use `panel_screen_2d` mainly for graphic/UI shots, symbolic panels, emotion closeups, text/SFX layout, or cases where 3D inference would create false constraints; record the reason in `spatial_contract_extraction` or page notes. Default `scene_3d` `usage` is `validation_only`; do not attach a headless 3D render as a generation reference unless a future workflow explicitly enables `camera_render_reference`.
- `scene_3d` data should use one shared canonical space per connected location set, with panel-specific `panel_snapshots[]` and `transitions[]`. Do not create unrelated per-panel 3D spaces for the same physical set; record a new `scene_id` only when the story actually moves to an unrelated location.
- `scene_3d` is provisional until generated storyboard inspection. During parent inspection, hard locks from the scenario/page plan are rerun criteria, while soft or inferred geometry may be reconciled to the approved storyboard when doing so preserves the page design, hard invariants, and prior continuity. The first page/panel with no prior spatial continuity is a calibration anchor for soft/inferred geometry.
- Include page-level layout notes, panel-level composition/viewpoint notes, and optional `narrative_plan` fields such as `story_function`, `reader_experience`, `pacing_intent`, and `composition_intent`.
- Include character blocking, action, setting, props, mood, continuity notes, source dialogue, adapted dialogue, SFX, captions, spatial logic, motion checks, and `must_match`.
- For action or staging where direction, line of sight, moving-object path, visibility/occlusion, landmark continuity, or page-to-page state continuity matters, include a structured `spatial_contract` after the page/panel design. Use it to define stable entities, coordinate space, per-panel positions/vectors/visibility/occlusion, temporal state fields, and machine-checkable constraints before generation.
- In gunfight, pursuit, cover, ambush, or tactical movement scenes, any "behind", "cover", "엄폐", "뒤", or line-of-fire relation must create a cover constraint with explicit `viewpoint_entity` or an explicit `threat`; reader-side/front-back placement is not a valid substitute.
- Use `spatial_contract_extraction` to record that the contract was derived from `narrative_plan_and_panels`, why it is being verified, the validation focus, and `must_not_override_page_design: true`.
- Use `spatial_contract.entities[].blocking_symbol` to predefine the quick blocking mark for important characters, objects, occluding elements, landmarks, and motion markers. Prefer a recognizable 3-second rough form or silhouette plus any needed fallback symbol, not a meaningless geometric mark alone. Unimportant props/background elements may be simplified or omitted when they are not needed for story readability, action readability, spatial contract verification, visibility/occlusion, landmark continuity, or page composition.
- Use `spatial_contract.panel_snapshots[].entities[]` fields such as `pose`, `cover`, `visibility`, `occlusion`, `location_anchor`, `held_props`, `state_tags`, and optional `screen_box` when state continuity or cover geometry matters.
- Use `spatial_contract.constraints` for general relation checks such as directional alignment (`aims_at`), movement path toward a destination (`trajectory_to`), occluding-element placement (`cover_between`, `behind_cover_from`), visibility/line-of-sight blocking (`line_of_sight_blocked`), negative firing/aim relations (`no_line_of_fire`, `not_aims_at`), left/right or landmark relation continuity (`left_of`, `right_of`, `same_landmark_relation_as`, `same_cover_as`), state continuity (`state_persists_from`, `occlusion_persists_from`), approved transitions (`allowed_transition`), and required causes (`requires_cause`). Treat failures as validation blockers before approval and rerun causes after image inspection, without letting the contract replace the approved narrative/page design.
- For `scene_3d`, supported validation constraints include `on_level`, `above`, `below`, `vertical_separation`, `same_location_as`, `trajectory_to`, `allowed_transition`, `requires_cause`, and `visual_evidence_required`. `visual_evidence_required` is an inspection checklist item, not a machine-check failure by itself.
- Use `spatial_contract.locks[]` to separate `hard`, `soft`, and `inferred` spatial assumptions. Hard locks represent scenario/page-plan/explicit continuity invariants and should trigger rerun when violated. Soft and inferred locks represent model-estimated geometry such as camera FOV, furniture offsets, railing length, or approximate spacing and may be reconciled after inspection.
- `cover_between` means only that the cover lies between the actor and source/threat. `behind_cover_from` means the actor must be behind cover from `viewpoint_entity` or `threat` line of fire, not from the reader's camera. `line_of_sight_blocked` is stronger: direct visibility or hit line must be blocked by the named cover.
- Cover constraints may include `allowed_exposure` such as `side_edge_peek_only`, `weapon_edge_only`, or `eyes_only`, and `forbidden_exposure` such as `torso_visible`, `above_roofline`, or `open_field`. Treat listed forbidden exposure as a worker and parent-inspection reject condition.
- During image generation, translate cover and visibility constraints into visual occlusion rendering rules before using the raw `spatial_contract`. `allowed_exposure` is a validation term, not a literal thing to draw on a wall edge.
- For any character hidden by a wall, pillar, vehicle, furniture, or other cover, require a clean border, shadow gap, or negative-space sliver between the character silhouette and the occluder. Reject shared contour, shared hatching, continuous cover texture crossing into the character, or any face/eye/hand/weapon tip pasted onto the cover edge.
- For tiny allowed exposure such as `eyes_only`, `weapon_edge_only`, `eyes_and_weapon_edge_only`, `eyes_and_hand_only`, or `side_edge_peek_only`, clear full concealment is acceptable and preferred when a partial peek would become unreadable or visually fused with the occluder. If the approved beat requires deliberate exposure, show only that required exposure while keeping the silhouette separated from the cover.
- Cover constraints may include `screen_box: [x, y, w, h]` for the approximate screen region occupied by the cover. When present, the runner checks actor-threat segment intersection with that box instead of only checking one cover point near the segment.
- If a beat says a character "does not fire", "not_firing", "발사하지 않음", "쏘지 않음", or pressures by presence only, include `no_line_of_fire` from source to target. Use `not_aims_at` when aim/gaze/weapon vector must explicitly avoid a target.
- For `trajectory_to`, moving objects should include `origin_entity` and `destination_entity` when those endpoints matter, so the prompt can state the origin and destination explicitly.
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

After drafting the proposed page plan and before presenting the approval request, save it as `<run-dir>/proposed_storyboard_plan.json`. If any page has `spatial_contract`, run `spatial-preview` against that proposed plan and include the generated HTML path plus `SPATIAL_CHECK` status and issue count in the approval request. If `spatial-preview` reports `SPATIAL_CHECK: fail`, revise the plan until the issues are resolved before asking for generation approval, unless the user explicitly asked to inspect a failing draft. If no page has structured `spatial_contract`, state that no spatial-preview HTML was generated.

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
- 사전 공간 설계(spatial_continuity_plan): 같은 장소/이어지는 공간/랜드마크 연속성이 있는 경우 페이지별 컷 설계 전에 location_id, 물리적 세트, 출입구/벽/창/가구/고정 랜드마크, 카메라/세계 축, 조명, 이동 경로, 허용되는 변화, 페이지별 위치 전환을 먼저 확정함. 같은 location_id는 명시적 전환/허용 변화 없이는 같은 물리 공간으로 유지
- 페이지/컷 구성 원칙: 사전 공간 설계를 지킨 상태에서 시나리오, 감정선, 액션 리듬, 독자 시선, 컷 밀도, 여백, 디테일/강약/효과선 중심으로 만화 페이지를 설계함
- 구조화 공간/시간 계약(spatial_contract): 페이지 구성 이후 추출하는 검수 레이어. 방향/시선/이동체 경로/가림 요소/랜드마크/상태 유지 관계가 중요한 컷은 승인 전 벡터, 관계, 시간적 상태 검증을 통과해야 하지만, spatial_contract가 컷 설계의 목적이 되어서는 안 됨
- 승인 전 공간 검수 미리보기(spatial-preview HTML): <run-dir>/proposed_storyboard_plan_spatial_preview.html | 구조화 spatial_contract 없음
- 승인 전 공간 검수 결과(spatial-check): pass/fail, structured pages: ..., issues: ...

| id | 파일명 | 장면 | 만화적 장면 목적 | 독자 경험/감정 리듬 | location_id/고정 랜드마크 | 페이지 구성 | 컷 수 | 컷 형태/여백 | 디테일/강약/효과선 연출 | 텍스트 정책/SFX | 캐릭터/외형/문자 고정 조건 | 공간/동선/상태유지/spatial_contract 검수 포인트 |
| ... |

승인 후 진행 방식:
- 1단계: 만화 페이지 러프 블로킹 + 공간 검수 보조 storyboard_blocking
- 각 페이지는 $create-comic-storyboard-blocking subagent가 생성/1차 검수하되, 새 run은 기본적으로 한 번에 한 페이지만 순차 예약한다.
- 두 번째 페이지부터는 같은 stage에서 parent-inspection을 통과한 이전 페이지 이미지들을 모두 `Required image attachments` / `Prior page continuity references`로 함께 첨부해 연속성과 일관성을 유지한다.
- 각 stage의 첫 페이지는 이후 페이지의 수준을 정하는 stage-level anchor다. 첫 페이지가 parent-inspection을 통과한 뒤 `anchor-review`를 통과해야 같은 stage의 두 번째 페이지 이후를 예약한다.
- 1단계 이미지는 먼저 승인된 만화 페이지의 패널 구도, 장면 리듬, 독자 시선 흐름을 보존한다. 중요한 캐릭터/오브젝트/환경 1개당 펜으로 3초 정도 빠르게 그린 수준의 러프 형체를 사용하고, 사람/손에 든 물체/움직이는 물체/기준 랜드마크/가림 요소/벽/문/차량/가구/소품처럼 무엇인지 알아볼 수 있어야 한다. 위치/방향/벡터/관계 선, 화살표, 시선/방향선, 이동 궤적선, 가림/차단 표시는 검수에 필요한 만큼만 추가한다. 중요하지 않은 소품/배경 요소는 스토리 판독, 액션 판독, 가림/차단, 랜드마크 연속성, 페이지 구성에 필요하지 않으면 단순화하거나 생략한다. 같은 이름의 `<page_stem>_desc.md`를 반드시 작성하고, `*_desc.md`는 runner 필수 heading은 그대로 유지하되 본문 설명은 한국어로 작성
- 부모 세션 최종 검수
- 모든 페이지 1단계 부모 검수 후 stage-review
- 1단계 stage-review 통과 후 runner가 생성한 `feedback_requests/storyboard_blocking_to_storyboard_sketch_ink.json`과 1단계 산출물을 사용자에게 보고하고, sketch/ink 진행 여부를 반드시 별도로 확인
- blocking 사용자 피드백 게이트 선택지: 그대로 sketch/ink 승인(`approve-next-stage --feedback-request ... --feedback-choice approve_sketch_ink`) | 수정 UI 열기 또는 에이전트 좌표 마킹 생성(`$review-image-overlays`) | 현재 단계에서 중단(`stop-after-stage`)
- approve-next-stage 전에는 storyboard_sketch_ink 예약 금지. `stage-review`, `approve-next-stage`, sketch/ink `next-batch`를 같은 병렬 실행이나 같은 사용자 응답 없이 연속 실행하지 않는다.
- 사용자가 승인하면 2단계: 스케치/펜선 storyboard_sketch_ink
- 2단계는 $create-comic-storyboard-sketch-ink subagent가 현재 페이지의 parent-inspected blocking 이미지와 `*_desc.md`, 그리고 이전 페이지들의 inspected sketch/ink 이미지를 필수 입력으로 사용
- 2단계 모든 페이지 부모 검수와 stage-review 통과 후 runner가 생성한 `feedback_requests/storyboard_sketch_ink_to_finish.json`과 2단계 산출물을 사용자에게 보고하고, finish 진행 여부를 반드시 별도로 확인
- 처음 페이지 계획 승인, blocking 이후 sketch/ink 승인, 2단계 이후 finish 승인은 모두 별개의 승인이다. 초기 "승인"이나 blocking 승인을 다음 단계 승인으로 재사용하지 않는다.
- sketch/ink 사용자 피드백 게이트 선택지: 그대로 finish 승인(`approve-next-stage --feedback-request ... --feedback-choice approve_finish`) | 수정 UI 열기 또는 에이전트 좌표 마킹 생성(`$review-image-overlays`) | 현재 단계에서 중단(`stop-after-stage`)
- approve-next-stage 전에는 finish 예약 금지. `stage-review`, `approve-next-stage`, finish `next-batch`를 같은 병렬 실행이나 같은 사용자 응답 없이 연속 실행하지 않는다.
- 사용자가 중단하면 stop-after-stage로 스케치/펜선 산출물까지만 완료 처리
- 사용자 또는 에이전트가 수정을 요청하면 `$review-image-overlays`로 색상별 오버레이 PNG/TXT와 `revision_requests.json`을 저장하고, `request-revisions`로 해당 페이지를 rerun 처리
- 사용자가 승인하면 3단계: 톤/채색/마무리 finish
- 3단계는 $create-comic-storyboard-finish subagent가 생성/1차 검수
- 3단계는 현재 페이지의 parent-inspected storyboard_sketch_ink 이미지, blocking `*_desc.md` 공간/시간 잠금, 그리고 이전 페이지들의 inspected finish 이미지를 필수 입력으로 사용
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
  "spatial_continuity_plan": {
    "scope": "single recurring corridor set across pages 1-3",
    "locations": [
      {
        "id": "main_corridor",
        "name": "Main corridor",
        "layout_summary": "Long interior passage with entrance near foreground, window light on the right wall, folding screen at mid-depth, and exit marker on the far wall.",
        "camera_axis": "depth runs from lower-left foreground toward upper-right far wall",
        "lighting": "right-wall window is the stable light source",
        "fixed_landmarks": [
          {"id": "entrance_frame", "description": "near foreground doorway", "relative_position": "near-left foreground"},
          {"id": "folding_screen", "description": "mid-depth partial occluder", "relative_position": "middle corridor"},
          {"id": "window_light", "description": "right-wall window light", "relative_position": "right wall"},
          {"id": "exit_marker", "description": "far-wall destination marker", "relative_position": "far wall"}
        ]
      }
    ],
    "continuity_rules": [
      "same location_id keeps the same physical set and landmark relations even when cropped",
      "do not move the exit_marker to another wall without an explicit page transition or cause"
    ],
    "allowed_changes": ["door may open after a panel action causes it"]
  },
  "pages": [
    {
      "id": "001-corridor-arrival",
      "filename": "001-corridor-arrival.png",
      "page_no": 1,
      "scene_refs": ["S01"],
      "location_id": "main_corridor",
      "location_continuity": {
        "location_id": "main_corridor",
        "zone": "entrance-to-mid-corridor",
        "camera_axis": "matches main_corridor depth axis",
        "fixed_landmarks_visible": ["entrance_frame", "folding_screen", "window_light", "exit_marker"],
        "offscreen_landmarks": [],
        "must_preserve": ["exit_marker remains on far wall", "window_light remains on right wall"],
        "changes_from_previous_page": [],
        "location_transition": ""
      },
      "layout_brief": "Three-panel cinematic page with a wide establishing panel, diagonal action panel, and close reaction panel.",
      "narrative_plan": {
        "story_function": "Establish the protagonist's arrival and the quiet corridor mood.",
        "reader_experience": "The reader feels a calm setup before the important movement begins.",
        "pacing_intent": "One wide breath, one movement beat, one reaction beat.",
        "composition_intent": "Design a readable comic page first; spatial validation is extracted afterward."
      },
      "reading_order": "top-to-bottom, left-to-right",
      "text_policy": "dialogue_sfx_captions",
      "pacing_notes": "3-5 panels by default; 1-2 panels only for special staging.",
      "panel_shape_notes": "Experimental freeform panel composition.",
      "negative_space_notes": "Leave breathing room around key faces, hands, action, balloons, and SFX.",
      "detail_density_notes": "Detail focal characters, props, hands, and faces; simplify low-priority background.",
      "visual_emphasis_notes": "Use stronger line weight and contrast on the focal beat.",
      "comic_effects_notes": "Use effect lines only where they clarify action, emotion, impact, speed, or eye guidance.",
      "spatial_logic_notes": "Exit marker remains on the far wall; the rolling object moves toward the marker.",
      "motion_checks": ["moving object path follows the approved direction toward the landmark"],
      "must_match": [
        "three readable panels",
        "no impossible moving-object direction",
        "two-eyed characters must not look one-eyed unless explicitly approved"
      ],
      "spatial_contract_extraction": {
        "derived_from": "narrative_plan_and_panels",
        "verification_purpose": "Validate moving-object path, landmark relation, visibility/occlusion, and state continuity after the comic page design is chosen.",
        "must_not_override_page_design": true,
        "focus": ["moving object path", "exit marker landmark relation", "occluding element placement", "protagonist state continuity"]
      },
      "spatial_contract": {
        "coordinate_space": {
          "type": "panel_screen_2d",
          "origin": "top_left",
          "x_axis": "right",
          "y_axis": "down",
          "units": "normalized 0..1 or consistent scene units"
        },
        "entities": [
          {
            "id": "protagonist",
            "type": "character",
            "role": "main subject",
            "blocking_symbol": {"shape": "rough_gesture_silhouette", "tone": "loose black line", "meaning": "protagonist 3-second standing pose"}
          },
          {
            "id": "rolling_object",
            "type": "object",
            "role": "moving object",
            "blocking_symbol": {"shape": "small_rough_box_on_wheels", "tone": "hollow", "meaning": "small rolling object"}
          },
          {
            "id": "exit_marker",
            "type": "landmark",
            "role": "destination landmark",
            "blocking_symbol": {"shape": "rough_wall_marker", "tone": "gray outline", "meaning": "far-wall destination marker"}
          },
          {
            "id": "folding_screen",
            "type": "object",
            "role": "occluding element",
            "blocking_symbol": {"shape": "rough_vertical_screen", "tone": "gray block", "meaning": "partial visual barrier"}
          },
          {
            "id": "window_light",
            "type": "landmark",
            "role": "visibility source",
            "blocking_symbol": {"shape": "rough_bright_window", "tone": "light outline", "meaning": "background light source"}
          }
        ],
        "panel_snapshots": [
          {
            "panel": 1,
            "entities": [
              {
                "id": "protagonist",
                "position": [0.25, 0.68],
                "facing_vector": [1, -0.15],
                "pose": "standing and looking down the corridor",
                "cover": "none",
                "visibility": "visible",
                "occlusion": "none",
                "location_anchor": "near corridor entrance",
                "held_props": [],
                "state_tags": ["watching"]
              },
              {"id": "rolling_object", "position": [0.34, 0.62], "trajectory_vector": [1, -0.1], "state_tags": ["moving"]},
              {"id": "exit_marker", "position": [0.82, 0.36], "location_anchor": "far wall"},
              {"id": "folding_screen", "position": [0.50, 0.58], "occlusion": "between protagonist and window_light"},
              {"id": "window_light", "position": [0.75, 0.58], "location_anchor": "right wall"}
            ]
          }
        ],
        "constraints": [
          {"id": "rolling-object-to-exit-marker", "type": "trajectory_to", "panel": 1, "object": "rolling_object", "target": "exit_marker", "origin_entity": "protagonist", "destination_entity": "exit_marker"},
          {"id": "exit-marker-right-of-protagonist", "type": "right_of", "panel": 1, "subject": "exit_marker", "anchor": "protagonist"},
          {"id": "screen-between-protagonist-and-window-light", "type": "cover_between", "panel": 1, "actor": "protagonist", "cover": "folding_screen", "source": "window_light"},
          {
            "id": "protagonist-state-carries-from-prior-panel",
            "type": "state_persists_from",
            "panel": 1,
            "entity": "protagonist",
            "reference_page": "001-corridor-arrival",
            "reference_panel": 1,
            "state_fields": ["cover", "visibility", "location_anchor"]
          },
          {
            "id": "approved-rolling-transition",
            "type": "allowed_transition",
            "entity": "rolling_object",
            "from_page": "001-corridor-arrival",
            "from_panel": 1,
            "to_page": "001-corridor-arrival",
            "to_panel": 1,
            "cause_page": "001-corridor-arrival",
            "cause_panel": 1
          }
        ]
      },
      "panels": [
        {
          "panel_no": 1,
          "beat": "The protagonist enters the quiet corridor.",
          "visual_brief": "Wide establishing panel of a quiet interior passage.",
          "characters": ["protagonist"],
          "action": "Standing near the entrance, watching a small rolling object move toward the far marker.",
          "composition": "entrance frame foreground, destination marker in distance",
          "source_dialogue": ["It's quiet in here."],
          "adapted_dialogue": ["...조용하네."],
          "sfx": ["끼익"],
          "caption": ["늦은 오후, 복도."],
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

`scene_3d` validation mode uses the same narrative-first extraction flow. Use it by default for spatially important pages where height, floor, connected-location, camera continuity, object state, or recurring-set continuity matters. Use `panel_screen_2d` instead only when the page is primarily a graphic/UI shot, symbolic panel, emotion closeup, text/SFX layout, or another case where 3D inference would add false constraints:

```json
{
  "spatial_continuity_plan": {
    "scene_3d_scenes": [
      {
        "id": "building_main",
        "status": "provisional",
        "usage": "validation_only",
        "units": "meters",
        "origin": "building_ground_floor_center",
        "axes": {"x": "east", "y": "north", "z": "up"},
        "levels": [
          {"id": "floor_1", "label": "1층", "z_range": [0, 3]},
          {"id": "floor_2", "label": "2층", "z_range": [3, 6]}
        ],
        "locations": [
          {"id": "floor_1_lobby", "level_id": "floor_1"},
          {"id": "floor_2_balcony", "level_id": "floor_2"}
        ],
        "fixed_entities": [
          {"id": "stairs", "type": "landmark", "position": [0, 1.5, 0]},
          {"id": "balcony_railing", "type": "landmark", "position": [0, 0.5, 3.2]}
        ],
        "reconciliation_policy": {
          "mode": "adjust_soft_geometry_preserve_hard_invariants",
          "first_panel_calibration_weight": "high"
        }
      }
    ]
  },
  "pages": [
    {
      "id": "001-two-level-lobby",
      "spatial_contract": {
        "coordinate_space": {
          "type": "scene_3d",
          "usage": "validation_only",
          "scene_id": "building_main",
          "location_id": "floor_1_lobby"
        },
        "locks": [
          {"id": "hero-floor-lock", "type": "hard", "source": "page_plan", "rule": "hero remains on floor_1"},
          {"id": "camera-fov", "type": "soft", "source": "model_inferred", "rule": "camera FOV may reconcile to match the approved comic panel"}
        ],
        "panel_snapshots": [
          {
            "panel": 1,
            "location_id": "floor_1_lobby",
            "camera": {"position": [-3, -4, 1.6], "look_at": [0, 0.5, 2.2], "fov": 45},
            "entities": [
              {"id": "hero", "position": [0, -1, 0], "level_id": "floor_1"},
              {"id": "villain", "position": [0, 0.7, 3.4], "level_id": "floor_2"}
            ]
          }
        ],
        "transitions": [],
        "constraints": [
          {"id": "hero-on-floor-1", "type": "on_level", "panel": 1, "entity": "hero", "level": "floor_1"},
          {"id": "villain-above-hero", "type": "above", "panel": 1, "subject": "villain", "anchor": "hero"},
          {"id": "floor-readability", "type": "visual_evidence_required", "panel": 1, "evidence": ["balcony railing separates floor_2 from floor_1"]}
        ]
      }
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
# Before presenting the approval request, save the proposed plan under the run folder.
python3 "$RUNNER" spatial-check --plan-file <run-dir>/proposed_storyboard_plan.json
python3 "$RUNNER" spatial-preview --plan-file <run-dir>/proposed_storyboard_plan.json
# After explicit user approval, approve the same plan or the user-revised plan.
python3 "$RUNNER" approve-plan --run-dir <run-dir> --plan-file <run-dir>/proposed_storyboard_plan.json
```

`approve-plan` automatically runs `spatial-check` against every page with `spatial_contract`. Unknown entities, unsupported constraints, target-opposite direction vectors, forbidden firing/aim vectors, impossible moving-object paths, missing occluding elements between related subjects/sources, cover `screen_box` misses, non-firing pressure without `no_line_of_fire`, fixed-landmark relation drift, visibility/occlusion or state persistence drift, missing allowed-transition causes, and hard `scene_3d` invariant failures fail before any generation is reserved. `scene_3d` soft/inferred lock differences are warnings for later inspection/reconciliation, not plan-approval blockers. This validation checks the approved comic page design; it must not become the driver for page or panel composition. Legacy plans without `spatial_contract` remain valid and continue to use free-form `spatial_logic_notes`, `motion_checks`, and `must_match`.

When a top-level `spatial_continuity_plan` is present, `spatial-check` also verifies that every page declares a known `location_id`, references known fixed landmarks through `location_continuity`, and records an explicit `location_transition` or `transition_from_previous` when the location changes. This is a pre-page setting-continuity gate, separate from `spatial_contract`: it prevents accidental room/corridor/street drift before generation while still leaving panel composition narrative-first.

`spatial-preview` writes a read-only static HTML inspection page for `spatial_contract` positions, vectors, cover/line-of-sight relations, landmark/state continuity constraints, and the current `spatial-check` pass/fail issues plus warnings. When `scene_3d` is present, the same file includes a dependency-free orbit-capable canvas preview for level/camera/snapshot/transition/lock data: the default view is top-down for distance/line-of-fire inspection, drag rotates, shift-drag or middle-drag pans, wheel zooms, preset buttons reset to top/front/side/camera views, and optional `Sync scene view` keeps enabled previews with the same `scene_id` aligned. The canvas uses short key labels by default, supports `key/all/off` label modes, collision-avoids labels with leader lines, shows a compact status strip and z-level rail, links legend/constraint hover targets back to the canvas, draws preview-only wireframe boxes for major buildings/vehicles/walls/slabs/cover, uses oriented wedges for actors or moving objects, and overlays dotted relationship/trajectory/blocked-line guides. Level planes are bounded to the active/referenced entity footprint for that level instead of spanning the whole battlefield, so building interiors, upper floors, streets, and ramps do not visually collapse into one floor. Layer filters let reviewers choose actors, obstacles, landmarks, relations, vectors, camera, ghost panels, and levels so the tactical context remains readable. Optional `preview_geometry` on fixed entities, spatial-contract entities, or panel snapshot entities may define `shape`, `size`, `yaw_degrees`, `anchor`, and `style`; when absent, the preview infers a conservative footprint from id/type/role. `preview_geometry`, wireframes, direction shapes, dotted overlays, and filters are inspection-only helpers; they do not affect `spatial-check` hard validation and are not generation references. For `scene_3d` pages, the old 2D SVG projection is not rendered because raw x/y world coordinates are not a meaningful panel-screen projection. This is a lightweight validation projection, not WebGL, Three.js, mesh rendering, or a generation reference. Use `--plan-file`, `--plan-json --output <html>`, or `--run-dir`; the default output is `<plan-stem>_spatial_preview.html` for plan files or `<run-dir>/spatial_contract_preview.html` for approved runs.

Optional single-stage targets:

```bash
python3 "$RUNNER" approve-plan --run-dir <run-dir> --plan-file <approved-plan.json> --target-stage storyboard_blocking
python3 "$RUNNER" approve-plan --run-dir <run-dir> --plan-file <approved-plan.json> --target-stage storyboard_sketch_ink
python3 "$RUNNER" approve-plan --run-dir <run-dir> --plan-file <approved-plan.json> --target-stage finish
```

Reserve and process a sequential page batch:

```bash
python3 "$RUNNER" next-batch --run-dir <run-dir> --limit 1
# Spawn one fork_context=true subagent for the printed item.
# Use the printed SUBAGENT_PROMPT_FILE content as the subagent task.
# Attach every printed VISUAL_REFERENCE_IMAGE as a local image item when spawning the subagent.
python3 "$RUNNER" import --run-dir <run-dir> --item <page> --stage storyboard_blocking --generated <generated-path> --description <page_stem>_desc.md --worker-status pass --worker-note "<subagent note>"
python3 "$RUNNER" inspect-pass --run-dir <run-dir> --item <page> --stage storyboard_blocking --note "<parent inspection note>" --spatial-verdict pass --spatial-note "<spatial/temporal contract visual inspection pass>"
python3 "$RUNNER" anchor-review --run-dir <run-dir> --stage storyboard_blocking --item <first-page> --status pass --note "<stage-level blocking anchor pass>"
python3 "$RUNNER" inspect-pass --run-dir <run-dir> --item <page> --stage storyboard_blocking --note "<parent inspection note>" --spatial-verdict needs_rerun --spatial-note "<spatial/temporal contradiction found>"
python3 "$RUNNER" anchor-review --run-dir <run-dir> --stage storyboard_blocking --item <first-page> --status needs_rerun --note "<stage level mismatch>" --issue "<issue>"
python3 "$RUNNER" rerun --run-dir <run-dir> --item <page> --stage storyboard_blocking --note "<reason>"
python3 "$RUNNER" batch-status --run-dir <run-dir> --batch-id <batch-id>
```

For each stage in a new `sequential_prior_pages` run, page 1 follows `next-batch -> subagent -> import -> inspect-pass -> anchor-review -> next-batch page 2`. If `next-batch` prints `STAGE_ANCHOR_REVIEW_REQUIRED`, do not spawn page 2 yet; inspect the first page as the stage-level anchor and run `anchor-review`.

After every page in `storyboard_blocking` passes parent inspection:

```bash
python3 "$RUNNER" stage-review --run-dir <run-dir> --stage storyboard_blocking --status pass --note "<blocking spatial/temporal continuity pass>"
```

This sets `stage_gates.storyboard_blocking_to_storyboard_sketch_ink.status` to `pending_user_feedback` and writes:

```text
<run-dir>/feedback_requests/storyboard_blocking_to_storyboard_sketch_ink.json
<run-dir>/feedback_requests/storyboard_blocking_to_storyboard_sketch_ink.md
```

At that point report the blocking-stage image/desc outputs and the feedback request path to the user, then wait for the user's explicit next-stage choice. Do not reserve sketch/ink with `next-batch` until `approve-next-stage` has consumed the runner-generated feedback request.

Offer exactly these feedback choices:

- Approve next stage: continue to `storyboard_sketch_ink` with `approve-next-stage --feedback-request <json> --feedback-choice approve_sketch_ink`.
- Open revision UI or create agent markup: use `$review-image-overlays` against `--stage storyboard_blocking` to collect color-coded overlay requests.
- Stop after stage: keep only `storyboard_blocking` with `stop-after-stage`.

If the user approves sketch/ink:

```bash
python3 "$RUNNER" approve-next-stage --run-dir <run-dir> --from-stage storyboard_blocking --to-stage storyboard_sketch_ink --feedback-request <run-dir>/feedback_requests/storyboard_blocking_to_storyboard_sketch_ink.json --feedback-choice approve_sketch_ink --note "<user approved sketch/ink>"
python3 "$RUNNER" next-batch --run-dir <run-dir> --limit 1
```

If the user wants the blocking revision UI:

```bash
REVIEW_SKILL_DIR=".agents/skills/review-image-overlays"
REVIEW_RUNNER="$REVIEW_SKILL_DIR/scripts/review_overlay_server.py"
python3 "$REVIEW_RUNNER" serve --run-dir <run-dir> --stage storyboard_blocking
```

Import blocking revision overlays the same way as later stages:

```bash
python3 "$RUNNER" request-revisions --run-dir <run-dir> --review-manifest <run-dir>/review_overlays/storyboard_blocking/<review-id>/revision_requests.json
python3 "$RUNNER" next-batch --run-dir <run-dir> --limit 1
```

The approved next batch is `storyboard_sketch_ink`. Import/inspect it the same way, except no `--description` is used:

```bash
python3 "$RUNNER" import --run-dir <run-dir> --item <page> --stage storyboard_sketch_ink --generated <generated-path> --worker-status pass --worker-note "<subagent note>"
python3 "$RUNNER" inspect-pass --run-dir <run-dir> --item <page> --stage storyboard_sketch_ink --note "<parent inspection note>" --spatial-verdict pass --spatial-note "<spatial/temporal contract visual inspection pass>"
python3 "$RUNNER" anchor-review --run-dir <run-dir> --stage storyboard_sketch_ink --item <first-page> --status pass --note "<stage-level sketch/ink anchor pass>"
```

After every page in `storyboard_sketch_ink` passes parent inspection:

```bash
python3 "$RUNNER" stage-review --run-dir <run-dir> --stage storyboard_sketch_ink --status pass --note "<source consistency and continuity pass>"
```

This sets `stage_gates.storyboard_sketch_ink_to_finish.status` to `pending_user_feedback` and writes:

```text
<run-dir>/feedback_requests/storyboard_sketch_ink_to_finish.json
<run-dir>/feedback_requests/storyboard_sketch_ink_to_finish.md
```

At that point report the sketch/ink-stage outputs and the feedback request path to the user, then wait for the user's explicit next-stage choice. The original page-plan approval is not a finish approval.

Offer exactly these feedback choices:

- Approve next stage: continue to `finish` with `approve-next-stage --feedback-request <json> --feedback-choice approve_finish`.
- Open revision UI or create agent markup: use `$review-image-overlays` to collect color-coded overlay requests.
- Stop after stage: keep only `storyboard_sketch_ink` with `stop-after-stage`.

Do not run `approve-next-stage` in the same tool call, parallel group, or assistant turn as the `stage-review` unless the user has explicitly answered this feedback request after seeing the sketch/ink-stage outputs. Do not reserve finish with `next-batch` until `approve-next-stage` has consumed the runner-generated feedback request.

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
python3 "$RUNNER" next-batch --run-dir <run-dir> --limit 1
```

`request-revisions` resets the affected page stage to `pending`, records the color-specific overlay PNG/TXT paths and request text, resets stage-review and following gates, and injects a `User revision overlays` section into the next prompt/subagent prompt. Use the color-specific overlay files as canonical instructions; the combined overlay is only for quick visual review.

If the user approves finish:

```bash
python3 "$RUNNER" approve-next-stage --run-dir <run-dir> --from-stage storyboard_sketch_ink --to-stage finish --feedback-request <run-dir>/feedback_requests/storyboard_sketch_ink_to_finish.json --feedback-choice approve_finish --note "<user approved finish>"
python3 "$RUNNER" next-batch --run-dir <run-dir> --limit 1
python3 "$RUNNER" import --run-dir <run-dir> --item <page> --stage finish --generated <generated-path> --worker-status pass --worker-note "<subagent note>"
python3 "$RUNNER" inspect-pass --run-dir <run-dir> --item <page> --stage finish --note "<parent inspection note>" --spatial-verdict pass --spatial-note "<spatial/temporal contract visual inspection pass>"
python3 "$RUNNER" anchor-review --run-dir <run-dir> --stage finish --item <first-page> --status pass --note "<stage-level finish anchor pass>"
```

If the user stops after sketch/ink:

```bash
python3 "$RUNNER" stop-after-stage --run-dir <run-dir> --stage storyboard_sketch_ink --note "<user stops before finish>"
```

For finish-only runs with an external sketch/ink image:

```bash
python3 "$RUNNER" import-prior-stage --run-dir <run-dir> --item <page> --stage storyboard_sketch_ink --generated <sketch-ink-image> --note "<external prior reference>"
python3 "$RUNNER" stage-review --run-dir <run-dir> --stage storyboard_sketch_ink --status pass --note "<external prior stage accepted>"
python3 "$RUNNER" approve-next-stage --run-dir <run-dir> --from-stage storyboard_sketch_ink --to-stage finish --feedback-request <run-dir>/feedback_requests/storyboard_sketch_ink_to_finish.json --feedback-choice approve_finish --note "<user approved finish>"
python3 "$RUNNER" next-batch --run-dir <run-dir> --limit 1
```

## State Rules

- `approve-plan` is the only transition from approval-gated planning into generation-ready state.
- `target_stages` defaults to `["storyboard_blocking", "storyboard_sketch_ink", "finish"]`.
- Existing already-approved legacy states keep their recorded `target_stages`; they are not force-migrated into blocking.
- New approved runs default to `page_generation_mode: sequential_prior_pages`; already-approved legacy states without this field are treated as `parallel_batch`.
- `storyboard_blocking` must finish parent inspection and stage-review before default `storyboard_sketch_ink` reservation.
- `storyboard_sketch_ink` also requires `approve-next-stage` with the active runner-generated `storyboard_blocking_to_storyboard_sketch_ink` feedback request and `--feedback-choice approve_sketch_ink`; blocking stage-review pass alone is not enough.
- `storyboard_blocking` imports require `--description <desc.md>`, and the runner validates required headings plus all active entity/constraint ids. Required heading text stays fixed, but the description body must be written in Korean.
- `storyboard_sketch_ink` must finish parent inspection and stage-review before `finish`.
- `finish` also requires `approve-next-stage` with the active runner-generated feedback request and `--feedback-choice approve_finish`; stage-review pass or parent-only note is not enough.
- `stop-after-stage` changes the completion target to the requested completed stage.
- `finish` requires a parent-inspected or imported prior `storyboard_sketch_ink` image.
- `next-batch --limit 1` reserves one eligible page in `sequential_prior_pages` mode and writes both `prompts/<stage>/...prompt.txt` and `subagent_prompts/<stage>/...subagent.txt`. Legacy `parallel_batch` states may still reserve up to four pages.
- `next-batch` records `visual_reference_paths` on the page stage and prints one `VISUAL_REFERENCE_IMAGE: <absolute path>` line per image that must be attached as a local image item when spawning the subagent.
- In `sequential_prior_pages` mode, page N waits for pages 1..N-1 in the same stage to pass parent inspection before reservation. If an earlier page is rerun, later generated/imported/passed pages in that same stage are reset to rerun-pending because their continuity references may be stale.
- In `sequential_prior_pages` mode, page 2 or later also waits for the same stage's first page to pass `anchor-review`. The runner records this in `stage_anchor_reviews` and injects `Stage level anchor reference` into prompts/subagent prompts.
- Use `anchor-review --status pass` only after the first page has passed parent `inspect-pass`. Use `anchor-review --status needs_rerun` when the first page is too rough, too polished, or otherwise mismatched for the stage level; this routes the first page back to rerun and resets same-stage review/following gates.
- `next-batch` injects the top-level `spatial_continuity_plan` and the page's `location_continuity` before narrative-first page design, so subagents keep the same physical set, fixed landmarks, entrances/exits, camera axis, lighting, and allowed page-to-page changes before applying page-specific composition.
- `next-batch` injects narrative-first page design, spatial validation overlay, and `spatial_contract` summaries into the stage prompt and subagent prompt. Generated images must preserve the approved comic page design first, then preserve entity positions, vectors, visibility/occlusion, threat/viewpoint-based cover, line-of-sight, trajectory, negative firing/aim constraints, landmark-relation constraints, temporal state constraints, and `scene_3d` hard locks as validation constraints.
- In `scene_3d validation_only` mode, prompts must explicitly say that hard locks are rerun criteria, soft/inferred geometry may reconcile after parent inspection, and the first panel can act as a calibration anchor. Do not attach 3D render images as `VISUAL_REFERENCE_IMAGE` for this mode.
- Do not reserve a new batch while any page stage is `generation_requested` or `imported`.
- Subagent inspection is advisory. Only the parent session may run `inspect-pass`.
- Parent `inspect-pass --spatial-verdict needs_rerun` never marks the page passed; it routes the page back to `pending` rerun and resets stage review / following gates.
- Parent `inspect-pass --spatial-verdict reconciled --reconciliation-note "<note>"` marks the page passed while recording `spatial_reconciliations[]`. Use this only when hard invariants pass and the generated storyboard should calibrate soft/inferred `scene_3d` geometry without harming the approved page plan or prior continuity.
- `request-revisions --review-manifest <revision_requests.json>` imports `$review-image-overlays` feedback, marks affected page stages `pending`/`rerun_pending`, resets stage-review and following gates, and adds overlay PNG/TXT paths plus request text to the next rerun prompt.
- `$review-image-overlays create-markup` is valid for subagent self-verification and parent comprehensive verification when the issue can be localized with rect/polygon coordinates; it must still flow through `request-revisions`.
- If a subagent returns `completed:null`, no final message, or no generated path, do not invent an import path. Route the page to `rerun`.
- Rerun resets the relevant stage review and any following stage gate.

## Parent Verification

Inspect every imported page before marking it passed. Check page id, stage, panel count, reading order, layout brief, text policy, character locks, character appearance/anatomy locks, visual text guard, source consistency, pre-page `spatial_continuity_plan` / `location_continuity` compliance, structured `spatial_contract` compliance, temporal continuity, spatial continuity, motion plausibility, visual emphasis, effect-line direction, technical quality, and output filename mapping.

For `storyboard_blocking`, inspect both the generated PNG and sibling `*_desc.md`. Reject missing required description headings, non-Korean description body text, missing entity ids, missing constraint ids, meaningless pure-symbol blocking that makes entities impossible to identify, over-detailed/final-art rendering, or semantic labels drawn into the image instead of the Markdown description.

For a stage first page in `sequential_prior_pages`, perform `anchor-review` after parent inspection and before reserving page 2. The anchor check verifies stage level, not just local correctness: `storyboard_blocking` must stay rough comic-page blocking with recognizable 3-second forms and no final-art polish; `storyboard_sketch_ink` must preserve blocking while adding real sketch/ink line art without tone/color/final finish; `finish` must preserve sketch/ink structure while adding tone/color/final polish without redraw. All anchor checks also include text policy, character locks, character appearance/anatomy, visual text guard, `spatial_contract`, and page-to-page continuity.

When `spatial_continuity_plan` is active, inspect every generated page against the approved physical set before judging page-specific `spatial_contract`: same `location_id` must keep the same room/corridor/street, wall relationships, entrances/exits, windows, furniture layout, fixed landmarks, lighting sources, and allowed state changes. Reject pages that silently redraw the same `location_id` as a different space, move a fixed landmark to another wall/side/depth, duplicate or remove a required landmark without `offscreen_landmarks` or an approved crop, or change location without `location_transition`.

When a page has `spatial_contract`, inspect against every entity, panel snapshot, vector, visibility/occlusion, temporal state field, and constraint. Reject target-opposite direction vectors, forbidden firing/aim vectors, moving-object paths that do not move toward the approved destination, occluding elements that are not between the required subjects/sources, `behind_cover_from` that only works from reader POV, forbidden exposure around cover, subjects that were specified as hidden but appear exposed, broken line-of-sight blocking, left/right relation flips, fixed landmark relation drift, a partial occluding element turning into a different barrier without cause, and pose/cover/location/held-prop/state-tag drift without an `allowed_transition`. Record the result with `--spatial-verdict` and `--spatial-note`.

When `spatial_contract.coordinate_space.type` is `scene_3d`, inspect hard invariants before judging soft geometry: level/floor membership, above/below relation, vertical separation, location continuity, transition causes, object state changes, and visual evidence such as balcony/railing/stair cues. Rerun hard failures. If the generated storyboard preserves the approved page design and hard invariants but differs from soft/inferred model-estimated details, record a `reconciled` verdict and describe the calibrated geometry in `--reconciliation-note`.

Character appearance/anatomy is an independent reject criterion, not just a technical-quality note. Unless explicitly approved by the plan or source, rerun pages with missing/extra/merged eyes, one-eyed appearance for a two-eyed character, one-eyed face unless explicitly approved, missing/extra limbs or fingers, changed species/body type, broken joints, or broken body proportions.

For `storyboard_sketch_ink`, verify that sketch/ink preserved the inspected rough comic-page blocking PNG, approved panel design, and `*_desc.md` spatial validation overlay while adding real drawing detail.

For `finish`, verify that tone/color/final polish preserved the inspected `storyboard_sketch_ink` layout, panel shapes, negative space, text placement or required text absence, line-weight rhythm, visual emphasis, effect lines, character/object blocking, blocking `*_desc.md` spatial validation overlay, structured spatial contract, eye/face/hand/limb/silhouette/body proportion/posture structure, movement direction, and action logic.

Do not claim page coverage, text quality, continuity, spatial logic, or stage quality unless the image was inspected.

## Reporting

After each batch or gate, report in Korean:

```text
[만화 콘티 팩 진행 결과]
- 줄거리/시나리오: ...
- 저장 폴더: ...
- 상태 파일: ...
- 대상 단계(target_stages): ...
- 현재 단계: storyboard_blocking | storyboard_sketch_ink | finish | complete
- 승인된 페이지 수: ...
- 이번 병렬 그룹: ...
- worker 검수 결과: ...
- 부모 검수 결과: ...
- 텍스트 정책 검수: ...
- 캐릭터 고정 조건 검수: ...
- 캐릭터 외형/해부 검수: ...
- 이미지 내 문자 방지 검수: ...
- 사전 공간 설계/고정 랜드마크 검수: ...
- 공간/동선/상태유지 검수: ...
- 단계 마무리 검수 결과: ...
- 다음 단계 사용자 피드백 게이트: storyboard_blocking_to_storyboard_sketch_ink 또는 storyboard_sketch_ink_to_finish = pending_user_feedback | approved | stopped
- 피드백 요청 파일: <run-dir>/feedback_requests/<from_stage>_to_<to_stage>.json
- 보완 대상 페이지: ...
- 다음 결정: approve-next-stage --feedback-request ... --feedback-choice approve_sketch_ink 또는 approve_finish로 다음 단계 진행 | $review-image-overlays로 수정 UI 열기/에이전트 마킹 생성 | stop-after-stage로 종료
```
