#!/usr/bin/env python3
"""
HEIC/HEIF → JPEG 일괄 변환 스크립트

사용법:
  python3 heic_to_jpeg.py <폴더> [옵션]
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
import time

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    print("오류: pillow-heif가 설치되어 있지 않습니다.")
    print(f"설치: {_VENV_DIR}/bin/pip install pillow-heif")
    sys.exit(1)

from PIL import Image

HEIC_EXTENSIONS = {".heic", ".heif"}


# ── 메인 ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="폴더 내 HEIC/HEIF 이미지를 JPEG로 일괄 변환",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  python3 heic_to_jpeg.py /mnt/d/photos
  python3 heic_to_jpeg.py /mnt/d/photos --quality 90
  python3 heic_to_jpeg.py /mnt/d/photos --keep
  python3 heic_to_jpeg.py /mnt/d/photos --recursive
  python3 heic_to_jpeg.py /mnt/d/photos --dry-run
        """,
    )
    parser.add_argument("input_dir", help="변환할 HEIC 파일이 있는 폴더")
    parser.add_argument(
        "--quality", "-q", type=int, default=95,
        help="JPEG 품질 (1~100, 기본: 95)",
    )
    parser.add_argument(
        "--keep", action="store_true",
        help="변환 후 원본 HEIC 파일 유지 (기본: 삭제)",
    )
    parser.add_argument(
        "--recursive", "-r", action="store_true",
        help="하위 폴더까지 재귀 처리",
    )
    parser.add_argument(
        "--dry-run", "-n", action="store_true",
        help="실제 변환 없이 처리할 파일 목록만 출력",
    )
    args = parser.parse_args()

    if not 1 <= args.quality <= 100:
        print("오류: --quality 는 1~100 사이 값이어야 합니다.")
        sys.exit(1)

    input_dir = Path(args.input_dir)
    if not input_dir.is_dir():
        print(f"오류: {input_dir} 폴더가 존재하지 않습니다.")
        sys.exit(1)

    if args.recursive:
        heic_files = sorted(
            f for f in input_dir.rglob("*")
            if f.suffix.lower() in HEIC_EXTENSIONS
        )
    else:
        heic_files = sorted(
            f for f in input_dir.iterdir()
            if f.suffix.lower() in HEIC_EXTENSIONS
        )

    if not heic_files:
        print(f"변환할 HEIC/HEIF 파일이 없습니다: {input_dir}")
        return

    mode_label = "[DRY RUN] " if args.dry_run else ""
    print(f"=== {mode_label}HEIC → JPEG 변환 ===")
    print(f"폴더  : {input_dir}")
    print(f"파일  : {len(heic_files)}개")
    print(f"품질  : {args.quality}")
    print(f"원본  : {'유지 (--keep)' if args.keep else '삭제'}")
    if args.recursive:
        print(f"모드  : 재귀 (하위 폴더 포함)")
    print()

    start = time.time()
    pad = len(str(len(heic_files)))
    converted = skipped = deleted = errors = 0

    for i, src in enumerate(heic_files, 1):
        dest = src.with_suffix(".jpg")
        rel = src.relative_to(input_dir) if args.recursive else Path(src.name)
        print(f"[{i:>{pad}}/{len(heic_files)}] {rel}")

        if dest.exists():
            print(f"          건너뜀 (이미 존재: {dest.name})")
            skipped += 1
            continue

        if args.dry_run:
            print(f"          → {dest.name}")
            converted += 1
            continue

        try:
            img = Image.open(src).convert("RGB")
            img.save(dest, "JPEG", quality=args.quality, optimize=True)
            size_kb = dest.stat().st_size / 1024
            print(f"          → {dest.name}  ({size_kb:.0f}KB)")
            converted += 1

            if not args.keep:
                src.unlink()
                deleted += 1

        except Exception as e:
            print(f"          오류: {e}")
            if dest.exists():
                dest.unlink()  # 불완전한 파일 정리
            errors += 1

    elapsed = time.time() - start

    print(f"\n=== 변환 완료 ===")
    print(f"변환: {converted}개  건너뜀: {skipped}개  오류: {errors}개")
    if not args.keep and not args.dry_run:
        print(f"삭제: {deleted}개 (원본 HEIC)")
    print(f"소요: {elapsed:.1f}초")


if __name__ == "__main__":
    main()
