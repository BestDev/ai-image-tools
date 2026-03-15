# gemini_batch.py 사용 가이드

> 최종 업데이트: 2026-03-16
> 환경: WSL2 / Ubuntu-24.04 / Python 3.12
> 요구사항: Gemini CLI 설치 + Google 계정 로그인 (API 키 불필요)

---

## 목차

1. [개요](#1-개요)
2. [사전 요구사항](#2-사전-요구사항)
3. [Web UI 사용법](#3-web-ui-사용법)
4. [실행 방법 (CLI)](#4-실행-방법-cli)
5. [옵션 상세](#5-옵션-상세)
6. [출력 파일 구조](#6-출력-파일-구조)
7. [세션 모드 (Session Warmup Chain)](#7-세션-모드-session-warmup-chain)
8. [모델 선택 기준](#8-모델-선택-기준)
9. [쿼터 및 속도 설정](#9-쿼터-및-속도-설정)
10. [실 사용 예제](#10-실-사용-예제)
11. [트러블슈팅](#11-트러블슈팅)

---

## 1. 개요

**Gemini CLI의 헤드리스 모드**(`-p` 플래그)를 subprocess로 호출하여 이미지 폴더를 배치 처리한다.
API 키 없이 Gemini CLI의 OAuth 인증(Google AI Pro 구독 등)을 그대로 활용하므로 별도 과금이 발생하지 않는다.

### 동작 방식

```
gemini -p "...@{/절대경로/image.jpg}..." --approval-mode=yolo -m flash
```

- `@{/절대경로/image.jpg}` 문법으로 이미지를 multimodal 입력으로 CLI에 전달
- CLI 내부에서 인증·분석·응답 생성을 모두 처리하며 stdout으로 결과를 반환
- OAuth 토큰을 스크립트가 직접 사용하지 않음 — CLI가 자체 인증으로 처리

### prompt_generator_v2.py(Gemini API 방식)와의 차이

| 항목 | gemini_batch.py (CLI) | prompt_generator_v2.py (API) |
|------|----------------------|------------------------------|
| 인증 | Google 계정 OAuth (구독) | Gemini API 유료 키 |
| 과금 | 구독료 포함 (토큰별 추가 없음) | 토큰당 과금 |
| 모델 지정 | 별칭(flash/flash-lite 등) | 정확한 모델 ID 지정 |
| GPU 필요 여부 | 불필요 | 불필요 |
| VRAM 사용 | 없음 | 없음 |

---

## 2. 사전 요구사항

### Gemini CLI 설치 확인

```bash
which gemini
# /home/bestdev/.nvm/versions/node/v24.13.1/bin/gemini

gemini --version
# 0.33.1 이상
```

설치가 안 된 경우:
```bash
npm install -g @google/gemini-cli
```

### Google 계정 로그인 (최초 1회)

```bash
gemini
# 대화형 모드에서 로그인 완료 후 종료
# OAuth 토큰이 ~/.gemini/ 에 캐시됨
```

> Google AI Pro 구독 계정으로 로그인하면 헤드리스 모드에서도 구독 쿼터가 적용된다.

---

## 3. Web UI 사용법

```bash
python3 web_ui.py
# → http://localhost:7860
```

**☁ Gemini Batch** 탭을 선택하면 아래 옵션을 GUI로 설정하고 실행할 수 있다.

| UI 항목 | 설명 |
|---------|------|
| 입력 폴더 | 이미지가 있는 폴더 (📁 탐색기 또는 직접 입력) |
| 출력 폴더 | 비워두면 이미지 옆에 저장 |
| Gemini 모델 | flash / flash-lite / pro / auto |
| 출력 언어 | 영어(en) / 중국어(zh) |
| 출력 모드 | both / individual / collect |
| 누적 파일명 | 기본 `prompts.txt` |
| 이미지 간 대기 | 초 단위 (기본 3초) |
| 타임아웃 | 초 단위 (기본 120초) |
| 세션 리셋 주기 | N장마다 리셋 (기본 100) |
| 이어서 실행 | --skip-existing |
| 세션 없이 실행 | --no-session |
| 드라이런 | 처리 목록만 출력 |

**Web UI 주요 기능:**
- 실시간 터미널 출력 (`OK` 녹색 / `FAIL` 적색 / `[WARMUP]` 강조)
- 이미지별 처리 진행률 및 ETA 표시
- 이미지 썸네일 미리보기 + 완료 체크 오버레이
- 완료 후 `prompts.txt` 내용 자동 inline 표시 (클릭하여 복사)
- **배치 큐**에 추가하여 다른 작업과 순차 처리 가능

---

## 4. 실행 방법 (CLI)

```bash
python3 scripts/gemini_batch.py <입력폴더> [옵션]
```

### 기본 실행 (flash 모델, 영어, 이미지 옆에 txt 저장)

```bash
python3 scripts/gemini_batch.py ./photos
```

### 출력폴더 별도 지정

```bash
python3 scripts/gemini_batch.py ./photos -o ./prompts
```

### 중국어 출력 + flash-lite 모델

```bash
python3 scripts/gemini_batch.py ./photos -o ./prompts --lang zh --model flash-lite
```

### 중단 후 재개 (이미 처리된 파일 건너뜀)

```bash
python3 scripts/gemini_batch.py ./photos -o ./prompts --skip-existing
```

### 실행 전 처리 목록 확인

```bash
python3 scripts/gemini_batch.py ./photos --dry-run
```

---

## 5. 옵션 상세

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `input_dir` | (필수) | 이미지가 있는 폴더 경로 |
| `-o`, `--output-dir` | 이미지 옆 | 프롬프트 txt 저장 폴더 |
| `--lang` | `en` | 출력 언어: `en` (영어) / `zh` (중국어) |
| `-m`, `--model` | `flash` | Gemini 모델 별칭 (아래 표 참고) |
| `--delay` | `3.0` | 이미지 간 대기 시간(초) |
| `--timeout` | `120` | 이미지당 최대 대기 시간(초) |
| `--skip-existing` | off | 이미 `.txt`가 존재하면 건너뜀 |
| `--dry-run` | off | 실제 실행 없이 처리 목록만 출력 |
| `--output-mode` | `both` | 출력 모드: `both`=개별+누적 / `individual`=개별만 / `collect`=누적만 |
| `--collect-file` | `prompts.txt` | 누적 프롬프트 파일명 |
| `--no-session` | off | 세션 없이 매 이미지마다 전체 프롬프트 전달 |
| `--reset-every` | `100` | 세션 모드: N장마다 세션 리셋 (0=리셋 없음) |

---

## 6. 출력 파일 구조

### 개별 txt 파일

이미지 파일명과 동일한 이름의 `.txt` 파일이 생성된다.

```
photos/
├── photo001.jpg
├── photo001.txt    ← 프롬프트
├── photo002.jpg
├── photo002.txt
└── prompts.txt     ← 누적 파일
```

출력폴더(`-o`)를 지정한 경우:

```
photos/
├── photo001.jpg
└── photo002.jpg

prompts/
├── photo001.txt
├── photo002.txt
└── prompts.txt
```

### 누적 파일 (`prompts.txt`) 형식 — 한 줄 = 한 프롬프트

모델 출력의 내부 줄바꿈을 공백으로 압축하여 **한 줄에 하나의 프롬프트**를 기록한다.

```
A young woman in a fitted white satin mini dress stands facing the camera...
An interior living room with exposed concrete walls and warm tungsten lighting...
A young woman sits on a wooden boat with a deep V-neck white satin dress...
```

- 줄 수 = 이미지 수 (1:1 대응)
- ComfyUI 와일드카드 형식과 동일 → 직접 사용 가능
- 성공한 이미지만 누적, 배치 재실행 시 기존 내용 뒤에 이어서 추가(append)

### ComfyUI 와일드카드 변환

`prompts.txt`는 이미 와일드카드 형식이다. 개별 `.txt` 파일(단락 구조 보존)을 변환할 때는 `to_wildcard.py`를 사용한다.

```bash
python3 scripts/to_wildcard.py output/폴더/prompts.txt
# → output/폴더/prompts-wildcard.txt 생성 (이미 단일 줄이므로 그대로 복사됨)
```

### 실패 로그 (`.err`)

처리 실패 시 에러 내용이 `.err` 파일로 저장된다.

```
photos/photo003.err    ← 에러 메시지
```

---

## 7. 세션 모드 (Session Warmup Chain)

기본 동작(세션 모드)에서는 Gemini CLI의 `-r "latest"` 세션 재개 기능을 활용해 토큰을 절약하고 컨텍스트를 누적합니다.

### 동작 원리

```
[워밍업] gemini -p "페르소나 확립 지시문" → 세션 시작
[이미지 1] gemini -r "latest" -p "@{img1} 분석해줘" → 세션 재개
[이미지 2] gemini -r "latest" -p "@{img2} 분석해줘" → 세션 재개
...
[N장 후] 새 워밍업 → 세션 리셋 (컨텍스트 초기화)
```

### 토큰 효율 비교

| 방식 | 이미지당 토큰 | 컨텍스트 |
|------|-------------|---------|
| `--no-session` | 전체 지시문 (~400토큰) × N | 없음 |
| 세션 모드 (기본) | 최소 태스크 (~10토큰) + 워밍업(1회/N장) | 누적 |

### 세션 리셋 주기 조정

```bash
# 기본 (100장마다 리셋)
python3 scripts/gemini_batch.py ./photos

# 50장마다 리셋 (컨텍스트를 오래 유지)
python3 scripts/gemini_batch.py ./photos --reset-every 50

# 리셋 없음 (한 세션으로 전체 처리, 컨텍스트 누적 위험)
python3 scripts/gemini_batch.py ./photos --reset-every 0

# 세션 없이 이전 방식으로 동작
python3 scripts/gemini_batch.py ./photos --no-session
```

### 워밍업 실패 시 동작

워밍업이 실패하면 해당 이미지부터 자동으로 `--no-session` 방식(전체 프롬프트)으로 폴백합니다.
다음 이미지에서 워밍업을 재시도하지 않으므로, 오류 메시지를 확인하고 CLI 로그인 상태를 점검하세요.

---

## 8. 모델 선택 기준

| 별칭 | 실제 모델 | 속도 | 품질 | 권장 용도 |
|------|----------|------|------|----------|
| `flash` | gemini-2.5-flash | 빠름 | 높음 | **기본 권장** |
| `flash-lite` | gemini-2.5-flash-lite | 매우 빠름 | 보통 | 대량 처리, 쿼터 절약 |
| `pro` | gemini-2.5-pro | 느림 | 최고 | 소량 고품질 |
| `auto` | 자동 선택 | - | - | CLI 판단에 맡길 때 |

> 모델 별칭은 Gemini CLI 공식 문서 기준. CLI 버전에 따라 실제 매핑 모델이 달라질 수 있다.

---

## 9. 쿼터 및 속도 설정

### Google AI Pro 구독 쿼터

Gemini CLI는 **Gemini Code Assist** 쿼터 기준을 적용한다.

| 계정 유형 | 일일 요청 | 분당 요청 |
|----------|----------|----------|
| 개인 Google 계정 (무료) | 1,000 req/day | 60 req/min |
| Google AI Pro 구독 | 구독 플랜에 따라 증가 | 동일 |

### `--delay` 설정 권장값

| 목표 처리량 | delay 설정 |
|-----------|-----------|
| 안정적 (일 300장) | `10` ~ `15`초 |
| 보통 (일 600장) | `5` ~ `8`초 |
| 빠름 (일 1,000장) | `3`초 (기본값) |

> 분당 60 req 제한 기준으로 `delay=1`이 이론상 최소값이나, 응답 시간 포함 시 `delay=3`이 안전하다.

---

## 10. 실 사용 예제

### 1,000장 폴더 배치 처리 (재개 포함)

```bash
# 1차 실행
python3 scripts/gemini_batch.py ./dataset -o ./prompts --model flash --delay 3

# 중단 후 재개
python3 scripts/gemini_batch.py ./dataset -o ./prompts --model flash --delay 3 --skip-existing
```

### 누적 파일명 커스텀 지정

```bash
python3 scripts/gemini_batch.py ./photos -o ./out --collect-file dataset_prompts.txt
```

### 누적 파일 없이 개별 txt만 저장

```bash
python3 scripts/gemini_batch.py ./photos --collect-file ""
```

### 중국어 프롬프트 생성

```bash
python3 scripts/gemini_batch.py ./photos -o ./prompts_zh --lang zh --model flash
```

### 출력 모드 선택

```bash
# 기본: 개별 txt + 누적 prompts.txt 모두 저장
python3 scripts/gemini_batch.py ./photos -o ./out

# 학습 데이터셋용: 개별 txt 파일만 저장 (image.jpg → image.txt)
python3 scripts/gemini_batch.py ./photos -o ./out --output-mode individual

# 와일드카드용: 누적 prompts.txt만 저장
python3 scripts/gemini_batch.py ./photos -o ./out --output-mode collect

# 누적 파일명 변경
python3 scripts/gemini_batch.py ./photos -o ./out --output-mode collect --collect-file dataset.txt
```

### 세션 모드 조정

```bash
# 10장마다 리셋 (짧은 컨텍스트 유지)
python3 scripts/gemini_batch.py ./photos --reset-every 10

# 세션 없이 이전 방식 (전체 프롬프트 매 이미지)
python3 scripts/gemini_batch.py ./photos --no-session
```

---

## 11. 트러블슈팅

### `gemini CLI not found` 오류

```bash
# nvm 환경 PATH 확인
export PATH="$HOME/.nvm/versions/node/v24.13.1/bin:$PATH"
which gemini
```

### `[EXIT 1]` 오류 반복

- Gemini CLI가 로그인 상태가 아닐 때 발생
- `gemini` 를 대화형으로 실행해 로그인 완료 후 재시도

### 응답이 비어있음 (`[EXIT 0]` 이지만 txt 파일이 빈 상태)

- `--timeout` 값을 늘려서 재시도: `--timeout 180`
- 또는 `--delay` 를 늘려 서버 부하 감소

### 특정 이미지만 실패 반복

- `.err` 파일 내용 확인
- 이미지 파일이 손상됐거나 지원 포맷(JPG/PNG/WEBP/BMP/TIFF)이 아닐 수 있음
- HEIC/HEIF는 지원하지 않음 — `heic_to_jpeg.py` 로 변환 후 처리
