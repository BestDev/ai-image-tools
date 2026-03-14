# Z-Image Tools

AI 이미지 학습 데이터셋 준비를 위한 통합 도구 모음.
**Z-Image Turbo** 등 텍스트→이미지 모델을 위한 고품질 프롬프트 자동 생성 및 이미지 전처리를 지원합니다.

---

## 도구 목록

| 도구 | 설명 | 문서 |
|------|------|------|
| **prompt_generator_v2** | 이미지→프롬프트 자동 생성 (11가지 방식, 로컬 LLM + Gemini API) | [docs/prompt_generator_v2_guide.md](docs/prompt_generator_v2_guide.md) |
| **gemini_batch** | Gemini CLI 헤드리스 배치 분석 (API 키 없이 구독 사용) | [docs/gemini_batch_guide.md](docs/gemini_batch_guide.md) |
| **to_wildcard** | prompts.txt → ComfyUI 와일드카드 형식 변환 | [docs/to_wildcard_guide.md](docs/to_wildcard_guide.md) |
| **image_classifier** | 이미지 자동 분류 (화풍 / 배경 / 인물 수) | [docs/image_classifier_guide.md](docs/image_classifier_guide.md) |
| **heic_to_jpeg** | iPhone HEIC 이미지 일괄 JPEG 변환 | [docs/heic_to_jpeg_guide.md](docs/heic_to_jpeg_guide.md) |
| **extract_clothing** | 프롬프트에서 의상 항목 자동 추출 | — |
| **web_ui** | 위 도구 전체를 웹 브라우저에서 제어 | 아래 참고 |

---

## 빠른 시작

### 1. 가상환경 설치

프롬프트 생성용 (`venv-prompt`) — Flask, LLM 추론:

```bash
cd /path/to/image-classifier
python3 -m venv venv-prompt
source venv-prompt/bin/activate
pip install -r requirements-prompt.txt
```

이미지 분류용 (`venv-classifier`) — CLIP, YOLO:

```bash
python3 -m venv venv-classifier
source venv-classifier/bin/activate
pip install -r requirements-classifier.txt
```

> 두 가상환경 모두 저장소 루트에 생성해야 자동 전환이 동작합니다.

### 2. Web UI 실행 (권장)

```bash
python3 web_ui.py
# → http://localhost:7860 에서 접속
```

브라우저에서 모든 도구를 GUI로 조작할 수 있습니다.

**Web UI 주요 기능:**
- 6개 탭: 프롬프트 생성 / HEIC 변환 / 이미지 분류 / 의상 추출 / 배치 큐 / 실행 이력
- 실시간 터미널 출력, GPU/VRAM/RAM 모니터링
- 이미지 썸네일 미리보기 (처리 완료 표시)
- 모델 다운로드 진행률 표시
- 배치 큐: 여러 작업을 등록하여 GPU 순차 자동 처리 / 큐 작업 시작 시 자동 스트림 연결
- 폴더 입력창 옆 📁 탐색기 버튼 (서버 사이드 디렉토리 브라우저, WSL 호환)
- 실행 중인 작업의 모델·방식·옵션 실시간 표시
- WSL→Windows 접속 가이드 내장 (헤더 ℹ WSL 버튼)

### 3. 커맨드라인 직접 사용

```bash
# 프롬프트 생성 (방식 2 - Qwen3-VL, 영어)
python3 scripts/prompt_generator_v2.py image/dataset --output-dir output/out --method 2 --lang en

# 프롬프트 생성 (Gemini CLI 배치, GPU 불필요)
python3 scripts/gemini_batch.py image/dataset -o output/out --model flash

# prompts_raw.txt → ComfyUI 와일드카드 변환
python3 scripts/to_wildcard.py output/out/prompts_raw.txt

# HEIC → JPEG 변환
python3 scripts/heic_to_jpeg.py image/iphone_photos --quality 95

# 이미지 화풍 분류
python3 scripts/image_classifier.py image/dataset --by style --copy

# 의상 항목 추출
python3 scripts/extract_clothing.py --input output/out/prompts.txt
```

---

## 디렉토리 구조

```
image-classifier/
├── web_ui.py              # Web UI 서버 (Flask)
├── requirements-prompt.txt     # venv-prompt 패키지 목록
├── requirements-classifier.txt # venv-classifier 패키지 목록
├── venv-prompt/           # Python 가상환경 (git 제외)
├── venv-classifier/       # 분류용 가상환경 (git 제외)
├── scripts/               # CLI 스크립트
│   ├── prompt_generator_v2.py   # 프롬프트 생성 (11가지 방식)
│   ├── gemini_batch.py          # Gemini CLI 헤드리스 배치
│   ├── shared_prompts.py        # 공유 프롬프트 정의 (두 스크립트가 공통 사용)
│   ├── to_wildcard.py           # ComfyUI 와일드카드 변환
│   ├── image_classifier.py      # 이미지 분류
│   ├── heic_to_jpeg.py          # HEIC 변환
│   ├── extract_clothing.py      # 의상 추출
│   ├── prompt_generator.py      # v1 (레거시)
│   ├── test_qwen3vl.py          # Qwen3-VL 단독 테스트
│   └── test_qwen35.py           # Qwen3.5 단독 테스트
├── docs/                  # 사용 가이드 문서
│   ├── prompt_generator_v2_guide.md
│   ├── gemini_batch_guide.md
│   ├── to_wildcard_guide.md
│   ├── image_classifier_guide.md
│   ├── heic_to_jpeg_guide.md
│   └── z-image-turbo-prompt-guide.md
├── html/                  # Web UI 프론트엔드
│   └── web_ui.html
├── image/                 # 이미지 데이터 (git 제외)
│   └── dataset/           # 기본 입력 폴더
└── output/                  # 생성 결과 (git 제외)
    └── YYYY-MM-DD-HHMMSS-m{N}/
        └── prompts.txt
```

---

## 프롬프트 생성 방식 비교

### 로컬 모델 (GPU 필요)

| 방식 | 모델 | 언어 | VRAM | 특징 |
|------|------|------|------|------|
| 1 | JoyCaption Beta One | EN | ~10GB | 영어 전용, 안정적 |
| 2 | Qwen3-VL-8B | EN/ZH | ~16GB | 빠르고 정확 |
| 3 | Qwen3.5-9B | EN/ZH | ~18GB | 상세한 묘사 |
| 4 | JoyCaption → Qwen3-VL | EN/ZH | ~16GB | 2-pass 정제 |
| 5 | JoyCaption → Qwen3.5 | EN/ZH | ~18GB | 2-pass 정제 |
| 6 | Huihui-Qwen3-VL (검열 해제) | EN/ZH | ~16GB | 성인 이미지 포함 가능 |
| 7 | Huihui-Qwen3.5 (검열 해제) | EN/ZH | ~18GB | 성인 이미지 포함 가능 |
| 8 | JoyCaption → Huihui-Qwen3-VL | EN/ZH | ~16GB | 2-pass 정제 (검열 해제) |
| 9 | JoyCaption → Huihui-Qwen3.5 | EN/ZH | ~18GB | 2-pass 정제 (검열 해제) |

### 클라우드 API (GPU 불필요)

| 방식 / 도구 | 모델 | 언어 | 인증 | 특징 |
|------------|------|------|------|------|
| 10 (prompt_generator_v2) | Gemini 3 Flash | EN/ZH | 유료 API 키 | RPD 10K, 고품질 |
| 11 (prompt_generator_v2) | Gemini 3.1 Flash-Lite | EN/ZH | 유료 API 키 | RPD 150K, 대용량 |
| gemini_batch.py | Gemini CLI (flash/pro) | EN/ZH | Google 계정 구독 | API 키 불필요 |

자세한 내용: [docs/prompt_generator_v2_guide.md](docs/prompt_generator_v2_guide.md)

---

## 대상 모델

생성된 프롬프트는 [Z-Image Turbo](docs/z-image-turbo-prompt-guide.md) 에 최적화되어 있으며,
Stable Diffusion, FLUX 등 일반 텍스트→이미지 모델에도 사용 가능합니다.
