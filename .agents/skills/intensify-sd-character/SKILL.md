---
name: intensify-sd-character
description: Use when a text-free SD character sheet still looks too normal-proportioned, adult, photoreal, semi-real, generic mascot, inconsistent, over-detailed, or not clearly chibi/super-deformed while the original layout and identity must stay locked.
---

# Intensify SD Character

## Overview

Use this stage after a text-free, layout-locked base exists but still does not read clearly as SD/chibi, or its SD style is inconsistent across panels. The goal is stronger super-deformed readability without weakening the original expression, Character Identity Lock, SD Proportion Target, sheet-annotation-free state, in-image costume/prop typography, or source-sheet structure.

## Inputs

Use the latest Stage 1 image as input. Include `structure-inventory.md` and its Character Identity Lock and SD Proportion Target when available, and include the original 2D sheet only if it helps preserve identity or costume details.

## Prompt

Use this prompt as the stage instruction:

```text
이 이미지를 기준으로, 캐릭터를 더 명확하고 일관된 SD/chibi 스타일로 보정해줘.

여기서 SD는 Stable Diffusion이 아니라 super-deformed/chibi 캐릭터 스타일을 뜻한다.

가장 중요한 목표:
- 이미지 전체의 기존 레이아웃과 패널 구조는 그대로 유지
- 각 이미지 슬롯의 캐릭터를 더 분명한 2D SD 캐릭터로 보이게 조정
- 원본 캐릭터 정체성, 의상, 소품, 표정, 포즈, 이미지 슬롯 의미는 변경하지 않음
- 새 시트 주석 텍스트나 가짜 글자를 만들지 않음

강화할 요소:
- 큰 머리와 작은 몸의 SD 비율
- 짧고 단순한 팔다리
- 읽기 쉬운 손/발 형태
- 선명한 얼굴 표정과 감정
- 귀엽고 압축된 실루엣
- 패널 전체에 일관된 SD 비율과 스타일
- 의상 디테일을 SD 크기에 맞게 단순화하되 핵심 형태는 유지
- 헤어 실루엣과 장식의 식별성

반드시 유지할 요소:
- 캔버스 비율, 패널 배치, 이미지 슬롯 수, 디테일 컷 위치
- 콜아웃 선, 박스, 컬러칩, 비문자 그래픽
- Character Identity Lock: 나이대/성숙도 인상, 성격/감정 인상, 얼굴과 눈의 인상, 헤어 실루엣, 핵심 의상, 상징 소품, 팔레트, 모티프, 표정 강도
- SD Proportion Target: 지정되거나 추론된 SD 비율
- 원본/입력 이미지의 각 슬롯 역할, 방향, 표정, 포즈, 디테일 대상
- 의상/소품/액세서리/패치/자수/각인 타이포그래피
- 텍스트 없는 상태

중요:
- 정상 비율 캐릭터처럼 보이면 안 됨
- 실사, 반실사, 3D 장난감, 인형, plush mascot처럼 만들지 말 것
- 캐릭터를 새로운 마스코트로 바꾸지 말 것
- 원본보다 어려 보이게 단순화하더라도 유아/아기처럼 재해석하지 말 것, 사용자가 명시하지 않은 경우에만
- 둘 이상의 슬롯을 합치거나 생략하지 말 것
- 같은 이미지를 반복해서 다른 슬롯을 대체하지 말 것
- 시트 주석 텍스트, 라벨, 캡션, 번호, 가짜 글자를 만들지 말 것

결과물:
- stronger clean 2D SD/chibi character sheet
- same layout and panel structure
- no sheet labels, captions, section numbers, or pseudo annotation text
- preserve original in-image costume and prop typography
- consistent SD proportions across image slots
```

## Execution Guidance

- Diagnose the dominant issue before running: normal proportions, weak chibi proportions, inconsistent head/body ratio, over-detailed outfit, generic mascot drift, photoreal/semi-real rendering, toy/3D material, or identity drift.
- Keep layout, panel placement, view count, image-slot count, slot meanings, detail crop positions, empty sheet annotation areas, pose, expression, hair, costume, in-image costume/prop typography, color relationships, Character Identity Lock, and SD Proportion Target stable.
- Do not restore sheet annotation text in this stage.
- Do not add new sheet annotation text, pseudo annotation text, labels, section numbers, or captions.
- If a candidate improves SD style but merges, omits, duplicates, or changes the meaning of a source image slot, reject it instead of self-approving.
- If a candidate improves SD style but changes identity, outfit, age/maturity impression, expression intensity, hair silhouette, or same-character impression, reject it instead of self-approving.
- If only one area fails, ask the image tool for localized correction when possible.

## Quality Check

Pass only when:

- Every image slot clearly reads as SD/chibi.
- SD proportions are consistent with the SD Proportion Target.
- The original text-free sheet layout, panel structure, view positions, image-slot count, slot meanings, empty sheet annotation areas, in-image costume/prop typography, and non-text graphics remain stable.
- Character Identity Lock still passes, including age/maturity impression, face/personality impression, hair silhouette, outfit, palette, props, expression intensity, and emotional impression.
- No readable sheet annotation text, labels, section numbers, captions, or fake annotation typography were added.
- The result does not look photoreal, semi-real, 3D rendered, toy-like, plush-like, normal-proportioned, or generically mascot-replaced.

If it passes, hand the image to Stage 3. If it fails, repeat this stage with the failed artifact named explicitly.
