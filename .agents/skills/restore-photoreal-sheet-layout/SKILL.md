---
name: restore-photoreal-sheet-layout
description: Rebuild the final photoreal character sheet by combining an approved live-action character image with the original 2D sheet layout, information structure, views, text boxes, and readable labels. Use as stage 3 after photoreal character quality is accepted.
---

# Restore Photoreal Sheet Layout

## Overview

Use this stage after the photoreal character base is approved. Restore the character sheet layout and text structure while keeping the character itself fully live-action and photographic.

## Inputs

Require:

- Approved photoreal character image from Stage 1 or Stage 2.
- Original 2D character sheet for layout and text reference.

If exact text matters, inspect the original first and note any unreadable source text before generation.

## Prompt

Use this prompt as the stage instruction:

```text
방금 완성된 실사 캐릭터 이미지를 기준으로, 원본 2D 캐릭터 시트의 정보 구조와 레이아웃을 참고하여 최종 실사 캐릭터 시트로 정리해줘.

목표:
- 캐릭터와 의상은 이미 완성된 실사 스타일을 그대로 유지
- 원본 캐릭터 시트의 구성과 정보 전달 방식은 최대한 유지
- 최종 결과물은 “실제 배우를 기준으로 만든 실사 캐릭터 디자인 시트”처럼 보여야 함

유지할 것:
- 실사 얼굴과 피부 질감
- 현실적인 의상 재질과 디테일
- 자연스러운 표정과 감정
- 캐릭터 정체성
- 포즈 및 전반적인 시트 구성

복원할 것:
- 캐릭터 시트 레이아웃
- 각 뷰 배치
- 표정/포즈 설명용 레이아웃
- 텍스트 박스 위치와 정보 구조
- 원본 시트의 시각적 정리 방식

텍스트 관련:
- 원본 캐릭터 시트의 텍스트 내용을 가능한 한 정확하고 읽기 쉽게 복원
- 텍스트가 깨지지 않도록 또렷하게 배치
- 원본 문구가 잘 보이도록 정리
- 텍스트는 실사 캐릭터를 방해하지 않게 깔끔한 캐릭터 시트 디자인으로 정리
- 텍스트가 너무 많으면 원문을 최대한 유지하되 가독성을 최우선으로 조정

중요:
- 캐릭터만 다시 2D처럼 보이지 않게 할 것
- 텍스트와 그래픽 요소를 추가하더라도 캐릭터 본체는 끝까지 완전 실사 느낌 유지
- 최종 결과는 실사 인물 사진 기반의 캐릭터 시트여야 함

피해야 할 것:
- 캐릭터가 다시 일러스트처럼 보이는 것
- 3D 모델 시트처럼 보이는 것
- 텍스트가 깨지거나 뭉개지는 것
- 지나치게 화려한 UI로 캐릭터가 묻히는 것

출력:
- 고해상도 최종본
- readable text
- polished live-action character sheet
- realistic character design reference board
```

## Execution Guidance

- Treat character realism as locked. Do not restyle the face, skin, hair, or outfit to match graphic elements.
- Use the original sheet mainly for layout hierarchy, label placement, view grouping, and information structure.
- If source text is unreadable, report that before claiming exact restoration.
- If text generation degrades the character, rerun with less text or reserve text cleanup for Stage 4.

## Quality Check

Pass only when:

- The character still looks photographic and live-action.
- Layout resembles a usable character reference sheet.
- Text and labels are readable enough for the user's target.
- Graphic elements support the sheet without overpowering the character.

If text is the only remaining problem, hand the image to Stage 4 instead of regenerating the whole sheet.
