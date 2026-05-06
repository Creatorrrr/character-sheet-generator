---
name: create-photoreal-character-base
description: Create the stage 1 text-free photoreal live-action sheet from a 2D character sheet. Use when converting a 2D character sheet into a realistic photographed character sheet while preserving the original canvas, panel layout, view positions, non-text graphics, identity, hair, costume, pose, and expression, but removing all readable text.
---

# Create Photoreal Character Base

## Overview

Generate or edit from the original 2D character sheet to produce a text-free photoreal character sheet with the same structure as the source. This stage prioritizes real human photography while locking the original sheet layout and removing only readable text.

## Inputs

Require the original 2D character sheet image. If the user has special identity constraints, include them before the prompt.

## Prompt

Use this prompt as the stage instruction:

```text
첨부한 2D 캐릭터 시트를 기준으로, 원본과 동일한 캔버스 비율과 패널 구조를 유지한 텍스트 없는 실사 캐릭터 시트로 변환해줘.

가장 중요한 목표:
이 결과물은 실사풍 일러스트, 반실사 그림, 3D 캐릭터 렌더가 아니라, 실제 배우나 모델을 촬영한 라이브액션 캐릭터 레퍼런스 사진처럼 보여야 한다.
원본 시트를 자유롭게 재구성하지 말고, 읽히는 글자만 제거한 상태로 원본 구조를 유지해야 한다.

유지할 요소:
- 원본 캔버스 비율과 전체 페이지 구도
- 원본 패널 그리드와 섹션 위치
- 큰 전신 정면도, 턴어라운드, 얼굴/눈 디테일, 의상 디테일, 하체/소품 디테일, 프로필/키포인트 패널의 위치와 크기 관계
- 콜아웃 선, 박스, 패널 테두리, 컬러칩, 비문자 그래픽 장식
- 원본 캐릭터의 정체성
- 헤어스타일과 머리색
- 의상 디자인과 색상
- 포즈와 구도
- 표정과 감정

제거할 텍스트 범위:
- 제목, 섹션 번호, 라벨, 설명문, 캡션, 로고 텍스트, 모델명, 버전 표기 등 읽히는 글자는 모두 제거
- 가짜 문자, 깨진 문자, 임의의 새 라벨도 만들지 말 것
- 텍스트가 있던 박스, 선, 빈 라벨 자리, 패널 구조는 가능한 한 유지하되 내부 글자만 비워둘 것

변환 방향:
- 얼굴은 애니메이션식 비율이 아니라 실제 인간의 얼굴 비율과 골격으로 자연스럽게 변환
- 피부는 실제 피부 질감이 보이게 표현: 미세한 모공, 자연스러운 피부결, 약간의 비대칭, 자연스러운 혈색
- 눈, 코, 입, 턱선, 귀가 실제 사람처럼 자연스럽게 연결되게
- 머리카락은 실제 머리카락처럼 가닥감과 잔머리가 보이게
- 의상은 현실에서 제작된 옷처럼 표현: 실제 원단, 봉제선, 주름, 두께감, 재질감, 착용감
- 금속, 가죽, 플라스틱, 천 등 각 소재가 현실적으로 구분되게
- 조명은 과하게 완벽한 CG 조명이 아니라 현실적인 촬영 조명으로 표현
- 선명하지만 과도하게 샤프하지 않게
- 자연스러운 카메라 사진 느낌, 라이브액션 캐릭터 디자인 레퍼런스 사진 시트 느낌

중요:
- 텍스트는 이번 단계에서 절대 재현하지 말 것
- 원본 시트의 구조를 단순화하거나 새 레퍼런스 보드로 재배치하지 말 것
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
- cosplay poster look
- unreal beauty retouching

출력 형태:
- 고해상도
- 텍스트 없는 실사 캐릭터 레퍼런스 시트
- same canvas ratio and same panel/view structure as the original sheet
- no readable text, no labels, no numbers, no fake typography
- realistic live-action character reference sheet
- documentary studio reference photo sheet
```

## Execution Guidance

- Use image generation or image editing with the source sheet attached when available.
- Do not ask for text preservation in this stage.
- Treat the original sheet as a layout lock: keep panel placement, view count, non-text graphic frames, callout lines, empty text areas, and color chips.
- Preserve recognizable design traits even while converting anime proportions into believable human anatomy.
- If the model changes the sheet structure, rerun with stronger "same layout, same panel grid" language.
- If the model keeps readable text or invents pseudo text, rerun with stronger "remove all readable text, keep empty boxes" language.

## Quality Check

Pass only when:

- The character reads as a real photographed person.
- Skin, hair, clothing, lighting, and materials are plausibly physical.
- The original canvas ratio, panel structure, major view groups, detail-panel positions, and non-text graphic structure are preserved.
- All readable text, labels, section numbers, captions, logo text, and fake typography are absent.
- The result does not look like anime, digital painting, 3D render, game asset, mannequin, doll, or glossy AI retouch.

Report remaining risks to the workflow manager.
