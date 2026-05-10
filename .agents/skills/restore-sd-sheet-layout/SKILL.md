---
name: restore-sd-sheet-layout
description: Use when restoring original sheet annotation text onto a self-approved text-free SD/chibi character sheet without changing the SD character image set, layout, panels, non-text graphics, identity, costume, or in-image typography.
---

# Restore SD Sheet Layout

## Overview

Use this stage after the text-free SD/chibi character sheet is self-approved. Add the original 2D sheet's sheet annotation text and labels onto the text-free sheet while keeping the character, Character Identity Lock, SD Proportion Target, panels, view positions, non-text graphics, and in-image costume/prop typography fully locked.

## Inputs

Require:

- `final-sd-text-free-sheet.png` or the latest self-approved text-free SD sheet from Stage 1 or Stage 2.
- Original 2D character sheet for layout and text reference.
- `structure-inventory.md` for the original section/panel/image-slot/text-slot contract, Character Identity Lock, and SD Proportion Target.

Inspect the original first and note any unreadable source sheet annotation text before generation. The text-free SD sheet is the visual base and the locked SD image-set source of truth; the original 2D sheet is only the sheet annotation text source of truth and placement reference. Any typography already present inside the character image, costume, props, accessories, patches, embroidery, or engravings is locked visual content, not text to restore.

## Prompt

Use this prompt as the stage instruction:

```text
방금 완성된 무텍스트 SD 캐릭터 시트를 기준으로, 원본 2D 캐릭터 시트의 시트 주석 텍스트와 라벨만 원래 위치에 복원해서 텍스트 포함 최종 SD 캐릭터 시트로 만들어줘.

목표:
- 캐릭터와 의상은 이미 완성된 무텍스트 SD 시트 그대로 유지
- Character Identity Lock과 SD Proportion Target은 그대로 유지
- 캔버스 비율, 패널 그리드, 뷰 배치, 디테일 컷 위치, 콜아웃 선, 박스, 컬러칩, 비문자 그래픽은 변경하지 않음
- 무텍스트 SD 시트의 모든 이미지 슬롯을 그대로 유지: 슬롯 개수, 위치, 개별 이미지 내용, 시점, 표정/감정, 디테일 대상, 소품/의상/신체 부위, SD 스타일은 절대 바꾸지 않음
- 원본 2D 시트는 텍스트와 위치 참조로만 사용하고, 이미지 슬롯의 시각적 기준은 무텍스트 SD 시트로 고정
- 무텍스트 SD 시트에 이미 남아 있는 의상/소품/액세서리/패치/자수/각인 타이포그래피는 그대로 유지하고 덮어쓰지 않음
- 원본 캐릭터 시트의 시트 주석 텍스트, 라벨, 제목, 섹션 번호, 설명문만 원래 위치에 복원

유지할 것:
- SD/chibi 캐릭터 스타일
- 큰 머리, 작은 몸, 단순한 팔다리, 읽기 쉬운 실루엣
- 캐릭터 정체성, 의상, 소품, 헤어, 표정
- 의상/소품/액세서리/이미지 슬롯 내부의 기존 타이포그래피와 로고형 디자인
- 포즈 및 전반적인 시트 구성
- 무텍스트 최종본의 패널 배치와 비문자 그래픽

복원할 것:
- 원본 시트의 제목, 섹션 번호, 라벨, 설명문, 캡션, UI 로고 텍스트, 모델명, 버전 표기
- 원본과 대응되는 위치의 텍스트 박스와 라벨 영역 내부 텍스트
- 텍스트의 시각적 위계와 정렬

복원 대상이 아닌 것:
- 무텍스트 SD 시트에 이미 들어 있는 의상 프린트, 로고형 패치, 자수, 소품 각인, 액세서리 문양 같은 이미지 슬롯 내부 타이포그래피
- 이런 인이미지 타이포그래피는 캐릭터/소품 디자인 디테일로 보고 새 텍스트로 덮어쓰거나 정렬하지 말 것

텍스트 관련:
- 원본 캐릭터 시트의 시트 주석 텍스트 내용을 가능한 한 정확하고 읽기 쉽게 복원
- 텍스트가 깨지지 않도록 또렷하게 배치
- 원본 문구가 잘 보이도록 정리
- 텍스트는 SD 캐릭터를 방해하지 않게 깔끔한 캐릭터 시트 디자인으로 정리
- 텍스트가 너무 많으면 원문을 최대한 유지하되 가독성을 최우선으로 조정

중요:
- 새 레이아웃을 만들거나 패널을 재배치하지 말 것
- 캐릭터, 의상, 배경, 이미지 슬롯, 디테일 컷, 콜아웃 선, 박스, 컬러칩 등 비문자 요소는 다시 그리지 말 것
- 텍스트 복원 과정에서 둘 이상의 이미지 슬롯을 하나로 합치거나, 이미지 슬롯을 생략하거나, 슬롯의 의미를 다른 표정/방향/디테일/소품으로 바꾸지 말 것
- 텍스트 복원 과정에서 의상/소품/액세서리 안의 기존 타이포그래피를 바꾸거나 제거하지 말 것
- 무텍스트 SD 시트에 있던 이미지 내용을 새로 생성한 다른 내용으로 대체하지 말 것
- 텍스트가 좋아져도 캐릭터 정체성, SD 비율, 의상, 표정, 슬롯 의미가 바뀌면 실패
- 어떤 이미지 슬롯도 photoreal, semi-real, 3D render, toy render, plush mascot, normal anime proportions로 바꾸지 말 것

피해야 할 것:
- 캐릭터가 다른 스타일로 변하는 것
- 이미지 슬롯 일부가 다시 정상 비율 캐릭터처럼 보이는 것
- 원본과 다른 패널 배치나 새 UI 구조
- 무텍스트 최종본의 캐릭터, 포즈, 디테일 컷, 비문자 그래픽 변경
- 텍스트가 깨지거나 뭉개지는 것
- 지나치게 화려한 UI로 캐릭터가 묻히는 것

출력:
- 고해상도 최종본
- readable sheet annotation text
- same layout as the text-free SD sheet
- polished SD/chibi character sheet
```

## Execution Guidance

- Treat the SD character image set as locked. Do not restyle the face, hair, body, outfit, or props to match graphic elements.
- Treat the Character Identity Lock and SD Proportion Target as locked.
- Treat the text-free SD sheet and `structure-inventory.md` as locked. Do not change panel layout, view grouping, image-slot count, slot meanings, detail crop positions, non-text graphics, empty structural elements, or the approved SD image set.
- Use the original 2D sheet only for sheet annotation text and placement. Do not use it as the visual style source for any image slot during Stage 3.
- Treat every image slot in the text-free SD sheet as locked visual content: it must keep the same location, count, role, content, view, crop target, detail target, and SD/chibi style.
- If source sheet annotation text is unreadable, report that before claiming exact restoration.
- If sheet annotation text generation changes identity, SD proportions, layout, character content, in-image costume/prop typography, any non-text image-slot content, or the SD style of any image slot, fail this stage and retry with stronger "sheet annotation text-only edit; do not redraw non-text slots" language.

## Quality Check

Pass only when:

- The character image set still looks like the approved SD/chibi text-free base.
- Layout, panel positions, view groups, image-slot count, slot meanings, non-text graphics, in-image costume/prop typography, and character content match the self-approved text-free sheet and original inventory.
- Every image slot matches the approved text-free SD image set in location, count, role, content, view, crop target, detail target, and SD/chibi style.
- Character Identity Lock and SD Proportion Target still match the approved text-free sheet.
- No image slot was redrawn, replaced, or regressed into photoreal, semi-real, 3D render, toy render, plush mascot, or normal anime proportions.
- Sheet annotation text and labels are readable enough for the user's target.
- Graphic elements support the sheet without overpowering the character.

If text is the only remaining problem and the approved SD image set plus Character Identity Lock are unchanged, hand the image to Stage 4 instead of regenerating the whole sheet. If layout, character, identity, SD proportions, slot count, slot content, or image-slot style changed, retry Stage 3 as a stricter text-only pass.
