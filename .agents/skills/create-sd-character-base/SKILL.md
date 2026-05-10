---
name: create-sd-character-base
description: Use when converting an original 2D character sheet into a text-free SD, chibi, or super-deformed character sheet while preserving canvas, panel layout, image-slot meaning, identity, hair, costume, props, in-image typography, pose, and expression.
---

# Create SD Character Base

## Overview

Generate or edit from the original 2D character sheet to produce a text-free SD/chibi character sheet with the same structure as the source. This stage prioritizes clear super-deformed 2D character styling while locking the original sheet layout, Character Identity Lock, SD Proportion Target, and removing only sheet annotation text. Typography or logo-like marks inside the character image, costume, props, accessories, patches, embroidery, or engravings are character design details and must stay.

## Inputs

Require the original 2D character sheet image. If the workflow has created `structure-inventory.md`, include it as the structure/content contract, Character Identity Lock, and SD Proportion Target. If the user has special SD style constraints, include them before the prompt.

## Prompt

Use this prompt as the stage instruction:

```text
첨부한 2D 캐릭터 시트를 기준으로, 원본과 동일한 캔버스 비율과 패널 구조를 유지한 텍스트 없는 SD 캐릭터 시트로 변환해줘.

여기서 SD는 Stable Diffusion이 아니라 super-deformed/chibi 캐릭터 스타일을 뜻한다.

가장 중요한 목표:
- 원본 시트를 자유롭게 재구성하지 말고, 시트 설명/라벨/캡션 같은 주석 텍스트만 제거한 상태로 원본 구조를 유지한다.
- 캐릭터 이미지는 귀엽고 명확한 2D SD/chibi 스타일로 변환한다.
- 기본 비율은 큰 머리, 작은 몸, 짧은 팔다리의 2-3등신 SD 스타일이다. 사용자가 별도 비율을 지정했다면 그 비율을 따른다.
- 결과물은 photoreal, semi-real, 3D toy render, plush mascot suit가 아니라 깔끔한 2D SD 캐릭터 레퍼런스 시트처럼 보여야 한다.

유지할 요소:
- 원본 캔버스 비율과 전체 페이지 구도
- 원본 패널 그리드와 섹션 위치
- 원본의 모든 이미지 슬롯을 1:1로 유지: 각 슬롯의 개수, 위치 관계, 역할, 시점, 표정/감정, 디테일 대상, 소품/의상/신체 부위가 원본과 대응되어야 함
- 콜아웃 선, 박스, 패널 테두리, 컬러칩, 비문자 그래픽 장식
- 원본 캐릭터의 정체성
- Character Identity Lock: 원본에서 보이는 나이대/성숙도 인상, 성격/감정 인상, 얼굴과 눈의 인상, 헤어 실루엣, 핵심 의상, 상징 소품, 팔레트, 모티프, 포즈, 표정 강도
- SD Proportion Target: 지정되거나 추론된 2-3등신 SD 비율, 큰 머리, 작은 몸, 단순한 몸통, 짧은 팔다리, 읽기 쉬운 손/발 형태
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
- SD 단순화 때문에 너무 작게 보이는 경우에도 위치, 크기, 색, 형태감은 유지하되 정확한 글자 재현을 주장하지 말 것

SD 변환 방향:
- 머리는 크고 표정이 잘 보이게
- 몸은 작고 단순하지만 원본 의상 구조와 핵심 디테일은 알아볼 수 있게
- 손발은 작고 단순화하되 포즈와 제스처 의미는 유지
- 눈, 입, 눈썹은 감정 전달이 선명한 SD 표현으로 정리
- 원본의 나이대/성숙도 인상을 과도하게 유아화하지 말 것
- 원본 캐릭터의 성격이 다른 캐릭터처럼 바뀌지 않게
- 헤어 실루엣, 앞머리, 장식, 색상, 상징 소품은 SD 크기에 맞춰 단순화하되 식별 가능하게
- 세부 묘사는 과도하게 줄이지 말고, SD 캐릭터 디자인에서 읽히는 핵심 형태로 압축

중요:
- 시트 주석 텍스트는 이번 단계에서 절대 재현하지 말 것
- 원본 의상/소품 타이포그래피는 새 라벨로 취급하지 말고 캐릭터 디자인 일부로 유지할 것
- 원본 시트의 구조를 단순화하거나 새 레퍼런스 보드로 재배치하지 말 것
- 둘 이상의 원본 이미지 슬롯을 하나로 합치지 말 것
- 원본 이미지 슬롯을 생략하거나 다른 의미의 표정, 방향, 디테일, 소품, 의상 영역으로 바꾸지 말 것
- SD화는 새로운 마스코트를 만드는 것이 아니라 원본 캐릭터를 같은 정체성으로 SD 변환하는 것임
- 귀여워지더라도 원본의 나이대/성격/표정 인상, 얼굴 인상, 의상, 상징 디테일이 다른 캐릭터처럼 바뀌면 실패

피해야 할 것:
- photoreal
- semi-realistic painting
- adult fashion illustration
- normal anime proportions
- 3D render
- toy figure render
- plush mascot suit
- generic mascot replacement
- toddler/baby recasting when not requested
- changed identity
- changed outfit
- changed expression meaning
- merged or omitted image slots
- readable sheet labels, captions, section numbers, or pseudo annotation text

출력 형태:
- 고해상도
- 텍스트 없는 SD 캐릭터 레퍼런스 시트
- same canvas ratio and same panel/view structure as the original sheet
- no sheet labels, no captions, no section numbers, no pseudo annotation text
- preserve original in-image costume and prop typography as design detail
- clean 2D SD/chibi character sheet
```

## Execution Guidance

- Use image generation or image editing with the source sheet attached when available.
- Do not ask for sheet annotation text preservation in this stage; preserve original in-image costume/prop typography as part of the visual design.
- Treat the original sheet and `structure-inventory.md` as a layout/content lock: keep panel placement, view count, image-slot count, slot roles, non-text graphic frames, callout lines, empty sheet annotation areas, color chips, and in-image costume/prop typography.
- Treat the `Character Identity Lock` as a same-character contract: preserve age/maturity impression, face/personality impression, hair silhouette, outfit, palette, motif, expression intensity, and emotional impression while converting proportions into SD form.
- Treat the `SD Proportion Target` as the proportion contract. Do not keep normal body proportions when SD is requested, but do not over-babyfy the character unless requested.
- If the model changes the sheet structure, rerun with stronger "same layout, same panel grid" language.
- If the model merges, omits, duplicates, or changes the meaning of any source image slot, rerun with stronger "each source image slot must remain separate and semantically equivalent" language.
- If the model changes identity, outfit, age/maturity impression, face/personality impression, expression intensity, or signature details, rerun with stronger "same Character Identity Lock; do not recast the character" language.
- If the model keeps readable sheet annotation text or invents pseudo annotation text, rerun with stronger "remove all sheet labels/captions, keep empty boxes" language.

## Quality Check

Pass only when:

- Every character image slot reads as a coherent 2D SD/chibi character.
- Large head, compact body, simplified limbs, readable silhouette, and expressive face are present.
- The original canvas ratio, panel structure, major view groups, image-slot count, detail-panel positions, slot meanings, and non-text graphic structure are preserved.
- Character Identity Lock passes: face/personality impression, age/maturity impression, hair silhouette, outfit, palette, motifs, props, expression intensity, and emotional impression still match the source.
- SD Proportion Target passes consistently across slots.
- All readable sheet annotation text, labels, section numbers, captions, UI logo text, and fake annotation typography are absent.
- Original in-image typography on clothing, props, accessories, patches, embroidery, or engravings is preserved as character design detail.
- The result does not look photoreal, semi-real, normal-proportioned, 3D rendered, toy-like, plush-like, or generically mascot-replaced.

Report remaining risks to the workflow manager.
