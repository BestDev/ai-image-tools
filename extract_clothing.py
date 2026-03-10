#!/usr/bin/env python3
"""
extract_clothing.py

이미지 생성 프롬프트에서 의상 항목을 추출합니다.
spaCy(빠름/경량) 또는 Ollama(정확/LLM) 중 선택 가능합니다.

설치:
    # spaCy 모드
    pip install spacy
    python -m spacy download en_core_web_sm

    # Ollama 모드
    pip install requests
    (Windows에 Ollama 실행 중이어야 함)

사용:
    python extract_clothing.py --mode spacy
    python extract_clothing.py --mode ollama
    python extract_clothing.py --mode ollama --model huihui_ai/qwen3.5-abliterated:35b --batch 5
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

# ── 공통: 의상 키워드 사전 ─────────────────────────────────────────────────────
# 우선순위: dresses > bottoms > tops > legwear > footwear > accessories
CLOTHING_KEYWORDS: dict[str, set[str]] = {
    "dresses": {
        "dress", "dresses", "gown", "gowns", "costume", "costumes",
        "jumpsuit", "jumpsuits", "romper", "rompers", "sundress",
    },
    "bottoms": {
        "pants", "skirt", "skirts", "shorts", "trousers",
        "jeans", "leggings", "overalls", "culottes",
    },
    "tops": {
        "top", "tops", "shirt", "shirts", "blouse", "blouses",
        "camisole", "camisoles", "jacket", "jackets", "coat", "coats",
        "corset", "corsets", "bodysuit", "bodysuits",
        "hoodie", "hoodies", "sweater", "sweaters",
        "sweatshirt", "sweatshirts", "cardigan", "cardigans",
        "pullover", "pullovers", "vest", "vests",
        "tunic", "tunics", "blazer", "blazers",
        "bra", "bras", "bikini", "crop", "halter", "tee",
    },
    "legwear": {
        "sock", "socks", "stocking", "stockings",
        "tights", "pantyhose", "hosiery",
    },
    "footwear": {
        "shoe", "shoes", "boot", "boots", "heel", "heels",
        "sneaker", "sneakers", "sandal", "sandals",
        "pump", "pumps", "loafer", "loafers",
        "stiletto", "stilettos", "mule", "mules",
        "wedge", "wedges", "flat", "flats", "platform",
    },
    "accessories": {
        "necklace", "necklaces", "bracelet", "bracelets",
        "earring", "earrings", "ring", "rings",
        "choker", "chokers", "pendant", "pendants",
        "brooch", "brooches", "anklet", "anklets",
        "watch", "watches", "bag", "bags",
        "handbag", "handbags", "purse", "purses",
        "backpack", "backpacks", "hat", "hats",
        "cap", "caps", "headband", "headbands",
        "crown", "crowns", "tiara", "tiaras",
        "glove", "gloves", "scarf", "scarves",
        "parasol", "umbrella", "ribbon", "ribbons",
        "bow", "bows", "hairpin", "hairpins", "hairclip", "hairclips",
    },
}

CATEGORIES = list(CLOTHING_KEYWORDS.keys())
ARTICLE_RE = re.compile(r"^(a|an|the)\s+", re.IGNORECASE)
POSSESSIVE_RE = re.compile(r"^(her|his)\s+", re.IGNORECASE)

# " and " 분리 시 색상 단어만으로 된 before는 노이즈로 보지 않음 (예: "black and white dress" 보존)
COLOR_WORDS = {
    "black", "white", "red", "blue", "green", "yellow", "pink", "purple",
    "gray", "grey", "brown", "orange", "beige", "cream", "gold", "silver",
    "navy", "turquoise", "lavender", "violet", "magenta", "cyan", "maroon",
    "olive", "coral", "peach", "mint", "teal", "indigo", "crimson",
}


# ── 공통 유틸 ──────────────────────────────────────────────────────────────────

def collect_input_files(input_path: Path) -> list[Path]:
    """파일 또는 디렉토리를 받아 처리할 txt 파일 목록을 반환."""
    if input_path.is_file():
        return [input_path]
    if input_path.is_dir():
        files = sorted(input_path.glob("*.txt"))
        if not files:
            print(f"오류: '{input_path}' 디렉토리에 txt 파일이 없습니다.")
            sys.exit(1)
        return files
    print(f"오류: 입력 경로를 찾을 수 없습니다: {input_path}")
    sys.exit(1)


def load_existing(filepath: Path) -> set[str]:
    """기존 출력 파일에서 항목을 읽어 소문자 set으로 반환 (세션 간 중복 방지)."""
    if not filepath.exists():
        return set()
    result = set()
    for line in filepath.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            result.add(stripped[2:].strip().lower())
    return result


def read_prompts(files: list[Path]) -> list[str]:
    """파일 목록에서 비어 있지 않은 줄을 모두 읽어 반환."""
    prompts = []
    for f in files:
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                prompts.append(line)
    return prompts


def save_items(new_items: dict[str, list[str]], output_files: dict[str, Path]) -> None:
    """추출 결과를 각 카테고리 파일에 누적 저장."""
    print()
    for cat, items in new_items.items():
        fp = output_files[cat]
        if items:
            with open(fp, "a", encoding="utf-8") as f:
                for item in items:
                    f.write(f"- {item}\n")
        print(f"  [{cat:10s}] 신규 {len(items):4d}개 -> {fp.name}")
    print("\n완료!")


# ── spaCy 모드 ─────────────────────────────────────────────────────────────────

def spacy_categorize(chunk_text: str) -> str | None:
    """명사구를 의상 카테고리로 분류. 매칭 없으면 None."""
    words = set(re.sub(r"[-–]", " ", chunk_text.lower()).split())
    for category, keywords in CLOTHING_KEYWORDS.items():
        if words & keywords:
            return category
    return None


def spacy_clean(text: str) -> str:
    """명사구 앞의 관사(a/an/the) 및 소유격(her/his) 제거."""
    text = ARTICLE_RE.sub("", text).strip()
    text = POSSESSIVE_RE.sub("", text).strip()
    return text


def split_and_categorize(chunk_text: str) -> list[tuple[str, str]]:
    """명사구를 처리해 (카테고리, 항목) 쌍의 리스트 반환.

    ' and '를 기준으로 양쪽을 각각 분류 시도:
      - 양쪽 모두 분류 가능 → 각각 별도 항목으로 반환
        예: "silver choker necklace and white ankle socks"
            → [("accessories", "silver choker necklace"), ("legwear", "white ankle socks")]
      - after만 분류 가능 + before가 색상 단어만으로 구성 → 전체 유지
        예: "black and white dress" → [("dresses", "black and white dress")]
      - after만 분류 가능 + before가 노이즈 → after만 반환
        예: "chest and black thigh-high stockings" → [("legwear", "black thigh-high stockings")]
    """
    cleaned = spacy_clean(chunk_text)
    if not cleaned:
        return []

    if " and " in cleaned:
        before, after = cleaned.split(" and ", 1)
        before, after = before.strip(), after.strip()
        cat_before = spacy_categorize(before)
        cat_after = spacy_categorize(after)

        if cat_before and cat_after:
            # 양쪽 모두 분류 가능 → 각각 반환
            return [(cat_before, before), (cat_after, after)]
        elif cat_before and not cat_after:
            return [(cat_before, before)]
        elif cat_after and not cat_before:
            before_words = set(re.sub(r"[-–]", " ", before.lower()).split())
            # before가 색상 단어만으로 구성되면 전체 텍스트 유지
            if before_words <= COLOR_WORDS:
                cat_full = spacy_categorize(cleaned)
                if cat_full:
                    return [(cat_full, cleaned)]
            return [(cat_after, after)]

    category = spacy_categorize(cleaned)
    if category:
        return [(category, cleaned)]
    return []


def run_spacy(input_files: list[Path], output_dir: Path) -> None:
    try:
        import spacy
    except ImportError:
        print("오류: spaCy가 설치되지 않았습니다.")
        print("  pip install spacy")
        sys.exit(1)

    print("spaCy 모델 로딩 중 (en_core_web_sm)...")
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        print("오류: en_core_web_sm 모델이 없습니다.")
        print("  python -m spacy download en_core_web_sm")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_files = {cat: output_dir / f"{cat}.txt" for cat in CATEGORIES}
    existing = {cat: load_existing(fp) for cat, fp in output_files.items()}
    new_items: dict[str, list[str]] = {cat: [] for cat in CATEGORIES}
    new_items_set: dict[str, set[str]] = {cat: set() for cat in CATEGORIES}

    prompts = read_prompts(input_files)
    total = len(prompts)
    print(f"입력 파일: {len(input_files)}개 | 총 {total}개 프롬프트 처리 중...\n")

    for i, prompt in enumerate(prompts, 1):
        doc = nlp(prompt)
        for chunk in doc.noun_chunks:
            for category, item in split_and_categorize(chunk.text):
                item_lower = item.lower()
                if (
                    item_lower not in existing[category]
                    and item_lower not in new_items_set[category]
                ):
                    new_items[category].append(item)
                    new_items_set[category].add(item_lower)

        if i % 1000 == 0 or i == total:
            print(f"  [{i:5d}/{total}] 처리 완료")

    save_items(new_items, output_files)


# ── Ollama 모드 ────────────────────────────────────────────────────────────────

OLLAMA_SYSTEM = """/no_think
You are a clothing and accessory extractor. Extract ONLY wearable items from the given prompts.
Categorize each item into: tops, bottoms, dresses, legwear, footwear, accessories.
Output ONLY a valid JSON array. Each element corresponds to one prompt (in order).

Category definitions:
- tops: shirts, blouses, jackets, sweaters, corsets, bodysuits, crop tops, bras, bikini tops, etc.
- bottoms: pants, skirts, shorts, jeans, leggings, overalls, etc.
- dresses: dresses, gowns, costumes, jumpsuits, rompers, etc.
- legwear: socks, stockings, tights, pantyhose, etc.
- footwear: shoes, boots, heels, sneakers, sandals, etc.
- accessories: necklaces, bracelets, earrings, rings, bags, hats, headbands, gloves, scarves, crowns, tiaras, parasols, etc.

Output format (JSON array, one object per prompt):
[
  {"tops": ["item1"], "bottoms": ["item2"], "dresses": [], "legwear": [], "footwear": ["item3"], "accessories": ["item4"]},
  ...
]"""


def ollama_build_prompt(batch: list[tuple[int, str]]) -> str:
    lines = "\n".join(f"{num}. {text}" for num, text in batch)
    return f"{OLLAMA_SYSTEM}\n\nPrompts:\n{lines}\n\nJSON array:"


def ollama_call(prompt: str, model: str, base_url: str, timeout: int = 180) -> str:
    try:
        import requests
    except ImportError:
        print("오류: requests가 설치되지 않았습니다.")
        print("  pip install requests")
        sys.exit(1)

    resp = requests.post(
        f"{base_url}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0},
        },
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()["response"]


def ollama_parse(text: str, batch_size: int) -> list[dict]:
    """응답 텍스트에서 JSON 배열 추출. 파싱 실패 시 빈 결과 반환."""
    empty = [
        {"tops": [], "bottoms": [], "dresses": [], "legwear": [], "footwear": [], "accessories": []}
        for _ in range(batch_size)
    ]
    match = re.search(r"\[.*?\]", text, re.DOTALL)
    if not match:
        return empty
    try:
        parsed = json.loads(match.group())
        if isinstance(parsed, list) and len(parsed) == batch_size:
            return parsed
        return empty
    except json.JSONDecodeError:
        return empty


def run_ollama(
    input_files: list[Path],
    output_dir: Path,
    model: str,
    batch_size: int,
    base_url: str,
) -> None:
    print(f"Ollama 모드: {model} | 배치 크기: {batch_size} | URL: {base_url}")

    try:
        import requests
        r = requests.get(f"{base_url}/api/tags", timeout=5)
        r.raise_for_status()
        available = [m["name"] for m in r.json().get("models", [])]
        if model not in available:
            print(f"경고: '{model}' 모델이 목록에 없습니다.")
            print(f"사용 가능한 모델: {', '.join(available)}")
    except Exception as e:
        print(f"오류: Ollama 서버에 연결할 수 없습니다 ({base_url})")
        print(f"  {e}")
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_files = {cat: output_dir / f"{cat}.txt" for cat in CATEGORIES}
    existing = {cat: load_existing(fp) for cat, fp in output_files.items()}
    new_items: dict[str, list[str]] = {cat: [] for cat in CATEGORIES}
    new_items_set: dict[str, set[str]] = {cat: set() for cat in CATEGORIES}

    prompts = read_prompts(input_files)
    total = len(prompts)
    total_batches = (total + batch_size - 1) // batch_size
    print(f"입력 파일: {len(input_files)}개 | 총 {total}개 프롬프트 | {total_batches}개 배치\n")

    for batch_idx, batch_start in enumerate(range(0, total, batch_size), 1):
        batch_texts = prompts[batch_start: batch_start + batch_size]
        batch = [(batch_start + i + 1, text) for i, text in enumerate(batch_texts)]
        t0 = time.time()

        try:
            response = ollama_call(ollama_build_prompt(batch), model, base_url)
            results = ollama_parse(response, len(batch))
        except Exception as e:
            print(f"  배치 {batch_idx}/{total_batches} 오류: {e} -> 건너뜀")
            results = [
                {"tops": [], "bottoms": [], "dresses": [], "legwear": [], "footwear": [], "accessories": []}
                for _ in batch
            ]

        for result in results:
            for cat in CATEGORIES:
                for item in result.get(cat, []):
                    item = item.strip()
                    if not item:
                        continue
                    item_lower = item.lower()
                    if (
                        item_lower not in existing[cat]
                        and item_lower not in new_items_set[cat]
                    ):
                        new_items[cat].append(item)
                        new_items_set[cat].add(item_lower)

        elapsed = time.time() - t0
        done = min(batch_start + batch_size, total)
        total_new = sum(len(v) for v in new_items.values())
        print(
            f"  배치 [{batch_idx:4d}/{total_batches}] "
            f"프롬프트 {done:5d}/{total} | "
            f"{elapsed:.1f}s | 누적 추출: {total_new}개"
        )

    save_items(new_items, output_files)


# ── 진입점 ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="이미지 프롬프트에서 의상 항목을 추출합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
모드별 사용 예시:
  # spaCy 모드 (빠름, 경량) - 기본
  python extract_clothing.py --mode spacy
  python extract_clothing.py --mode spacy --input prompts/ --output output/

  # Ollama 모드 (정확, LLM 사용)
  python extract_clothing.py --mode ollama
  python extract_clothing.py --mode ollama --model qwen3.5:35b --batch 10
  python extract_clothing.py --mode ollama --ollama-url http://localhost:11434

  # 입력: 단일 파일 또는 폴더 모두 가능
  python extract_clothing.py --input prompts/my_prompts.txt
  python extract_clothing.py --input prompts/
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["spacy", "ollama"],
        default="spacy",
        help="추출 방식 선택: spacy(기본) 또는 ollama",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("prompts"),
        help="입력 경로: txt 파일 또는 폴더 (기본값: prompts/)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output"),
        help="출력 디렉토리 경로 (기본값: output/)",
    )

    ollama_group = parser.add_argument_group("Ollama 옵션 (--mode ollama 전용)")
    ollama_group.add_argument(
        "--model",
        type=str,
        default="huihui_ai/qwen3.5-abliterated:35b",
        help="사용할 Ollama 모델명 (기본값: huihui_ai/qwen3.5-abliterated:35b)",
    )
    ollama_group.add_argument(
        "--batch",
        type=int,
        default=5,
        help="배치당 프롬프트 수 (기본값: 5, 클수록 빠르나 파싱 오류 위험 증가)",
    )
    ollama_group.add_argument(
        "--ollama-url",
        type=str,
        default="http://host.docker.internal:11434",
        help="Ollama API URL (WSL 기본값: http://host.docker.internal:11434)",
    )

    args = parser.parse_args()

    input_files = collect_input_files(args.input)
    print(f"입력 파일 {len(input_files)}개: {[f.name for f in input_files]}")

    if args.mode == "spacy":
        run_spacy(input_files, args.output)
    else:
        run_ollama(input_files, args.output, args.model, args.batch, args.ollama_url)


if __name__ == "__main__":
    main()
