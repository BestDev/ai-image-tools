#!/usr/bin/env python3
"""
로컬 이미지 자동 분류 스크립트

사용법:
  python3 image_classifier.py <폴더> --by style      [--move] [-o 출력폴더]
  python3 image_classifier.py <폴더> --by background [--move] [-o 출력폴더]
  python3 image_classifier.py <폴더> --by person     [--move] [-o 출력폴더]
"""

# ── 가상환경 자동 활성화 ────────────────────────────────────────────────────────
import sys
import os
from pathlib import Path

_VENV_DIR = Path(__file__).resolve().parent.parent / "venv-classifier"
if _VENV_DIR.exists() and Path(sys.prefix) != _VENV_DIR:
    _VENV_PYTHON = _VENV_DIR / "bin" / "python3"
    os.execv(str(_VENV_PYTHON), [str(_VENV_PYTHON)] + sys.argv)

# ── 임포트 ────────────────────────────────────────────────────────────────────
import argparse
import csv
import shutil
import time
from pathlib import Path

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif", ".heic", ".heif"}

STYLE_LABELS: dict[str, list[str]] = {
    "photorealistic": [
        "a real photograph of a scene or person",
        "a photorealistic image of real life",
    ],
    "3d_render": [
        "a 3D rendered CGI image",
        "a computer generated 3D scene with rendered lighting",
    ],
    "anime": [
        "an anime or manga style illustration",
        "a Japanese animation style drawing with large eyes and colorful hair",
    ],
    "sci_fi": [
        "a science fiction scene with futuristic technology or space",
        "a science fiction scene with spaceships, robots, or cyberpunk city",
    ],
    "fantasy": [
        "a fantasy scene with magic, dragons, or medieval elements",
        "a fantasy scene with swords, castles, elves, or magical creatures",
    ],
}


# ── 모델 로드 ─────────────────────────────────────────────────────────────────

def load_clip(model_name: str):
    import torch
    from transformers import pipeline

    device = 0 if torch.cuda.is_available() else -1
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    print(f"[로드] CLIP 모델: {model_name}")
    return pipeline(
        task="zero-shot-image-classification",
        model=model_name,
        device=device,
        torch_dtype=dtype,
    )


def load_yolo():
    from ultralytics import YOLO
    print("[로드] YOLO 모델: yolo11n.pt")
    return YOLO("yolo11n.pt")


# ── 분류 함수 ─────────────────────────────────────────────────────────────────

def classify_style(clip, image_path: str) -> tuple[str, float, dict[str, float]]:
    all_labels = [lbl for labels in STYLE_LABELS.values() for lbl in labels]
    results = clip(image_path, candidate_labels=all_labels)
    score_map = {r["label"]: r["score"] for r in results}

    style_scores = {
        style: max(score_map.get(lbl, 0.0) for lbl in labels)
        for style, labels in STYLE_LABELS.items()
    }
    best = max(style_scores, key=lambda k: style_scores[k])
    return best, style_scores[best], style_scores


def classify_background(image_path: str, std_threshold: float = 15.0) -> tuple[str, float, tuple]:
    import cv2
    import numpy as np
    from PIL import Image

    pil_img = Image.open(image_path).convert("RGB")
    img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    h, w = img.shape[:2]
    edge_h = max(1, int(h * 0.1))
    edge_w = max(1, int(w * 0.1))
    regions = [img[:edge_h, :], img[h - edge_h:, :], img[:, :edge_w], img[:, w - edge_w:]]
    edge_pixels = np.concatenate([r.reshape(-1, 3) for r in regions], axis=0)

    mean_std = float(np.mean(np.std(edge_pixels.astype(np.float32), axis=0)))
    dominant_bgr = tuple(int(x) for x in np.median(edge_pixels, axis=0))
    b, g, r = dominant_bgr
    category = "solid" if mean_std < std_threshold else "complex"
    return category, round(mean_std, 2), (r, g, b)


def classify_person(yolo, image_path: str) -> tuple[str, int]:
    from PIL import Image
    suffix = Path(image_path).suffix.lower()
    img_input = Image.open(image_path).convert("RGB") if suffix in {".heic", ".heif"} else image_path
    results = yolo(img_input, verbose=False)
    for r in results:
        count = int((r.boxes.cls == 0).sum().item())
        if count == 0:
            return "no_person", 0
        if count == 1:
            return "single_person", 1
        return "multiple_people", count
    return "no_person", 0


# ── 축별 배치 실행 ────────────────────────────────────────────────────────────

def run_by_style(image_files: list[Path], args) -> list[dict]:
    clip = load_clip(args.model)
    print()
    results = []
    pad = len(str(len(image_files)))
    for i, img in enumerate(image_files, 1):
        try:
            category, score, all_scores = classify_style(clip, str(img))
            result = {"filename": img.name, "category": category, "score": round(score, 4)}
            results.append(result)
            print(f"[{i:>{pad}}/{len(image_files)}] {img.name}")
            print(f"          → {category} ({score:.2f})")
            if args.verbose:
                detail = " | ".join(
                    f"{k}: {v:.3f}"
                    for k, v in sorted(all_scores.items(), key=lambda x: -x[1])
                )
                print(f"          └ {detail}")
        except Exception as e:
            print(f"[{i:>{pad}}/{len(image_files)}] {img.name} — 오류: {e}")
    return results


def run_by_background(image_files: list[Path], args) -> list[dict]:
    print()
    results = []
    pad = len(str(len(image_files)))
    for i, img in enumerate(image_files, 1):
        try:
            category, std, color_rgb = classify_background(str(img), args.bg_threshold)
            result = {"filename": img.name, "category": category, "bg_std": std, "bg_color_rgb": color_rgb}
            results.append(result)
            color_str = f"rgb{color_rgb}" if category == "solid" else ""
            print(f"[{i:>{pad}}/{len(image_files)}] {img.name}")
            print(f"          → {category}  std={std:.1f} {color_str}")
        except Exception as e:
            print(f"[{i:>{pad}}/{len(image_files)}] {img.name} — 오류: {e}")
    return results


def run_by_person(image_files: list[Path], args) -> list[dict]:
    yolo = load_yolo()
    print()
    results = []
    pad = len(str(len(image_files)))
    for i, img in enumerate(image_files, 1):
        try:
            category, count = classify_person(yolo, str(img))
            result = {"filename": img.name, "category": category, "person_count": count}
            results.append(result)
            print(f"[{i:>{pad}}/{len(image_files)}] {img.name}")
            print(f"          → {category} ({count}명)")
        except Exception as e:
            print(f"[{i:>{pad}}/{len(image_files)}] {img.name} — 오류: {e}")
    return results


# ── 통계 출력 ─────────────────────────────────────────────────────────────────

def print_summary(results: list[dict], elapsed: float):
    total = len(results)
    counts: dict[str, int] = {}
    for r in results:
        counts[r["category"]] = counts.get(r["category"], 0) + 1

    print(f"\n=== 분류 완료 ===")
    print(f"총 {total}개  ({elapsed:.1f}초, {elapsed/total:.2f}초/이미지)\n")
    for cat, cnt in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {cat:<22} {cnt:>4}개 ({cnt/total*100:5.1f}%)")


# ── CSV 저장 ──────────────────────────────────────────────────────────────────

def save_csv(results: list[dict], csv_path: Path):
    if not results:
        return
    fieldnames = list(results[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"CSV 저장: {csv_path}")


# ── 파일 정리 (move / copy) ───────────────────────────────────────────────────

def organize(results: list[dict], input_dir: Path, output_dir: Path, move: bool):
    output_dir.mkdir(parents=True, exist_ok=True)
    for r in results:
        src = input_dir / r["filename"]
        if not src.exists():
            continue
        dest_dir = output_dir / r["category"]
        dest_dir.mkdir(exist_ok=True)
        if move:
            shutil.move(str(src), dest_dir / r["filename"])
        else:
            shutil.copy2(src, dest_dir / r["filename"])

    verb = "이동" if move else "복사"
    print(f"폴더 {verb} 완료: {output_dir}")


# ── 메인 ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="로컬 이미지 자동 분류",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
분류 축:
  style       스타일 분류 — photorealistic / 3d_render / anime / sci_fi / fantasy  (CLIP)
  background  배경 분류   — solid / complex                                         (OpenCV)
  person      인물 수 분류 — no_person / single_person / multiple_people            (YOLO)
        """
    )
    parser.add_argument("input_dir", help="분류할 이미지 폴더")
    parser.add_argument(
        "--by", required=True, choices=["style", "background", "person"],
        help="분류 기준 선택"
    )
    parser.add_argument("--move", action="store_true", help="분류 후 파일 이동 (원본 삭제)")
    parser.add_argument("--copy", action="store_true", help="분류 후 파일 복사 (원본 유지)")
    parser.add_argument("--output-dir", "-o", help="출력 폴더 (기본: input_dir/by_<축>)")
    parser.add_argument("--csv", help="CSV 저장 경로 (기본: input_dir/report_<축>.csv)")
    parser.add_argument(
        "--model", default="openai/clip-vit-large-patch14",
        choices=["openai/clip-vit-large-patch14", "google/siglip-so400m-patch14-384"],
        help="CLIP 모델 선택 (--by style 전용)"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="세부 점수 출력 (--by style 전용)")
    parser.add_argument("--bg-threshold", type=float, default=15.0,
                        help="단색 판정 임계값 (--by background 전용, 기본: 15.0)")
    args = parser.parse_args()

    if args.copy and args.move:
        print("오류: --copy 와 --move 는 동시에 사용할 수 없습니다.")
        return

    input_dir = Path(args.input_dir)
    if not input_dir.is_dir():
        print(f"오류: {input_dir} 폴더가 존재하지 않습니다.")
        return

    image_files = sorted(f for f in input_dir.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS)
    if not image_files:
        print(f"오류: {input_dir} 에서 이미지를 찾을 수 없습니다.")
        return

    output_dir = Path(args.output_dir) if args.output_dir else input_dir / f"by_{args.by}"
    csv_path = Path(args.csv) if args.csv else input_dir / f"report_{args.by}.csv"

    axis_label = {"style": "스타일", "background": "배경", "person": "인물 수"}
    file_op = "이동 (원본 삭제)" if args.move else "복사 (원본 유지)" if args.copy else "없음 (CSV만)"

    print(f"=== 이미지 분류 시작 ===")
    print(f"분류 기준: {args.by} ({axis_label[args.by]})")
    print(f"입력: {input_dir} ({len(image_files)}개)")
    print(f"파일 처리: {file_op}")
    if args.copy or args.move:
        print(f"출력: {output_dir}")

    start = time.time()

    if args.by == "style":
        results = run_by_style(image_files, args)
    elif args.by == "background":
        results = run_by_background(image_files, args)
    else:
        results = run_by_person(image_files, args)

    elapsed = time.time() - start

    if results:
        print_summary(results, elapsed)
        save_csv(results, csv_path)
        if args.move:
            organize(results, input_dir, output_dir, move=True)
        elif args.copy:
            organize(results, input_dir, output_dir, move=False)


if __name__ == "__main__":
    main()
