---
name: create-full-body-side-reference
description: Generate a photoreal full-body side reference for a video-production character pack. Use when the user needs side silhouette, posture, hair profile, outfit thickness, accessories, shoes, and body proportions stabilized for video AI.
---

# Create Full Body Side Reference

## Overview

Create a neutral full-body side view. If the user cares about left or right direction, state it explicitly in the prompt.

## Prompt

```text
첨부한 실사화 캐릭터 시트 또는 승인된 마스터 레퍼런스와 동일 인물로, 전신 측면 실사 레퍼런스 이미지를 생성해줘.

구도:
- head-to-toe full body side view
- 자연스러운 중립 스탠딩 포즈
- 얼굴 프로필, 헤어 실루엣, 의상 두께감이 보이게
- 단순한 스튜디오 배경과 바닥

유지:
- 동일한 얼굴 프로필과 헤어스타일
- 동일한 의상 구조와 소재
- 액세서리, 신발, 하단 의상까지 포함
- 실제 사람의 무게중심과 자세

목표:
영상 AI가 걷거나 방향을 바꾸는 장면에서 측면 실루엣과 의상 두께감을 유지하게 하는 기준 이미지.

금지:
distorted legs, floating feet, mannequin pose, random outfit changes, 3D render, CGI, text.
```

## Quality Check

Pass only when the side silhouette is clear and the full outfit remains consistent.
