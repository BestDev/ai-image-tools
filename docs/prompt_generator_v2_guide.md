# prompt_generator_v2.py 사용 가이드

> 최종 업데이트: 2026-03-18
> 환경: WSL2 / Ubuntu-24.04 / RTX 4090 24GB / Python 3.12
> 가상환경: `<저장소 루트>/venv-prompt`
> 검증 상태: transformers 5.2.0 / bitsandbytes 0.49.2 / GPU 실행 확인

---

## 목차

1. [개요](#1-개요)
2. [설치 방법](#2-설치-방법)
3. [실행 방법](#3-실행-방법)
4. [옵션 상세](#4-옵션-상세)
5. [방식별 상세](#5-방식별-상세)
6. [출력 파일 구조](#6-출력-파일-구조)
7. [누적 재개 모드](#7-누적-재개-모드)
8. [실 사용 예제](#8-실-사용-예제)
9. [모델별 특성 및 권장 사항](#9-모델별-특성-및-권장-사항)
10. [트러블슈팅](#10-트러블슈팅)

---

## 1. 개요

이미지를 분석하여 **Z-Image Turbo에 최적화된 서술형 프롬프트**를 자동 생성한다.
v2는 11가지 방식을 단일 스크립트로 통합하였으며, 누적 재개(`--accumulate`) 기능을 지원한다.

분석 지시문(시스템 프롬프트)은 `scripts/shared_prompts.py`에서 단일 관리되며,
`gemini_batch.py`(Gemini CLI 배치)도 동일한 지시문을 사용한다.

### 지원 방식

| 방식 | 모델(들) | 언어 | VRAM | 특징 |
|------|---------|------|------|------|
| 1 | JoyCaption Beta One | EN only | ~10 GB | raw 캡션, 가장 빠름 |
| 2 | Qwen3-VL-8B-Instruct | EN / ZH | ~16 GB | 이미지 직접 분석, 고품질 |
| 3 | Qwen3.5-9B | EN / ZH | ~18 GB | 이미지 직접 분석, 상세 묘사 |
| 4 | JoyCaption → Qwen3-VL | EN / ZH | ~16 GB | 2-pass: raw 캡션 → 정제 |
| 5 | JoyCaption → Qwen3.5 | EN / ZH | ~18 GB | 2-pass: raw 캡션 → 정제 |
| 6 | Huihui-Qwen3-VL (✦검열 해제) | EN / ZH | ~16 GB | 이미지 직접 분석, 필터 없음 |
| 7 | Huihui-Qwen3.5 (✦검열 해제) | EN / ZH | ~18 GB | 이미지 직접 분석, 필터 없음 |
| 8 | JoyCaption → Huihui-Qwen3-VL | EN / ZH | ~16 GB | 2-pass 정제, 검열 해제 |
| 9 | JoyCaption → Huihui-Qwen3.5 | EN / ZH | ~18 GB | 2-pass 정제, 검열 해제 |
| 10 | Gemini 3 Flash (☁ API) | EN / ZH | 없음 | 클라우드 API, GPU 불필요 |
| 11 | Gemini 3.1 Flash-Lite (☁ API) | EN / ZH | 없음 | 클라우드 API, 대용량 배치 |

### 지원 이미지 형식

`.jpg` `.jpeg` `.png` `.webp` `.bmp` `.tiff` `.tif` `.heic` `.heif`

---

## 2. 설치 방법

### 2.1 가상환경 생성

```bash
cd /path/to/image-classifier   # 저장소 루트
python3 -m venv venv-prompt
source venv-prompt/bin/activate
```

### 2.2 패키지 설치

```bash
# requirements 파일 사용 (권장)
pip install -r requirements-prompt.txt

# 또는 수동 설치
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
pip install transformers>=5.2.0 accelerate bitsandbytes
pip install Pillow pillow-heif flask psutil
```

### 2.3 모델 사전 다운로드 (선택)

스크립트 실행 시 자동 다운로드되지만, 느린 네트워크 환경에서는 사전 다운로드 권장:

```bash
python3 -c "
from huggingface_hub import snapshot_download
snapshot_download('fancyfeast/llama-joycaption-beta-one-hf-llava')  # method 1,4,5
snapshot_download('Qwen/Qwen3-VL-8B-Instruct')                      # method 2,4
snapshot_download('Qwen/Qwen3.5-9B')                                # method 3,5
"
```

---

## 3. 실행 방법

### 기본 구문

```bash
TORCHINDUCTOR_DISABLED=1 TORCH_COMPILE_DISABLE=1 \
python3 prompt_generator_v2.py <입력> -o <출력폴더> [옵션]
```

> `TORCHINDUCTOR_DISABLED=1 TORCH_COMPILE_DISABLE=1` — torch compile 워커 생성 방지. 생략 시 불필요한 서브프로세스가 발생할 수 있다.

### 입력

- **파일 경로**: 이미지 1장만 처리
- **폴더 경로**: 폴더 내 이미지 전체 처리 (파일명 오름차순 정렬)

---

## 4. 옵션 상세

| 옵션 | 단축 | 기본값 | 설명 |
|------|------|--------|------|
| `input` | — | 필수 | 이미지 파일 또는 폴더 경로 |
| `--output-dir` | `-o` | 필수 | 출력 폴더 경로 |
| `--method` | `-m` | `2` | 방식 선택 (1~11) |
| `--instr-lang` | — | `en` | 지시 언어: `en` (영어) / `zh` (중국어). 모델에게 지시하는 언어 |
| `--lang` | — | `en` | 출력 언어: `en` (영어) / `zh` (중국어). 결과물 언어 |
| `--quant` | — | `bf16` | 양자화: `bf16` / `nf4` / `int8` (로컬 모델 전용) |
| `--accumulate` | `-a` | off | 누적 재개 모드 (기존 결과 유지, 미완성분만 처리) |
| `--individual` | `-I` | off | 개별 저장 모드: 이미지명과 동일한 .txt 파일로 각각 저장 (예: image.jpg → image.txt) |
| `--uncensored` | — | off | 비검열 모드: 모델에 비검열 지시문 주입, 거부/순화 없이 묘사 |
| `--prompt-style` | — | `standard` | 프롬프트 스타일: `standard` / `spec` (아래 참조) |
| `--thinking` | — | off | Qwen3.5 Thinking 모드 활성화 (method 3/5/7/9 전용, 아래 참조) |
| `--gemini-key` | — | — | Gemini API 키 (method 10/11 전용, `GEMINI_API_KEY` 환경변수로도 설정 가능) |

### `--prompt-style` 옵션

분석 모델에 주입할 프롬프트 방식을 선택한다. JoyCaption(method 1/4/5/8/9 Pass1) 포함 **전 method에 적용**된다.

| 값 | 적용 대상 | 설명 |
|----|----------|------|
| `standard` | 전 method | 범용 이미지 분석 프롬프트 (기존 방식) |
| `spec` | 전 method | Z-Image Turbo 기술 사양 기반 (아래 참조) |

**spec 스타일 주요 차이:**
- **계층 구조**: 출력 순서를 scene/environment → subject → details → constraints로 강제
- **카메라 (조건부)**: 고정 카메라 스펙 주입 없이 이미지에서 실제 카메라 특성을 식별. 인물 포트레이트에서 압축 투시·얕은 심도가 실제로 보일 때만 포트레이트 렌즈 특성 묘사. 제품/건축/풍경은 실제 화각·심도 그대로
- **피부 텍스처**: pore-level detail, subsurface scattering, 미세 결함(주근깨, 색차) 지시
- **색상**: 60-30-10 규칙 (주색 60% / 보조색 30% / 액센트 10%)
- **네거티브**: stock-photo 미학, 플라스틱 피부, 과포화 네온, 강한 블룸, 과도한 샤프닝 명시 금지

**모델별 spec 적용 위치:**

| Method | 모델 | spec 적용 위치 |
|--------|------|---------------|
| 1 | JoyCaption | user content (분석 지시문 교체) |
| 2, 3, 6, 7 | Qwen / Huihui (직접 분석) | user content (전체 분석 프롬프트) |
| 4, 5, 8, 9 Pass1 | JoyCaption | user content (raw 캡션 지시문 교체) |
| 4, 5, 8, 9 Pass2 | Qwen / Huihui (정제) | user content (정제 프롬프트 교체) |
| 10, 11 | Gemini API | user content (분석 프롬프트 교체) |

### `--thinking` 옵션 (Qwen3.5 전용)

**적용 대상:** method 3 (Qwen3.5 직접), 5 (JoyCaption→Qwen3.5), 7 (Huihui-Qwen3.5), 9 (JoyCaption→Huihui-Qwen3.5)

Qwen3.5의 내부 추론 모드(Thinking Mode)를 활성화한다. 응답 전 `<think>...</think>` 블록으로 추론을 수행한 뒤 최종 결과만 출력한다. 추론 내용은 자동으로 제거된다.

| 항목 | 비활성화 (기본) | 활성화 (`--thinking`) |
|------|---------------|----------------------|
| temperature | 0.7 | 1.0 (공식 권장) |
| top_p | 0.9 | 0.95 (공식 권장) |
| 처리 시간 | 기준 | +20~40% |
| spec 구조 준수율 | 안정적 | **향상** |
| IFEval 기반 | 91.5% | 추론으로 더 높음 |

**권장 조합:** `--prompt-style spec --thinking` — spec 복잡한 지시문을 내부 추론으로 더 충실히 이행

### `--quant` 옵션

| 값 | VRAM 절감 | 품질 | 비고 |
|----|-----------|------|------|
| `bf16` | — | 최상 | 기본값, 24GB GPU 권장 |
| `nf4` | ~50% | 약간 저하 | 12GB GPU 이하 권장 |
| `int8` | ~30% | 경미한 저하 | 중간 절충 |

---

## 5. 방식별 상세

### Method 1 — JoyCaption (raw 캡션)

- 모델: `fancyfeast/llama-joycaption-beta-one-hf-llava`
- 영어 전용 (`--lang` 무시됨)
- 출력: `prompts_raw.txt` (raw 캡션) + `prompts.txt` (동일 내용)
- 속도: ~5.8초/장 (RTX 4090)
- 특징: 빠른 처리, Method 4/5의 1단계로 재활용 가능

### Method 2 — Qwen3-VL-8B-Instruct (직접 분석)

- 모델: `Qwen/Qwen3-VL-8B-Instruct`
- 영어/중국어 지원
- 속도: ~8.6초/장 (RTX 4090)
- 특징: 이미지를 직접 분석, 고품질 묘사. 누드/성인 이미지도 필터 없이 정확히 묘사

### Method 3 — Qwen3.5-9B (직접 분석)

- 모델: `Qwen/Qwen3.5-9B`
- 영어/중국어 지원
- 속도: ~9.5초/장 (RTX 4090), Thinking ON 시 +20~40%
- 특징: 멀티모달 통합 아키텍처(early fusion). IFEval 91.5%로 전 모델 중 instruction-following 최고. `--thinking` 활성화 시 복잡한 spec 지시문 준수율이 추가 향상됨

### Method 4 — JoyCaption → Qwen3-VL (2-pass 정제)

- 1단계: JoyCaption이 raw 캡션 생성 → `prompts_raw.txt`
- 2단계: Qwen3-VL이 raw 캡션을 Z-Image Turbo 최적 프롬프트로 정제
- 영어/중국어 지원 (정제 단계에서 언어 적용)
- 속도: ~5.8 + 7.1 = 12.9초/장 (1단계 캐시 시 7.1초/장)

### Method 5 — JoyCaption → Qwen3.5 (2-pass 정제)

- 1단계: JoyCaption raw 캡션 생성 (확산 모델 친화적 자연 묘사)
- 2단계: Qwen3.5가 정제 (`--thinking` 적용 가능)
- 영어/중국어 지원
- 속도: ~5.8 + 9.1 = 14.9초/장 (1단계 캐시 시 9.1초/장), Thinking ON 시 Pass2 +20~40%
- 특징: JoyCaption의 확산 친화적 묘사력 + Qwen3.5의 높은 instruction-following 조합. `--prompt-style spec --thinking` 병용 시 최고 spec 준수율

### Method 10 — Gemini 3 Flash (클라우드 API)

- 모델: `gemini-3-flash-preview`
- GPU 불필요, Gemini API 키 필수 (`--gemini-key` 또는 `GEMINI_API_KEY`)
- 영어/중국어 지원
- RPD 10,000 / TPM 2,000,000
- 비용: $0.50 / $3.00 per 1M tokens (입력/출력)
- 특징: 클라우드 추론, 사내 Thinking 기능으로 2-pass 불필요

### Method 11 — Gemini 3.1 Flash-Lite (클라우드 API)

- 모델: `gemini-3.1-flash-lite-preview`
- GPU 불필요, Gemini API 키 필수
- 영어/중국어 지원
- RPD 150,000 / TPM 4,000,000 (대용량 배치에 최적)
- 비용: $0.25 / $1.50 per 1M tokens (입력/출력)
- 특징: 저비용 대용량 처리, 속도 빠름

```bash
# Gemini API 키 환경변수 설정
export GEMINI_API_KEY="your-api-key"

# Method 10
python3 prompt_generator_v2.py image/dataset -o output/gemini --method 10

# Method 11 (대용량)
python3 prompt_generator_v2.py image/dataset -o output/gemini --method 11 --lang zh
```

---

## 6. 출력 파일 구조

### 기본 모드 (누적 저장)

```
<출력폴더>/
├── prompts.txt       # 최종 프롬프트 (모든 방식)
└── prompts_raw.txt   # JoyCaption raw 캡션 (method 1, 4, 5, 8, 9만 생성)
```

### 개별 저장 모드 (`--individual`)

```
<출력폴더>/
├── image1.txt        # image1.jpg의 프롬프트
├── image2.txt        # image2.jpg의 프롬프트
├── image3.txt        # image3.jpg의 프롬프트
└── ...
```

- 이미지 파일명과 동일한 `.txt` 파일로 개별 저장
- 학습 데이터셋 구성에 적합 (이미지-텍스트 쌍)
- `--accumulate`와 함께 사용하면 이미 존재하는 `.txt` 파일은 건너뜀

```bash
# 개별 저장 예시
python3 prompt_generator_v2.py image/dataset -o output/individual --method 2 --individual

# 이어서 실행 (완료된 파일 건너뜀)
python3 prompt_generator_v2.py image/dataset -o output/individual --method 2 --individual --accumulate
```

### prompts.txt — 한 줄 = 한 프롬프트

모델 출력의 내부 줄바꿈을 공백으로 압축하여 **한 줄에 하나의 프롬프트**를 기록한다.

```
A young woman with long pink hair sits gracefully...
A mystical woman stands in a dimly lit stone chamber...
An interior living room with warm tungsten lighting...
```

- 줄 수 = 이미지 수 (1:1 대응, 파싱 오류 없음)
- ComfyUI 와일드카드 형식과 동일 → 직접 사용 가능
- `to_wildcard.py` 변환 불필요

### prompts_raw.txt — 단락 구조 보존, `---` 구분자

모델이 출력한 단락 구조를 그대로 보존한다. 프롬프트 사이는 `---`로 구분된다.

```
A young woman with long pink hair sits gracefully...

Her dress is made of white satin...
---
A mystical woman stands in a dimly lit stone chamber...
```

- 가독성용 원본 보존 파일
- 2-pass 방식에서 Pass 2의 입력으로 재사용됨
- ComfyUI 와일드카드로 변환하려면 `to_wildcard.py` 사용

### ComfyUI 와일드카드 변환

`prompts.txt`는 이미 와일드카드 형식이므로 직접 사용 가능하다.
구버전 출력(빈 줄 구분) 또는 `prompts_raw.txt`를 변환할 때는 `to_wildcard.py`를 사용한다.

```bash
python3 scripts/to_wildcard.py output/폴더/prompts_raw.txt
# → output/폴더/prompts-wildcard.txt 생성
```

자세한 내용은 [`to_wildcard_guide.md`](to_wildcard_guide.md) 참고.

---

## 7. 누적 재개 모드

`--accumulate` (`-a`) 플래그를 사용하면 중단된 작업을 이어서 처리할 수 있다.

```bash
# 처음 실행 (중단됨)
python3 prompt_generator_v2.py image/photos -o output --method 2

# 이어서 실행 (완료된 이미지 스킵)
python3 prompt_generator_v2.py image/photos -o output --method 2 --accumulate
```

### 2-pass 방식(4, 5)에서의 활용

Method 1의 `prompts_raw.txt`를 Method 4/5에 재사용하면 JoyCaption 재실행을 생략할 수 있다:

```bash
# Method 1로 raw 캡션 생성
python3 prompt_generator_v2.py image/photos -o output_m4 --method 1

# raw 캡션 복사 후 Method 4 Pass 2만 실행
cp output_m4/prompts_raw.txt output_m4_refined/
python3 prompt_generator_v2.py image/photos -o output_m4_refined --method 4 --accumulate
# → "[Pass 1/2] 완료 — prompts_raw.txt 38개 복원" 출력 후 바로 Qwen3-VL 정제 시작
```

---

## 8. 실 사용 예제

### 단순 처리 (Method 2, 영어)

```bash
TORCHINDUCTOR_DISABLED=1 TORCH_COMPILE_DISABLE=1 \
python3 prompt_generator_v2.py image/dataset -o output/prompts --method 2
```

### 중국어 출력 (Method 3)

```bash
TORCHINDUCTOR_DISABLED=1 TORCH_COMPILE_DISABLE=1 \
python3 prompt_generator_v2.py image/dataset -o output/prompts_zh --method 3 --lang zh
```

### 교차 언어 모드 테스트

```bash
# EN 지시 + ZH 출력 (영어 지시, 중국어 결과)
TORCHINDUCTOR_DISABLED=1 TORCH_COMPILE_DISABLE=1 \
python3 prompt_generator_v2.py image/dataset -o output/en_zh --method 2 --instr-lang en --lang zh

# ZH 지시 + EN 출력 (중국어 지시, 영어 결과)
TORCHINDUCTOR_DISABLED=1 TORCH_COMPILE_DISABLE=1 \
python3 prompt_generator_v2.py image/dataset -o output/zh_en --method 2 --instr-lang zh --lang en

# ZH 지시 + ZH 출력 (기존 --lang zh 와 동일)
TORCHINDUCTOR_DISABLED=1 TORCH_COMPILE_DISABLE=1 \
python3 prompt_generator_v2.py image/dataset -o output/zh_zh --method 2 --instr-lang zh --lang zh
```

### VRAM 부족 시 NF4 양자화

```bash
TORCHINDUCTOR_DISABLED=1 TORCH_COMPILE_DISABLE=1 \
python3 prompt_generator_v2.py image/dataset -o output/prompts --method 2 --quant nf4
```

### 대용량 배치 처리 (누적 재개 활성화)

```bash
# 처음 실행 또는 재개 모두 동일한 명령어
TORCHINDUCTOR_DISABLED=1 TORCH_COMPILE_DISABLE=1 \
python3 prompt_generator_v2.py image/large_dataset -o output/prompts --method 2 --accumulate
```

### Method 4: JoyCaption raw 캡션 재활용

```bash
# Step 1: JoyCaption으로 raw 캡션만 생성
TORCHINDUCTOR_DISABLED=1 TORCH_COMPILE_DISABLE=1 \
python3 prompt_generator_v2.py image/dataset -o output_m4 --method 1

# Step 2: raw 캡션 복사 후 Qwen3-VL로 정제 (JoyCaption 재실행 없음)
cp output_m4/prompts_raw.txt output_m4/prompts_raw.txt  # 이미 있으면 불필요
TORCHINDUCTOR_DISABLED=1 TORCH_COMPILE_DISABLE=1 \
python3 prompt_generator_v2.py image/dataset -o output_m4 --method 4 --accumulate
```

### 비검열 모드 (성인 이미지 등)

```bash
TORCHINDUCTOR_DISABLED=1 TORCH_COMPILE_DISABLE=1 \
python3 prompt_generator_v2.py image/dataset -o output/prompts --method 2 --uncensored
```

### 개별 저장 모드 (학습 데이터셋용)

```bash
# 이미지별 개별 .txt 파일로 저장
TORCHINDUCTOR_DISABLED=1 TORCH_COMPILE_DISABLE=1 \
python3 prompt_generator_v2.py image/dataset -o output/dataset --method 2 --individual

# 결과: image1.jpg → image1.txt, image2.jpg → image2.txt ...
```

### 단일 이미지 테스트

```bash
TORCHINDUCTOR_DISABLED=1 TORCH_COMPILE_DISABLE=1 \
python3 prompt_generator_v2.py image/test.jpg -o output/test --method 2
```

---

## 9. 모델별 특성 및 권장 사항

### 실측 성능 (RTX 4090 24GB, bf16, 38장 테스트)

| 방식 | 평균 속도 | VRAM | 누드 묘사 | 권장 용도 |
|------|-----------|------|-----------|-----------|
| 1 (JoyCaption) | 5.8초/장 | ~9 GB | ✅ 정확 | 빠른 raw 캡션, 2-pass 1단계 |
| 2 (Qwen3-VL) | 8.6초/장 | ~16 GB | ✅ 정확 | 범용, 고품질 권장 |
| 3 (Qwen3.5) | 9.5초/장 | ~18 GB | ✅ 정확 | 상세한 묘사가 필요할 때 |
| 4 (JoyCaption→VL) | 7.1초/장* | ~17 GB | ✅ 정확 | raw 캐시 재활용 시 |
| 5 (JoyCaption→3.5) | 9.1초/장* | ~18 GB | ✅ 정확 | raw 캐시 재활용 시 |

*Pass 1 캐시 재사용 기준 (prompts_raw.txt 있을 때)

### 언어 조합 (`--instr-lang` × `--lang`)

`--instr-lang`(지시 언어)과 `--lang`(출력 언어)을 독립적으로 설정하여 4가지 조합으로 테스트할 수 있다.

| 조합 | 명령 예시 | 특징 |
|------|-----------|------|
| EN 지시 + EN 출력 (기본) | `--instr-lang en --lang en` | 소형 모델 instruction-following 안정 |
| EN 지시 + ZH 출력 | `--instr-lang en --lang zh` | 개념 이해는 EN, 출력만 ZH. Gemini에 권장 |
| ZH 지시 + ZH 출력 | `--instr-lang zh --lang zh` | Qwen3 계열 비교 테스트 |
| ZH 지시 + EN 출력 | `--instr-lang zh --lang en` | ZH 문법 간결성 + EN 기술 용어 출력 |

- `--instr-lang`를 생략하면 기본값 `en`으로 동작 (기존 동작 유지)
- method 1(JoyCaption)은 항상 `en`/`en` 고정 (옵션 무시)

### 출력 언어별 특성

- **영어(en)**: Z-Image Turbo의 영문 텍스트 인코더에 최적화. 80~250단어 단일 단락
- **중국어(zh)**: Z-Image Turbo의 Qwen 기반 중문 인코더와 호환. 150~400자 단일 단락

### 이미지 읽기 순서

폴더 내 이미지를 **파일명 오름차순(ASCII)**으로 정렬하여 처리한다.  
숫자 > 대문자 > 소문자 순서로 정렬되므로, 파일명에 따라 처리 순서가 달라질 수 있다.

예시 정렬 순서:
```
449398452_...jpg   # 숫자 시작
ComfyUI_00019_.png # 대문자 C
Xplus_00014_.png   # 대문자 X
itzyhime_...jpg    # 소문자 i
zit_0046.png       # 소문자 z
```

---

## 10. 트러블슈팅

### `'list' object has no attribute 'replace'`

transformers 5.x에서 LlavaProcessor API가 변경되었다.  
`prompt_generator_v2.py`는 이미 호환 처리되어 있으므로, **가상환경 패키지 버전을 확인**:

```bash
pip show transformers | grep Version
# 5.2.0 이상이어야 함
```

### VRAM 부족 (`CUDA out of memory`)

```bash
# NF4 양자화로 VRAM 약 50% 절감
python3 prompt_generator_v2.py ... --quant nf4
```

### `TORCHINDUCTOR_DISABLED=1` 없이 실행 시 느린 시작

torch compile이 백그라운드 워커를 spawning하여 초기 지연이 발생할 수 있다.  
항상 환경변수를 지정하여 실행 권장:

```bash
export TORCHINDUCTOR_DISABLED=1
export TORCH_COMPILE_DISABLE=1
```

### `--uncensored` 사용 시 주의

`--uncensored`는 모델에 비검열 지시문을 추가하여 거부·순화 없이 시각 콘텐츠를 묘사하도록 유도한다.

- **이미지 분석 단계** (JoyCaption / Qwen 직접 분석): 이미지에 보이는 내용을 있는 그대로 묘사하도록 지시
- **정제 단계** (2-pass refine): 입력된 텍스트를 검열·생략 없이 그대로 재구성하도록 지시
- JoyCaption은 이미 비검열 모델이나 Llama 잔여 안전 필터가 가끔 트리거될 수 있으며, `--uncensored`로 시스템 프롬프트 교체 시 이를 우회할 수 있다.
- abliterated 모델(method 6~9)은 이미 필터가 제거된 모델이므로 `--uncensored` 없이도 동작하지만, 함께 사용하면 더 일관된 묘사를 기대할 수 있다.

```bash
TORCHINDUCTOR_DISABLED=1 TORCH_COMPILE_DISABLE=1 \
python3 prompt_generator_v2.py image/dataset -o output/prompts --method 2 --uncensored
```

### Method 4/5에서 Pass 1이 다시 실행되는 경우

`--accumulate` 옵션을 지정해야 한다. 미지정 시 기존 `prompts_raw.txt`를 덮어쓴다.

```bash
# 잘못된 방법 (Pass 1 재실행)
python3 prompt_generator_v2.py ... --method 4

# 올바른 방법 (Pass 1 스킵)
python3 prompt_generator_v2.py ... --method 4 --accumulate
```

### HEIC 이미지 처리 불가

```bash
pip install pillow-heif
```

---

## v1 → v2 주요 변경점

| 항목 | v1 | v2 |
|------|----|----|
| 스크립트 | 방식별 별도 스크립트 | 단일 스크립트로 통합 |
| 방식 수 | 5가지 | 11가지 (로컬 9 + 클라우드 API 2) |
| 누적 재개 | 지원 | 지원 (`--accumulate`) |
| 개별 저장 | 지원 | 지원 (`--individual`) |
| 파일 초기화 | 재실행 시 append 문제 | 비누적 모드에서 자동 초기화 |
| 이미지 정렬 | 전체 경로 기준 sort | 파일명 기준 sort (`p.name`) |
| 2-pass 캐시 | 미지원 | prompts_raw.txt 재활용 가능 |
| 시스템 프롬프트 관리 | 인라인 정의 | shared_prompts.py 분리 (gemini_batch 공유) |

---

## 11. Abliterated 모델 (검열 해제)

### 지원 모델

| 방식 | 모델 | 기반 |
|------|------|------|
| 6 | `huihui-ai/Huihui-Qwen3-VL-8B-Instruct-abliterated` | Qwen3-VL-8B 기반 |
| 7 | `huihui-ai/Huihui-Qwen3.5-9B-abliterated` | Qwen3.5-9B 기반 |
| 8 | JoyCaption → Huihui-Qwen3-VL | m4의 검열 해제 버전 |
| 9 | JoyCaption → Huihui-Qwen3.5 | m5의 검열 해제 버전 |

abliterated 모델은 원본 모델과 동일한 아키텍처를 사용하며, 콘텐츠 필터(거부/검열)가 제거된 버전이다.  
누드, 성인 이미지 등 원본 모델이 거부하거나 할루시네이션을 일으킬 수 있는 이미지에 대해 일관된 묘사를 생성한다.

### 사용법

```bash
# Method 6: Huihui-Qwen3-VL abliterated (영어)
TORCHINDUCTOR_DISABLED=1 TORCH_COMPILE_DISABLE=1 \
python3 prompt_generator_v2.py image/dataset -o output/ab_vl_en --method 6 --lang en

# Method 6: Huihui-Qwen3-VL abliterated (중국어)
TORCHINDUCTOR_DISABLED=1 TORCH_COMPILE_DISABLE=1 \
python3 prompt_generator_v2.py image/dataset -o output/ab_vl_zh --method 6 --lang zh

# Method 7: Huihui-Qwen3.5 abliterated (영어)
TORCHINDUCTOR_DISABLED=1 TORCH_COMPILE_DISABLE=1 \
python3 prompt_generator_v2.py image/dataset -o output/ab_35_en --method 7 --lang en

# Method 7: Huihui-Qwen3.5 abliterated (중국어)
TORCHINDUCTOR_DISABLED=1 TORCH_COMPILE_DISABLE=1 \
python3 prompt_generator_v2.py image/dataset -o output/ab_35_zh --method 7 --lang zh
```

### 실측 성능 (RTX 4090 24GB, bf16, 10장 테스트)

| 방식 | 평균 속도 | VRAM | 비고 |
|------|-----------|------|------|
| 6 (Huihui-Qwen3-VL) | ~8.4초/장 | ~16 GB | 원본 m2와 동급 속도 |
| 7 (Huihui-Qwen3.5) | ~9.5초/장 | ~18 GB | 원본 m3와 동급 속도 |
| 8 (JoyCaption→Huihui-VL) | ~7.1초/장* | ~16 GB | Pass 1 캐시 재사용 기준 |
| 9 (JoyCaption→Huihui-3.5) | ~9.1초/장* | ~18 GB | Pass 1 캐시 재사용 기준 |

### 원본 vs Abliterated 비교

| 항목 | 원본 (m2/m3) | Abliterated (m6/m7) |
|------|-------------|---------------------|
| 누드 이미지 묘사 | 일부 거부/할루시네이션 가능 | 필터 없이 정확 묘사 |
| 일반 이미지 품질 | 동일 | 동일 |
| 속도 | 동일 | 동일 |
| VRAM | 동일 | 동일 |

---

## 10. 모델별 특성 및 최적 조합 가이드

### 3개 모델 핵심 비교

| 항목 | JoyCaption Beta One | Qwen3-VL-8B | Qwen3.5-9B |
|------|---------------------|-------------|------------|
| 아키텍처 | SigLIP2 + Llama 3.1 8B (LLaVA) | Qwen 비전 인코더 + Qwen3 | Hybrid (DeltaNet+MoE) + early fusion |
| 학습 목적 | 확산 모델 학습 캡션 전용 | 범용 VLM | 범용 멀티모달 + 추론 |
| Instruction-following | **1.5~3% 실패율** | 안정적 | **IFEval 91.5% (최고)** |
| 자연스러운 확산 캡션 | **최고** (특화 파인튜닝) | 프롬프트 의존 | 프롬프트 의존 |
| Thinking 모드 | 없음 | 없음 | **기본 탑재** |
| 다국어 | 영어 전용 | 영어/중국어 | **201개 언어** |
| spec 구조 준수 | 불안정 | 안정적 | **가장 안정적** |

### 모델 특성의 본질

**JoyCaption의 강점은 "더 잘 보는 것"이 아니다.**
확산 모델 학습 데이터 목적으로 파인튜닝되어, 별도 프롬프트 없이도 의상·포즈·피부·재질 위주 캡션을 자연스럽게 출력하는 경향이 있을 뿐이다. 비전 지각 능력 자체는 Qwen3-VL과 유사하다.

**Qwen3.5-9B의 Thinking 모드**는 복잡한 spec 지시문을 응답 전에 내부적으로 분석해 더 정확하게 이행한다. spec 스타일과 병용하면 구조적 품질이 추가 향상된다.

### 목적별 권장 조합

| 목적 | 권장 설정 |
|------|----------|
| 속도 우선, 안정적 품질 | `--method 2 --prompt-style standard` |
| spec 준수, 빠른 처리 | `--method 2 --prompt-style spec` |
| spec 준수, 최고 품질 | `--method 3 --prompt-style spec --thinking` |
| 자연스러운 확산 캡션 (영어) | `--method 1 --prompt-style standard` |
| JoyCaption 스타일 + spec 단일패스 | `--method 1 --prompt-style spec` |
| **최고 품질 종합** | `--method 5 --prompt-style spec --thinking` |
| 성인 이미지, 최고 품질 | `--method 9 --prompt-style spec --thinking` |
| GPU 없음 | `--method 10 --prompt-style spec` (Gemini API) |

### 2-pass의 실제 가치

`JoyCaption(spec) → Qwen3.5(spec + thinking)` 조합의 의미:
- **Pass 1 (JoyCaption)**: 확산 모델 친화적 자연 묘사 + spec 구조 유도
- **Pass 2 (Qwen3.5 + thinking)**: JoyCaption raw 캡션을 spec에 맞게 신뢰성 높게 재구성

단순히 "JoyCaption이 더 잘 보기 때문"이 아니라, JoyCaption의 출력 스타일(확산 특화)을 Qwen3.5의 높은 instruction-following과 추론 능력으로 정제하는 구조다.
