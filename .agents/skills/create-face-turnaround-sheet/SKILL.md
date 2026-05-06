---
name: create-face-turnaround-sheet
description: Generate a five-angle photoreal face turnaround sheet for a video-production character reference pack. Use when the user needs front, left 3/4, right 3/4, left side profile, and right side profile in one image to stabilize head rotation and avoid left/right mismatch.
---

# Create Face Turnaround Sheet

## Overview

Create one image containing all key head angles. This is the safest format when left and right directions must both be generated correctly.

## Prompt

```text
첨부한 실사화 캐릭터 시트 또는 승인된 마스터 얼굴 레퍼런스와 동일 인물로, 고개 회전용 얼굴 레퍼런스 시트를 생성해줘.

구성:
- 같은 조명, 같은 배경, 같은 표정
- 5개의 얼굴 각도
1. front view
2. left 3/4 view: 피사체의 코와 얼굴 방향이 이미지의 왼쪽을 향함
3. right 3/4 view: 피사체의 코와 얼굴 방향이 이미지의 오른쪽을 향함
4. left side profile: 완전 측면, 코가 이미지의 왼쪽을 향함
5. right side profile: 완전 측면, 코가 이미지의 오른쪽을 향함
- 텍스트 라벨 없이 이미지 배열만

목표:
영상 AI에서 캐릭터가 고개를 돌려도 같은 인물로 유지되도록 하는 얼굴 턴어라운드 레퍼런스.

유지:
- 동일한 얼굴형
- 동일한 헤어스타일
- 동일한 눈색
- 동일한 헤어 장식
- 동일한 의상 상단

스타일:
photorealistic actor head turnaround reference, live-action, realistic skin texture, consistent identity, no anime, no illustration, no CGI, no 3D render.
```

## Quality Check

Pass only when all five angles are present, left/right directions are correct, and every panel is the same person.
