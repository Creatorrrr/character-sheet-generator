---
name: create-photoreal-character-base
description: Create the stage 1 text-free photoreal live-action sheet from a 2D character sheet. Use when converting a 2D character sheet into a realistic photographed character sheet while preserving the original canvas, panel layout, view positions, non-text graphics, identity, hair, costume, in-image typography, pose, and expression, but removing sheet annotation text.
---

# Create Photoreal Character Base

## Overview

Generate or edit from the original 2D character sheet to produce a text-free photoreal character sheet with the same structure as the source. This stage prioritizes real human photography while locking the original sheet layout, Character Appearance Lock, and removing only sheet annotation text. Typography or logo-like marks inside the character image, costume, props, accessories, patches, embroidery, or engravings are character design details and must stay.

## Inputs

Require the original 2D character sheet image. If the workflow has created `structure-inventory.md`, include it as the structure/content contract and Character Appearance Lock. If the user has special identity constraints, include them before the prompt.

## Prompt

Use this prompt as the stage instruction:

```text
첨부한 2D 캐릭터 시트를 기준으로, 원본과 동일한 캔버스 비율과 패널 구조를 유지한 텍스트 없는 실사 캐릭터 시트로 변환해줘.

가장 중요한 목표:
이 결과물은 실사풍 일러스트, 반실사 그림, 3D 캐릭터 렌더가 아니라, 실제 배우나 모델을 촬영한 라이브액션 캐릭터 레퍼런스 사진처럼 보여야 한다.
원본 시트를 자유롭게 재구성하지 말고, 시트 설명/라벨/캡션 같은 주석 텍스트만 제거한 상태로 원본 구조를 유지해야 한다.
여기서 "텍스트 없는"은 시트 주석 텍스트가 없다는 뜻이다. 캐릭터 이미지 안의 의상 프린트, 로고형 패치, 자수, 소품 각인, 액세서리 문양처럼 디자인 일부인 타이포그래피는 제거하지 말고 실사화된 디테일로 유지한다.

유지할 요소:
- 원본 캔버스 비율과 전체 페이지 구도
- 원본 패널 그리드와 섹션 위치
- 큰 전신 정면도, 턴어라운드, 얼굴/눈 디테일, 의상 디테일, 하체/소품 디테일, 프로필/키포인트 패널의 위치와 크기 관계
- 원본의 모든 이미지 슬롯을 1:1로 유지: 각 슬롯의 개수, 위치 관계, 역할, 시점, 표정/감정, 디테일 대상, 소품/의상/신체 부위가 원본과 대응되어야 함
- 콜아웃 선, 박스, 패널 테두리, 컬러칩, 비문자 그래픽 장식
- 원본 캐릭터의 정체성
- Character Appearance Lock: 원본에서 보이는 apparent age/maturity, height/stature impression, body type and body proportions, head-to-body ratio, silhouette, posture, face shape, cheek/jaw/chin softness, eye shape, brow shape, nose/mouth/lip traits, skin tone/visible marks, hair silhouette, expression intensity, emotional/personality impression
- 헤어스타일과 머리색
- 의상 디자인과 색상
- 의상/소품/액세서리/이미지 슬롯 내부에 인쇄, 자수, 각인, 패치 형태로 들어간 원본 타이포그래피와 로고형 디자인
- 포즈와 구도
- 표정과 감정

제거할 텍스트 범위:
- 시트의 제목, 섹션 번호, 라벨, 설명문, 캡션, UI성 로고 텍스트, 모델명, 버전 표기 등 시트 레이아웃에 속한 주석 텍스트는 모두 제거
- 가짜 주석 문자, 깨진 주석 문자, 임의의 새 라벨도 만들지 말 것
- 시트 주석 텍스트가 있던 박스, 선, 빈 라벨 자리, 패널 구조는 가능한 한 유지하되 내부 글자만 비워둘 것

보존할 텍스트성 디자인:
- 의상, 소품, 액세서리, 신발, 가방, 무기, 패치, 자수, 각인 등 캐릭터 이미지 범위 안에 들어간 원본 타이포그래피는 디자인 디테일로 유지
- 너무 작거나 흐려서 정확히 읽기 어려운 경우에도 위치, 크기, 색, 형태감은 유지하되 정확한 글자 재현을 주장하지 말 것

변환 방향:
- 얼굴은 애니메이션식 비율이 아니라 실제 인간의 얼굴 비율과 골격으로 자연스럽게 변환
- 애니메이션 신체/얼굴 비율은 현실 인체로 자연스럽게 번역하되, 원본의 나이대 인상, 얼굴 인상, 체형/키감, 표정 톤, 분위기가 다른 인물처럼 바뀌면 안 됨
- 실사화는 새로운 배우를 캐스팅하거나 성숙한 모델로 재해석하는 것이 아니라, 원본 캐릭터의 시각적 인상을 실제 인물 사진으로 번역하는 것임
- 피부는 실제 피부 질감이 보이게 표현: 미세한 모공, 자연스러운 피부결, 약간의 비대칭, 자연스러운 혈색
- 눈, 코, 입, 턱선, 귀가 실제 사람처럼 자연스럽게 연결되게
- 머리카락은 실제 머리카락처럼 가닥감과 잔머리가 보이게
- 의상은 현실에서 제작된 옷처럼 표현: 실제 원단, 봉제선, 주름, 두께감, 재질감, 착용감
- 금속, 가죽, 플라스틱, 천 등 각 소재가 현실적으로 구분되게
- 조명은 과하게 완벽한 CG 조명이 아니라 현실적인 촬영 조명으로 표현
- 선명하지만 과도하게 샤프하지 않게
- 자연스러운 카메라 사진 느낌, 라이브액션 캐릭터 디자인 레퍼런스 사진 시트 느낌

중요:
- 시트 주석 텍스트는 이번 단계에서 절대 재현하지 말 것
- 원본 의상/소품 타이포그래피는 새 라벨로 취급하지 말고 캐릭터 디자인 일부로 유지할 것
- 원본 시트의 구조를 단순화하거나 새 레퍼런스 보드로 재배치하지 말 것
- 둘 이상의 원본 이미지 슬롯을 하나로 합치지 말 것
- 원본 이미지 슬롯을 생략하거나 다른 의미의 표정, 방향, 디테일, 소품, 의상 영역으로 바꾸지 말 것
- 원본의 외형 락을 바꾸지 말 것: 귀여운 10대 소녀 인상이 30대 성인 여성처럼 보이거나, 부드러운 얼굴이 강인하고 성숙한 얼굴로 바뀌거나, 살짝 웃는 표정이 무표정으로 바뀌거나, 작고 여린 체형이 장신 성인 모델 체형으로 바뀌면 실패
- 캐릭터와 의상, 표정, 포즈, 실사화 품질과 함께 원본 구조 보존을 최우선으로 할 것

피해야 할 것:
- anime look
- manga look
- cel shading
- illustration
- digital painting
- 3D render
- CGI
- game asset render
- doll-like face
- waxy skin
- plastic skin
- glossy AI smoothness
- over-sharpening
- over-clean studio glamour lighting
- overly symmetrical face
- mannequin-like body
- changed apparent age
- changed face shape
- changed body proportions
- changed expression intensity
- mature glamour-model recasting
- inconsistent face shape or apparent age across panels
- cosplay poster look
- unreal beauty retouching

출력 형태:
- 고해상도
- 텍스트 없는 실사 캐릭터 레퍼런스 시트
- same canvas ratio and same panel/view structure as the original sheet
- no sheet labels, no captions, no section numbers, no pseudo annotation text
- preserve original in-image costume and prop typography as design detail
- realistic live-action character reference sheet
- documentary studio reference photo sheet
```

## Execution Guidance

- Use image generation or image editing with the source sheet attached when available.
- Do not ask for sheet annotation text preservation in this stage; preserve original in-image costume/prop typography as part of the visual design.
- Treat the original sheet and `structure-inventory.md` as a layout/content lock: keep panel placement, view count, image-slot count, slot roles, non-text graphic frames, callout lines, empty sheet annotation areas, color chips, and in-image costume/prop typography.
- Treat the `Character Appearance Lock` as a same-character contract: preserve apparent age, body proportions, face shape, expression intensity, silhouette, posture, hair silhouette, and emotional/personality impression while converting anime proportions into believable human anatomy.
- Preserve recognizable design traits and 외형 동등성 even while converting anime proportions into believable human anatomy.
- If the model changes the sheet structure, rerun with stronger "same layout, same panel grid" language.
- If the model merges, omits, duplicates, or changes the meaning of any source image slot, rerun with stronger "each source image slot must remain separate and semantically equivalent" language.
- If the model changes apparent age, face shape, body proportions, expression intensity, silhouette, or same-character impression, rerun with stronger "same Character Appearance Lock; do not recast the character" language.
- If the model keeps readable sheet annotation text or invents pseudo annotation text, rerun with stronger "remove all sheet labels/captions, keep empty boxes" language.

## Quality Check

Pass only when:

- The character reads as a real photographed person.
- Skin, hair, clothing, lighting, and materials are plausibly physical.
- The original canvas ratio, panel structure, major view groups, image-slot count, detail-panel positions, slot meanings, and non-text graphic structure are preserved.
- 외형 동등성 passes: apparent age/maturity, face shape, expression intensity, body proportions, silhouette, posture, hair silhouette, and emotional/personality impression still match the Character Appearance Lock.
- All readable sheet annotation text, labels, section numbers, captions, UI logo text, and fake annotation typography are absent.
- Original in-image typography on clothing, props, accessories, patches, embroidery, or engravings is preserved as character design detail.
- The result does not look like anime, digital painting, 3D render, game asset, mannequin, doll, or glossy AI retouch.

Report remaining risks to the workflow manager.
