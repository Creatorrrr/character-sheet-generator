# Character Sheet Generator Skills

이 저장소는 캐릭터 시트 제작, 2D 캐릭터 시트의 실사화, 영상 AI용 레퍼런스 팩 생성을 위한 Codex/agent skill 모음입니다. 각 skill은 `.agents/skills/<skill-name>/SKILL.md`에 정의되어 있으며, 필요한 경우 `$skill-name` 형식으로 호출해 작업을 시작할 수 있습니다.

## 빠른 선택 가이드

| 목표 | 사용할 skill |
| --- | --- |
| 캐릭터 이미지와 설정을 바탕으로 새 마스터 캐릭터 시트를 만들기 | `$character-sheet-orchestrator` |
| 승인된 캐릭터 시트에서 스타일을 유지한 클로즈업/디테일 팩 만들기 | `$create-character-sheet-closeup-reference-pack` |
| 2D 캐릭터 시트를 실사 라이브액션 캐릭터 시트로 변환하기 | `$convert-2d-sheet-to-photoreal` |
| 실사 캐릭터 시트나 마스터 얼굴을 바탕으로 영상 AI용 포토리얼 레퍼런스 팩 만들기 | `$create-video-closeup-reference-pack` |
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

스타일 보존 클로즈업 팩:

```text
$create-character-sheet-closeup-reference-pack
승인된 애니메이션 캐릭터 시트의 스타일은 유지하고 core closeup reference pack을 만들어줘.
```
