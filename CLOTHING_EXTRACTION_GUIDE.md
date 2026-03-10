# 의상 추출 가이드

이미지 생성 프롬프트에서 의상 및 액세서리 항목을 자동 추출하는 도구입니다.
`extract_clothing.py` 하나로 **spaCy** 또는 **Ollama** 방식을 선택해 사용합니다.

---

## 목차

1. [방식 비교](#방식-비교)
2. [출력 형식](#출력-형식)
3. [spaCy 모드](#spacy-모드)
4. [Ollama 모드](#ollama-모드)
5. [공통 옵션](#공통-옵션)
6. [추출 원리 및 한계](#추출-원리-및-한계)

---

## 방식 비교

| 항목 | spaCy | Ollama (LLM) |
|------|-------|--------------|
| 속도 | ~1분 (7,000개 기준) | ~29시간 (단일) / ~10시간 (배치 30) |
| 정확도 | 높음 (단순 표현) / 중간 (복합 나열) | 매우 높음 |
| 설치 크기 | ~30MB | 모델별 상이 (예: qwen3.5:35b = 24GB) |
| 오프라인 | 가능 | 가능 (로컬 Ollama) |
| 선정적 프롬프트 | 처리 가능 | abliterated 모델 필요 |
| 권장 용도 | 대량 처리 (1,000개 이상) | 소량 정밀 추출 또는 검수 |

---

## 출력 형식

카테고리별로 각각의 txt 파일에 저장됩니다.

```
output/
  tops.txt
  bottoms.txt
  dresses.txt
  legwear.txt
  footwear.txt
  accessories.txt
```

각 파일 형식:

```
- light gray, sleeveless crop top
- black leather pants
- white knee-high socks
```

- 실행할 때마다 기존 파일에 **누적 저장**됩니다.
- 이미 저장된 항목은 **자동으로 중복 제거**됩니다 (대소문자 무시).

---

## spaCy 모드

### 설치

```bash
pip install spacy
python -m spacy download en_core_web_sm

# 시스템 Python 환경인 경우
pip install spacy --break-system-packages
python3 -m spacy download en_core_web_sm --break-system-packages
```

### 사용법

```bash
# 기본 실행 (prompts/ 폴더의 모든 txt 파일 처리, 결과는 output/ 에 저장)
python extract_clothing.py --mode spacy

# 특정 파일 지정
python extract_clothing.py --mode spacy --input prompts/my_prompts.txt

# 입력/출력 경로 모두 지정
python extract_clothing.py --mode spacy --input prompts/ --output results/
```

### 동작 원리

1. spaCy의 `en_core_web_sm` 모델로 각 프롬프트를 파싱
2. **명사구(noun chunk)** 단위로 분리
3. 명사구에서 관사(`a/an/the`), 소유격(`her/his`) 제거
4. `" and "`를 기준으로 양쪽을 각각 카테고리 분류 시도
5. 의상 키워드 사전과 대조해 카테고리 분류 후 저장

### " and " 분리 처리 규칙

| 케이스 | 예시 | 결과 |
|--------|------|------|
| 양쪽 모두 분류 가능 | `"silver choker necklace and white ankle socks"` | accessories + legwear 각각 저장 |
| before가 색상 단어만 | `"black and white dress"` | 전체 유지 → dresses |
| before가 노이즈 | `"chest and black thigh-high stockings"` | after만 → legwear |

### 예시

입력 프롬프트:
```
A beautiful Asian woman wearing a light gray, sleeveless crop top.
Her black leather pants contrast with her top. She wears white
knee-high socks, white high-heeled shoes, and a small gold necklace.
```

추출 결과:
```
tops.txt         -> - light gray, sleeveless crop top
bottoms.txt      -> - black leather pants
legwear.txt      -> - white knee-high socks
footwear.txt     -> - white high-heeled shoes
accessories.txt  -> - small gold necklace
```

### spaCy가 놓치는 케이스

| 패턴 | 예시 | 이유 |
|------|------|------|
| featuring/including 뒤 나열 | `"an outfit featuring a strappy top, shorts"` | outfit 전체가 하나의 청크로 묶임 |
| 쉼표 나열 | `"mini-skirt, white ankle socks"` | 두 항목이 하나의 청크로 추출 |
| 모호한 단어 | `"outfit"`, `"attire"` | 키워드 미매핑 시 누락 |

---

## Ollama 모드

### 사전 조건

- Windows에 [Ollama](https://ollama.com) 설치 및 실행 중
- WSL에서 `host.docker.internal:11434` 로 접근 가능
- `pip install requests`

### 모델 선택

| 모델 | 특징 | 선정적 프롬프트 |
|------|------|----------------|
| `qwen3.5:35b` | 일반 모델 | 일부 거부 가능 |
| `huihui_ai/qwen3.5-abliterated:35b` | 무검열 모델 | 모두 처리 가능 (권장) |

### 사용법

```bash
# 기본 실행 (abliterated 모델, 배치 5개)
python extract_clothing.py --mode ollama

# 모델 및 배치 크기 지정
python extract_clothing.py --mode ollama \
  --model huihui_ai/qwen3.5-abliterated:35b \
  --batch 5

# 일반 qwen3.5 사용
python extract_clothing.py --mode ollama --model qwen3.5:35b

# Ollama가 localhost에서 실행 중인 경우
python extract_clothing.py --mode ollama --ollama-url http://localhost:11434

# 입력/출력 경로 지정
python extract_clothing.py --mode ollama --input prompts/ --output results/
```

### 배치 크기 가이드

| --batch | 프롬프트당 소요 (추정) | 파싱 안정성 |
|---------|----------------------|-------------|
| 1 | ~13초 | 매우 안정 |
| 5 | ~5초 | 안정 (권장) |
| 10 | ~3초 | 보통 |
| 30+ | 빠르지만 | JSON 파싱 오류 위험 |

> 배치 크기가 클수록 모델이 JSON 배열 형식을 지키지 못할 확률이 높아집니다.
> 오류 발생 시 해당 배치는 건너뛰고 계속 진행됩니다.

### 동작 원리

1. 지정된 배치 크기만큼 프롬프트를 묶어 Ollama API에 전송
2. `/no_think` 지시어로 thinking 모드를 비활성화해 속도 향상 (~85초 → ~13초)
3. 모델이 JSON 배열 형식으로 카테고리별 항목 반환
4. JSON 파싱 후 중복 제거 및 누적 저장

### Ollama 추출 예시

입력 (배치 2개):
```
1. A woman wearing a white crop top, black leather pants, red high heels, and a gold necklace.
2. A woman in a floral summer dress, white knee-high socks, and a beaded parasol.
```

모델 응답:
```json
[
  {
    "tops": ["white crop top"],
    "bottoms": ["black leather pants"],
    "dresses": [],
    "legwear": [],
    "footwear": ["red high heels"],
    "accessories": ["gold necklace"]
  },
  {
    "tops": [],
    "bottoms": [],
    "dresses": ["floral summer dress"],
    "legwear": ["white knee-high socks"],
    "footwear": [],
    "accessories": ["beaded parasol"]
  }
]
```

---

## 공통 옵션

```
--mode        spacy 또는 ollama (기본값: spacy)
--input       입력 파일 또는 폴더 (기본값: prompts/)
--output      출력 폴더 (기본값: output/)

Ollama 전용:
--model       Ollama 모델명 (기본값: huihui_ai/qwen3.5-abliterated:35b)
--batch       배치당 프롬프트 수 (기본값: 5)
--ollama-url  Ollama API 주소 (기본값: http://host.docker.internal:11434)
```

### 도움말 확인

```bash
python extract_clothing.py --help
```

---

## 추출 원리 및 한계

### 카테고리 우선순위

동일 청크에 여러 키워드가 겹칠 경우 아래 순서로 우선 분류합니다:

```
dresses > bottoms > tops > legwear > footwear > accessories
```

예: `"corset-style dress"` → dress 키워드 → **dresses** 분류

### 의상 키워드 목록

| 카테고리 | 키워드 예시 |
|----------|------------|
| tops | shirt, blouse, jacket, sweater, corset, bodysuit, crop top, bra, bikini, camisole ... |
| bottoms | pants, skirt, shorts, jeans, leggings, overalls, trousers ... |
| dresses | dress, gown, costume, jumpsuit, romper ... |
| legwear | socks, stockings, tights, pantyhose ... |
| footwear | shoes, boots, heels, sneakers, sandals, pumps, loafers ... |
| accessories | necklace, bracelet, earring, ring, choker, bag, hat, headband, glove, scarf, crown, parasol ... |

### 키워드 추가 방법

`extract_clothing.py` 상단의 `CLOTHING_KEYWORDS` 딕셔너리에 직접 추가합니다:

```python
CLOTHING_KEYWORDS = {
    "tops": {
        "top", "shirt", ...,
        "tube top",       # 추가 예시
        "off-shoulder",
    },
    "accessories": {
        "necklace", ...,
        "sunglasses",     # 추가 예시
        "brooch",
    },
    ...
}
```
