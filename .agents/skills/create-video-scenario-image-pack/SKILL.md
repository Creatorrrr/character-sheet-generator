---
name: create-video-scenario-image-pack
description: Use when a video script, storyboard, shot list, or scene brief needs non-character production image sources such as locations, spatial anchors, props, inserts, environmental details, mood keys, or continuity references.
---

# Create Video Scenario Image Pack

## Core Rule

Create a resumable, approved image-source pack for video generation. Default outputs are non-character sources only: locations, spatial anchors, props, inserts, environmental details, mood keys, and continuity references.

Do not generate images before the user approves the exact source list.

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
2. Extract and deduplicate useful image sources, then ask for approval in Korean.
3. After approval, write `approved_image_plan.json` and approve it:
   ```bash
   python3 "$RUNNER" approve-plan --run-dir <run-dir> --plan-file <approved-plan.json>
   ```
4. Reserve only dependency-ready work:
   ```bash
   python3 "$RUNNER" next-batch --run-dir <run-dir> --limit 4
   python3 "$RUNNER" batch-prompts --run-dir <run-dir> --batch-id <batch-id>
   ```
5. Spawn one subagent per reserved item, maximum four per batch. Each subagent generates exactly one image with `image_gen`. If using `fork_context=true`, omit subagent role fields such as `agent_type` or `role`; put the generation/inspection behavior in the task prompt instead.
6. Import worker results through the runner. Prefer batch manifests over parallel shell calls:
   ```bash
   python3 "$RUNNER" import-batch --manifest <import-manifest.json>
   ```
7. Parent-inspect every imported image before passing it:
   ```bash
   python3 "$RUNNER" inspect-batch-pass --manifest <inspect-manifest.json>
   ```
8. Route failures through rerun. Rerun notes become prompt hints for the next attempt:
   ```bash
   python3 "$RUNNER" rerun --run-dir <run-dir> --item <id-or-filename> --note "<reason>"
   ```
9. Report status in Korean:
   ```bash
   python3 "$RUNNER" report --run-dir <run-dir>
   ```

## Extraction Policy

- Merge repeated needs when one reusable source can cover multiple scenes.
- Split sources when continuity would break: time of day, weather, set dressing, prop design, damage state, camera-critical inserts, or spatially distinct areas.
- Prefer categories: `location_master`, `location_view`, `set_detail`, `prop`, `vehicle`, `insert`, `vfx_plate`, `mood_key`, `spatial_layout`, `continuity_reference`.
- Create one `location_master` or `spatial_layout` continuity anchor per major place before dependent details.
- Use `spatial_group`, `continuity_anchor`, `fixed_layout_notes`, `camera_view`, `must_match`, and `dependencies` for spatial continuity.

## Strict No-Character Policy

Unless the user explicitly approves character-bearing outputs, reject people and human-like artifacts anywhere in the image, including the far background.

Fail and rerun if the image includes pedestrians, players, body parts, hands, faces, silhouettes, crowds, cars, vehicles, bicycles, scooters, posters, signage, window figures, reflections, or tiny vertical marks that read as human figures.

For empty locations, prefer closed-off or simplified backgrounds: blank masonry walls, fence mesh, empty pavement, sky, and stable landmarks. This avoids repeated background silhouette failures.

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

승인 후 진행 방식:
- 최대 4개씩 서브에이전트 병렬 생성
- 각 서브에이전트 1차 검수
- 부모 세션 최종 검수
- 실패 항목 rerun 후 다음 배치 진행
```

## Contracts

Read `references/runner-contract.md` when writing plan JSON, import manifests, inspection manifests, or subagent task text.
