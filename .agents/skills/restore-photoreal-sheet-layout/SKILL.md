---
name: restore-photoreal-sheet-layout
description: Restore original text onto a self-approved text-free photoreal character sheet. Use as stage 3 after the text-free sheet already preserves the original 2D sheet layout, character realism, panels, views, and non-text graphics; this stage should add readable labels and copy without changing character, layout, or graphics.
---

# Restore Photoreal Sheet Layout

## Overview

Use this stage after the text-free photoreal character sheet is self-approved. Add the original 2D sheet's text and labels onto the text-free sheet while keeping the character, panels, view positions, and non-text graphics fully locked.

## Inputs

Require:

- `final-photoreal-text-free-sheet.png` or the latest self-approved text-free photoreal sheet from Stage 1 or Stage 2.
- Original 2D character sheet for layout and text reference.

Inspect the original first and note any unreadable source text before generation. The text-free photoreal sheet is the visual base; the original 2D sheet is the text source of truth.

## Prompt

Use this prompt as the stage instruction:

```text
방금 완성된 무텍스트 실사 캐릭터 시트를 기준으로, 원본 2D 캐릭터 시트의 텍스트와 라벨만 원래 위치에 복원해서 텍스트 포함 최종 실사 캐릭터 시트로 만들어줘.

목표:
- 캐릭터와 의상은 이미 완성된 무텍스트 실사 시트 그대로 유지
- 캔버스 비율, 패널 그리드, 뷰 배치, 디테일 컷 위치, 콜아웃 선, 박스, 컬러칩, 비문자 그래픽은 변경하지 않음
- 원본 캐릭터 시트의 텍스트, 라벨, 제목, 섹션 번호, 설명문만 원래 위치에 복원
- 최종 결과물은 “실제 배우를 기준으로 만든 실사 캐릭터 디자인 시트”처럼 보여야 함

유지할 것:
- 실사 얼굴과 피부 질감
- 현실적인 의상 재질과 디테일
- 자연스러운 표정과 감정
- 캐릭터 정체성
- 포즈 및 전반적인 시트 구성
- 무텍스트 최종본의 패널 배치와 비문자 그래픽

복원할 것:
- 원본 시트의 제목, 섹션 번호, 라벨, 설명문, 캡션, 로고 텍스트, 모델명, 버전 표기
- 원본과 대응되는 위치의 텍스트 박스와 라벨 영역 내부 텍스트
- 텍스트의 시각적 위계와 정렬

텍스트 관련:
- 원본 캐릭터 시트의 텍스트 내용을 가능한 한 정확하고 읽기 쉽게 복원
- 텍스트가 깨지지 않도록 또렷하게 배치
- 원본 문구가 잘 보이도록 정리
- 텍스트는 실사 캐릭터를 방해하지 않게 깔끔한 캐릭터 시트 디자인으로 정리
- 텍스트가 너무 많으면 원문을 최대한 유지하되 가독성을 최우선으로 조정

중요:
- 새 레이아웃을 만들거나 패널을 재배치하지 말 것
- 캐릭터, 의상, 배경, 콜아웃 선, 박스, 컬러칩 등 비문자 요소는 다시 그리지 말 것
- 캐릭터만 다시 2D처럼 보이지 않게 할 것
- 텍스트와 그래픽 요소를 추가하더라도 캐릭터 본체는 끝까지 완전 실사 느낌 유지
- 최종 결과는 실사 인물 사진 기반의 캐릭터 시트여야 함

피해야 할 것:
- 캐릭터가 다시 일러스트처럼 보이는 것
- 3D 모델 시트처럼 보이는 것
- 원본과 다른 패널 배치나 새 UI 구조
- 무텍스트 최종본의 캐릭터, 포즈, 디테일 컷, 비문자 그래픽 변경
- 텍스트가 깨지거나 뭉개지는 것
- 지나치게 화려한 UI로 캐릭터가 묻히는 것

출력:
- 고해상도 최종본
- readable text
- same layout as the text-free photoreal sheet
- polished live-action character sheet
- realistic character design reference board
```

## Execution Guidance

- Treat character realism as locked. Do not restyle the face, skin, hair, or outfit to match graphic elements.
- Treat the text-free photoreal sheet as locked. Do not change panel layout, view grouping, detail crop positions, non-text graphics, or empty structural elements.
- Use the original sheet as the text source of truth and placement reference.
- If source text is unreadable, report that before claiming exact restoration.
- If text generation degrades the character, rerun with less text or reserve text cleanup for Stage 4.
- If text generation changes layout or character content, fail this stage and retry with stronger "text-only edit" language.

## Quality Check

Pass only when:

- The character still looks photographic and live-action.
- Layout, panel positions, view groups, non-text graphics, and character content match the self-approved text-free sheet.
- Text and labels are readable enough for the user's target.
- Graphic elements support the sheet without overpowering the character.

If text is the only remaining problem, hand the image to Stage 4 instead of regenerating the whole sheet. If layout or character changed, retry Stage 3 as a stricter text-only pass.
