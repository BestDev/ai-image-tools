#!/usr/bin/env python3
"""
txt_to_yaml_wildcard.py — ComfyUI ImpactPack TXT 와일드카드 → YAML 변환

TXT 와일드카드(한 줄 = 한 옵션)를 YAML 계층 구조로 변환합니다.

사용법:
  # 단일 파일 변환 (prompts.yaml 생성, 키: prompts)
  python3 txt_to_yaml_wildcard.py prompts.txt

  # 여러 파일을 하나의 YAML로 병합
  python3 txt_to_yaml_wildcard.py flowers.txt colors.txt -o wildcards.yaml

  # 키 이름 직접 지정 (단일 파일)
  python3 txt_to_yaml_wildcard.py prompts.txt --key portrait

  # 기존 YAML에 추가 (append 모드)
  python3 txt_to_yaml_wildcard.py new.txt -o existing.yaml --append
"""

import argparse
import sys
from pathlib import Path


def load_txt(path: Path) -> list[str]:
    """TXT 파일에서 유효한 옵션 목록 로드. # 주석·빈 줄 제외."""
    lines = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            lines.append(stripped)
    return lines


def load_existing_yaml(path: Path) -> dict:
    """기존 YAML 파일 로드 (append 모드용). yaml 없으면 빈 dict 반환."""
    try:
        import yaml
    except ImportError:
        print("[ERROR] PyYAML이 필요합니다: pip install pyyaml", file=sys.stderr)
        sys.exit(1)

    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def write_yaml(data: dict, path: Path):
    """딕셔너리를 YAML로 저장. 멀티라인 문자열은 literal block 스타일."""
    try:
        import yaml
    except ImportError:
        print("[ERROR] PyYAML이 필요합니다: pip install pyyaml", file=sys.stderr)
        sys.exit(1)

    # 긴 문자열(프롬프트)도 한 줄로 유지하기 위해 width 크게 설정
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(
            data,
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
            width=4096,
        )


def main():
    parser = argparse.ArgumentParser(
        description="TXT 와일드카드 → YAML 변환",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("inputs", type=Path, nargs="+", help="입력 TXT 파일(들)")
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help="출력 YAML 파일 (기본: 입력 파일명.yaml, 복수 입력 시 필수)")
    parser.add_argument("--key", type=str, default=None,
                        help="YAML 키 이름 지정 (단일 파일 전용, 기본: 파일명)")
    parser.add_argument("--append", action="store_true",
                        help="기존 YAML에 이어쓰기 (덮어쓰기 방지)")
    args = parser.parse_args()

    # 복수 입력 시 -o 필수
    if len(args.inputs) > 1 and args.output is None:
        print("[ERROR] 여러 파일 병합 시 -o 출력 파일을 지정해야 합니다.", file=sys.stderr)
        sys.exit(1)

    # --key 는 단일 파일에서만 유효
    if args.key and len(args.inputs) > 1:
        print("[ERROR] --key 는 단일 파일 변환에서만 사용 가능합니다.", file=sys.stderr)
        sys.exit(1)

    # 입력 파일 존재 확인
    for p in args.inputs:
        if not p.exists():
            print(f"[ERROR] 파일 없음: {p}", file=sys.stderr)
            sys.exit(1)

    # 단일 파일: 출력 경로 자동 결정
    if len(args.inputs) == 1 and args.output is None:
        args.output = args.inputs[0].with_suffix(".yaml")

    # 기존 YAML 로드 (append 모드)
    data = load_existing_yaml(args.output) if args.append else {}

    # 각 TXT 파일 처리
    total_options = 0
    for txt_path in args.inputs:
        key = args.key if args.key else txt_path.stem
        options = load_txt(txt_path)

        if not options:
            print(f"[WARN] 유효한 옵션 없음, 건너뜀: {txt_path.name}")
            continue

        if key in data and not args.append:
            print(f"[WARN] 키 '{key}' 중복 — 덮어씁니다.")

        data[key] = options
        total_options += len(options)
        print(f"  {txt_path.name} → 키: '{key}', {len(options)}개 옵션")

    if not data:
        print("[ERROR] 변환할 데이터가 없습니다.", file=sys.stderr)
        sys.exit(1)

    write_yaml(data, args.output)
    print(f"\n저장 완료: {args.output.resolve()}")
    print(f"총 키: {len(data)}개 / 총 옵션: {total_options}개")
    print(f"\nComfyUI 사용법:")
    for key in data:
        print(f"  __{key}__")


if __name__ == "__main__":
    main()
