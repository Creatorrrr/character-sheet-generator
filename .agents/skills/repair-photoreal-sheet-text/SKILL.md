---
name: repair-photoreal-sheet-text
description: Repair only the sheet annotation text, labels, and text box alignment of a finished photoreal character sheet while preserving the character, face, skin, outfit, in-image typography, pose, expression, lighting, and overall layout. Use as optional stage 4 when the image is good but sheet annotation text is blurry, broken, misaligned, or hard to read.
---

# Repair Photoreal Sheet Text

## Overview

Use this optional final stage when the character and layout are acceptable but sheet annotation text quality is not. Keep edits minimal and scoped to sheet annotation text, labels, and text box alignment. Typography inside the character image, costume, props, accessories, patches, embroidery, or engravings is locked visual content, not repair text.

## Inputs

Require the finished photoreal character sheet. Use the original 2D sheet or user-provided sheet annotation text as the source of truth for labels and copy. When available, also use `final-photoreal-text-free-sheet.png` and `structure-inventory.md` to verify that sheet annotation text repair does not alter non-text structure, in-image costume/prop typography, or content.

## Prompt

Use this prompt as the stage instruction:

```text
이 최종 실사 캐릭터 시트 이미지를 유지한 채, 시트 주석 텍스트와 라벨만 더 읽기 쉽고 또렷하게 수정해줘.

유지할 것:
- 캐릭터의 실사 스타일
- 얼굴, 피부 질감, 의상 재질감
- 의상/소품/액세서리/패치/자수/각인 안의 기존 타이포그래피와 로고형 디자인
- 전체 레이아웃
- 포즈와 표정
- 시트의 구성
- 모든 비텍스트 이미지 슬롯의 개수와 내용

수정할 것:
- 깨지거나 흐린 시트 주석 텍스트
- 읽기 어려운 라벨
- 정렬이 어색한 텍스트 박스
- 가독성이 낮은 설명 문구

텍스트 처리 원칙:
- 가능한 한 원본 시트 주석 텍스트 내용 유지
- 시트 주석 텍스트는 또렷하고 자연스럽게
- 캐릭터 시트 디자인에 어울리는 방식으로 정리
- 폰트는 깔끔하고 가독성 좋은 스타일
- 실사 캐릭터가 핵심이므로 텍스트는 보조적이지만 분명하게 읽혀야 함
- 의상/소품 내부 타이포그래피는 수리 대상이 아니며 새 텍스트로 덮어쓰거나 정렬하지 않음

중요:
- 캐릭터나 의상의 실사 표현은 절대 약해지지 않게
- 시트 주석 텍스트만 개선하는 방향으로 최소 수정
- 의상/소품/액세서리 안의 기존 타이포그래피를 바꾸거나 제거하지 않게
- 이미지 슬롯을 합치거나 생략하거나 다른 의미의 표정, 방향, 디테일, 소품, 의상 영역으로 바꾸지 않게
```

## Execution Guidance

- Do not re-render the character unless sheet annotation text repair is impossible otherwise.
- If possible, provide exact replacement sheet annotation text to the image tool instead of asking it to infer text.
- Keep text boxes, labels, and alignment consistent with the existing layout.
- Compare the repaired result against both the Stage 3 input and `final-photoreal-text-free-sheet.png`; reject it if non-text panel structure, slot count, slot meaning, character, pose, clothing, in-image costume/prop typography, prop, expression, or detail content changed.
- If sheet annotation text remains unreliable after image editing, recommend a deterministic layout pass outside generative image editing.

## Quality Check

Pass only when:

- Character realism, pose, clothing, and layout remain stable.
- Non-text image slots and in-image costume/prop typography remain present, separate, and semantically unchanged.
- Sheet annotation text is visibly clearer than before.
- No new labels, incorrect words, or unintended design changes were introduced.

Report any sheet annotation text that still cannot be verified.
