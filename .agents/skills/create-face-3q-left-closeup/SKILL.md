---
name: create-face-3q-left-closeup
description: Generate the left-facing 3/4 face closeup for a video-production photoreal character reference pack. Use when only the left 3/4 face view is needed; if both left and right 3/4 views are requested, the manager skill must combine them into one paired image request.
---

# Create Face 3Q Left Closeup

## Overview

Create one left-facing 3/4 portrait. If the user also needs the right-facing 3/4 portrait, use the manager's paired-image rule instead of separate generation.

## Prompt

```text
첨부한 실사화 캐릭터 시트 또는 승인된 마스터 얼굴 레퍼런스와 동일 인물로, left-facing 3/4 view 얼굴 클로즈업 레퍼런스 이미지를 생성해줘.

구도:
- 3/4 view portrait
- 피사체의 코와 얼굴 방향이 이미지의 왼쪽을 향하게
- 눈은 카메라를 자연스럽게 바라봄
- 어깨 위까지 보이는 클로즈업
- 배경은 단순한 스튜디오 배경

유지:
- 동일한 얼굴형과 눈매
- 동일한 헤어스타일과 머리색
- 동일한 의상 상단 디테일
- 캐릭터의 원래 분위기와 표정 톤

목표:
영상 AI가 고개를 왼쪽으로 돌린 장면에서도 같은 인물로 인식할 수 있도록 만드는 고해상도 레퍼런스.

스타일:
true photorealistic live-action character reference photo, natural skin texture, realistic hair strands, soft but realistic lighting, no CGI, no illustration, no 3D render.
```

## Quality Check

Pass only when the subject clearly turns toward image-left while identity, hair, outfit, and realism remain stable.
