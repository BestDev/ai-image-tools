# prompt_generator.py 사용 가이드

> 최종 업데이트: 2026-03-09 (transformers 5.x 호환성 수정 / 재개 지원 / LoRA 권장 방식 추가 / --lang 중국어 출력 지원)
> 환경: WSL2 / Ubuntu-24.04 / RTX 4090 24GB / Python 3.12
> 가상환경: `/home/bestdev/ai_training/venv-prompt`
> 검증 상태: `Ubuntu-24.04` 에서 GPU 실행 확인 (transformers 5.2.0 / bitsandbytes 0.49.2)

---

## 목차

1. [개요](#1-개요)
2. [실행 방법](#2-실행-방법)
3. [옵션 상세](#3-옵션-상세)
4. [방식별 상세](#4-방식별-상세)
5. [저장 모드](#5-저장-모드)
6. [출력 예시](#6-출력-예시)
7. [실 사용 예제](#7-실-사용-예제)
8. [트러블슈팅](#8-트러블슈팅)

---

## 1. 개요

이미지를 분석하여 **Z-Image Turbo에 최적화된 서술형 프롬프트**를 생성한다.
기본 출력 언어는 **영어**이며, `--lang zh` 옵션으로 **중국어** 출력도 지원한다 (방식 2·3).

### 지원 방식

| 방식 | 모델 | 특징 | VRAM |
|------|------|------|------|
| **1** | JoyCaption Beta One | 이미지→프롬프트 전용 모델, 배치 처리에 적합 | ~9GB (nf4) |
| **2** | Qwen2.5-VL-7B | Z-Image 4-Layer 형식 직접 생성, 기본값 | ~8-12GB (nf4) |
| **3** | JoyCaption → Qwen 파이프라인 | 최고 품질, 두 모델 순차 실행 | 최대 12GB (순차) |

### Z-Image Turbo 4-Layer 출력 구조

```
[피사체 & 외모] + [의상 & 소품] + [배경 & 설정] + [카메라 스타일] + [조명 & 분위기] + [품질 제약]
```

### 지원 이미지 형식

`.jpg` `.jpeg` `.png` `.webp` `.bmp` `.tiff` `.tif` `.heic` `.heif`

> HEIC/HEIF는 iPhone·Apple 기기 촬영 이미지 형식이다.
> `pillow-heif` 라이브러리가 venv-prompt에 포함되어 있어 별도 설치 없이 지원된다.
> Qwen(방식 2·3)은 내부적으로 HEIC를 임시 JPEG로 변환 후 처리한다.

---

## 2. 실행 방법

### 가상환경 자동 활성화

스크립트 실행 시 **가상환경을 수동으로 활성화할 필요 없다.**
시스템 Python으로 실행해도 자동으로 `venv-prompt` 환경으로 전환된다. 기본 작업 배포판은 `Ubuntu-24.04` 를 사용하고, CUDA 경로 충돌 방지를 위해 `LD_LIBRARY_PATH` 를 비우고 실행하는 방식을 권장한다.

```bash
# 가상환경 활성화 없이 바로 실행
env -u LD_LIBRARY_PATH python3 prompt_generator.py <이미지_또는_폴더>

# 스크립트 직접 실행도 가능
env -u LD_LIBRARY_PATH ./prompt_generator.py <이미지_또는_폴더>
```

### 기본 구조

```bash
python3 prompt_generator.py <input> [--method {1,2,3}] [--mode MODE] [--quant {nf4,bf16}] [--output-dir DIR] [--accumulate] [--lang {en,zh}]
```

---

## 3. 옵션 상세

| 옵션 | 단축 | 기본값 | 설명 |
|------|------|--------|------|
| `input` | — | 필수 | 이미지 파일 또는 폴더 경로 |
| `--method` | `-m` | `2` | 생성 방식 (1 / 2 / 3) |
| `--mode` | — | `descriptive` | JoyCaption 캡션 타입 (방식 1·3에서 사용) |
| `--quant` | — | `nf4` | 양자화 방식 |
| `--output-dir` | `-o` | 없음 | 저장 폴더 (미지정 시 콘솔 출력만) |
| `--accumulate` | `-a` | off | 누적 저장 모드 (하나의 .txt에 이어쓰기). **중단 후 재실행 시 자동 재개** |
| `--lang` | — | `en` | 출력 언어 (`en`: 영어 / `zh`: 중국어). **방식 2·3에서만 적용** (방식 1은 무시) |

### `--mode` 옵션 (방식 1·3에서만 사용)

| 값 | 설명 | 권장 상황 |
|----|------|----------|
| `descriptive` | 격식체 장문 서술 (기본, 가장 안정적) | 일반적인 프롬프트 생성 |
| `straightforward` | 간결한 서술 (Beta One 신규) | 짧고 명확한 프롬프트 필요 시 |
| `training` | Stable Diffusion 학습용 프롬프트 | LoRA 학습 데이터 준비 |

### `--quant` 옵션

| 값 | VRAM | 속도 | 품질 |
|----|------|------|------|
| `nf4` | ~9-12GB | 빠름 | 충분 (기본값) |
| `bf16` | ~17-18GB | 더 빠름 | 최대 |

> bf16은 RTX 4090(24GB)에서 Qwen 고해상도 이미지 입력 시 OOM 발생 위험이 있다.
> 안정적 실행을 위해 기본값 nf4 사용을 권장한다.

---

## 4. 방식별 상세

### 방식 1: JoyCaption Beta One

```
[이미지] → JoyCaption → [서술형 캡션]
```

- 이미지→프롬프트 전용으로 학습된 모델
- `--mode` 옵션으로 출력 스타일 조정 가능
- Instruction Following 불가 (형식 고정)
- 배치 처리 시 모델을 한 번만 로드하여 효율적

### 방식 2: Qwen2.5-VL-7B (기본)

```
[이미지] → Qwen2.5-VL + 시스템 프롬프트 → [Z-Image 4-Layer 형식 프롬프트]
```

- Z-Image Turbo 4-Layer 형식을 시스템 프롬프트로 직접 지시
- Instruction Following 가능 (스크립트 내 `QWEN_SYSTEM_PROMPT` 수정으로 형식 커스텀)
- `--mode` 옵션 미사용 (Qwen은 시스템 프롬프트로 제어)
- `--lang zh` 옵션으로 중국어 프롬프트 출력 가능

### 방식 3: 파이프라인 (최고 품질)

```
[이미지] → JoyCaption (1차: 풍부한 시각 묘사) → Qwen (2차: Z-Image 형식 변환) → [최종 프롬프트]
```

- JoyCaption의 캡셔닝 정확도 + Qwen의 형식 제어 결합
- 이미지당 모델 로드/해제를 2회 반복 (속도 느림)
- 1차 결과(`_raw`)와 최종 결과(`_final`)를 별도 저장
- `--lang zh` 옵션으로 최종 프롬프트를 중국어로 출력 가능 (1차 JoyCaption 캡션은 항상 영어)

---

## 5. 저장 모드

### 개별 저장 (기본)

이미지마다 동일한 이름의 `.txt` 파일로 저장된다.

```
output/
├── photo_001.txt
├── photo_002.txt
└── anime_003.txt
```

방식 3은 1차·최종 결과가 각각 저장된다.

```
output/
├── photo_001_raw.txt      ← JoyCaption 1차 캡션
├── photo_001_final.txt    ← Qwen 변환 최종 프롬프트
```

### 누적 저장 (`--accumulate` / `-a`)

모든 프롬프트가 하나의 `.txt` 파일에 이어쓰기된다.
프롬프트 사이에 빈 줄 한 줄이 삽입된다.

```
output/
└── prompts.txt
```

방식 3 누적 저장:

```
output/
├── prompts_raw.txt        ← 전체 이미지 JoyCaption 캡션 누적
└── prompts_final.txt      ← 전체 이미지 최종 프롬프트 누적
```

**`prompts.txt` 내부 구조:**

```
A 28-year-old woman with dark brown wavy hair sitting at a rustic wooden cafe table...

A cyberpunk city street at night, rain-slicked surfaces reflecting neon signs...

A fantasy warrior in silver plate armor standing on a clifftop at dusk...
```

### 재개 지원 (중단 후 이어하기)

프로세스가 중단되어도 **동일한 명령어를 그대로 재실행**하면 자동으로 이어서 처리된다.

| 모드 | 재개 기준 | 동작 |
|------|----------|------|
| 누적 저장 | `prompts.txt` 라인 수로 완료 이미지 수 계산 | 완료분을 건너뛰고 다음 이미지부터 재개 |
| 개별 저장 | 각 `{stem}.txt` 파일 존재 여부 확인 | 파일이 있는 이미지는 건너뜀 |

방식 3은 Pass 1·2 각각 독립적으로 재개된다.

```
재시작 시 콘솔 출력 예시 (방식 3, 누적 모드):

[재개] prompts_raw.txt: 3,200/7,971개 완료
[Pass 1/2] JoyCaption — 7,971개 이미지
  → 3,200개 복원, 342382189_...n.webp부터 재개

[재개] prompts_raw.txt 완전 완료 상태 → Pass 1 건너뜀
[재개] prompts_final.txt: 1,500/7,971개 완료
[Pass 2/2] Qwen 변환 — 7,971개
  → 1,500개 완료, 342502865_...n.webp부터 재개
```

> 누적 파일을 초기화하고 처음부터 다시 시작하려면 기존 `prompts*.txt`를 삭제한다.

---

## 6. 출력 예시

### 콘솔 출력 (방식 2, 단일 이미지)

```
=== Z-Image Turbo 프롬프트 생성 ===
방식  : 2 - Qwen2.5-VL-7B
양자화: nf4
이미지: 1개

[로드] Qwen2.5-VL-7B (nf4) ...

[1/1] photo_001.jpg
  완료 (8.3초)

────────────────────────────────────────────────────────────
[Qwen → Z-Image] photo_001.jpg
────────────────────────────────────────────────────────────
A 28-year-old East Asian woman with dark brown wavy shoulder-length hair and
light freckles across her nose, calm contemplative expression with soft brown
eyes gazing slightly off-camera to the left, seated at a rustic wooden cafe
table with both hands wrapped around a ceramic coffee mug. She wears a cream
chunky cable-knit sweater with visible fabric texture and a thin gold pendant
necklace. The background features an intimate cafe interior with exposed red
brick walls, warm Edison pendant lighting, and blurred wooden bookshelves.
Photorealistic, shallow depth of field, creamy bokeh, Fujifilm X-T4, subtle
film grain, natural skin texture. Warm window light from the right, golden
hour tone, cozy intimate atmosphere. 8K resolution, ultra-detailed, sharp
focus, correct anatomy, no watermark.
────────────────────────────────────────────────────────────

=== 완료: 총 1개, 10.1초 (10.1초/이미지) ===
```

### 콘솔 출력 (방식 3, 배치)

```
=== Z-Image Turbo 프롬프트 생성 ===
방식  : 3 - JoyCaption + Qwen 파이프라인
양자화: nf4
이미지: 3개
저장  : ./prompts  [누적 (prompts.txt)]

============================================================
[1/3] photo_001.jpg
============================================================

[Step 1] JoyCaption 로드 중...
[로드] JoyCaption Beta One (nf4) ...
  완료 (12.4초)

────────────────────────────────────────────────────────────
[1차 캡션 (JoyCaption)] photo_001.jpg
────────────────────────────────────────────────────────────
The image depicts a young woman, likely in her late twenties...
────────────────────────────────────────────────────────────
  누적: ./prompts/prompts_raw.txt

[Step 1] 모델 해제 중...
[해제] 모델 VRAM 해제 완료
[Step 2] Qwen2.5-VL 로드 중...
[로드] Qwen2.5-VL-7B (nf4) ...
  완료 (9.1초)

────────────────────────────────────────────────────────────
[최종 프롬프트 (Z-Image Turbo)] photo_001.jpg
────────────────────────────────────────────────────────────
A 28-year-old East Asian woman with dark brown wavy hair...
────────────────────────────────────────────────────────────
  누적: ./prompts/prompts_final.txt
```

---

## 7. 실 사용 예제

### 예제 A: 단일 이미지 — 콘솔 확인용 (저장 없음)

결과를 저장하지 않고 콘솔에서만 확인할 때.

```bash
python3 prompt_generator.py /mnt/d/images/photo.jpg
```

---

### 예제 B: 단일 이미지 — 방식 2, 파일 저장

```bash
python3 prompt_generator.py /mnt/d/images/photo.jpg \
  --method 2 \
  --output-dir /mnt/d/prompts
```

**결과:**
```
/mnt/d/prompts/photo.txt
```

---

### 예제 C: 폴더 배치 — 방식 1, 개별 저장

대량 이미지를 빠르게 처리할 때. 모델을 한 번만 로드해 효율적이다.

```bash
python3 prompt_generator.py /mnt/d/images \
  --method 1 \
  --output-dir /mnt/d/prompts
```

**결과:**
```
/mnt/d/prompts/
├── photo_001.txt
├── photo_002.txt
└── anime_003.txt
```

---

### 예제 D: 폴더 배치 — 방식 1, 누적 저장

모든 이미지 프롬프트를 하나의 파일로 모을 때.

```bash
python3 prompt_generator.py /mnt/d/images \
  --method 1 \
  --output-dir /mnt/d/prompts \
  --accumulate
```

**결과:**
```
/mnt/d/prompts/prompts.txt   ← 전체 이미지 프롬프트 누적
```

**단축 옵션:**
```bash
python3 prompt_generator.py /mnt/d/images -m 1 -o /mnt/d/prompts -a
```

---

### 예제 E: 폴더 배치 — 방식 2, Z-Image 형식 누적 저장

Z-Image Turbo 형식 프롬프트를 한 파일에 모아 바로 활용할 때.

```bash
python3 prompt_generator.py /mnt/d/images \
  --method 2 \
  --output-dir /mnt/d/prompts \
  --accumulate
```

---

### 예제 F: 폴더 배치 — 방식 3, 최고 품질, 누적 저장

품질이 가장 중요할 때. 속도는 느리나 결과물이 가장 정밀하다.

```bash
python3 prompt_generator.py /mnt/d/images \
  --method 3 \
  --output-dir /mnt/d/prompts \
  --accumulate
```

**결과:**
```
/mnt/d/prompts/
├── prompts_raw.txt      ← JoyCaption 1차 캡션 전체 누적
└── prompts_final.txt    ← Z-Image 최종 프롬프트 전체 누적
```

---

### 예제 G: LoRA 학습 데이터 준비

인물 얼굴 LoRA 제작 기준. **방식 3 한 번 실행으로 두 모델용 캡션을 동시에 생성**한다.

#### G-1: Z-Image Turbo LoRA + Qwen-Image LoRA 동시 준비 (권장)

```bash
# 방식 3 개별 저장 — raw와 final을 이미지와 같은 폴더에 생성
env -u LD_LIBRARY_PATH TRANSFORMERS_VERBOSITY=error HF_HUB_DISABLE_PROGRESS_BARS=1 \
  python3 prompt_generator.py /mnt/d/lora_dataset \
  --method 3 \
  --output-dir /mnt/d/lora_dataset
```

**결과:**
```
/mnt/d/lora_dataset/
├── photo_001.jpg
├── photo_001_raw.txt    ← Qwen-Image LoRA 학습용
├── photo_001_final.txt  ← Z-Image Turbo LoRA 학습용
├── photo_002.jpg
├── photo_002_raw.txt
└── photo_002_final.txt
```

**파일 용도:**

| 파일 | 사용 모델 | 이유 |
|------|----------|------|
| `{stem}_final.txt` | **Z-Image Turbo LoRA** | Z-Image 4-Layer 형식이 모델 네이티브 포맷 |
| `{stem}_raw.txt` | **Qwen-Image LoRA** | Qwen-Image는 20B MMDiT(FLUX 계열) → 격식체 자연어 묘사가 적합. `8K resolution, no watermark` 등 품질 키워드는 노이즈 |

> **Qwen-Image**: Alibaba 20B MMDiT 텍스트→이미지 생성 모델 (FLUX 동일 계열 아키텍처).
> LoRA 학습 도구는 `ai-toolkit` 또는 `kohya` 사용, rank 16~32 권장.

#### G-2: Z-Image Turbo LoRA만 준비할 때

```bash
# 방식 2 — 빠르고 Z-Image 형식 직접 생성
env -u LD_LIBRARY_PATH TRANSFORMERS_VERBOSITY=error HF_HUB_DISABLE_PROGRESS_BARS=1 \
  python3 prompt_generator.py /mnt/d/lora_dataset \
  --method 2 \
  --output-dir /mnt/d/lora_dataset
```

**결과:**
```
/mnt/d/lora_dataset/
├── photo_001.jpg
├── photo_001.txt    ← Z-Image Turbo LoRA 학습용
```

#### 인물 얼굴 LoRA 공통 주의사항

| 항목 | 내용 |
|------|------|
| 트리거 워드 | 캡션 맨 앞에 `"ohwx woman,"` 등 고유 토큰 수동 삽입 필요 (스크립트 미지원) |
| 이미지 수 | 최소 15~30장, 다양한 각도·표정·조명 |
| 이미지 해상도 | 512×512 또는 768×768 크롭 권장 |
| 데이터셋 정제 | `image_classifier.py --by person`으로 `single_person` 폴더만 사용 권장 |

---

### 예제 H: 중국어 프롬프트 출력 (`--lang zh`)

방식 2·3에서 `--lang zh` 옵션을 추가하면 프롬프트가 중국어로 생성된다.

```bash
# 방식 2 — 단일 이미지, 중국어 출력
python3 prompt_generator.py /mnt/d/images/photo.jpg \
  --method 2 \
  --lang zh

# 방식 3 — 폴더 배치, 중국어 출력, 누적 저장
python3 prompt_generator.py /mnt/d/images \
  --method 3 \
  --lang zh \
  --output-dir /mnt/d/prompts \
  --accumulate
```

> **참고:**
> - 방식 1(JoyCaption)은 `--lang zh`를 지정해도 무시된다. JoyCaption은 영어 전용 모델이다.
> - 방식 3에서는 Pass 1 JoyCaption 캡션(`_raw`)이 항상 영어로 생성되고, Pass 2 Qwen 변환 결과(`_final`)만 중국어로 출력된다.
> - 기본값은 `en` (영어)이며, 옵션 미지정 시 동일하게 영어로 동작한다.

---

### 예제 I: bf16 고품질 모드 (VRAM 여유 시)

```bash
python3 prompt_generator.py /mnt/d/images/photo.jpg \
  --method 1 \
  --quant bf16
```

---

### 예제 J: JoyCaption straightforward 모드

간결하고 명확한 스타일 프롬프트가 필요할 때.

```bash
python3 prompt_generator.py /mnt/d/images \
  --method 1 \
  --mode straightforward \
  --output-dir /mnt/d/prompts \
  --accumulate
```

---

### 방식·저장 조합 매트릭스

| 상황 | 방식 | 저장 | 명령 |
|------|------|------|------|
| 빠른 배치, 개별 저장 | 1 | 개별 | `--method 1 -o DIR` |
| 빠른 배치, 하나로 모으기 | 1 | 누적 | `--method 1 -o DIR -a` |
| Z-Image 형식 준수, 개별 | 2 | 개별 | `--method 2 -o DIR` |
| Z-Image 형식 준수, 하나로 | 2 | 누적 | `--method 2 -o DIR -a` |
| 최고 품질, 중간 결과 포함 | 3 | 개별 | `--method 3 -o DIR` |
| 최고 품질, 최종만 하나로 | 3 | 누적 | `--method 3 -o DIR -a` |
| Z-Image Turbo LoRA 단독 | 2 | 개별 | `--method 2 -o 이미지폴더` |
| Z-Image Turbo + Qwen-Image LoRA 동시 | 3 | 개별 | `--method 3 -o 이미지폴더` |
| 중국어 프롬프트, 단일 이미지 | 2 | — | `--method 2 --lang zh` |
| 중국어 프롬프트, 폴더 배치 | 3 | 누적 | `--method 3 --lang zh -o DIR -a` |

---

## 8. 트러블슈팅

### 최초 실행 시 모델 다운로드 시간

| 모델 | 크기 | 비고 |
|------|------|------|
| JoyCaption Beta One | ~16GB | `~/.cache/huggingface/` 캐시 |
| Qwen2.5-VL-7B | ~15GB | 동일 |

이후 실행부터는 캐시에서 즉시 로드된다.

### CUDA OOM 발생 시

현재 문서 기준의 정상 GPU 환경은 `Ubuntu-24.04` 에서 검증되었다. 실행은 아래처럼 `LD_LIBRARY_PATH` 를 비우고 하는 방식을 권장한다.

```bash
# 1. nvidia-smi로 현재 VRAM 사용량 확인
nvidia-smi

# 2. bf16 → nf4 변경
env -u LD_LIBRARY_PATH python3 prompt_generator.py ... --quant nf4

# 3. 방식 3 사용 중이면 방식 1 또는 2로 전환
env -u LD_LIBRARY_PATH python3 prompt_generator.py ... --method 2
```

### transformers 5.x 업그레이드 후 오류 발생 시

transformers 5.x + bitsandbytes 0.49.x 환경에서 아래 두 가지 호환성 문제가 확인되었으며,
스크립트 내에서 자동으로 수정된다. 별도 조치 없이 정상 동작한다.

| 증상 | 원인 | 스크립트 처리 |
|------|------|--------------|
| `NotImplementedError: lanczos` | `SiglipImageProcessor`가 fast processor로 기본 전환됨 | `use_fast=False`로 slow processor 강제 사용 |
| `RuntimeError: BFloat16 and Byte dtype mismatch` | nf4 양자화 시 `SiglipMultiheadAttentionPoolingHead.out_proj`가 `Linear4bit`로 교체되나 `F.multi_head_attention_forward`가 역양자화 경로를 우회 | 모델 로드 후 해당 레이어를 `dequantize_4bit`로 bf16 linear로 교체 |

경고 메시지(`SiglipImageProcessor is now loaded as a fast processor`)가 콘솔에 출력되어도 정상 실행된다.

### HEIC 이미지가 처리되지 않을 때

`pillow-heif` 패키지가 venv-prompt에 포함되어 있다.
만약 오류가 발생하면 직접 설치한다:

```bash
/home/bestdev/ai_training/venv-prompt/bin/pip install pillow-heif
```

Qwen(방식 2·3)에서 HEIC 입력 시 내부적으로 임시 JPEG 변환 후 처리하므로
속도가 소폭 느릴 수 있다.

### 이미지가 처리되지 않을 때

지원 형식을 확인한다: `.jpg` `.jpeg` `.png` `.webp` `.bmp` `.tiff` `.tif` `.heic` `.heif`

```bash
# 폴더 내 이미지 파일 수 확인
ls /mnt/d/images/*.jpg | wc -l
```

### 백그라운드 실행 시 로그 파일이 너무 커질 때

모델 로드 시마다 출력되는 `Loading weights: X%` 진행바가 수백만 줄을 생성한다.
`TRANSFORMERS_VERBOSITY=error`와 `HF_HUB_DISABLE_PROGRESS_BARS=1` 환경변수로 억제한다.
스크립트 자체의 출력(`[Pass 1/2]`, `완료`, 프롬프트 내용 등)은 그대로 유지된다.

```bash
nohup env -u LD_LIBRARY_PATH \
  TRANSFORMERS_VERBOSITY=error \
  HF_HUB_DISABLE_PROGRESS_BARS=1 \
  python3 prompt_generator.py <입력> \
  --method 3 --accumulate \
  --output-dir <저장폴더> \
  > ./run.log 2>&1 &
```

### 누적 파일에 이미 내용이 있을 때

`--accumulate` 모드는 **항상 이어쓰기(append)** 한다.
새로 시작하려면 기존 `prompts.txt`를 삭제하거나 `--output-dir`를 새 폴더로 지정한다.

```bash
rm /mnt/d/prompts/prompts.txt
python3 prompt_generator.py /mnt/d/images -o /mnt/d/prompts -a
```
