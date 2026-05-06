---
name: intensify-photoreal-character
description: Refine a stage 1 text-free character sheet that still looks too anime, illustrated, 3D rendered, CGI, plastic, or AI-smoothed. Use during 2D to photoreal character sheet workflows when the base image needs stronger live-action realism while keeping identity, pose, expression, original sheet layout, empty sheet annotation areas, non-text graphics, hair, costume, and in-image typography stable.
---

# Intensify Photoreal Character

## Overview

Use this stage after a text-free, layout-locked base exists but still carries 2D, CGI, 3D render, game asset, plastic skin, or overly polished AI traits. The goal is stronger real-camera realism without weakening the original expression, design identity, sheet-annotation-free state, in-image costume/prop typography, or source-sheet structure.

## Inputs

Use the latest stage 1 image as input. Include `structure-inventory.md` when available, and include the original 2D sheet only if it helps preserve identity or costume details.

## Prompt

Use this prompt as the stage instruction:

```text
이 이미지를 기준으로, 2D 느낌과 3D 렌더링 느낌을 더 제거하고 훨씬 더 강한 실사 사진 느낌으로 보정해줘.

가장 중요한 목표:
이 이미지는 그림이나 렌더링처럼 보이면 안 되고, 실제 사람을 카메라로 촬영한 결과처럼 보여야 한다.

강화할 요소:
- 실제 인간 피부의 질감과 미세한 불균일성
- 자연스러운 모공, 잔피부결, 미세한 명암 변화
- 실제 사람 같은 얼굴 골격과 입체감
- 실제 머리카락의 가닥감, 잔머리, 자연스러운 볼륨
- 실제 의복의 재질감, 주름, 봉제선, 마찰 흔적
- 현실적인 조명과 그림자
- 실제 카메라 촬영 이미지 같은 자연스러움

반드시 줄일 요소:
- 애니메이션 비율
- 일러스트 선 느낌
- 3D 모델 같은 매끈함
- 게임 캐릭터 렌더 같은 표면감
- 과한 피부 보정
- 지나치게 완벽한 얼굴 대칭
- 지나치게 깨끗하고 인공적인 조명
- 과도한 샤프닝
- glossy AI smoothness
- plastic skin
- CGI 느낌

표정과 감정은 유지:
- 원본의 표정과 감정 전달력은 유지할 것
- 감정 표현이 약해지지 않게 할 것

중요:
- 원본 시트 기반 레이아웃은 절대 변경하지 말 것
- 패널 배치, 뷰 개수, 디테일 컷 위치, 빈 시트 주석 영역, 콜아웃 선, 컬러칩, 비문자 그래픽 장식은 그대로 유지할 것
- 모든 이미지 슬롯을 1:1로 유지할 것: 원본/입력 이미지의 각 슬롯은 개별 슬롯으로 남아야 하며 역할, 시점, 표정/감정, 디테일 대상, 소품/의상/신체 부위가 바뀌면 안 됨
- 둘 이상의 슬롯을 하나로 합치거나, 슬롯을 생략하거나, 같은 이미지를 반복해 다른 슬롯을 대체하지 말 것
- 새 시트 주석 텍스트, 가짜 주석 문자, 임의 라벨, 번호, 캡션을 만들지 말 것
- 입력 이미지에 이미 남아 있는 의상/소품/액세서리/패치/자수/각인 타이포그래피는 새 라벨로 취급하지 말고 실사화된 디자인 디테일로 유지할 것
- 시각적으로 더 “실제 배우 사진 시트”처럼 보이게 조정하되 실사감만 강화할 것
- 디지털 렌더링 느낌보다 다큐멘터리한 라이브액션 참고사진 느낌을 우선

결과물:
- ultra realistic
- live-action
- true photoreal
- natural skin
- realistic fabric
- same layout and panel structure
- no sheet labels, captions, section numbers, or pseudo annotation text
- preserve original in-image costume and prop typography
- no illustration look
- no CGI look
```

## Execution Guidance

- Diagnose the dominant artifact before running: anime proportions, CGI lighting, plastic skin, mannequin body, game-render material, or over-sharpening.
- Keep layout, panel placement, view count, image-slot count, slot meanings, detail crop positions, empty sheet annotation areas, pose, expression, hair, costume, in-image costume/prop typography, and color relationships stable.
- Do not restore sheet annotation text in this stage.
- Do not add new sheet annotation text, pseudo annotation text, labels, section numbers, or captions.
- If a candidate improves photorealism but merges, omits, duplicates, or changes the meaning of a source image slot, reject it instead of self-approving.
- If only one area fails, ask the image tool for localized correction when possible.

## Quality Check

Pass only when:

- The result looks like a live-action photographed person.
- Skin and hair include believable natural irregularity.
- Clothing materials look sewn, worn, folded, and physically lit.
- The original text-free sheet layout, panel structure, view positions, image-slot count, slot meanings, empty sheet annotation areas, in-image costume/prop typography, and non-text graphics remain stable.
- No readable sheet annotation text, labels, section numbers, captions, or fake annotation typography were added.
- The face is not overly symmetrical, waxy, doll-like, or plastic.

If it passes, hand the image to Stage 3. If it fails, repeat this stage with the failed artifact named explicitly.
