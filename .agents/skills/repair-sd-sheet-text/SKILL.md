---
name: repair-sd-sheet-text
description: Use when a finished SD/chibi character sheet has acceptable character images and layout but broken, blurry, fake, misaligned, or unreadable sheet annotation text that must be fixed without redrawing image slots.
---

# Repair SD Sheet Text

## Overview

Use this stage only after a text-inclusive SD/chibi character sheet mostly works but sheet annotation text needs cleanup. This stage must preserve the approved SD image set, Character Identity Lock, SD Proportion Target, layout, non-text graphics, and in-image costume/prop typography. It is not a general redraw stage.

## Inputs

Require:

- Latest Stage 3 or Stage 4 text-inclusive SD sheet.
- `final-sd-text-free-sheet.png` as the locked visual base.
- Original 2D character sheet as the sheet annotation text source.
- `structure-inventory.md` for original text-slot placement, image-slot contract, Character Identity Lock, and SD Proportion Target.
- A short list of text defects observed during self-verification.

## Prompt

Use this prompt as the stage instruction:

```text
이 SD 캐릭터 시트에서 시트 주석 텍스트와 라벨만 보정해줘.

목표:
- 깨지거나 흐릿하거나 가짜처럼 보이는 시트 주석 텍스트, 라벨, 제목, 섹션 번호, 캡션만 수리
- 캐릭터 이미지, 의상, 포즈, 표정, SD 비율, 패널, 레이아웃, 색상, 비문자 그래픽은 변경하지 않음
- final-sd-text-free-sheet.png의 승인된 SD 이미지 세트와 동일한 캐릭터 이미지 슬롯을 유지

반드시 유지:
- 모든 이미지 슬롯의 위치, 크기, 내용, 방향, 표정, 디테일 대상
- Character Identity Lock: 얼굴/눈 인상, 성격/감정 인상, 헤어 실루엣, 핵심 의상, 상징 소품, 팔레트, 모티프, 표정 강도
- SD Proportion Target: 큰 머리, 작은 몸, 짧은 팔다리, 일관된 SD 비율
- 의상/소품/액세서리/패치/자수/각인 타이포그래피
- 콜아웃 선, 박스, 컬러칩, 패널 테두리, 비문자 그래픽
- 전체 캔버스 비율과 페이지 구도

수정할 것:
- 원본 시트의 위치와 의미에 맞는 시트 주석 텍스트
- 깨진 글자, 뭉개진 글자, 가짜 글자, 오탈자처럼 보이는 라벨
- 라벨 정렬, 텍스트 박스 안 여백, 읽기 어려운 작은 글자

절대 하지 말 것:
- 캐릭터를 다시 그리거나 얼굴, 헤어, 의상, 소품, 포즈를 바꾸지 말 것
- 이미지 슬롯을 크롭, 이동, 재배치, 합치기, 생략하지 말 것
- SD 스타일을 photoreal, semi-real, 3D, toy, plush, normal anime proportions로 바꾸지 말 것
- 의상/소품 내부 타이포그래피를 새 라벨로 착각해서 덮어쓰지 말 것
- 새 패널 구조나 새 정보 구조를 만들지 말 것
- 텍스트 개선 때문에 캐릭터 이미지가 바뀌면 실패

출력:
- 같은 레이아웃의 최종 SD 캐릭터 시트
- sheet annotation text repaired and readable where possible
- approved SD image set unchanged
```

## Execution Guidance

- Use only for text defects when the SD character image set and layout already pass.
- Treat all image slots as locked. Text repair must not redraw, repaint, restyle, crop, replace, or otherwise modify the approved SD image set.
- Use `final-sd-text-free-sheet.png` to compare whether any image slot drifted.
- Use the original 2D sheet as the source of sheet annotation text and placement.
- If a text-only repair changes non-text content, reject it even if the text improves.
- If source text is too small or illegible, do not claim exact repair. Report approximate or manual overlay need.

## Quality Check

Pass only when:

- The repaired sheet annotation text is more readable or better aligned.
- The character image set is unchanged from the Stage 3 input and the approved text-free SD base.
- Character Identity Lock and SD Proportion Target remain unchanged.
- Layout, panel structure, image-slot count, slot meanings, non-text graphics, color chips, and callout lines remain unchanged.
- In-image costume/prop typography remains unchanged.
- No image slot was redrawn, replaced, cropped, shifted, restyled, or weakened.

Fail when:

- Any character image slot changes.
- SD proportions or identity drift.
- Text repair changes layout or non-text graphics.
- Text remains unreadable after the allowed attempts.

If text cannot be repaired without changing the approved SD image set, stop and report `수동 텍스트 오버레이 필요`.
