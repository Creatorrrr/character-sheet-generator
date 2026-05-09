# Character Sheet Generator Skills

이 저장소는 캐릭터 시트 제작, 2D 캐릭터 시트의 실사화, 영상 AI용 레퍼런스 팩 생성을 위한 Codex/agent skill 모음입니다. 각 skill은 `.agents/skills/<skill-name>/SKILL.md`에 정의되어 있으며, 필요한 경우 `$skill-name` 형식으로 호출해 작업을 시작할 수 있습니다.

## 빠른 선택 가이드

| 목표 | 사용할 skill |
| --- | --- |
| 캐릭터 이미지와 설정을 바탕으로 새 마스터 캐릭터 시트를 만들기 | `$character-sheet-orchestrator` |
| 승인된 캐릭터 시트에서 스타일을 유지한 클로즈업/디테일 팩 만들기 | `$create-character-sheet-closeup-reference-pack` |
| 2D 캐릭터 시트를 실사 라이브액션 캐릭터 시트로 변환하기 | `$convert-2d-sheet-to-photoreal` |
| 실사 캐릭터 시트나 마스터 얼굴을 바탕으로 영상 AI용 포토리얼 레퍼런스 팩 만들기 | `$create-video-closeup-reference-pack` |
| 줄거리/시나리오를 여유 있는 자유형 컷 만화책 페이지로 단계별 생성하기 | `$create-comic-storyboard-pack` |
| 승인된 만화 페이지의 콘티/스케치/펜선 단계만 생성하기 | `$create-comic-storyboard-sketch-ink` |
| 검수된 콘티/스케치/펜선 이미지를 톤/채색/마무리 단계로 완성하기 | `$create-comic-storyboard-finish` |
| 특정 부위나 특정 각도의 이미지 한 장만 만들기 | 아래의 개별 생성 skill |

## 공통 운영 규칙

- 기본 산출물 위치는 `/Users/chasoik/Projects/character-sheet-generator/output/`입니다.
- 별도 저장 위치가 없으면 workflow skill이 `output/<slug>-<workflow>-YYYYMMDD-HHMMSS/` 형태의 run 폴더를 사용합니다.
- 재개 작업이면 기존 run 폴더와 승인된 중간 산출물을 계속 사용합니다.
- 캐릭터 정체성, 얼굴, 헤어, 의상, 팔레트, 상징 소품처럼 승인된 요소를 우선 보존합니다.
- 왼쪽/오른쪽 시점이 모두 필요한 경우 별도 이미지로 나누기보다 한 장의 paired image로 생성하는 것이 기본입니다.
- 텍스트가 중요한 최종 시트는 이미지 생성 단계와 텍스트 합성/수정 단계를 분리합니다.
- 결과를 실제로 검수하지 않았다면 텍스트 가독성, 좌우 방향, 동일 인물 유지가 통과했다고 말하지 않습니다.

## 상위 Workflow Skills

### `$character-sheet-orchestrator`

사용자가 제공한 캐릭터 이미지와 설명을 바탕으로 새 캐릭터 마스터 시트, 설정화, mascot sheet, anime/photoreal reference board를 단계적으로 만듭니다.

주요 단계:

1. 입력 이미지와 설명 분석
2. 캐릭터 정체성, 외형, 성격, 팔레트, 모티프 정리
3. 시트 레이아웃과 패널 구성 설계
4. 필요한 경우 얼굴, 전신, 측후면, 의상 anchor 생성
5. 텍스트 없는 초안 시트 생성
6. 초안 검수
7. 최종 문구 작성
8. 텍스트 합성과 최종 QA

기본 레이아웃은 `character-sheet-orchestrator/assets/master-sheet-template.png`를 참고합니다. 이 템플릿은 와이어프레임 기준이며, 회색 마네킹이나 빈 placeholder를 캐릭터 내용으로 복사하지 않습니다.

### `$create-character-sheet-closeup-reference-pack`

`$character-sheet-orchestrator`로 만든 승인된 캐릭터 시트에서 스타일을 유지한 클로즈업/디테일 팩을 만듭니다. anime, mascot, semi-real, photoreal 등 원본 시트의 승인된 스타일을 그대로 유지하는 것이 핵심입니다.

기본 `core` preset:

- `01_face_front.png`
- `02_03_face_3q_pair.png`
- `04_05_face_side_pair.png`
- `06_eye_detail.png`
- `07_expression_sheet.png`
- `08_hair_detail.png`
- `09_upper_outfit_detail.png`
- `10_lower_outfit_shoes.png`
- `11_hand_gesture_sheet.png`
- `12_signature_props.png`

`full` preset은 `core` 전체에 얼굴 턴어라운드, 입모양, 뒷모습/후면 디테일, 소재 질감, 전신 정면, 전신 측후면, idle pose, 팔레트/모티프 레퍼런스를 추가합니다.

### `$convert-2d-sheet-to-photoreal`

2D 캐릭터 시트를 실사 라이브액션 캐릭터 시트로 바꾸는 전체 workflow입니다. 한 번에 모든 것을 바꾸지 않고, 실사 캐릭터 품질과 텍스트/레이아웃 복원을 분리합니다.

사용하는 하위 단계:

1. `$create-photoreal-character-base`: 텍스트 없는 실사 캐릭터 base 생성
2. `$intensify-photoreal-character`: anime, 3D, CGI, plastic 느낌이 남은 경우 실사감 강화
3. `$restore-photoreal-sheet-layout`: 승인된 실사 base에 원본 시트 구조와 텍스트 영역 복원
4. `$repair-photoreal-sheet-text`: 캐릭터는 좋지만 글자나 라벨만 깨진 경우 텍스트만 수리

### `$create-video-closeup-reference-pack`

승인된 포토리얼 캐릭터 시트나 마스터 얼굴 레퍼런스에서 영상 AI용 고해상도 레퍼런스 팩을 만듭니다. 영상 생성 중 동일 인물, 헤어, 의상, 소품, 손, 얼굴 방향을 안정적으로 유지하기 위한 자료를 만드는 workflow입니다.

주요 산출물:

| 파일 | 연결 skill |
| --- | --- |
| `01_face_front.png` | `$create-face-front-closeup` |
| `02_face_3q_left.png` | `$create-face-3q-left-closeup` |
| `03_face_3q_right.png` | `$create-face-3q-right-closeup` |
| `04_face_side_left.png` | `$create-face-side-left-profile` |
| `05_face_side_right.png` | `$create-face-side-right-profile` |
| `06_eye_macro.png` | `$create-eye-brow-macro-closeup` |
| `07_expression_sheet.png` | `$create-expression-six-sheet` |
| `08_mouth_speech_sheet.png` | `$create-mouth-speech-sheet` |
| `09_hair_front_detail.png` | `$create-hair-front-detail-closeup` |
| `10_hair_accessory_macro.png` | `$create-hair-accessory-macro` |
| `11_upper_costume_closeup.png` | `$create-upper-costume-closeup` |
| `12_hand_sleeve_closeup.png` | `$create-hand-sleeve-gesture-closeup` |
| `13_belt_props_closeup.png` | `$create-belt-props-closeup` |
| `14_shoes_closeup.png` | `$create-shoes-lower-outfit-closeup` |
| `15_full_body_front.png` | `$create-full-body-front-reference` |
| `16_full_body_back.png` | `$create-full-body-back-reference` |
| `17_full_body_side.png` | `$create-full-body-side-reference` |
| `18_character_pose_idle.png` | `$create-character-idle-pose` |
| `19_face_turnaround_sheet.png` | `$create-face-turnaround-sheet` |
| `20_hand_gesture_four_sheet.png` | `$create-hand-gesture-four-sheet` |

### `$create-comic-storyboard-pack`

줄거리/시나리오, 장면 메모, 대본, 씬 브리프, 샷 리스트를 바탕으로 기본 3-5컷 권장의 영화적 호흡, 실험적 자유형 컷 구성, 디테일 밀도, 표현 강약, 효과선 연출을 가진 만화책 페이지 계획을 만들고, 승인 후 단계별 이미지 생성을 조율합니다. 이 skill은 계획/승인, runner 상태 관리, batch 예약, 부모 검수, rerun, 단계 마무리 검수, 다음 단계 사용자 피드백 게이트를 담당합니다.

진행 단계:

1. `$create-comic-storyboard-sketch-ink`: 콘티/스케치/펜선 `storyboard_sketch_ink`
2. 사용자 피드백 및 다음 단계 진행 승인
3. `$create-comic-storyboard-finish`: 톤/채색/마무리 `finish`

기본 정책:

- 승인 전에는 이미지를 생성하지 않습니다.
- 기본 페이지는 3-5컷을 권장하고, 1-2컷은 큰 감정 컷/전면 컷/침묵/정적/강한 액션 순간 같은 특수 연출에 권장합니다.
- 6컷 이상은 몽타주/개그 타이밍/빠른 액션 연쇄처럼 명확한 이유가 있을 때만 사용합니다.
- 사선, 비대칭, 오픈 컷, 무테 컷, 삽입컷, 부분 겹침, 넓은 여백 같은 실험적 자유형 컷 구성을 기본으로 허용합니다.
- 컷별 초점, 디테일 밀도, 선 굵기/먹선 강약, 배경 생략/강조, 속도선/집중선/충격선/감정선 같은 만화적 시각 연출을 계획하고 검수합니다.
- 만화 페이지/컷은 먼저 시나리오, 감정선, 액션 리듬, 독자 시선 흐름, 컷 밀도, 여백, 디테일/강약/효과선 중심으로 설계하고, `spatial_contract`는 그 설계 이후에 추출하는 검수 레이어로 사용합니다.
- `spatial_contract`는 page/composition driver가 아니라 validation overlay입니다. 사선/엄폐/벡터/랜드마크/상태 유지 오류를 잡기 위한 것이며, 공간 관계를 잘 보이게 하려고 컷을 전술 도해처럼 설계하지 않습니다.
- 과도하게 압축된 페이지, 의도 없는 균일 직각 그리드, 여백 없이 대사/SFX가 꽉 찬 구성은 검수에서 보완 대상으로 봅니다.
- 모든 페이지의 `storyboard_sketch_ink` 부모 검수와 단계 마무리 검수 통과 전에는 `finish`를 진행하지 않습니다.
- `storyboard_sketch_ink` 단계 마무리 검수 후에는 사용자 피드백을 받고, `approve-next-stage`로 승인되기 전까지 `finish` batch를 예약하지 않습니다.
- 사용자가 1단계 결과만 원하면 `stop-after-stage`로 `storyboard_sketch_ink`까지만 완료 처리할 수 있습니다.
- `finish`는 앞선 단계에서 생성한 이미지를 필수 입력/구조 참조로 사용합니다.
- 사용자가 소스/레퍼런스 경로를 지정하지 않으면 `/Users/chasoik/Projects/character-sheet-generator/sources/`에서 필요한 자료를 참고하고, `/Users/chasoik/Projects/character-sheet-generator/output/` 하위 파일은 소스 데이터로 쓰지 않습니다.
- 승인된 각색 대사, 효과음, 짧은 캡션은 말풍선/효과음 글자/캡션 영역으로 페이지 이미지 내부에 포함합니다.
- 단계 마무리 검수에서 캐릭터/소품/프로필/배경 등 소스 데이터 일관성과 컷 내부/컷 사이/페이지 간 연속성을 확인하고, 필요하면 해당 페이지를 rerun으로 보완합니다.
- 캐릭터, 물체, 배경, 공/소품의 위치와 움직임이 상식적인지 worker와 부모 세션이 모두 검수합니다.
- `spatial_contract`가 있는 계획은 `spatial-preview`로 정적 HTML 검수 화면을 생성해 컷별 위치, 방향 벡터, 조준/투사체/엄폐/시선 차단, 랜드마크/상태 유지 조건과 `spatial-check` 이슈를 이미지 생성 전에 확인할 수 있습니다. 이 검수는 승인된 만화 페이지 설계를 확인하는 단계이며, 페이지/컷 설계를 대체하지 않습니다.
- 승인 계획의 `character_locks`와 `must_match`에 캐릭터 외형/해부 고정 조건을 기록하고, 종족/신체 구조, 얼굴 구조, 눈 개수/배치, 손/손가락/팔/다리 개수, 실루엣, 체형 비율, 자세를 독립 검수합니다.
- 승인안이나 source가 외눈/비대칭/비인간 구조를 명시하지 않았다면 눈 누락/추가/병합, 두 눈 캐릭터가 외눈처럼 보이는 경우, 손가락/팔/다리 누락이나 추가, 종족/체형 변경, 관절/비율 붕괴는 rerun 대상입니다.
- 예: 두 눈 캐릭터는 두 눈이 보이거나 각도상 자연스럽게 가려져야 하며, 외눈 캐릭터처럼 보이면 rerun합니다.
- 다음 단계는 이전 단계의 모든 페이지가 부모 검수와 단계 마무리 검수를 통과하고 사용자가 진행을 승인한 뒤에만 진행합니다.

```bash
python3 .agents/skills/create-comic-storyboard-pack/scripts/comic_storyboard_runner.py spatial-preview --plan-file <approved-plan.json>
python3 .agents/skills/create-comic-storyboard-pack/scripts/comic_storyboard_runner.py spatial-preview --run-dir <run-dir>
```

### 만화 콘티 Stage Skills

| Skill | 용도 |
| --- | --- |
| `$create-comic-storyboard-sketch-ink` | 승인된 만화 페이지 plan과 runner prompt를 바탕으로 한 페이지의 콘티/스케치/펜선 이미지를 생성하고 1차 검수합니다. `state.json`은 수정하지 않고 결과 경로, `worker_status`, `worker_note`만 반환합니다. 캐릭터 외형/해부 고정 조건 위반은 `needs_rerun`입니다. |
| `$create-comic-storyboard-finish` | 부모 검수 통과한 `storyboard_sketch_ink` 이미지를 필수 구조 참조로 사용해 톤/채색/마무리를 생성하고 1차 검수합니다. 레이아웃, 컷 수, 동선, 텍스트 정책, 효과선 방향, 눈/얼굴/손/체형 구조를 변경하지 않습니다. |

## 2D to Photoreal Stage Skills

| Skill | 용도 |
| --- | --- |
| `$create-photoreal-character-base` | 원본 2D 캐릭터 시트를 텍스트 없는 실사 캐릭터 레퍼런스 base로 변환합니다. 캐릭터 정체성, 헤어, 의상, 포즈, 표정, 구성을 보존하되 글자는 임시로 제외합니다. |
| `$intensify-photoreal-character` | base 결과가 아직 anime, illustration, 3D render, CGI, plastic skin, AI smoothness처럼 보일 때 실사 사진 느낌을 강화합니다. |
| `$restore-photoreal-sheet-layout` | 승인된 실사 캐릭터 이미지를 유지하면서 원본 2D 시트의 패널 구조, 정보 구조, 라벨, 텍스트 박스를 복원합니다. |
| `$repair-photoreal-sheet-text` | 최종 실사 시트의 캐릭터와 레이아웃은 유지하고 흐릿하거나 깨진 텍스트, 라벨, 정렬만 수리합니다. |

## 개별 생성 Skills

### 얼굴과 표정

| Skill | 용도 |
| --- | --- |
| `$create-face-front-closeup` | 영상용 identity anchor로 쓸 정면 얼굴 클로즈업을 생성합니다. |
| `$create-face-3q-left-closeup` | 왼쪽을 향한 3/4 얼굴 클로즈업이 한 장만 필요할 때 사용합니다. |
| `$create-face-3q-right-closeup` | 오른쪽을 향한 3/4 얼굴 클로즈업이 한 장만 필요할 때 사용합니다. |
| `$create-face-side-left-profile` | 코와 얼굴 방향이 이미지 왼쪽을 향하는 완전 측면 얼굴을 생성합니다. |
| `$create-face-side-right-profile` | 코와 얼굴 방향이 이미지 오른쪽을 향하는 완전 측면 얼굴을 생성합니다. |
| `$create-face-turnaround-sheet` | 정면, 좌우 3/4, 좌우 측면을 한 장에 담은 5-angle 얼굴 턴어라운드 시트를 생성합니다. |
| `$create-expression-six-sheet` | neutral, smile, surprise, thinking, embarrassment, confidence 등 여섯 표정 시트를 생성합니다. |
| `$create-mouth-speech-sheet` | 대사/립싱크용 입모양과 표정 변형 여섯 패널을 생성합니다. |

### 헤어, 눈, 의상, 소품

| Skill | 용도 |
| --- | --- |
| `$create-eye-brow-macro-closeup` | 눈 모양, 홍채색, 속눈썹, 눈썹, 눈 주변 피부 질감의 macro closeup을 생성합니다. |
| `$create-hair-front-detail-closeup` | 앞머리, 헤어라인, 머리색, 볼륨, 잔머리, 앞쪽 헤어 장식을 고정합니다. |
| `$create-hair-accessory-macro` | 리본, 핀, 클립, 장식 등 헤어 액세서리의 소재와 부착 방식을 closeup으로 생성합니다. |
| `$create-upper-costume-closeup` | 카라, 리본, 상의, 재킷, 셔츠, 원단, 봉제, 단추, 지퍼 등 상체 의상 디테일을 생성합니다. |
| `$create-belt-props-closeup` | 벨트, 파우치, 키링, 허리 장식, 가방, 상징 소품의 소재와 스케일을 고정합니다. |
| `$create-shoes-lower-outfit-closeup` | 신발, 양말, 하의 실루엣, 밑창, 끈, 버클, 밑단, 하체 의상 디테일을 생성합니다. |

### 손, 전신, 포즈

| Skill | 용도 |
| --- | --- |
| `$create-hand-sleeve-gesture-closeup` | 손, 손가락, 손톱, 소매, 장갑, 손목 액세서리와 단일 자연 제스처를 생성합니다. |
| `$create-hand-gesture-four-sheet` | 설명하기, 가리키기, 작은 소품 잡기, relaxed idle 손동작을 네 패널로 생성합니다. |
| `$create-full-body-front-reference` | 얼굴, 헤어, 전신 의상, 비율, 액세서리, 신발을 보존한 정면 전신 레퍼런스를 생성합니다. |
| `$create-full-body-back-reference` | 후면 실루엣, 뒷머리, 재킷 후면, 액세서리, 하의, 신발을 보존한 후면 전신 레퍼런스를 생성합니다. |
| `$create-full-body-side-reference` | 측면 실루엣, 자세, 헤어 profile, 의상 두께, 액세서리, 신발, 신체 비율을 안정화합니다. |
| `$create-character-idle-pose` | 캐릭터 태도가 드러나는 자연스러운 서 있는 pose나 relaxed pose를 생성합니다. |

## 예시 요청

새 캐릭터 시트:

```text
$character-sheet-orchestrator
첨부한 캐릭터 이미지 기준으로 한국어 마스터 캐릭터 시트를 만들어줘.
표정, 턴어라운드, 의상 디테일, 프로필, 팔레트가 포함되면 좋겠어.
```

2D 시트 실사화:

```text
$convert-2d-sheet-to-photoreal
이 2D 캐릭터 시트를 실사 라이브액션 캐릭터 시트로 변환해줘.
단계별로 결과를 확인하고 진행해줘.
```

영상용 레퍼런스 팩:

```text
$create-video-closeup-reference-pack
승인된 실사 캐릭터 시트를 기준으로 영상 AI용 face, expression, hand, costume, full-body 레퍼런스 팩을 만들어줘.
```

만화 콘티 팩:

```text
$create-comic-storyboard-pack
이 줄거리/시나리오를 일반 한국 만화책처럼 페이지당 여러 컷, 말풍선 대사, 효과음이 들어간 구성으로 만들어줘.
기본은 3-5컷 권장으로 하고, 1-2컷은 특수 연출에만 쓰며, 사선/비대칭/오픈 컷 같은 자유로운 컷 구성을 활용해줘.
디테일 밀도, 표현 강약, 효과선/집중선/속도선 같은 만화적 시각 연출도 컷별로 계획하고 검수해줘.
먼저 페이지 목록과 컷 구성, 각색 대사/SFX, 만화적 연출, 공간/동선 검수 기준을 보고하고, 승인 후 콘티/스케치/펜선 단계를 생성해줘.
캐릭터 외형/해부 고정 조건에는 눈 개수/배치, 얼굴 구조, 손/팔다리 개수, 체형 비율도 포함해줘. 두 눈 캐릭터가 외눈처럼 보이면 rerun으로 봐줘.
1단계 결과를 내가 확인한 뒤 톤/채색/마무리 단계 진행 여부를 다시 물어봐줘.
```

스타일 보존 클로즈업 팩:

```text
$create-character-sheet-closeup-reference-pack
승인된 애니메이션 캐릭터 시트의 스타일은 유지하고 core closeup reference pack을 만들어줘.
```
