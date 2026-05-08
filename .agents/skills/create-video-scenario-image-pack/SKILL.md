---
name: create-video-scenario-image-pack
description: Use when a video script, storyboard, shot list, or scene brief needs non-character production image sources such as locations, spatial anchors, props, inserts, environmental details, mood keys, or continuity references.
---

# Create Video Scenario Image Pack

## Core Rule

Create a resumable, approved image-source pack for video generation. Default outputs are non-character sources only: locations, spatial anchors, props, inserts, environmental details, mood keys, and continuity references.

Do not generate images before the user approves the exact source list and any web reference images that will be used.

## Runner

Use `[스킬 경로]/scripts/video_scenario_image_pack_runner.py` for this workflow. `[스킬 경로]` means the directory that contains this `SKILL.md`, not the checkout root.

```bash
SKILL_DIR=".agents/skills/create-video-scenario-image-pack"
RUNNER="$SKILL_DIR/scripts/video_scenario_image_pack_runner.py"
python3 "$RUNNER" <command>
```

Do not use the video closeup pack runner; that runner belongs to a different workflow.

## Workflow

1. Save or initialize the scenario run.
   ```bash
   python3 "$RUNNER" init --title "<scenario title>" --scenario <scenario-file>
   ```
2. Extract and deduplicate useful image sources.
3. Search the web for real-world references when useful, download approved candidates under `<run-dir>/web_references/<item-id>/`, and record source/provenance plus observed facts.
4. Ask for approval in Korean with the source list and web reference collection summary.
5. After approval, write `approved_image_plan.json` and approve it:
   ```bash
   python3 "$RUNNER" approve-plan --run-dir <run-dir> --plan-file <approved-plan.json>
   ```
6. Reserve only dependency-ready work:
   ```bash
   python3 "$RUNNER" next-batch --run-dir <run-dir> --limit 4
   python3 "$RUNNER" batch-prompts --run-dir <run-dir> --batch-id <batch-id>
   ```
7. Spawn one subagent per reserved item, maximum four per batch. Each subagent generates exactly one image with `image_gen`. If using `fork_context=true`, omit subagent role fields such as `agent_type` or `role`; put the generation/inspection behavior in the task prompt instead.
8. Import worker results through the runner. Prefer batch manifests over parallel shell calls:
   ```bash
   python3 "$RUNNER" import-batch --manifest <import-manifest.json>
   ```
9. Parent-inspect every imported image before passing it:
   ```bash
   python3 "$RUNNER" inspect-batch-pass --manifest <inspect-manifest.json>
   ```
10. Route failures through rerun. Rerun notes become prompt hints for the next attempt:
   ```bash
   python3 "$RUNNER" rerun --run-dir <run-dir> --item <id-or-filename> --note "<reason>"
   ```
11. Report status in Korean:
   ```bash
   python3 "$RUNNER" report --run-dir <run-dir>
   ```

## Extraction Policy

- Merge repeated needs when one reusable source can cover multiple scenes.
- Split sources when continuity would break: time of day, weather, set dressing, prop design, damage state, camera-critical inserts, or spatially distinct areas.
- Prefer categories: `location_master`, `location_view`, `set_detail`, `prop`, `vehicle`, `insert`, `vfx_plate`, `mood_key`, `spatial_layout`, `continuity_reference`.
- Create one `location_master` or `spatial_layout` continuity anchor per major place before dependent details.
- Use `spatial_group`, `continuity_anchor`, `fixed_layout_notes`, `camera_view`, `must_match`, and `dependencies` for spatial continuity.
- Write `must_match` and `fixed_layout_notes` as verification locks: no tiny human-like marks for non-character outputs, fixed landmark relative positions, approved prop shape/material/scale, damage state, time of day, weather, and set dressing.

## Web Reference Collection

When real-world visual grounding would help, the parent session may search the web before approval. Search broadly across public sources for actual places, facilities, props, vehicles, architecture, weather, time of day, surface materials, streets, shops, courts, fields, and environmental details.

Save downloaded reference images under `<run-dir>/web_references/<item-id>/<reference-id>.<ext>` and record them in each plan item as `web_references`. Each entry must include `id`, `local_path`, `source_url`, `page_url`, `source_title`, `reference_purpose`, `observed_facts`, and `usage_note`.

Web references are factual references only. Use them for shape, spatial layout, material, landmarks, mood, prop state, weather, and time of day. Do not copy source image composition, watermark, logo, people, artist-specific style, brand styling, or copyrighted visual expression. The runner validates that registered files exist under the current run's `web_references/` folder and writes `web_reference_manifest.json`.

## Strict No-Character Policy

Unless the user explicitly approves character-bearing outputs, reject people and human-like artifacts anywhere in the image, including the far background.

Fail and rerun if the image includes pedestrians, players, body parts, hands, faces, silhouettes, crowds, cars, vehicles, bicycles, scooters, posters, signage, window figures, reflections, or tiny vertical marks that read as human figures.

For empty locations, prefer closed-off or simplified backgrounds: blank masonry walls, fence mesh, empty pavement, sky, and stable landmarks. This avoids repeated background silhouette failures.

## Production Source Verification

Treat these as independent rerun criteria, not just technical quality notes:

- No-character artifact lock: for `contains_character=false`, reject tiny human-like marks, human-like reflections, poster/window figures, vehicle silhouettes, background street activity, and any person/body/face/hand/silhouette/crowd-like artifact anywhere in the frame.
- Spatial continuity lock: preserve fixed landmarks from `fixed_layout_notes`, `must_match`, `continuity_anchor`, and parent-inspected references. Reject moved landmarks, swapped building positions, wrong hoop side, wrong entrance side, wrong bench/wall/gate relationship, and fixed landmark relative-position drift.
- Prop/environment state lock: preserve approved prop shape/material/scale, damage state, time of day, weather, set dressing, and camera-critical insert details. Reject changed prop shape/material/scale, wrong damage state, wrong time of day/weather, unapproved set dressing drift, unrelated props, and cropped key subject.

If `contains_character=true`, only the people/character ban is relaxed. Spatial continuity and prop/environment state verification still apply.

## Approval Format

Before generation, present:

```text
[영상 시나리오 이미지 소스 승인 요청]
- 저장 폴더: ...
- 총 이미지 수: ...
- 중복 병합 기준: ...

| id | 파일명 | 장면 | 유형 | 생성 목적 | 핵심 시각 요소 | 의존성 |
| ... |

캐릭터 정책:
- 기본값: 캐릭터/인물 미포함
- 캐릭터 포함 항목: 명시 승인된 항목만

공간 일관성 기준:
- 공간 그룹: ...
- 기준 레이아웃/앵커: ...
- 고정 랜드마크: ...

웹 참고 이미지 수집 결과:
- 검색어/검색 의도: ...
- 수집 이미지 수: ...
- 선택한 출처 URL: ...
- 제외한 후보와 이유: ...
- 생성에 반영할 관찰 포인트: ...

비캐릭터/공간/소품 검수 기준:
- 사람처럼 읽히는 작은 세로 형상, 반사 인물, 포스터/창문 속 인물, 차량 실루엣, 배경 활동 금지
- 고정 랜드마크 상대 위치 유지
- 소품 형태/재질/크기, 손상 상태, 시간대/날씨, 세트드레싱 유지

승인 후 진행 방식:
- 최대 4개씩 서브에이전트 병렬 생성
- 각 서브에이전트 1차 검수
- 부모 세션 최종 검수
- 실패 항목 rerun 후 다음 배치 진행
```

## Contracts

Read `references/runner-contract.md` when writing plan JSON, import manifests, inspection manifests, or subagent task text.
