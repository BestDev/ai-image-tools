# 로컬 이미지 자동 분류 가이드

> 최종 업데이트: 2026-03-04
> 환경: Windows 11 / RTX 4090 24GB / Python 3.13

---

## 목차

1. [개요](#1-개요)
2. [모델 팩트 시트](#2-모델-팩트-시트)
3. [설치](#3-설치)
4. [분류 카테고리 설계](#4-분류-카테고리-설계)
5. [모듈 1: CLIP/SigLIP - 스타일/장르 분류](#5-모듈-1-clipsiglip---스타일장르-분류)
6. [모듈 2: YOLO - 인물 감지 및 카운팅](#6-모듈-2-yolo---인물-감지-및-카운팅)
7. [모듈 3: OpenCV - 배경 분석](#7-모듈-3-opencv---배경-분석)
8. [통합 분류 스크립트](#8-통합-분류-스크립트)
9. [레이블 튜닝 가이드](#9-레이블-튜닝-가이드)
10. [참고 자료](#10-참고-자료)

---

## 1. 개요

### 목적

로컬 환경에서 폴더 내 대량 이미지를 자동으로 분류한다.

### 분류 카테고리

| 카테고리 | 설명 |
|----------|------|
| 실사 (photorealistic) | 실제 사진 또는 포토리얼리스틱 렌더링 |
| 3D | 3D 렌더링, CGI |
| 애니메이션 (anime/animation) | 일본 애니메이션, 만화 스타일 |
| SF (sci-fi) | 과학적 미래, 우주, 사이버펑크 |
| 판타지 (fantasy) | 마법, 중세, 신화적 요소 |
| 배경단색 / solid 배경 | 단일 색상 또는 그라데이션 없는 배경 |
| 인물 여러명 | 2인 이상 인물이 포함된 이미지 |

### 기술 구성

```
[대량 이미지 폴더]
    │
    ├─ CLIP Zero-Shot ──→ 스타일 분류 (실사/3D/애니/SF/판타지)
    │   ~1GB VRAM, ~0.05초/이미지
    │
    ├─ YOLO ──→ 인물 감지 & 카운팅 (0명/1명/여러명)
    │   ~수백MB VRAM, 밀리초/이미지
    │
    └─ OpenCV ──→ 배경 분석 (단색/solid/복잡)
        GPU 불필요, 즉시
```

| 항목 | 수치 |
|------|------|
| 총 VRAM 사용 | ~2GB 이하 |
| 이미지당 처리 시간 | ~0.1초 이내 |
| GPU 필수 여부 | CLIP만 GPU 권장, 나머지 CPU 가능 |
| 학습/파인튜닝 | 불필요 (모두 zero-shot 또는 사전학습) |

---

## 2. 모델 팩트 시트

> 아래 정보는 공식 HuggingFace, GitHub, 논문에서 직접 확인한 내용입니다.

### CLIP ViT-L/14

| 항목 | 내용 | 출처 |
|------|------|------|
| HuggingFace | `openai/clip-vit-large-patch14` | [HF 모델 페이지](https://huggingface.co/openai/clip-vit-large-patch14) |
| 파라미터 | ~428M (비전 ~304M + 텍스트 ~124M) | [HF Discussion #30](https://huggingface.co/openai/clip-vit-large-patch14/discussions/30) |
| 모델 크기 (fp16) | ~816MB | HF 자동 분석 |
| VRAM (추론) | ~1-1.5GB | HF 벤치마크 |
| GPU 추론 속도 | 0.02-0.07초/이미지 | [CLIP-as-service 벤치마크](https://clip-as-service.jina.ai/user-guides/benchmark/) |
| 입력 해상도 | 224×224 | 공식 문서 |
| Zero-shot 방식 | 이미지-텍스트 임베딩 코사인 유사도 | [HF 공식 가이드](https://huggingface.co/docs/transformers/en/tasks/zero_shot_image_classification) |
| ImageNet 정확도 | ~75.5% (zero-shot) | CLIP 논문 |
| HF Pipeline | `zero-shot-image-classification` | [HF 공식 가이드](https://huggingface.co/docs/transformers/en/tasks/zero_shot_image_classification) |
| 학습 데이터 | 400M (이미지, 텍스트) 쌍 | CLIP 논문 |

**공식 문서 주의사항:**

> "CLIP's zero-shot classifiers can be sensitive to wording or phrasing and sometimes require trial and error 'prompt engineering' to perform well."
> — [OpenAI CLIP](https://openai.com/index/clip/)

### SigLIP so400m (대안)

| 항목 | 내용 | 출처 |
|------|------|------|
| HuggingFace | `google/siglip-so400m-patch14-384` | [HF 모델 페이지](https://huggingface.co/google/siglip-so400m-patch14-384) |
| CLIP과 차이 | Sigmoid loss (pairwise), CLIP은 Softmax (contrastive) | [SigLIP 논문](https://huggingface.co/papers/2303.15343) |
| 성능 | 소규모 배치에서 CLIP보다 우수 | [SigLIP 2 블로그](https://huggingface.co/blog/siglip2) |
| 입력 해상도 | 384×384 (CLIP보다 높음) | 공식 문서 |
| HF Pipeline | `zero-shot-image-classification` (동일) | [HF 공식 가이드](https://huggingface.co/docs/transformers/model_doc/siglip) |

### YOLO11

| 항목 | 내용 | 출처 |
|------|------|------|
| 설치 | `pip install ultralytics` | [GitHub](https://github.com/ultralytics/ultralytics) |
| 사전학습 | COCO 80 클래스, `person` = class 0 | [Ultralytics Docs](https://docs.ultralytics.com/tasks/detect/) |
| 모델 크기 (nano) | ~6MB | 공식 문서 |
| VRAM | 수백MB (nano) | 공식 문서 |
| 속도 | 밀리초 단위 | 공식 문서 |
| 사용법 | `model = YOLO("yolo11n.pt")` → 자동 다운로드 | [Ultralytics Docs](https://docs.ultralytics.com/) |

### Florence-2 (인물 감지 대안)

| 항목 | 내용 | 출처 |
|------|------|------|
| OD 출력 | `{'bboxes': [...], 'labels': ['person', ...]}` | [HF 모델 페이지](https://huggingface.co/microsoft/Florence-2-large) |
| 인물 카운팅 | `labels.count('person')` | 공식 예제 |
| 스타일 분류 | **미지원** (공식 태스크에 없음) | 공식 문서 |
| VRAM | ~2-4GB (0.77B) | 파라미터 기반 추정 |

### WD Tagger (부적합 판단 사유)

| 항목 | 내용 | 출처 |
|------|------|------|
| 학습 데이터 | Danbooru (애니메이션/일러스트 전용) | [HF 모델 카드](https://huggingface.co/SmilingWolf/wd-eva02-large-tagger-v3) |
| 실사/3D 구분 | **공식 미지원** | 학습 데이터 특성 |
| 결론 | 스타일 분류 목적에 부적합 | - |

---

## 3. 설치

```bash
# 가상환경 생성
python -m venv D:\_work\venv-classifier
D:\_work\venv-classifier\Scripts\activate

# PyTorch (CUDA 12.4)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124

# CLIP zero-shot 분류
pip install transformers pillow

# YOLO 인물 감지
pip install ultralytics

# OpenCV 배경 분석
pip install opencv-python numpy
```

---

## 4. 분류 카테고리 설계

### CLIP Zero-Shot 레이블 설계 원칙

공식 문서에 따르면 레이블 문구(phrasing)가 정확도에 직접 영향을 미침.

**HuggingFace 공식 가이드 권장 패턴:**

```python
# 공식 예제에서 사용하는 패턴
candidate_labels = ["a photo of a cat", "a photo of a dog"]

# 템플릿: "This is a photo of {label}." 또는 "a {label}"
```

### 본 프로젝트 레이블 설계

| 분류 | 레이블 (영문) | 설계 근거 |
|------|--------------|-----------|
| 실사 | `"a real photograph of a scene or person"` | 사진 매체 강조 |
| 3D | `"a 3D rendered CGI image"` | 3D 렌더링 매체 강조 |
| 애니메이션 | `"an anime or manga style illustration"` | 일본 애니메이션 스타일 특정 |
| SF | `"a science fiction scene with futuristic technology or space"` | SF 장르 요소 명시 |
| 판타지 | `"a fantasy scene with magic, dragons, or medieval elements"` | 판타지 장르 요소 명시 |

> **주의**: 위 레이블은 시작점이며, 실제 이미지에 맞게 튜닝이 필요할 수 있음.
> 자세한 튜닝 방법은 [9. 레이블 튜닝 가이드](#9-레이블-튜닝-가이드) 참고.

---

## 5. 모듈 1: CLIP/SigLIP - 스타일/장르 분류

### 동작 원리 (공식 문서 기반)

> "Zero-shot image classification models are multi-modal models trained on a large dataset of images and associated descriptions. These models learn aligned vision-language representations that can be used for many downstream tasks including zero-shot image classification."
> — [HF Zero-shot Classification Guide](https://huggingface.co/docs/transformers/en/tasks/zero_shot_image_classification)

```
이미지 → CLIP 이미지 인코더 → 이미지 임베딩
                                              → 코사인 유사도 → 점수 순위
레이블들 → CLIP 텍스트 인코더 → 텍스트 임베딩들
```

### Pipeline 방식 (공식 가이드 코드)

```python
import torch
from transformers import pipeline

classifier = pipeline(
    task="zero-shot-image-classification",
    model="openai/clip-vit-large-patch14",
    device=0,
    torch_dtype=torch.float16,
)

labels = [
    "a real photograph of a scene or person",
    "a 3D rendered CGI image",
    "an anime or manga style illustration",
    "a science fiction scene with futuristic technology or space",
    "a fantasy scene with magic, dragons, or medieval elements",
]

results = classifier("path/to/image.jpg", candidate_labels=labels)
# [{'score': 0.85, 'label': 'a real photograph...'}, ...]
```

### AutoModel 방식 (공식 가이드 코드)

```python
import torch
from PIL import Image
from transformers import AutoProcessor, AutoModel

model = AutoModel.from_pretrained(
    "openai/clip-vit-large-patch14",
    torch_dtype=torch.float16,
    device_map="cuda",
)
processor = AutoProcessor.from_pretrained("openai/clip-vit-large-patch14")

def classify_style(image_path: str, labels: list[str]) -> list[dict]:
    image = Image.open(image_path).convert("RGB")
    text_labels = [f"This is a photo of {label}." for label in labels]

    inputs = processor(images=image, text=text_labels, return_tensors="pt", padding=True)
    inputs = {k: v.to("cuda") for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    logits = outputs.logits_per_image[0]
    probs = logits.softmax(dim=-1).cpu().numpy()

    results = [
        {"label": label, "score": float(score)}
        for label, score in sorted(zip(labels, probs), key=lambda x: -x[1])
    ]
    return results
```

---

## 6. 모듈 2: YOLO - 인물 감지 및 카운팅

### 공식 사용법

```python
from ultralytics import YOLO

model = YOLO("yolo11n.pt")  # nano 모델, 최초 실행 시 자동 다운로드

def count_people(image_path: str) -> int:
    results = model(image_path, verbose=False)
    for r in results:
        # COCO class 0 = person
        person_count = int((r.boxes.cls == 0).sum().item())
        return person_count
    return 0
```

### 인물 수 기반 분류

| 감지 결과 | 분류 |
|-----------|------|
| 0명 | `no_person` |
| 1명 | `single_person` |
| 2명 이상 | `multiple_people` |

---

## 7. 모듈 3: OpenCV - 배경 분석

### 원리

이미지 가장자리 영역의 색상 분산(variance)을 측정하여 단색 배경 여부를 판단한다.

- 가장자리 픽셀의 색상 표준편차가 낮으면 → 단색/solid 배경
- 높으면 → 복잡한 배경

```python
import cv2
import numpy as np

def detect_solid_background(
    image_path: str,
    edge_ratio: float = 0.1,
    std_threshold: float = 15.0,
) -> dict:
    """
    이미지 가장자리 영역의 색상 분산으로 단색 배경 여부를 판단한다.

    Args:
        image_path: 이미지 경로
        edge_ratio: 가장자리 영역 비율 (0.1 = 상하좌우 10%)
        std_threshold: 표준편차 임계값 (낮을수록 엄격)

    Returns:
        {"is_solid": bool, "std": float, "dominant_color": tuple}
    """
    img = cv2.imread(image_path)
    if img is None:
        return {"is_solid": False, "std": 999.0, "dominant_color": (0, 0, 0)}

    h, w = img.shape[:2]
    edge_h = int(h * edge_ratio)
    edge_w = int(w * edge_ratio)

    # 가장자리 영역 추출 (상, 하, 좌, 우)
    regions = [
        img[:edge_h, :],           # 상단
        img[h - edge_h:, :],       # 하단
        img[:, :edge_w],           # 좌측
        img[:, w - edge_w:],       # 우측
    ]

    edge_pixels = np.concatenate([r.reshape(-1, 3) for r in regions], axis=0)

    # 각 채널별 표준편차의 평균
    std_per_channel = np.std(edge_pixels.astype(np.float32), axis=0)
    mean_std = float(np.mean(std_per_channel))

    # 주요 색상 (중앙값)
    dominant = tuple(int(x) for x in np.median(edge_pixels, axis=0))

    return {
        "is_solid": mean_std < std_threshold,
        "std": round(mean_std, 2),
        "dominant_color_bgr": dominant,
    }
```

### 임계값 가이드

| `std_threshold` | 판정 기준 |
|:---:|------------|
| < 5 | 거의 완벽한 단색 (스튜디오 배경) |
| < 15 | 약간의 노이즈/그라데이션 허용 (기본값) |
| < 25 | 느슨한 기준 (부드러운 그라데이션 포함) |

---

## 8. 통합 분류 스크립트

### `image_classifier.py`

아래 스크립트는 3개 모듈을 결합하여 폴더 내 이미지를 일괄 분류한다.

→ 별도 파일로 저장됨: `D:\_work\image_classifier.py`

### 출력 형식

#### 콘솔 출력

```
=== 이미지 분류 시작 ===
입력: D:\_work\images (총 150개 이미지)
출력: D:\_work\classified

[  1/150] photo_001.jpg
          스타일: photorealistic (0.92) | 인물: 1명 | 배경: complex
[  2/150] render_002.png
          스타일: 3d_render (0.87) | 인물: 0명 | 배경: solid (rgb: 255,255,255)
[  3/150] anime_003.jpg
          스타일: anime (0.95) | 인물: 3명 → multiple_people | 배경: complex
...

=== 분류 완료 ===
총 150개 이미지 처리 (12.3초, 0.08초/이미지)

분류 결과:
  photorealistic:  62개 (41.3%)
  3d_render:       28개 (18.7%)
  anime:           35개 (23.3%)
  sci_fi:          15개 (10.0%)
  fantasy:         10개 ( 6.7%)

  solid_background: 23개 (15.3%)
  multiple_people:  31개 (20.7%)
```

#### CSV 리포트

```csv
filename,style,style_score,person_count,person_category,is_solid_bg,bg_std,bg_color
photo_001.jpg,photorealistic,0.92,1,single_person,false,45.2,"(128,130,125)"
render_002.png,3d_render,0.87,0,no_person,true,3.1,"(255,255,255)"
anime_003.jpg,anime,0.95,3,multiple_people,false,67.8,"(45,120,200)"
```

#### 폴더 복사 모드 (선택)

```
D:\_work\classified\
├── photorealistic\
│   ├── photo_001.jpg
│   └── ...
├── 3d_render\
│   └── render_002.png
├── anime\
│   └── anime_003.jpg
├── sci_fi\
├── fantasy\
├── solid_background\
│   └── render_002.png  (중복 가능: 스타일 + 배경 둘 다 해당)
└── multiple_people\
    └── anime_003.jpg
```

---

## 9. 레이블 튜닝 가이드

CLIP의 zero-shot 정확도는 레이블 문구에 크게 의존한다.

### 튜닝 방법

1. **소규모 테스트**: 카테고리별 10-20개 이미지로 먼저 테스트
2. **점수 확인**: `--verbose` 모드로 각 레이블별 점수 확인
3. **레이블 수정**: 오분류가 많은 카테고리의 레이블 문구 조정

### 레이블 변형 예시

```python
# 실사가 3D로 오분류되는 경우 → 더 구체적으로
"a real photograph taken with a camera"  # 카메라 촬영 강조

# 3D가 실사로 오분류되는 경우 → 렌더링 강조
"a computer generated 3D render with CGI lighting and textures"

# SF와 판타지가 혼동되는 경우 → 키 요소 분리
"a science fiction scene with spaceships, robots, or cyberpunk city"
"a fantasy scene with swords, castles, elves, or magical creatures"

# 애니메이션이 일러스트와 혼동되는 경우
"a Japanese anime style drawing with large eyes and colorful hair"
```

### 다중 레이블 전략

하나의 카테고리에 여러 레이블을 두고 최고 점수를 사용:

```python
STYLE_LABELS = {
    "photorealistic": [
        "a real photograph taken with a camera",
        "a photorealistic image of real life",
    ],
    "3d_render": [
        "a 3D rendered CGI image",
        "a computer generated 3D scene with rendered lighting",
    ],
    "anime": [
        "an anime or manga style illustration",
        "a Japanese animation style drawing",
    ],
}
# 각 카테고리별 레이블 중 최고 점수를 해당 카테고리 점수로 사용
```

---

## 10. 참고 자료

### 공식 문서

- [HF Zero-shot Image Classification Guide](https://huggingface.co/docs/transformers/en/tasks/zero_shot_image_classification)
- [CLIP 공식 (HF Transformers)](https://huggingface.co/docs/transformers/model_doc/clip)
- [SigLIP 공식 (HF Transformers)](https://huggingface.co/docs/transformers/model_doc/siglip)
- [CLIP ViT-L/14 모델](https://huggingface.co/openai/clip-vit-large-patch14)
- [CLIP ViT-L/14 VRAM 분석](https://huggingface.co/openai/clip-vit-large-patch14/discussions/30)
- [OpenAI CLIP 소개](https://openai.com/index/clip/)
- [SigLIP 2 블로그](https://huggingface.co/blog/siglip2)
- [SigLIP VRAM Discussion](https://github.com/mlfoundations/open_clip/discussions/872)

### YOLO

- [Ultralytics YOLO Docs](https://docs.ultralytics.com/)
- [Object Detection Docs](https://docs.ultralytics.com/tasks/detect/)
- [Ultralytics GitHub](https://github.com/ultralytics/ultralytics)

### 대안 모델

- [Florence-2-large](https://huggingface.co/microsoft/Florence-2-large)
- [WD Tagger v3](https://huggingface.co/SmilingWolf/wd-eva02-large-tagger-v3) (애니 태깅 전용)


