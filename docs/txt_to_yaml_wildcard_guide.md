# txt_to_yaml_wildcard.py 사용 가이드

> 최종 업데이트: 2026-03-16
> 환경: WSL2 / Ubuntu-24.04 / Python 3.12
> 요구사항: PyYAML (`pip install pyyaml`)

---

## 목차

1. [개요](#1-개요)
2. [TXT vs YAML 와일드카드 비교](#2-txt-vs-yaml-와일드카드-비교)
3. [설치](#3-설치)
4. [실행 방법](#4-실행-방법)
5. [옵션 상세](#5-옵션-상세)
6. [출력 형식](#6-출력-형식)
7. [실 사용 예제](#7-실-사용-예제)

---

## 1. 개요

`prompts.txt` 등 TXT 와일드카드 파일을 **ComfyUI ImpactPack YAML 와일드카드** 형식으로 변환한다.

YAML 형식은 하나의 파일에 여러 카테고리를 묶을 수 있어, 상황별·언어별 프롬프트를 계층 구조로 관리할 때 유용하다.

---

## 2. TXT vs YAML 와일드카드 비교

| 항목 | TXT | YAML |
|------|-----|------|
| 구조 | 플랫 리스트 | 계층 그룹 |
| ComfyUI 참조 | `__파일명__` | `__파일명/키__` |
| 여러 카테고리 | 파일 여러 개 필요 | 파일 하나에 묶기 가능 |
| On-Demand 로드 | ✅ | ❌ (시작 시 전체 로드) |

### TXT 형식 (`prompts.txt`)

```
A young woman in a fitted white dress...
A mystical woman stands in a stone chamber...
An interior living room with warm lighting...
```

ComfyUI 사용: `__prompts__`

### YAML 형식 (`wildcards.yaml`)

```yaml
portrait_en:
  - A young woman in a fitted white dress...
  - A mystical woman stands in a stone chamber...

portrait_zh:
  - 一位穿着白色连衣裙的年轻女性...
  - 一位神秘女性站在昏暗的石室中...
```

ComfyUI 사용: `__wildcards/portrait_en__`, `__wildcards/portrait_zh__`

---

## 3. 설치

```bash
pip install pyyaml
```

---

## 4. 실행 방법

### 기본 구문

```bash
python3 scripts/txt_to_yaml_wildcard.py <입력.txt> [옵션]
```

### 단일 파일 변환

```bash
python3 scripts/txt_to_yaml_wildcard.py output/gemini-test/prompts.txt
# → output/gemini-test/prompts.yaml 생성 (키: prompts)
```

### 키 이름 직접 지정

```bash
python3 scripts/txt_to_yaml_wildcard.py output/gemini-test/prompts.txt --key portrait_en
# → output/gemini-test/prompts.yaml 생성 (키: portrait_en)
# ComfyUI: __portrait_en__
```

### 여러 파일을 하나의 YAML로 병합

```bash
python3 scripts/txt_to_yaml_wildcard.py \
  output/session-en/prompts.txt \
  output/session-zh/prompts.txt \
  -o wildcards/portrait.yaml
# → portrait.yaml 에 키 'prompts' 2개 (이름 충돌 주의 → --key 로 지정 권장)
```

### 기존 YAML에 추가 (append)

```bash
# 처음: portrait_en 키 생성
python3 scripts/txt_to_yaml_wildcard.py en_prompts.txt --key portrait_en -o wildcards/portrait.yaml

# 이어서: portrait_zh 키 추가
python3 scripts/txt_to_yaml_wildcard.py zh_prompts.txt --key portrait_zh -o wildcards/portrait.yaml --append
```

결과:
```yaml
portrait_en:
  - A young woman...
portrait_zh:
  - 一位年轻女性...
```

ComfyUI: `__portrait/portrait_en__`, `__portrait/portrait_zh__`

---

## 5. 옵션 상세

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `inputs` | (필수) | 입력 TXT 파일(들) |
| `-o`, `--output` | 입력파일명.yaml | 출력 YAML 파일 경로 |
| `--key` | 파일명(확장자 제외) | YAML 키 이름 (단일 파일 전용) |
| `--append` | off | 기존 YAML에 이어쓰기 (덮어쓰기 방지) |

> 여러 파일을 병합할 때는 `-o` 필수. `--key`는 단일 파일에서만 유효.

---

## 6. 출력 형식

### 입력 TXT

```
A young woman in a fitted white satin mini dress...
A mystical woman stands in a dimly lit stone chamber...
```

### 출력 YAML

```yaml
prompts:
- A young woman in a fitted white satin mini dress...
- A mystical woman stands in a dimly lit stone chamber...
```

- TXT의 `#` 주석과 빈 줄은 자동 제외
- 프롬프트 텍스트는 한 줄로 유지 (내부 줄바꿈 없음)
- UTF-8 인코딩, 유니코드(한·중·일) 보존

---

## 7. 실 사용 예제

### gemini_batch 결과 → YAML 변환

```bash
# 영어 결과물
python3 scripts/txt_to_yaml_wildcard.py \
  output/gemini-test/prompts.txt \
  --key portrait_en \
  -o wildcards/portrait.yaml

# 중국어 결과물 추가
python3 scripts/txt_to_yaml_wildcard.py \
  output/gemini-test-zh/prompts.txt \
  --key portrait_zh \
  -o wildcards/portrait.yaml \
  --append
```

ComfyUI에서:
```
__portrait_en__   ← 영어 프롬프트 랜덤 선택
__portrait_zh__   ← 중국어 프롬프트 랜덤 선택
```

### ComfyUI 와일드카드 폴더에 배치

```bash
cp wildcards/portrait.yaml \
  /mnt/f/_AI/ComfyUI/custom_nodes/comfyui-impact-pack/custom_wildcards/
```

### 실행 결과 예시

```
  prompts.txt → 키: 'portrait_en', 32개 옵션

저장 완료: /path/to/portrait.yaml
총 키: 1개 / 총 옵션: 32개

ComfyUI 사용법:
  __portrait_en__
```
