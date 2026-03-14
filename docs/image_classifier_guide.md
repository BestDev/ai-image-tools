# image_classifier.py 사용 가이드

> 최종 업데이트: 2026-03-05 (HEIC 지원 추가)
> 환경: WSL2 / Ubuntu-24.04 / RTX 4090 24GB / Python 3.12
> 가상환경: `<저장소 루트>/venv-classifier`
> 검증 상태: `Ubuntu-24.04` 에서 GPU 실행 확인

---

## 목차

1. [개요](#1-개요)
2. [실행 방법](#2-실행-방법)
3. [옵션 상세](#3-옵션-상세)
4. [분류 축별 출력](#4-분류-축별-출력)
5. [실 사용 예제](#5-실-사용-예제)
6. [레이블 튜닝](#6-레이블-튜닝)
7. [트러블슈팅](#7-트러블슈팅)

---

## 1. 개요

`image_classifier.py`는 폴더 내 이미지를 **하나의 기준으로 독립 분류**하는 스크립트다.
분류 기준(스타일 / 배경 / 인물 수)을 한 번에 하나씩 선택해 실행하고, 결과를 확인한 뒤 다음 기준으로 이어서 실행할 수 있다.

### 분류 축

| `--by` | 분류 기준 | 생성 폴더 | 사용 모델 |
|--------|----------|---------|---------|
| `style` | 이미지 장르/스타일 | photorealistic / 3d_render / anime / sci_fi / fantasy | CLIP (GPU) |
| `background` | 배경 유형 | solid / complex | OpenCV (CPU) |
| `person` | 인물 수 | no_person / single_person / multiple_people | YOLO (GPU) |

### 핵심 특징

- **이미지 1개 → 폴더 1개** : 중복 없음, `--move` 가 완전히 깔끔하게 동작
- **필요한 모델만 로드** : `--by background` 는 GPU 모델 전혀 불필요
- **단계별 확인 가능** : 각 축을 독립 실행 → 결과 확인 → 다음 축 실행

### 지원 이미지 형식

`.jpg` `.jpeg` `.png` `.webp` `.bmp` `.tiff` `.tif` `.heic` `.heif`

> HEIC/HEIF는 iPhone·Apple 기기 촬영 이미지 형식이다.
> `pillow-heif` 라이브러리가 venv-classifier에 포함되어 있어 별도 설치 없이 지원된다.

---

## 2. 실행 방법

### 가상환경 자동 활성화

시스템 Python으로 실행해도 자동으로 `venv-classifier` 환경으로 전환된다.
기본 작업 배포판은 `Ubuntu-24.04` 를 사용한다. CUDA 경로 충돌을 피하려면 아래처럼 `LD_LIBRARY_PATH` 를 비우고 실행하는 방식을 권장한다.

```bash
env -u LD_LIBRARY_PATH python3 image_classifier.py <폴더> --by <축> [옵션]
```

### 기본 구조

```
python3 image_classifier.py <input_dir> --by {style|background|person}
                             [--move | --copy]
                             [-o 출력폴더]
                             [--csv 경로]
                             [--verbose]         # style 전용
                             [--model MODEL]     # style 전용
                             [--bg-threshold N]  # background 전용
```

---

## 3. 옵션 상세

| 옵션 | 단축 | 기본값 | 설명 |
|------|------|--------|------|
| `--by` | — | 필수 | 분류 기준: `style` / `background` / `person` |
| `--move` | — | off | 분류 후 파일 이동 (원본 삭제) |
| `--copy` | — | off | 분류 후 파일 복사 (원본 유지) |
| `--output-dir` | `-o` | `input_dir/by_<축>/` | 출력 폴더 |
| `--csv` | — | `input_dir/report_<축>.csv` | CSV 저장 경로 |
| `--model` | — | `openai/clip-vit-large-patch14` | CLIP 모델 (`--by style` 전용) |
| `--verbose` | `-v` | off | 5개 스타일 전체 점수 출력 (`--by style` 전용) |
| `--bg-threshold` | — | `15.0` | 단색 판정 임계값 (`--by background` 전용) |

> `--move` 와 `--copy` 는 동시에 사용 불가.
> `--move` / `--copy` 모두 생략 시 CSV만 생성하고 파일은 건드리지 않는다.

### `--bg-threshold` 기준

| 값 | 판정 |
|:--:|------|
| 5.0 | 완벽한 단색만 (스튜디오 배경) |
| 15.0 | 약한 노이즈 허용 (기본값) |
| 25.0 | 부드러운 그라데이션도 solid 판정 |

---

## 4. 분류 축별 출력

### `--by style`

```
=== 이미지 분류 시작 ===
분류 기준: style (스타일)
입력: /mnt/d/images (150개)
파일 처리: 이동 (원본 삭제)
출력: /mnt/d/images/by_style

[로드] CLIP 모델: openai/clip-vit-large-patch14

[  1/150] photo_001.jpg
          → photorealistic (0.92)
[  2/150] render_002.png
          → 3d_render (0.87)
[  3/150] anime_003.jpg
          → anime (0.95)

=== 분류 완료 ===
총 150개  (12.3초, 0.08초/이미지)

  photorealistic          62개 (41.3%)
  anime                   35개 (23.3%)
  3d_render               28개 (18.7%)
  sci_fi                  15개 (10.0%)
  fantasy                 10개 ( 6.7%)

CSV 저장: /mnt/d/images/report_style.csv
폴더 이동 완료: /mnt/d/images/by_style
```

**`--verbose` 추가 시:**
```
[  1/150] photo_001.jpg
          → photorealistic (0.92)
          └ photorealistic: 0.920 | 3d_render: 0.041 | anime: 0.021 | sci_fi: 0.010 | fantasy: 0.008
```

**출력 폴더 구조:**
```
by_style/
├── photorealistic/
├── 3d_render/
├── anime/
├── sci_fi/
└── fantasy/
```

**CSV (`report_style.csv`):**
```csv
filename,category,score
photo_001.jpg,photorealistic,0.9200
render_002.png,3d_render,0.8700
anime_003.jpg,anime,0.9500
```

---

### `--by background`

```
[  1/150] photo_001.jpg
          → complex  std=45.2
[  2/150] render_002.png
          → solid  std=3.1 rgb(255,255,255)
```

**출력 폴더 구조:**
```
by_background/
├── solid/
└── complex/
```

**CSV (`report_background.csv`):**
```csv
filename,category,bg_std,bg_color_rgb
photo_001.jpg,complex,45.2,"(128, 130, 125)"
render_002.png,solid,3.1,"(255, 255, 255)"
```

---

### `--by person`

```
[  1/150] photo_001.jpg
          → single_person (1명)
[  2/150] render_002.png
          → no_person (0명)
[  3/150] anime_003.jpg
          → multiple_people (3명)
```

**출력 폴더 구조:**
```
by_person/
├── no_person/
├── single_person/
└── multiple_people/
```

**CSV (`report_person.csv`):**
```csv
filename,category,person_count
photo_001.jpg,single_person,1
render_002.png,no_person,0
anime_003.jpg,multiple_people,3
```

---

## 5. 실 사용 예제

### 기본 워크플로우 — 단계별 독립 실행

```
원본 폴더 /mnt/d/raw/
    │
    ├─ Step 1: --by style  --move  → by_style/
    │              확인 후
    ├─ Step 2: --by background --move → by_background/
    │              확인 후
    └─ Step 3: --by person --move  → by_person/
```

---

### 예제 A: 1단계 — 스타일로 정리 (결과 먼저 확인)

파일을 건드리지 않고 CSV만 생성해 분류 결과를 먼저 확인한다.

```bash
# CSV만 생성 (파일 이동 없음)
python3 image_classifier.py /mnt/d/raw --by style
```

`/mnt/d/raw/report_style.csv` 확인 후 분류가 올바르면 이동 실행:

```bash
# 결과가 만족스러우면 이동
python3 image_classifier.py /mnt/d/raw --by style --move -o /mnt/d/by_style
```

**결과:**
```
/mnt/d/by_style/
├── photorealistic/   ← 실사 이미지
├── 3d_render/        ← 3D 렌더링
├── anime/            ← 애니메이션
├── sci_fi/           ← SF
└── fantasy/          ← 판타지
```

---

### 예제 B: 2단계 — 스타일 정리된 폴더에서 배경으로 재정리

스타일 정리가 완료된 `anime/` 폴더 안에서 배경 유형으로 다시 분류한다.
`--by background` 는 OpenCV만 사용하므로 **GPU 불필요, 즉시 처리**된다.

```bash
python3 image_classifier.py /mnt/d/by_style/anime \
  --by background \
  --move \
  -o /mnt/d/by_style/anime/by_bg
```

**결과:**
```
/mnt/d/by_style/anime/by_bg/
├── solid/     ← 단색 배경 애니메이션
└── complex/   ← 복잡한 배경 애니메이션
```

---

### 예제 C: 3단계 — 인물 수로 재정리

배경 정리 후 인물 수 기준으로 다시 분류한다.

```bash
python3 image_classifier.py /mnt/d/by_style/anime/by_bg/solid \
  --by person \
  --move
```

**결과:**
```
/mnt/d/by_style/anime/by_bg/solid/by_person/
├── no_person/
├── single_person/
└── multiple_people/
```

---

### 예제 D: 전체 폴더 한 번에 인물 수로만 정리

스타일 구분 없이 인물 수만 기준으로 전체 정리할 때.

```bash
python3 image_classifier.py /mnt/d/raw --by person --move -o /mnt/d/by_person
```

**결과:**
```
/mnt/d/by_person/
├── no_person/
├── single_person/
└── multiple_people/
```

---

### 예제 E: 오분류 디버깅 — 스타일 세부 점수 확인

어떤 이미지가 왜 특정 스타일로 분류됐는지 전체 점수를 확인할 때.

```bash
python3 image_classifier.py /mnt/d/raw --by style --verbose
```

```
[  5/150] ambiguous_001.jpg
          → anime (0.38)
          └ anime: 0.380 | photorealistic: 0.350 | 3d_render: 0.180 | sci_fi: 0.050 | fantasy: 0.040
```

점수 차이가 0.1 미만이면 레이블 튜닝을 고려한다.

---

### 예제 F: 단색 배경 임계값 조정

기본값(15.0)에서 단색으로 잡히지 않는 그라데이션 배경을 포함하고 싶을 때.

```bash
python3 image_classifier.py /mnt/d/raw \
  --by background \
  --bg-threshold 25.0 \
  --move
```

---

### 예제 G: 원본 유지하며 테스트

이동하기 전에 결과물이 올바른지 별도 폴더에 복사해서 확인할 때.

```bash
# 복사로 먼저 확인
python3 image_classifier.py /mnt/d/raw \
  --by style \
  --copy \
  -o /mnt/d/test_result

# 확인 후 원본에서 이동
python3 image_classifier.py /mnt/d/raw \
  --by style \
  --move \
  -o /mnt/d/by_style
```

---

### 예제 H: SigLIP 모델로 스타일 분류

```bash
python3 image_classifier.py /mnt/d/raw \
  --by style \
  --model google/siglip-so400m-patch14-384 \
  --verbose
```

---

### 상황별 추천 조합

| 상황 | 명령 |
|------|------|
| 결과 먼저 확인 (파일 유지) | `--by style` |
| 스타일 정리 | `--by style --move` |
| 배경 정리 (GPU 없이) | `--by background --move` |
| 인물 수 정리 | `--by person --move` |
| 오분류 디버깅 | `--by style --verbose` |
| 그라데이션 배경 허용 | `--by background --bg-threshold 25.0 --move` |
| 복사로 먼저 검증 | `--by style --copy -o /tmp/test` |

---

## 6. 레이블 튜닝

CLIP 분류 정확도는 레이블 문구에 민감하다. `image_classifier.py` 상단의 `STYLE_LABELS`를 직접 수정한다.

```python
STYLE_LABELS: dict[str, list[str]] = {
    "photorealistic": [
        "a real photograph of a scene or person",
        "a photorealistic image of real life",
        # 필요 시 추가 → "a real photo taken with a DSLR camera",
    ],
    ...
}
```

> 카테고리당 레이블이 여러 개일 때 **최고 점수**를 해당 카테고리 점수로 사용한다.

### 튜닝 절차

1. `--by style --verbose` 로 오분류 이미지의 점수 분포 확인
2. 점수 차이가 작은 카테고리 레이블에 더 구체적인 표현 추가
3. 소규모 샘플(10~20장)로 재실행해 개선 확인

### 자주 발생하는 오분류와 대처

| 문제 | 레이블 추가 |
|------|-----------|
| 실사 → 3D 오분류 | photorealistic에 `"a real photograph taken with a camera"` 추가 |
| 3D → 실사 오분류 | 3d_render에 `"a computer generated image with CGI lighting"` 추가 |
| SF ↔ 판타지 혼동 | SF에 `"spaceships, robots, cyberpunk"`, 판타지에 `"swords, elves, castles"` 명시 |

---

## 7. 트러블슈팅

### 최초 실행 시 모델 다운로드

| 모델 | 크기 | 사용 축 |
|------|------|---------|
| CLIP ViT-L/14 | ~816MB | `--by style` |
| SigLIP so400m | ~1.7GB | `--by style` (선택) |
| YOLO11 nano | ~6MB | `--by person` |

이후 실행부터는 `~/.cache/huggingface/` 캐시에서 즉시 로드.

### `--by background` 가 가장 빠른 이유

OpenCV만 사용하므로 GPU 모델 로드 없이 즉시 처리된다.
1000장 기준 수초 내 완료.

### CUDA 오류 발생 시

기존 `Ubuntu` 배포판에서는 `cuInit=304` 문제가 있었고, 현재 문서 기준의 정상 GPU 환경은 `Ubuntu-24.04` 에서 검증되었다.

```bash
# 1. 현재 배포판 확인
echo "$WSL_DISTRO_NAME"

# 2. GPU 상태 확인
nvidia-smi

# 3. 권장 실행 방식
env -u LD_LIBRARY_PATH python3 image_classifier.py /mnt/d/raw --by style

# 4. CPU 강제 사용
CUDA_VISIBLE_DEVICES="" python3 image_classifier.py /mnt/d/raw --by style
```

### HEIC 이미지가 처리되지 않을 때

`pillow-heif` 패키지가 venv-classifier에 포함되어 있다.
만약 오류가 발생하면 직접 설치한다:

```bash
<저장소 루트>/venv-classifier/bin/pip install pillow-heif
```

### 이미지를 찾지 못할 때

지원 형식 확인: `.jpg` `.jpeg` `.png` `.webp` `.bmp` `.tiff` `.tif` `.heic` `.heif`
대문자 확장자(`.JPG`, `.PNG`, `.HEIC`)도 지원된다.
