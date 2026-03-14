# to_wildcard.py 사용 가이드

> 최종 업데이트: 2026-03-15
> 환경: WSL2 / Ubuntu-24.04 / Python 3.12
> 요구사항: Python 3.10+ (표준 라이브러리만 사용, 별도 설치 없음)

---

## 목차

1. [개요](#1-개요)
2. [지원 입력 형식](#2-지원-입력-형식)
3. [실행 방법](#3-실행-방법)
4. [출력 형식](#4-출력-형식)
5. [실 사용 예제](#5-실-사용-예제)
6. [형식 자동 감지 로직](#6-형식-자동-감지-로직)

---

## 1. 개요

`prompts.txt` 또는 `prompts_raw.txt`를 **ComfyUI ImpactPack 와일드카드 형식**으로 변환한다.

### ComfyUI 와일드카드 형식

```
프롬프트1 한 줄 내용...
프롬프트2 한 줄 내용...
프롬프트3 한 줄 내용...
```

- **한 줄 = 한 프롬프트** (줄 내부에 `\n` 없음)
- 프롬프트 사이 빈 줄 없음
- 파일을 ImpactPack 와일드카드 폴더에 배치하면 랜덤 또는 순차 선택 가능

### 현행 `prompts.txt`와의 관계

현행 버전의 `prompts.txt`(prompt_generator_v2.py, gemini_batch.py 출력)는 이미 와일드카드 형식으로 생성된다.
이 스크립트가 필요한 경우:

| 상황 | 변환 필요 여부 |
|------|--------------|
| 현행 `prompts.txt` | 불필요 (이미 와일드카드 형식) |
| `prompts_raw.txt` (--- 구분자) | **필요** |
| 구버전 `prompts.txt` (빈 줄 구분) | **필요** |
| 여러 폴더 결과를 하나로 합치기 | **필요** |

---

## 2. 지원 입력 형식

### 형식 1 — 구버전: 빈 줄(`\n\n`) 구분

구버전 `prompt_generator_v2.py`가 생성한 파일. 프롬프트 내 단락도 빈 줄로 구분되어 있어 경계가 모호하다.

```
프롬프트1 첫 단락

프롬프트1 둘째 단락

프롬프트2 첫 단락
```

### 형식 2 — 신버전: `---` 구분자

현행 `prompts_raw.txt` 형식. 프롬프트 내 단락 구조를 보존하면서 프롬프트 간 경계가 명확하다.

```
프롬프트1 첫 단락

프롬프트1 둘째 단락
---
프롬프트2 첫 단락

프롬프트2 둘째 단락
```

### 형식 3 — 단일 줄: 현행 `prompts.txt`

한 줄 = 한 프롬프트. 이미 와일드카드 형식과 동일하다.

```
프롬프트1 전체 내용 한 줄...
프롬프트2 전체 내용 한 줄...
```

---

## 3. 실행 방법

### 기본 구문

```bash
python3 scripts/to_wildcard.py <입력파일> [-o <출력파일>]
```

### 단일 파일 변환

```bash
python3 scripts/to_wildcard.py output/2026-03-15-053817-m7/prompts_raw.txt
# → output/2026-03-15-053817-m7/prompts-wildcard.txt 생성
```

### 출력 경로 지정

```bash
python3 scripts/to_wildcard.py output/폴더/prompts_raw.txt -o wildcards/dataset.txt
```

### 여러 파일을 하나로 합치기

출력 경로(`-o`)를 지정하고 여러 파일을 나열하면 하나의 파일로 병합한다.

```bash
python3 scripts/to_wildcard.py output/*/prompts_raw.txt -o wildcards/all.txt
```

```bash
python3 scripts/to_wildcard.py \
  output/2026-03-15-053817-m7/prompts_raw.txt \
  output/2026-03-14-120000-m6/prompts.txt \
  -o wildcards/combined.txt
```

---

## 4. 출력 형식

모든 입력 형식에 관계없이 동일한 와일드카드 형식으로 출력된다.

```
A young woman in a fitted white satin mini dress stands facing the camera with her arms relaxed at her sides...
A mystical woman stands in a dimly lit stone chamber, her upper body barely covered by translucent white gauze...
An interior living room features exposed concrete walls and warm tungsten pendant lighting...
```

- 각 프롬프트의 내부 줄바꿈(`\n`)은 공백으로 압축
- 프롬프트 사이 빈 줄 없음
- 파일 끝에 `\n` 하나

---

## 5. 실 사용 예제

### m7 폴더 prompts_raw.txt 변환

```bash
python3 scripts/to_wildcard.py output/2026-03-15-053817-m7/prompts_raw.txt
```

출력:
```
[--- 구분자] prompts_raw.txt → output/2026-03-15-053817-m7/prompts-wildcard.txt (15개)

완료: 15개 프롬프트 변환
```

### 구버전 파일 변환

```bash
python3 scripts/to_wildcard.py output/old_folder/prompts.txt
```

출력:
```
[빈 줄 구분] prompts.txt → output/old_folder/prompts-wildcard.txt (38개)

완료: 38개 프롬프트 변환
```

> 구버전 형식은 프롬프트 내 단락도 빈 줄로 구분되어 있어, 단락 수가 이미지 수보다 많을 수 있다.
> 이 경우 `prompts_raw.txt`(--- 구분자 형식)를 변환 소스로 사용하는 것이 정확하다.

### 여러 세션 결과 병합

```bash
python3 scripts/to_wildcard.py \
  output/2026-03-15-053817-m7/prompts_raw.txt \
  output/2026-03-15-053222-m6/prompts_raw.txt \
  -o wildcards/session_combined.txt
```

출력:
```
  [--- 구분자] output/.../prompts_raw.txt  →  15개
  [--- 구분자] output/.../prompts_raw.txt  →  15개

합계 30개 → wildcards/session_combined.txt
```

### ComfyUI에 배치

변환된 파일을 ComfyUI 와일드카드 폴더에 복사한다.

```bash
cp output/폴더/prompts-wildcard.txt \
  /mnt/f/_AI/ComfyUI/custom_nodes/comfyui-impact-pack/wildcards/my_prompts.txt
```

---

## 6. 형식 자동 감지 로직

| 파일 내용 | 감지 형식 | 구분 기준 |
|----------|----------|----------|
| `\n---\n` 포함 | `--- 구분자` | `---` 로 분리 |
| `\n\n` 포함 (위 조건 해당 없음) | `빈 줄 구분` | 빈 줄로 분리 |
| 둘 다 없음 | `단일 줄` | 각 줄 |

감지 결과는 실행 시 출력에 표시된다:

```
[--- 구분자] prompts_raw.txt → ...
[빈 줄 구분] prompts.txt → ...
[단일 줄] prompts.txt → ...
```
