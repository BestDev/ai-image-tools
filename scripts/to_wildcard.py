#!/usr/bin/env python3
"""
to_wildcard.py — prompts.txt → ComfyUI 와일드카드 형식 변환

지원 입력 형식:
  1. 구버전: 빈 줄(\n\n)로 프롬프트 구분 (단락이 섞여 있어도 처리)
  2. 신버전: --- 구분자로 프롬프트 구분 (prompts_raw.txt)
  3. 단일 줄: 한 줄 = 한 프롬프트 (현행 prompts.txt)

출력 형식 (ComfyUI wildcard):
  한 줄 = 한 프롬프트, 프롬프트 내부 줄바꿈은 공백으로 압축

사용법:
  python3 scripts/to_wildcard.py <입력파일> [-o <출력파일>]
  python3 scripts/to_wildcard.py output/2026-03-15-053817-m7/prompts.txt
  python3 scripts/to_wildcard.py output/*/prompts_raw.txt -o wildcards/all.txt
"""

import argparse
import sys
from pathlib import Path


def detect_format(text: str) -> str:
    """파일 형식 자동 감지"""
    if "\n---\n" in text:
        return "separator"   # 신버전 --- 구분자
    if "\n\n" in text:
        return "blank_line"  # 구버전 빈 줄 구분
    return "single_line"     # 현행 단일 줄


def parse_prompts(text: str, fmt: str) -> list[str]:
    """형식에 맞게 프롬프트 목록 추출"""
    text = text.strip()
    if fmt == "separator":
        parts = text.split("\n---\n")
    elif fmt == "blank_line":
        parts = text.split("\n\n")
    else:  # single_line
        parts = text.splitlines()
    return [p.strip() for p in parts if p.strip()]


def to_single_line(prompt: str) -> str:
    """줄바꿈을 공백으로 압축 → 한 줄"""
    return " ".join(prompt.split())


def convert(input_path: Path, output_path: Path) -> int:
    text = input_path.read_text(encoding="utf-8")
    fmt = detect_format(text)
    prompts = parse_prompts(text, fmt)

    if not prompts:
        print(f"[WARN] 프롬프트를 찾을 수 없습니다: {input_path}")
        return 0

    lines = [to_single_line(p) for p in prompts]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    fmt_label = {"separator": "--- 구분자", "blank_line": "빈 줄 구분", "single_line": "단일 줄"}[fmt]
    print(f"[{fmt_label}] {input_path.name} → {output_path} ({len(lines)}개)")
    return len(lines)


def main():
    parser = argparse.ArgumentParser(
        description="prompts.txt → ComfyUI 와일드카드 형식 변환",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("inputs", nargs="+", type=Path,
                        help="입력 파일 경로 (여러 개 지정 가능)")
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help="출력 파일 경로 (기본: 입력파일과 같은 폴더의 prompts-wildcard.txt)")
    args = parser.parse_args()

    # 여러 파일 → 하나로 합치기 모드
    merge_mode = args.output is not None and len(args.inputs) > 1

    if merge_mode:
        all_lines = []
        for input_path in args.inputs:
            if not input_path.is_file():
                print(f"[SKIP] 파일 없음: {input_path}", file=sys.stderr)
                continue
            text = input_path.read_text(encoding="utf-8")
            fmt = detect_format(text)
            prompts = parse_prompts(text, fmt)
            fmt_label = {"separator": "--- 구분자", "blank_line": "빈 줄 구분", "single_line": "단일 줄"}[fmt]
            print(f"  [{fmt_label}] {input_path}  →  {len(prompts)}개")
            all_lines.extend(to_single_line(p) for p in prompts)

        if not all_lines:
            print("변환할 프롬프트가 없습니다.")
            sys.exit(1)

        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text("\n".join(all_lines) + "\n", encoding="utf-8")
        print(f"\n합계 {len(all_lines)}개 → {args.output}")

    else:
        total = 0
        for input_path in args.inputs:
            if not input_path.is_file():
                print(f"[SKIP] 파일 없음: {input_path}", file=sys.stderr)
                continue
            out = args.output if args.output else input_path.parent / "prompts-wildcard.txt"
            total += convert(input_path, out)

        if total:
            print(f"\n완료: {total}개 프롬프트 변환")


if __name__ == "__main__":
    main()
