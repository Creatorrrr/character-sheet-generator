---
name: intensify-photoreal-character
description: Refine a stage 1 character image that still looks too anime, illustrated, 3D rendered, CGI, plastic, or AI-smoothed. Use during 2D to photoreal character sheet workflows when the base image needs stronger live-action realism while keeping identity, pose, expression, layout, hair, and costume stable.
---

# Intensify Photoreal Character

## Overview

Use this stage after a text-free base exists but still carries 2D, CGI, 3D render, game asset, plastic skin, or overly polished AI traits. The goal is stronger real-camera realism without weakening the original expression or design identity.

## Inputs

Use the latest stage 1 image as input. Include the original 2D sheet only if it helps preserve identity or costume details.

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
- 레이아웃은 유지하되, 시각적으로 더 “실제 배우 사진 시트”처럼 보이게 조정
- 디지털 렌더링 느낌보다 다큐멘터리한 라이브액션 참고사진 느낌을 우선

결과물:
- ultra realistic
- live-action
- true photoreal
- natural skin
- realistic fabric
- no illustration look
- no CGI look
```

## Execution Guidance

- Diagnose the dominant artifact before running: anime proportions, CGI lighting, plastic skin, mannequin body, game-render material, or over-sharpening.
- Keep layout, pose, expression, hair, costume, and color relationships stable.
- Do not restore text in this stage.
- If only one area fails, ask the image tool for localized correction when possible.

## Quality Check

Pass only when:

- The result looks like a live-action photographed person.
- Skin and hair include believable natural irregularity.
- Clothing materials look sewn, worn, folded, and physically lit.
- The face is not overly symmetrical, waxy, doll-like, or plastic.

If it passes, hand the image to Stage 3. If it fails, repeat this stage with the failed artifact named explicitly.
