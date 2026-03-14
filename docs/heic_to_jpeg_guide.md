# heic_to_jpeg.py 사용 가이드

> 최종 업데이트: 2026-03-05
> 환경: WSL2 / Ubuntu-24.04 / Python 3.12
> 가상환경: `<저장소 루트>/venv-classifier`
> 검증 상태: `Ubuntu-24.04` 에서 실행 확인

---

## 목차

1. [개요](#1-개요)
2. [실행 방법](#2-실행-방법)
3. [옵션 상세](#3-옵션-상세)
4. [실 사용 예제](#4-실-사용-예제)
5. [트러블슈팅](#5-트러블슈팅)

---

## 1. 개요

폴더 내 HEIC/HEIF 파일을 JPEG로 일괄 변환하고 원본을 삭제한다.
`image_classifier.py`, `prompt_generator.py`에서 HEIC를 직접 처리할 수도 있지만,
파일 수가 많을 경우 **미리 JPEG로 변환해두는 것이 전체 처리 속도에 유리**하다.

### 주요 특징

- **원본 자동 삭제**: 변환 성공 후 HEIC 삭제 → 용량·파일 수 두 배 증가 방지
- **건너뜀 처리**: 같은 이름의 `.jpg`가 이미 존재하면 덮어쓰지 않고 건너뜀
- **재귀 처리**: `--recursive` 로 하위 폴더까지 한 번에 처리
- **Dry-run**: `--dry-run` 으로 실제 변환 없이 대상 파일 목록만 확인
- **가상환경 자동 활성화**: 시스템 Python으로 실행해도 자동으로 `venv-classifier` 전환

### 지원 입력 형식

`.heic` `.heif`

### 출력 형식

`.jpg` (JPEG, 기본 품질 95)

---

## 2. 실행 방법

```bash
env -u LD_LIBRARY_PATH python3 heic_to_jpeg.py <폴더> [옵션]
```

가상환경 수동 활성화 없이 바로 실행 가능하다. `heic_to_jpeg.py` 는 GPU를 사용하지 않지만, 작업 환경 통일을 위해 `Ubuntu-24.04` 와 동일 실행 형식을 권장한다.

---

## 3. 옵션 상세

| 옵션 | 단축 | 기본값 | 설명 |
|------|------|--------|------|
| `input_dir` | — | 필수 | HEIC 파일이 있는 폴더 |
| `--quality` | `-q` | `95` | JPEG 품질 (1~100) |
| `--keep` | — | off | 변환 후 원본 HEIC 유지 (기본: 삭제) |
| `--recursive` | `-r` | off | 하위 폴더까지 재귀 처리 |
| `--dry-run` | `-n` | off | 실제 변환 없이 목록만 출력 |

### `--quality` 기준

| 값 | 용량 | 권장 상황 |
|:--:|------|----------|
| `95` | 원본 대비 약 60~80% | 기본값, 육안 구분 불가 수준 |
| `90` | 약 40~60% | 용량 절약 우선 |
| `85` | 약 30~50% | SNS 업로드·웹 배포용 |

---

## 4. 실 사용 예제

### 예제 A: 기본 변환 (원본 삭제)

폴더 내 모든 HEIC를 JPEG로 변환하고 원본 HEIC는 삭제한다.

```bash
python3 heic_to_jpeg.py /mnt/d/photos
```

**출력:**
```
=== HEIC → JPEG 변환 ===
폴더  : /mnt/d/photos
파일  : 42개
품질  : 95
원본  : 삭제

[ 1/42] IMG_0001.HEIC
          → IMG_0001.jpg  (2341KB)
[ 2/42] IMG_0002.heic
          → IMG_0002.jpg  (1892KB)
...

=== 변환 완료 ===
변환: 42개  건너뜀: 0개  오류: 0개
삭제: 42개 (원본 HEIC)
소요: 18.3초
```

---

### 예제 B: 변환 전 목록 확인 (Dry-run)

실제 변환 없이 어떤 파일이 처리될지 먼저 확인한다.

```bash
python3 heic_to_jpeg.py /mnt/d/photos --dry-run
```

**출력:**
```
=== [DRY RUN] HEIC → JPEG 변환 ===
폴더  : /mnt/d/photos
파일  : 42개
품질  : 95
원본  : 삭제

[ 1/42] IMG_0001.HEIC
          → IMG_0001.jpg
[ 2/42] IMG_0002.heic
          → IMG_0002.jpg
...
```

결과가 만족스러우면 `--dry-run` 없이 다시 실행한다.

---

### 예제 C: 원본 유지 (테스트용)

변환 결과를 먼저 확인하고 싶을 때 원본을 삭제하지 않는다.

```bash
python3 heic_to_jpeg.py /mnt/d/photos --keep
```

변환 결과 확인 후 원본 삭제:

```bash
# JPEG 정상 확인 후 수동 삭제
find /mnt/d/photos -name "*.heic" -o -name "*.HEIC" | xargs rm
```

---

### 예제 D: 품질 조정

용량이 중요할 때 품질을 낮춘다.

```bash
python3 heic_to_jpeg.py /mnt/d/photos --quality 90
```

---

### 예제 E: 하위 폴더까지 재귀 처리

여러 하위 폴더에 분산된 HEIC를 한 번에 변환한다.

```bash
python3 heic_to_jpeg.py /mnt/d/photos --recursive
```

**구조 예시:**
```
/mnt/d/photos/
├── 2024/
│   ├── IMG_0001.HEIC  →  IMG_0001.jpg  (HEIC 삭제)
│   └── IMG_0002.heic  →  IMG_0002.jpg  (HEIC 삭제)
└── 2025/
    ├── IMG_0100.HEIC  →  IMG_0100.jpg  (HEIC 삭제)
    └── IMG_0101.heic  →  IMG_0101.jpg  (HEIC 삭제)
```

---

### 예제 F: classifier 워크플로우 연계

iPhone 사진 폴더를 분류하기 전에 먼저 JPEG로 변환한다.

```bash
# 1단계: HEIC → JPEG 변환 (원본 삭제)
python3 heic_to_jpeg.py /mnt/d/iphone_photos

# 2단계: 스타일 분류
python3 image_classifier.py /mnt/d/iphone_photos --by style --move

# 3단계: 인물 수 분류
python3 image_classifier.py /mnt/d/iphone_photos/by_style/photorealistic --by person --move
```

---

### 예제 G: prompt_generator 연계

변환 후 바로 프롬프트 생성.

```bash
# 1단계: HEIC → JPEG 변환
python3 heic_to_jpeg.py /mnt/d/iphone_photos

# 2단계: 프롬프트 생성 (누적 저장)
python3 scripts/prompt_generator_v2.py /mnt/d/iphone_photos \
  --method 2 \
  --output-dir /mnt/d/prompts \
  --accumulate
```

---

### 옵션 조합 정리

| 상황 | 명령 |
|------|------|
| 기본 변환 (삭제) | `python3 heic_to_jpeg.py <폴더>` |
| 목록 먼저 확인 | `python3 heic_to_jpeg.py <폴더> --dry-run` |
| 원본 유지 | `python3 heic_to_jpeg.py <폴더> --keep` |
| 용량 절약 | `python3 heic_to_jpeg.py <폴더> -q 90` |
| 하위 폴더 포함 | `python3 heic_to_jpeg.py <폴더> --recursive` |
| 하위 폴더 + 삭제 | `python3 heic_to_jpeg.py <폴더> -r` |

---

## 5. 트러블슈팅

### pillow-heif 오류 발생 시

```bash
<저장소 루트>/venv-classifier/bin/pip install pillow-heif
```

### 변환 중 특정 파일에서 오류 발생 시

오류가 발생한 파일은 건너뛰고 계속 진행된다.
불완전하게 생성된 `.jpg`는 자동으로 삭제된다.
오류 파일은 HEIC 원본이 그대로 남아 있다.

### 이미 `.jpg`가 존재하는 파일

같은 이름의 `.jpg`가 이미 있으면 덮어쓰지 않고 `건너뜀`으로 표시된다.
재변환이 필요하면 기존 `.jpg`를 먼저 삭제한다.

### 대소문자 확장자 처리

`.HEIC`, `.Heic`, `.heif` 등 대소문자 구분 없이 모두 처리된다.
