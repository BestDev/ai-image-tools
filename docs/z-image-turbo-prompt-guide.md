# Z-Image Turbo 프롬프트 작성 가이드

> 최종 업데이트: 2026-03-04
> 참고 자료: [HuggingFace 공식](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo/discussions/8) · [fal.ai 가이드](https://fal.ai/learn/devs/z-image-turbo-prompt-guide) · [HackMD 엔지니어링 가이드](https://hackmd.io/_9H5DEekRS-haFKZ3nTqyA) · [GitHub Gist](https://gist.github.com/illuminatianon/c42f8e57f1e3ebf037dd58043da9de32) · [ComfyUI Docs](https://docs.comfy.org/tutorials/image/z-image/z-image-turbo)

---

## 1. 모델 개요

| 항목 | 내용 |
|------|------|
| 개발사 | Alibaba Tongyi-MAI Lab |
| 파라미터 | 6B |
| 아키텍처 | Scalable Single-Stream DiT (S3-DiT) |
| 추론 속도 | Sub-second (약 8 diffusion steps) |
| 언어 지원 | 영어 + 중국어 이중언어 |
| 특징 | 텍스트 렌더링 강점, 강한 instruction-following |

Z-Image Turbo는 텍스트 토큰과 이미지 토큰을 하나의 시퀀스에서 함께 처리하는 단일 스트림 확산 트랜스포머입니다. Few-step 증류(distillation) 모델로, 약 8단계만에 고품질 이미지를 생성합니다.

---

## 2. 핵심 차이점: Negative Prompt 미지원

**Z-Image Turbo는 Classifier-Free Guidance(CFG)를 사용하지 않으므로 Negative Prompt가 작동하지 않습니다.**

- `guidance_scale = 0.0` 고정 사용
- 제외하고 싶은 요소를 Negative Prompt가 아닌 **Positive Prompt에 직접 명시**해야 함

| 기존 방식 (작동 안 함) | Z-Image Turbo 방식 |
|---|---|
| Negative: `blurry, ugly hands` | Positive에 `sharp focus, correct anatomy` 추가 |
| Negative: `watermark, text` | Positive에 `no watermark, no text overlay` 추가 |
| Negative: `low quality` | Positive에 `8K resolution, high detail, masterpiece` 추가 |

---

## 3. 프롬프트 구조

### 권장 4-Layer 구조

```
[주제 & 행동] + [텍스트 요소] + [시각 스타일] + [조명 & 분위기]
```

| 레이어 | 설명 | 예시 |
|--------|------|------|
| **1. 주제 & 행동** | 누가, 무엇을 하는지 구체적으로 | `An elderly gardener with wrinkled hands pruning red roses` |
| **2. 텍스트 렌더링** | 이미지에 표시할 텍스트를 따옴표로 명시 | `a sign clearly reading "GARDEN OF LIFE"` |
| **3. 시각 스타일** | 사진/회화/3D 렌더 등 매체 정의 | `photorealistic, film grain, Kodak Portra 400` |
| **4. 조명 & 분위기** | 조명 방향, 색온도, 분위기 | `dappled sunlight filtering through oak trees, golden hour` |

### 확장 6-Part 공식

```
주제(Subject) → 장면(Scene) → 구도(Composition) → 조명(Lighting) → 스타일(Style) → 제약(Constraints)
```

**전체 구조 예시:**
```
[피사체 + 나이/외모] + [의류 및 상태] + [배경] + [조명] + [분위기] + [스타일/매체] + [기술 사항] + [안전 제약]
```

---

## 4. 프롬프트 작성 핵심 규칙

### 4.1 구체성
- **나쁜 예:** `a beautiful woman in a garden`
- **좋은 예:** `a 30-year-old woman with auburn curly hair, wearing a floral sundress, watering lavender in a sunlit cottage garden`

### 4.2 프롬프트 길이
- **최적 범위:** 80~250 단어 (또는 ~75 토큰)
- **주의:** 300단어 초과 시 일관성 저하
- **어텐션 감퇴:** 약 75 토큰(50~60단어) 이후부터 주의 집중도 감소
- **전략:** 가장 중요한 키워드(피사체 + 텍스트)를 **앞부분**에 배치

### 4.3 LLM 활용 권장 워크플로우
1. 핵심 아이디어를 간단히 직접 작성
2. ChatGPT/Claude 등 LLM에 입력하여 상세 묘사로 확장
3. 확장된 프롬프트로 생성 테스트

### 4.4 텍스처 명시
이미지가 플라스틱처럼 보이는 경우 텍스처 키워드 누락이 원인:
```
skin texture, fabric detail, surface imperfections, film grain, pores, weathered wood
```

### 4.5 시드 고정 전략
- 프롬프트 반복 수정 시 **seed를 고정**하여 프롬프트 차이만 확인
- 다양성 탐색 시 seed를 랜덤화

---

## 5. 파라미터 설정

| 파라미터 | 권장값 | 설명 |
|---------|--------|------|
| `num_inference_steps` | **8~9** | 기본값, 속도/품질 최적 균형 (4=빠름, 12+=최고품질) |
| `guidance_scale` | **0.0** | Turbo 모델 필수 설정값 |
| `height / width` | **1024×1024** | 기본 해상도 |
| `max_sequence_length` | **512** (온라인) / **1024** (로컬) | 토큰 최대 길이 |
| `acceleration` | `none` / `regular` / `high` | `high` = 1초 이내 생성 |
| `num_images` | 1~4 | 배치 생성 수 |

### 해상도별 종횡비 가이드
| 용도 | 권장 비율 |
|------|-----------|
| 풍경/배경 | 4:3 (landscape) |
| 프로필/아바타 | 1:1 (square) |
| 인물/초상화 | 9:16 (portrait) |
| 영화/시네마 | 16:9 (wide) |

### Python 코드 예시 (로컬 실행)
```python
image = pipe(
    prompt=prompt,
    height=1024,
    width=1024,
    num_inference_steps=9,
    guidance_scale=0.0,
    generator=torch.Generator("cuda").manual_seed(42),
    max_sequence_length=1024  # 기본값 512, 로컬에서 1024로 확장 가능
).images[0]
```

---

## 6. LoRA 사용

- 최대 **3개 LoRA 동시 적용** 가능
- 권장 스케일: **0.7~0.9**
  - 1.0으로 설정 시 색상 과포화, 아티팩트 발생 가능
  - 자연스러운 결과를 위해 약간 낮게 설정

---

## 7. 제약 키워드 레퍼런스

### 품질 향상
```
8K resolution, ultra-detailed, masterpiece, sharp focus, crisp details,
professional photography, RAW photo, high fidelity
```

### 아티팩트 방지
```
correct anatomy, no extra limbs, proper hand structure, no distortion,
clean composition, artifact-free
```

### 텍스트/워터마크 제거
```
no watermark, no text overlay, no logo, no signature, no border
```

### 인체 표현
```
realistic body proportions, natural skin texture, skin pores,
natural hair, realistic eyes
```

---

## 8. 피해야 할 실수

| 실수 | 문제 | 해결책 |
|------|------|--------|
| 모순된 지시 | `photorealistic cartoon style` | 하나의 스타일만 선택 |
| 모호한 표현 | `beautiful`, `nice`, `good` | 구체적 묘사로 대체 |
| 과도한 길이 | 300단어 초과 | 3~5개 핵심 개념으로 압축 |
| 텍스처 누락 | 플라스틱 느낌 이미지 | 텍스처 키워드 명시 |
| Negative Prompt 사용 | 효과 없음 | 긍정적 표현으로 전환 |
| 중요 키워드 후반 배치 | 어텐션 감퇴로 무시됨 | 앞부분에 배치 |

---

## 9. 예시 프롬프트

### 인물 사진
```
A 28-year-old woman with dark brown wavy hair, light freckles on her nose,
wearing a cream knit sweater, sitting at a wooden cafe table. Warm indoor
lighting, shallow depth of field, bokeh background, Fujifilm X-T4 aesthetic,
film grain, skin texture visible, no watermark, sharp focus.
```

### 풍경
```
Misty mountain valley at dawn, ancient pine forest, a narrow stone bridge
over a crystal-clear stream. Soft golden light breaking through fog,
volumetric rays, 8K landscape photography, ultra-detailed foliage,
realistic water reflections, no people, serene atmosphere.
```

### 텍스트 렌더링 (Z-Image 강점)
```
A rustic wooden shop sign hanging above an entrance, clearly reading
"THE OLD BOOKSHOP", hand-painted letters in faded gold on dark green wood.
Victorian street setting, warm evening light, photorealistic texture,
weathered wood grain, no blur, sharp focus on text.
```

### 상업용 제품 사진
```
Professional product photography of a minimalist ceramic coffee mug,
matte white finish with subtle texture, placed on a light grey marble surface.
Studio lighting with soft shadows, top-down angle, clean background,
ultra-sharp focus, no reflections, commercial photography style.
```

---

## 10. 필수 모델 파일 (ComfyUI 기준)

| 파일 | 경로 | 용도 |
|------|------|------|
| `qwen_3_4b.safetensors` | `models/text_encoders/` | 텍스트 인코더 |
| `z_image_turbo_bf16.safetensors` | `models/diffusion_models/` | 확산 모델 |
| `ae.safetensors` | `models/vae/` | VAE |

---

## 참고 자료

- [HuggingFace 공식 모델 페이지 - Tongyi-MAI/Z-Image-Turbo](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo)
- [HuggingFace 공식 프롬프팅 가이드 (Discussion #8)](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo/discussions/8)
- [fal.ai - Z-Image Turbo Prompt Guide](https://fal.ai/learn/devs/z-image-turbo-prompt-guide)
- [HackMD - Z-Image Prompt Engineering Guide](https://hackmd.io/_9H5DEekRS-haFKZ3nTqyA)
- [GitHub Gist - Z-Image-Turbo Prompting Guide](https://gist.github.com/illuminatianon/c42f8e57f1e3ebf037dd58043da9de32)
- [ComfyUI 공식 튜토리얼](https://docs.comfy.org/tutorials/image/z-image/z-image-turbo)
- [Replicate API](https://replicate.com/prunaai/z-image-turbo)
