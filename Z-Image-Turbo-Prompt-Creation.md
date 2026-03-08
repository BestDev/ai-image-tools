# 이미지 → Z-Image Turbo 프롬프트 생성 가이드

> 최종 업데이트: 2026-03-04
> 환경: Windows 11 / RTX 4090 24GB / Python 3.13

---

## 목차

1. [개요](#1-개요)
2. [모델 팩트 시트](#2-모델-팩트-시트)
3. [방식 1: JoyCaption Beta One 단독](#3-방식-1-joycaption-beta-one-단독)
4. [방식 2: Qwen2.5-VL-7B 단독](#4-방식-2-qwen25-vl-7b-단독)
5. [방식 3: JoyCaption + Qwen2.5-VL 파이프라인](#5-방식-3-joycaption--qwen25-vl-파이프라인)
6. [방식별 비교](#6-방식별-비교)
7. [Z-Image Turbo 프롬프트 형식 참고](#7-z-image-turbo-프롬프트-형식-참고)
8. [참고 자료](#8-참고-자료)

---

## 1. 개요

### 목적

로컬 환경에서 이미지를 분석하여 Z-Image Turbo 모델에 최적화된 **영문 서술형 프롬프트**를 생성한다.

### Z-Image Turbo 프롬프트 특성

- **서술형** (단어 나열/태그 방식이 아님)
- **4-Layer 구조**: `[피사체 & 행동] + [텍스트 요소] + [시각 스타일] + [조명 & 분위기]`
- **최적 길이**: 80~250 단어
- **Negative Prompt 미지원**: 제외 요소를 긍정 표현으로 명시
- **중요 키워드 앞배치**: ~75 토큰 이후 어텐션 감퇴

### 핵심 요구사항

이미지에서 다음 요소를 서술형으로 추출해야 함:

| 요소 | 설명 | 예시 |
|------|------|------|
| 인물 묘사 | 나이, 외모, 인종, 체형 | `a 28-year-old woman with dark brown wavy hair` |
| 표정 | 감정, 시선 방향 | `gentle smile, looking directly at camera` |
| 포즈 | 자세, 동작 | `sitting cross-legged, hands resting on knees` |
| 의상 | 옷 종류, 색상, 질감 | `wearing a cream knit sweater, fabric detail visible` |
| 배경 | 장소, 환경, 오브젝트 | `in a sunlit wooden cafe, bookshelves in background` |
| 무드 | 전체 분위기, 색감 톤 | `warm and cozy atmosphere, autumn palette` |
| 라이팅 | 조명 방향, 종류, 색온도 | `soft natural window light from the left, golden hour` |
| 스타일 | 사진/회화/3D 등 매체 | `photorealistic, Fujifilm X-T4, shallow depth of field` |

---

## 2. 모델 팩트 시트

> 아래 정보는 공식 HuggingFace, GitHub 문서에서 직접 확인한 내용입니다.

### JoyCaption Beta One

| 항목 | 내용 | 출처 |
|------|------|------|
| HuggingFace | `fancyfeast/llama-joycaption-beta-one-hf-llava` | [HF 모델 페이지](https://huggingface.co/fancyfeast/llama-joycaption-beta-one-hf-llava) |
| 아키텍처 | LLaVA (SigLIP-2 + Llama 3.1) | HF 모델 카드 |
| 비전 인코더 | `google/siglip2-so400m-patch14-384` | HF 모델 카드 |
| 베이스 LLM | Llama 3.1 (8B) | HF 모델 카드 |
| 파라미터 | 8B | HF 모델 카드 |
| VRAM (bf16) | ~17-18.7GB | [GitHub README](https://github.com/fpgaminer/joycaption) |
| VRAM (NF4) | ~8.5-9.2GB | GitHub README, 커뮤니티 테스트 |
| GGUF 지원 | 지원 (KoboldCpp 1.91+) | [Civitai Release](https://civitai.com/articles/14672/joycaption-beta-one-release) |
| 학습 데이터 | 2.4M 샘플 (Alpha Two의 2배) | Civitai Release |
| 시스템 프롬프트 | `"You are a helpful image captioner."` (고정) | [app.py 소스](https://huggingface.co/spaces/fancyfeast/joy-caption-alpha-two) |
| Instruction Following | **불가** ("not a general instruction follower") | GitHub README |

**캡션 타입 (공식 확인):**

| 모드 | 안정성 | 설명 |
|------|--------|------|
| **Descriptive (formal)** | **가장 안정적** | 격식체 서술형 캡션 |
| **Descriptive (Informal)** | 안정적 | 비격식 서술형 캡션 |
| **Straightforward** | 안정적 (Beta One 신규) | Descriptive와 SD 프롬프트의 중간 |
| Training Prompt | 불안정 (실험적) | 학습용 프롬프트 |
| MidJourney | 불안정 (실험적) | MidJourney 스타일 |
| Booru tag list | 개선됨 (Beta One) | 태그 목록 |
| Art Critic | - | 구도/스타일 분석 |
| Product Listing | - | 상품 설명 |
| Social Media Post | - | SNS 캡션 |

### Qwen2.5-VL-7B-Instruct

| 항목 | 내용 | 출처 |
|------|------|------|
| HuggingFace | `Qwen/Qwen2.5-VL-7B-Instruct` | [HF 모델 페이지](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct) |
| 파라미터 | 7B | HF 모델 카드 |
| VRAM (bf16) | ~17GB+ (이미지 해상도에 따라 증가) | [HF Discussion #18](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct/discussions/18) |
| RTX 4090 OOM | **보고됨** (bf16, 고해상도 이미지) | HF Discussion #18 |
| 4bit 양자화 VRAM | ~8-12GB | 커뮤니티 보고 |
| 시스템 프롬프트 | **지원** (chat template) | HF 모델 카드 |
| Instruction Following | **가능** (범용 VLM) | HF 모델 카드 |
| 로컬 파일 입력 | `file:///path/to/image.jpg` | HF 모델 카드 |
| 컨텍스트 윈도우 | 32,768 토큰 | HF 모델 카드 |
| 의존성 | `transformers` (소스 빌드 권장), `qwen-vl-utils`, `accelerate` | HF 모델 카드 |

### Florence-2-large (참고용)

| 항목 | 내용 |
|------|------|
| 파라미터 | 0.77B |
| `<MORE_DETAILED_CAPTION>` | 지원 (자연어 문장 출력) |
| VRAM | ~2-4GB (추정, 공식 미명시) |
| 한계 | 캡션 스타일이며 프롬프트 스타일 아님, 형식 커스텀 불가 |

---

## 3. 방식 1: JoyCaption Beta One 단독

### 3.1 설치

```bash
# 가상환경 생성 (권장)
python -m venv D:\_work\venv-joycaption
D:\_work\venv-joycaption\Scripts\activate

# 의존성 설치
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
pip install transformers==4.44.0 accelerate sentencepiece peft==0.12.0 pillow

# bf16 모드 (~17-18.7GB VRAM) - RTX 4090에서 실행 가능
# NF4 모드 (~9GB VRAM)를 원하면 추가 설치:
pip install bitsandbytes
```

### 3.2 사용법: bf16 모드

```python
import torch
from PIL import Image
from transformers import AutoProcessor, LlavaForConditionalGeneration

MODEL_NAME = "fancyfeast/llama-joycaption-beta-one-hf-llava"

# 모델 로드 (최초 실행 시 다운로드 ~16GB)
processor = AutoProcessor.from_pretrained(MODEL_NAME)
model = LlavaForConditionalGeneration.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.bfloat16,
    device_map=0
)
model.eval()

def generate_prompt(image_path: str, caption_type: str = "descriptive") -> str:
    """
    이미지에서 서술형 프롬프트를 생성한다.

    caption_type 옵션:
      - "descriptive"     : 격식체 서술형 (가장 안정적, 권장)
      - "straightforward" : 간결한 서술형 (Beta One 신규)
      - "training"        : 학습용 프롬프트 (불안정)
    """
    prompts = {
        "descriptive": "Write a long descriptive caption for this image in a formal tone.",
        "straightforward": "Write a straightforward caption for this image.",
        "training": "Write a stable diffusion prompt for this image.",
    }

    image = Image.open(image_path).convert("RGB")
    prompt_text = prompts.get(caption_type, prompts["descriptive"])

    convo = [
        {"role": "system", "content": "You are a helpful image captioner."},
        {"role": "user", "content": prompt_text},
    ]

    convo_string = processor.apply_chat_template(
        convo, tokenize=False, add_generation_prompt=True
    )
    inputs = processor(
        text=[convo_string], images=[image], return_tensors="pt"
    ).to("cuda")
    inputs["pixel_values"] = inputs["pixel_values"].to(torch.bfloat16)

    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=True,
            temperature=0.6,
            top_p=0.9,
        )[0]

    # 입력 토큰 제거하고 생성된 텍스트만 추출
    output = output[inputs["input_ids"].shape[1]:]
    caption = processor.tokenizer.decode(output, skip_special_tokens=True)
    return caption.strip()


# 사용 예시
if __name__ == "__main__":
    result = generate_prompt(
        image_path=r"D:\_work\test_image.jpg",
        caption_type="descriptive"
    )
    print(result)
```

### 3.3 사용법: NF4 양자화 모드 (VRAM 절약)

```python
import torch
from PIL import Image
from transformers import AutoProcessor, LlavaForConditionalGeneration, BitsAndBytesConfig

MODEL_NAME = "fancyfeast/llama-joycaption-beta-one-hf-llava"

# 4bit 양자화 설정 (~9GB VRAM)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
)

processor = AutoProcessor.from_pretrained(MODEL_NAME)
model = LlavaForConditionalGeneration.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    device_map=0
)
model.eval()

# 이후 generate_prompt 함수는 bf16 모드와 동일하게 사용
```

> **주의**: `bitsandbytes`는 Windows에서 공식 지원이 제한적일 수 있음.
> `pip install bitsandbytes-windows` 또는 커뮤니티 빌드 필요.

### 3.4 출력 예시 (Descriptive 모드)

입력 이미지: 카페에 앉아있는 젊은 여성 사진

```
The image depicts a young woman, likely in her late twenties, seated at a rustic
wooden table inside a warmly lit cafe. She has dark brown wavy hair that falls
just past her shoulders, with a few loose strands framing her face. Her expression
is calm and contemplative, with soft brown eyes gazing slightly off-camera to the
left. She wears a cream-colored chunky knit sweater with visible cable-knit
texture, paired with a delicate gold necklace. Her hands are wrapped around a
ceramic coffee mug. The background reveals exposed brick walls, warm pendant
lighting, and blurred shelves of books. The overall mood is cozy and intimate,
with warm amber tones dominating the color palette. Natural light enters from a
window to the right, creating soft shadows and gentle highlights on her skin.
The photograph has a shallow depth of field with creamy bokeh in the background,
suggesting a prime lens. Subtle film grain is present throughout.
```

### 3.5 배치 처리

```python
import os
from pathlib import Path

def batch_generate(image_dir: str, output_dir: str, caption_type: str = "descriptive"):
    """디렉토리 내 모든 이미지를 처리하여 .txt 파일로 저장"""
    image_dir = Path(image_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    images = [f for f in image_dir.iterdir() if f.suffix.lower() in extensions]

    print(f"총 {len(images)}개 이미지 처리 시작")

    for i, img_path in enumerate(images):
        print(f"[{i+1}/{len(images)}] {img_path.name}")
        caption = generate_prompt(str(img_path), caption_type)

        output_file = output_dir / f"{img_path.stem}.txt"
        output_file.write_text(caption, encoding="utf-8")

    print("완료")


# 사용
batch_generate(
    image_dir=r"D:\_work\images",
    output_dir=r"D:\_work\prompts",
    caption_type="descriptive"
)
```

### 3.6 장단점

| 장점 | 단점 |
|------|------|
| 이미지→프롬프트 **전용** 모델 (학습 자체가 Diffusion 프롬프트 역생성) | Z-Image 4-Layer 형식으로 출력 형식 지정 **불가** |
| Descriptive 모드 안정성 **가장 높음** | Instruction following 미지원 ("이렇게 써줘" 지시 불가) |
| GPT-4o급 캡셔닝 정확도 (공식 주장) | 시스템 프롬프트 고정 (`"You are a helpful image captioner."`) |
| 무료, 오픈소스, 무제한 사용 | bf16 기준 ~17GB VRAM (NF4로 ~9GB 가능) |
| 배치 처리 가능 | Windows에서 bitsandbytes 호환성 이슈 가능 |
| GGUF 양자화 지원 (Beta One) | 출력이 일반 묘사문이라 프롬프트 최적화 후가공 필요할 수 있음 |

---

## 4. 방식 2: Qwen2.5-VL-7B 단독

### 4.1 설치

```bash
# 가상환경 생성
python -m venv D:\_work\venv-qwen
D:\_work\venv-qwen\Scripts\activate

# transformers 소스 빌드 (공식 권장)
pip install git+https://github.com/huggingface/transformers accelerate

# Qwen VL 유틸리티
pip install qwen-vl-utils[decord]==0.0.8

# PyTorch (CUDA)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124

# 4bit 양자화 사용 시 (권장 - OOM 방지)
pip install bitsandbytes
# 또는
pip install auto-gptq
```

### 4.2 사용법: 4bit 양자화 (권장)

> **중요**: RTX 4090 24GB에서 bf16 모드 사용 시 이미지 해상도에 따라 **OOM 발생 보고**가 있음.
> 안정적 실행을 위해 4bit 양자화 또는 `min_pixels`/`max_pixels` 제한을 권장.

```python
import torch
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
from qwen_vl_utils import process_vision_info

MODEL_NAME = "Qwen/Qwen2.5-VL-7B-Instruct"

# 4bit 양자화 (~8-12GB VRAM)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
)

model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    device_map="auto",
)

# 해상도 제한으로 VRAM 절약
processor = AutoProcessor.from_pretrained(
    MODEL_NAME,
    min_pixels=256 * 28 * 28,    # 200,704
    max_pixels=1280 * 28 * 28,   # 1,003,520
)

# Z-Image Turbo 4-Layer 프롬프트 형식 시스템 프롬프트
SYSTEM_PROMPT = """You are an expert image-to-prompt converter specialized for text-to-image AI models.

Analyze the given image and generate a descriptive English prompt following this exact structure:

[Subject & Action] + [Visual Style] + [Lighting & Atmosphere] + [Technical Constraints]

Rules:
1. SUBJECT & ACTION (place first, most important):
   - Person: age, gender, ethnicity, hair (color/style/length), facial expression, eye direction, pose, body language
   - Clothing: type, color, fabric texture, condition, accessories
   - Action: what they are doing, hand positions, body orientation

2. VISUAL STYLE:
   - Medium: photorealistic / cinematic / oil painting / etc.
   - Camera: lens type, depth of field, film stock
   - Texture keywords: skin texture, fabric detail, surface imperfections, film grain

3. LIGHTING & ATMOSPHERE:
   - Light source direction and type (natural/artificial)
   - Color temperature (warm/cool/neutral)
   - Mood and overall atmosphere
   - Background description with depth

4. TECHNICAL CONSTRAINTS (place at end):
   - Quality: 8K resolution, ultra-detailed, sharp focus
   - Safety: correct anatomy, no extra limbs, no watermark

Output ONLY the prompt text. No explanations, no labels, no markdown.
Write as a single flowing paragraph, 80-250 words.
Place the most important descriptors (subject + appearance) at the very beginning."""


def generate_prompt(image_path: str) -> str:
    """이미지에서 Z-Image Turbo 형식의 서술형 프롬프트를 생성한다."""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "image", "image": f"file:///{image_path}"},
                {"type": "text", "text": "Generate a Z-Image Turbo prompt for this image."},
            ],
        },
    ]

    text = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    ).to("cuda")

    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
        )

    generated_ids_trimmed = [
        out_ids[len(in_ids):]
        for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    result = processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True
    )[0]
    return result.strip()


# 사용 예시
if __name__ == "__main__":
    result = generate_prompt(r"D:\_work\test_image.jpg")
    print(result)
```

### 4.3 사용법: bf16 모드 (VRAM 여유 시)

```python
# bf16 로드 (OOM 위험 - 이미지 해상도 반드시 제한)
model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    MODEL_NAME,
    torch_dtype=torch.bfloat16,
    device_map="auto",
)

# 해상도를 낮게 제한하여 OOM 방지
processor = AutoProcessor.from_pretrained(
    MODEL_NAME,
    min_pixels=256 * 28 * 28,
    max_pixels=512 * 28 * 28,   # 더 낮게 설정
)
```

### 4.4 기대 출력 예시

시스템 프롬프트의 4-Layer 형식 지시에 따른 기대 출력:

```
A 28-year-old East Asian woman with dark brown wavy hair falling past her
shoulders, light freckles across her nose, soft brown eyes with a calm
contemplative gaze directed slightly off-camera to the left, seated at a
rustic wooden cafe table with her hands wrapped around a ceramic coffee mug.
She wears a cream-colored chunky cable-knit sweater with visible fabric
texture, paired with a thin gold pendant necklace. The background reveals
an intimate cafe interior with exposed red brick walls, warm pendant Edison
bulb lighting, and blurred wooden bookshelves creating depth. Photorealistic
style with shallow depth of field, creamy bokeh, Fujifilm X-T4 aesthetic
with subtle film grain and natural skin texture with visible pores. Warm
natural window light enters from the right side casting soft directional
shadows, golden hour color temperature, creating an overall cozy and intimate
atmosphere with warm amber and brown tones dominating the palette. 8K
resolution, ultra-detailed, sharp focus on subject, correct anatomy, no
watermark, no text overlay.
```

### 4.5 시스템 프롬프트 커스텀 팁

Qwen2.5-VL은 instruction following이 가능하므로 시스템 프롬프트를 목적에 따라 수정할 수 있다:

```python
# 인물 중심 프롬프트 (인물 묘사 강화)
SYSTEM_PROMPT_PORTRAIT = """...(생략)...
Focus heavily on:
- Exact age estimation, ethnicity, facial bone structure
- Hair: color, length, style, texture (straight/wavy/curly)
- Expression: specific emotion, mouth position, eye direction, eyebrow position
- Skin: tone, texture, blemishes, makeup details
- Pose: exact body orientation, hand positions, weight distribution
..."""

# 풍경 중심 프롬프트
SYSTEM_PROMPT_LANDSCAPE = """...(생략)...
Focus heavily on:
- Terrain, vegetation, water features
- Sky conditions, cloud formations
- Depth layers (foreground/midground/background)
- Atmospheric effects (fog, haze, light rays)
..."""
```

### 4.6 장단점

| 장점 | 단점 |
|------|------|
| **시스템 프롬프트로 Z-Image 4-Layer 형식 직접 지정 가능** | 프롬프트 역생성 전용 모델이 아님 (범용 VLM) |
| Instruction following 가능 ("더 자세히", "인물 중심으로" 등) | bf16 기준 RTX 4090에서 **OOM 위험** (이미지 해상도 제한 필수) |
| 시스템 프롬프트 자유 커스텀 | 프롬프트 스타일 학습이 아니라 일반 묘사 품질에 의존 |
| 대화형 추가 질문 가능 ("배경을 더 자세히 설명해") | `transformers` 소스 빌드 필요 (공식 권장) |
| 다국어 지원 (한국어 입력도 가능) | Windows에서 `decord` 설치 이슈 가능 |
| 이미지 외 비디오 분석도 가능 | 출력 품질이 시스템 프롬프트 작성 능력에 의존 |

---

## 5. 방식 3: JoyCaption + Qwen2.5-VL 파이프라인

### 5.1 개요

```
[이미지] → JoyCaption (1차: 서술형 캡션) → Qwen2.5-VL (2차: Z-Image 형식 변환) → [최종 프롬프트]
```

| 단계 | 모델 | 역할 | VRAM |
|------|------|------|------|
| 1차 | JoyCaption Beta One | 이미지에서 풍부한 서술형 묘사 추출 | ~9GB (NF4) |
| 2차 | Qwen2.5-VL-7B | 1차 결과를 Z-Image 4-Layer 형식으로 재구성 | ~8-12GB (4bit) |

> **중요**: 두 모델을 **동시 로드할 수 없음** (~9GB + ~10GB = ~19GB+ 초과 위험).
> 순차 실행: 1차 완료 → 모델 해제 → 2차 로드.

### 5.2 설치

```bash
# 가상환경 (두 모델 공유)
python -m venv D:\_work\venv-pipeline
D:\_work\venv-pipeline\Scripts\activate

# 공통 의존성
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
pip install accelerate pillow bitsandbytes

# JoyCaption 의존성
pip install transformers==4.44.0 sentencepiece peft==0.12.0

# Qwen2.5-VL 의존성
# 주의: transformers 버전 충돌 가능성 있음
# JoyCaption은 4.44.0, Qwen은 최신 소스 빌드 권장
# 해결 방법: 별도 venv 또는 최신 transformers로 통일 후 테스트
pip install qwen-vl-utils[decord]==0.0.8
```

> **transformers 버전 충돌 주의:**
> - JoyCaption Alpha Two `requirements.txt`: `transformers==4.44.0`
> - Qwen2.5-VL 공식 권장: `pip install git+https://github.com/huggingface/transformers`
> - Beta One의 hf-llava 형식은 최신 transformers에서도 동작할 가능성 있으나 **미검증**.
> - 안전한 방법: 별도 가상환경 사용 또는 최신 transformers로 통일 후 JoyCaption 동작 확인.

### 5.3 파이프라인 코드

```python
import torch
import gc
from PIL import Image
from pathlib import Path


def load_joycaption():
    """JoyCaption Beta One 모델 로드 (NF4)"""
    from transformers import AutoProcessor, LlavaForConditionalGeneration, BitsAndBytesConfig

    model_name = "fancyfeast/llama-joycaption-beta-one-hf-llava"

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    processor = AutoProcessor.from_pretrained(model_name)
    model = LlavaForConditionalGeneration.from_pretrained(
        model_name, quantization_config=bnb_config, device_map=0
    )
    model.eval()
    return model, processor


def unload_model(model, processor):
    """모델을 VRAM에서 해제"""
    del model
    del processor
    gc.collect()
    torch.cuda.empty_cache()


def load_qwen():
    """Qwen2.5-VL-7B 모델 로드 (4bit)"""
    from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig

    model_name = "Qwen/Qwen2.5-VL-7B-Instruct"

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        model_name, quantization_config=bnb_config, device_map="auto"
    )
    processor = AutoProcessor.from_pretrained(
        model_name,
        min_pixels=256 * 28 * 28,
        max_pixels=1280 * 28 * 28,
    )
    return model, processor


def step1_joycaption(image_path: str, model, processor) -> str:
    """1단계: JoyCaption으로 서술형 캡션 생성"""
    image = Image.open(image_path).convert("RGB")

    convo = [
        {"role": "system", "content": "You are a helpful image captioner."},
        {"role": "user", "content": "Write a long descriptive caption for this image in a formal tone."},
    ]
    convo_string = processor.apply_chat_template(
        convo, tokenize=False, add_generation_prompt=True
    )
    inputs = processor(
        text=[convo_string], images=[image], return_tensors="pt"
    ).to("cuda")
    inputs["pixel_values"] = inputs["pixel_values"].to(torch.bfloat16)

    with torch.no_grad():
        output = model.generate(
            **inputs, max_new_tokens=512,
            do_sample=True, temperature=0.6, top_p=0.9,
        )[0]

    output = output[inputs["input_ids"].shape[1]:]
    return processor.tokenizer.decode(output, skip_special_tokens=True).strip()


def step2_qwen_reformat(raw_caption: str, model, processor) -> str:
    """2단계: Qwen2.5-VL로 Z-Image Turbo 4-Layer 형식 변환"""
    from qwen_vl_utils import process_vision_info

    system_prompt = """You are a prompt engineer for Z-Image Turbo, a text-to-image AI model.

Your task: Convert the provided image description into an optimized Z-Image Turbo prompt.

Output format (single flowing paragraph, 80-250 words):
[Subject & appearance details] + [Clothing & accessories] + [Background & setting] + [Visual style & camera] + [Lighting & atmosphere] + [Quality constraints]

Rules:
- Place the most important subject descriptors FIRST (the model pays most attention to the beginning)
- Include texture keywords: skin texture, fabric detail, film grain, surface imperfections
- Include quality keywords at end: 8K resolution, sharp focus, correct anatomy, no watermark
- Use ONLY positive descriptions (no "no ugly", instead say "beautiful")
- Write as natural English prose, NOT comma-separated tags
- Do NOT use contradictory styles (e.g., "photorealistic cartoon")

Output ONLY the final prompt. No explanations."""

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"Convert this image description into a Z-Image Turbo prompt:\n\n{raw_caption}",
        },
    ]

    text = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = processor(text=[text], return_tensors="pt").to("cuda")

    with torch.no_grad():
        generated_ids = model.generate(
            **inputs, max_new_tokens=512,
            do_sample=True, temperature=0.5, top_p=0.9,
        )

    generated_ids_trimmed = [
        out_ids[len(in_ids):]
        for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    return processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True
    )[0].strip()


def pipeline(image_path: str) -> dict:
    """전체 파이프라인 실행"""
    print("=" * 60)
    print(f"이미지: {image_path}")
    print("=" * 60)

    # Step 1: JoyCaption
    print("\n[Step 1] JoyCaption 로드 중...")
    joy_model, joy_proc = load_joycaption()

    print("[Step 1] 서술형 캡션 생성 중...")
    raw_caption = step1_joycaption(image_path, joy_model, joy_proc)
    print(f"\n--- 1차 캡션 (JoyCaption) ---\n{raw_caption}\n")

    # VRAM 해제
    print("[Step 1] 모델 해제 중...")
    unload_model(joy_model, joy_proc)

    # Step 2: Qwen2.5-VL
    print("[Step 2] Qwen2.5-VL 로드 중...")
    qwen_model, qwen_proc = load_qwen()

    print("[Step 2] Z-Image 형식 변환 중...")
    final_prompt = step2_qwen_reformat(raw_caption, qwen_model, qwen_proc)
    print(f"\n--- 최종 프롬프트 (Z-Image Turbo) ---\n{final_prompt}\n")

    # 정리
    unload_model(qwen_model, qwen_proc)

    return {
        "raw_caption": raw_caption,
        "final_prompt": final_prompt,
    }


# 사용 예시
if __name__ == "__main__":
    result = pipeline(r"D:\_work\test_image.jpg")

    # 파일 저장
    Path(r"D:\_work\prompts").mkdir(exist_ok=True)
    Path(r"D:\_work\prompts\test_image_raw.txt").write_text(
        result["raw_caption"], encoding="utf-8"
    )
    Path(r"D:\_work\prompts\test_image_final.txt").write_text(
        result["final_prompt"], encoding="utf-8"
    )
```

### 5.4 파이프라인 출력 예시

**Step 1 출력 (JoyCaption - 서술형 캡션):**

```
The image depicts a young woman, likely in her late twenties, seated at a rustic
wooden table inside a warmly lit cafe. She has dark brown wavy hair that falls just
past her shoulders, with a few loose strands framing her face. Her expression is
calm and contemplative, with soft brown eyes gazing slightly off-camera to the left.
She wears a cream-colored chunky knit sweater with visible cable-knit texture...
(이하 생략)
```

**Step 2 출력 (Qwen2.5-VL - Z-Image 형식 변환):**

```
A 28-year-old woman with dark brown wavy shoulder-length hair and light freckles
across her nose, calm contemplative expression with soft brown eyes gazing slightly
left, seated at a rustic wooden cafe table with both hands wrapped around a warm
ceramic coffee mug. She wears a cream chunky cable-knit sweater with visible fabric
texture and a delicate thin gold pendant necklace. The background features an
intimate cafe interior with exposed red brick walls, warm Edison pendant lighting,
and blurred wooden bookshelves adding depth. Photorealistic photography with shallow
depth of field, creamy circular bokeh, Fujifilm X-T4 aesthetic, subtle film grain,
natural skin texture with visible pores and fine details. Warm directional natural
light from a window on the right casting soft shadows, golden hour color temperature
creating a cozy intimate atmosphere with amber and warm brown tones throughout the
scene. 8K resolution, ultra-detailed, sharp focus on subject, correct anatomy,
proper hand structure, no watermark, no text overlay, clean composition.
```

### 5.5 장단점

| 장점 | 단점 |
|------|------|
| **최고 품질**: JoyCaption의 캡셔닝 정확도 + Qwen의 형식 변환 | **속도 느림**: 모델 로드/해제 2회 (각 1-3분) |
| JoyCaption이 놓치기 어려운 시각 디테일을 잡아냄 | **transformers 버전 충돌 가능** |
| Z-Image 4-Layer 형식 정확히 준수 가능 | 두 모델 동시 로드 불가 (순차 실행 필수) |
| 각 단계 결과를 별도 확인/수정 가능 | 설치 복잡도 높음 |
| 1차 결과만으로도 충분한 경우 2차 생략 가능 | 배치 처리 시 이미지당 처리 시간 길어짐 |

---

## 6. 방식별 비교

### 종합 비교표

| 기준 | 방식 1: JoyCaption | 방식 2: Qwen2.5-VL | 방식 3: 파이프라인 |
|------|:---:|:---:|:---:|
| **설치 난이도** | 낮음 | 중간 | 높음 |
| **VRAM 사용** | 9GB (NF4) / 17GB (bf16) | 8-12GB (4bit) / 17GB+ (bf16) | 최대 12GB (순차) |
| **처리 속도** | 빠름 (단일 모델) | 빠름 (단일 모델) | 느림 (2회 로드) |
| **캡셔닝 정확도** | 최고 (전용 모델) | 높음 (범용) | 최고 |
| **Z-Image 형식 준수** | 불가 (형식 지정 불가) | 가능 (시스템 프롬프트) | 최고 (조합) |
| **형식 커스텀** | 불가 | 자유 | 자유 |
| **Instruction Following** | 불가 | 가능 | 2단계에서 가능 |
| **배치 처리** | 용이 | 용이 | 복잡 |
| **의존성 충돌** | 없음 | 없음 | transformers 버전 |

### 상황별 추천

| 상황 | 추천 방식 | 이유 |
|------|-----------|------|
| **빠르게 시작, 프롬프트 품질 우선** | 방식 1 (JoyCaption) | 설치 간단, 출력 품질 높음 |
| **Z-Image 형식 정확히 맞춰야 함** | 방식 2 (Qwen2.5-VL) | 시스템 프롬프트로 형식 지정 |
| **최고 품질 + 형식 준수 둘 다** | 방식 3 (파이프라인) | 각 모델 강점 결합 |
| **대량 배치 처리** | 방식 1 (JoyCaption) | 단일 모델, 안정적 |
| **다양한 프롬프트 스타일 실험** | 방식 2 (Qwen2.5-VL) | 프롬프트 자유 변경 |
| **LoRA 학습용 캡션** | 방식 1 (JoyCaption) | 본래 목적이 Diffusion 학습 캡션 |

---

## 7. Z-Image Turbo 프롬프트 형식 참고

### 4-Layer 구조

```
[1. 주제 & 행동] + [2. 텍스트 요소(선택)] + [3. 시각 스타일] + [4. 조명 & 분위기]
```

### 확장 구조 (이미지 분석 시 권장)

```
[피사체 + 나이/외모] + [의류 및 상태] + [포즈/행동] + [배경/환경]
+ [카메라/매체 스타일] + [조명] + [분위기/무드] + [품질 제약]
```

### 핵심 규칙

1. **길이**: 80-250 단어 (300단어 초과 시 일관성 저하)
2. **키워드 배치**: 가장 중요한 요소를 앞에 (~75 토큰 이후 어텐션 감퇴)
3. **텍스처 필수**: `skin texture`, `fabric detail`, `film grain` 등
4. **Negative Prompt 불가**: `guidance_scale = 0.0` 고정, 긍정 표현만 사용
5. **단일 스타일**: `photorealistic cartoon` 같은 모순 금지

### 품질 키워드 (프롬프트 끝에 추가)

```
8K resolution, ultra-detailed, sharp focus, correct anatomy,
no watermark, no text overlay, skin texture, film grain
```

---

## 8. 참고 자료

### 모델 공식 페이지

- [JoyCaption GitHub](https://github.com/fpgaminer/joycaption)
- [JoyCaption Beta One (HuggingFace)](https://huggingface.co/fancyfeast/llama-joycaption-beta-one-hf-llava)
- [JoyCaption Beta One Release (Civitai)](https://civitai.com/articles/14672/joycaption-beta-one-release)
- [JoyCaption Alpha Two Space](https://huggingface.co/spaces/fancyfeast/joy-caption-alpha-two)
- [Qwen2.5-VL-7B-Instruct (HuggingFace)](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct)
- [Qwen2.5-VL VRAM Discussion](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct/discussions/18)
- [Florence-2-large (HuggingFace)](https://huggingface.co/microsoft/Florence-2-large)

### Z-Image Turbo 프롬프트 가이드

- [Z-Image Turbo 프롬프트 작성 가이드](./z-image-turbo-prompt-guide.md)
- [HuggingFace 공식 프롬프팅 가이드](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo/discussions/8)
- [fal.ai 가이드](https://fal.ai/learn/devs/z-image-turbo-prompt-guide)

### ComfyUI 통합

- [ComfyUI-JoyCaption](https://github.com/1038lab/ComfyUI-JoyCaption) - JoyCaption ComfyUI 노드
- [JoyCaption GGUF](https://huggingface.co/Mungert/llama-joycaption-beta-one-hf-llava-GGUF) - GGUF 양자화 버전


