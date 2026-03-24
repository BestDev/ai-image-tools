#!/usr/bin/env python3
"""
이미지 파일 일괄 이름 변경 스크립트

사용법:
  python3 rename_images.py <폴더> --prefix <접두사> [옵션]
"""

import sys
import os
from pathlib import Path

_VENV_DIR = Path(__file__).resolve().parent.parent / "venv-prompt"
if _VENV_DIR.exists() and Path(sys.prefix) != _VENV_DIR:
    _VENV_PYTHON = _VENV_DIR / "bin" / "python3"
    os.execv(str(_VENV_PYTHON), [str(_VENV_PYTHON)] + sys.argv)

import argparse

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".tif"}


def main():
    parser = argparse.ArgumentParser(
        description="폴더 내 이미지 파일 이름을 접두사-숫자 형식으로 일괄 변경",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  python3 rename_images.py ./images --prefix photo
  python3 rename_images.py ./images --prefix dataset --start 1 --digits 4
  python3 rename_images.py ./images --prefix img --dry-run
        """,
    )
    parser.add_argument("input_dir", help="이미지 파일이 있는 폴더")
    parser.add_argument(
        "--prefix", "-p", required=True,
        help="파일명 접두사 (예: photo -> photo-0001.jpg)",
    )
    parser.add_argument(
        "--start", "-s", type=int, default=1,
        help="시작 번호 (기본: 1)",
    )
    parser.add_argument(
        "--digits", "-d", type=int, default=4,
        help="숫자 자릿수 (기본: 4, 예: 0001)",
    )
    parser.add_argument(
        "--separator", "-sep", default="-",
        help="접두사와 숫자 구분자 (기본: -)",
    )
    parser.add_argument(
        "--dry-run", "-n", action="store_true",
        help="실제 변경 없이 미리보기만",
    )
    parser.add_argument(
        "--sort", choices=["name", "date", "size"], default="name",
        help="정렬 기준 (name/date/size, 기본: name)",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.is_dir():
        print(f"오류: {input_dir} 폴더가 존재하지 않습니다.")
        sys.exit(1)

    image_files = [
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    ]

    if not image_files:
        print(f"이미지 파일이 없습니다: {input_dir}")
        return

    if args.sort == "name":
        image_files.sort(key=lambda x: x.name.lower())
    elif args.sort == "date":
        image_files.sort(key=lambda x: x.stat().st_mtime)
    elif args.sort == "size":
        image_files.sort(key=lambda x: x.stat().st_size)

    mode_label = "[DRY RUN] " if args.dry_run else ""
    print(f"=== {mode_label}이미지 이름 변경 ===")
    print(f"폴더  : {input_dir}")
    print(f"접두사: {args.prefix}")
    print(f"시작  : {args.start}")
    print(f"자릿수: {args.digits}")
    print(f"구분자: '{args.separator}'")
    print(f"정렬  : {args.sort}")
    print(f"파일  : {len(image_files)}개")
    print()

    renamed = skipped = errors = 0
    fmt = f"{args.prefix}{args.separator}%0{args.digits}d"

    for i, src in enumerate(image_files, args.start):
        new_name = fmt % i + src.suffix.lower()
        dest = src.parent / new_name

        if src == dest:
            print(f"[{i:>{args.digits}}] {src.name} (동일, 건너뜀)")
            skipped += 1
            continue

        if dest.exists():
            print(f"[{i:>{args.digits}}] {src.name} -> {new_name} (이미 존재, 건너뜀)")
            skipped += 1
            continue

        if args.dry_run:
            print(f"[{i:>{args.digits}}] {src.name} -> {new_name}")
            renamed += 1
            continue

        try:
            src.rename(dest)
            print(f"[{i:>{args.digits}}] {src.name} -> {new_name}")
            renamed += 1
        except Exception as e:
            print(f"[{i:>{args.digits}}] {src.name} -> {new_name} 오류: {e}")
            errors += 1

    print(f"\n=== 변경 완료 ===")
    print(f"변경: {renamed}개  건너뜀: {skipped}개  오류: {errors}개")


if __name__ == "__main__":
    main()