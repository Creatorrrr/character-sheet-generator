---
name: create-photoreal-character-base
description: Create the stage 1 text-free photoreal live-action base from a 2D character sheet. Use when converting a 2D character sheet into realistic photographed character reference images while preserving identity, hair, costume, pose, expression, and composition but intentionally omitting all text.
---

# Create Photoreal Character Base

## Overview

Generate or edit from the original 2D character sheet to produce a text-free photoreal character reference base. This stage prioritizes real human photography qualities over sheet text, UI, and labels.

## Inputs

Require the original 2D character sheet image. If the user has special identity constraints, include them before the prompt.

## Prompt

Use this prompt as the stage instruction:

```text
첨부한 2D 캐릭터 시트를 참고해서, 같은 캐릭터를 텍스트 없는 실사 캐릭터 레퍼런스 시트로 변환해줘.

가장 중요한 목표:
이 결과물은 실사풍 일러스트, 반실사 그림, 3D 캐릭터 렌더가 아니라, 실제 배우나 모델을 촬영한 라이브액션 캐릭터 레퍼런스 사진처럼 보여야 한다.

유지할 요소:
- 원본 캐릭터의 정체성
- 헤어스타일과 머리색
- 의상 디자인과 색상
- 포즈와 구도
- 표정과 감정
- 캐릭터 시트의 전체적인 구성감

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
- 텍스트는 이번 단계에서 재현하지 말 것
- 텍스트 박스나 설명 텍스트는 생략해도 됨
- 오직 캐릭터와 의상, 표정, 포즈, 실사화 자체의 완성도를 최우선으로 해줘

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
- multiple views / expressions if the original has them
- realistic live-action character reference sheet
- documentary studio reference photo sheet
```

## Execution Guidance

- Use image generation or image editing with the source sheet attached when available.
- Do not ask for text preservation in this stage.
- Preserve recognizable design traits even while converting anime proportions into believable human anatomy.
- If the model keeps text boxes, rerun with stronger "text-free" language.

## Quality Check

Pass only when:

- The character reads as a real photographed person.
- Skin, hair, clothing, lighting, and materials are plausibly physical.
- Text and labels are absent or visually irrelevant.
- The result does not look like anime, digital painting, 3D render, game asset, mannequin, doll, or glossy AI retouch.

Report remaining risks to the workflow manager.
