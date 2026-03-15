#!/usr/bin/env python3
"""
gemini_batch.py — Gemini CLI 헤드리스 배치 이미지 분석

Gemini CLI를 subprocess로 호출하여 이미지 폴더를 배치 처리합니다.
API 키 없이 Gemini CLI의 OAuth 인증(Google AI Pro 등)을 그대로 사용합니다.

세션 모드(기본):
  워밍업 호출로 페르소나를 확립하고 -r "latest" 로 세션을 이어가며
  각 이미지에는 최소 지시문만 전달합니다. N장마다 세션을 리셋합니다.

no-session 모드(--no-session):
  매 이미지마다 전체 프롬프트를 전달하는 기존 방식으로 동작합니다.

사용법:
  python3 gemini_batch.py <입력폴더> [옵션]

예시:
  python3 gemini_batch.py ./photos
  python3 gemini_batch.py ./photos -o ./prompts --lang zh --model flash-lite
  python3 gemini_batch.py ./photos --delay 5 --skip-existing
  python3 gemini_batch.py ./photos --no-session          # 세션 없이 전체 프롬프트
  python3 gemini_batch.py ./photos --reset-every 10      # 10장마다 세션 리셋
"""

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

# shared_prompts.py 로드
sys.path.insert(0, str(Path(__file__).parent))
from shared_prompts import (
    SYSTEM_PROMPT_EN, SYSTEM_PROMPT_ZH,
    WARMUP_EN, WARMUP_ZH,
    IMAGE_TASK_EN, IMAGE_TASK_ZH,
)

# ──────────────────────────────────────────────
# 설정
# ──────────────────────────────────────────────
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}

GEMINI_CLI = shutil.which("gemini") or "/home/bestdev/.nvm/versions/node/v24.13.1/bin/gemini"

# 모델 별칭 (gemini CLI --model 플래그 값)
MODEL_ALIASES = {
    "auto":       "auto",
    "pro":        "pro",
    "flash":      "flash",
    "flash-lite": "flash-lite",
}

# ──────────────────────────────────────────────
# no-session 모드용 전체 프롬프트 빌더
# (매 이미지마다 전체 지시문 포함)
# ──────────────────────────────────────────────
def _full_prompt_en(image_path: Path) -> str:
    abs_path = str(image_path.resolve())
    # SYSTEM_PROMPT_EN 에는 이미지 경로가 없으므로 앞에 붙이고 @{path} 를 추가
    return (
        SYSTEM_PROMPT_EN + "\n\n"
        "Output ONLY the prompt text with no preamble or explanation.\n\n"
        f"Analyze @{{{abs_path}}} and output the image prompt."
    )


def _full_prompt_zh(image_path: Path) -> str:
    abs_path = str(image_path.resolve())
    return (
        SYSTEM_PROMPT_ZH + "\n\n"
        "只输出提示词本身，不加任何前言或说明。\n\n"
        f"分析 @{{{abs_path}}}，输出图像提示词。"
    )


def build_full_prompt(image_path: Path, lang: str) -> str:
    """no-session 모드: 매 이미지에 전체 지시문 포함."""
    return _full_prompt_zh(image_path) if lang == "zh" else _full_prompt_en(image_path)


def build_image_task(image_path: Path, lang: str) -> str:
    """session 모드: 세션 재개 후 각 이미지에 붙이는 최소 지시문."""
    abs_path = str(image_path.resolve())
    template = IMAGE_TASK_ZH if lang == "zh" else IMAGE_TASK_EN
    return template.replace("{IMAGE_PATH}", abs_path)


# ──────────────────────────────────────────────
# Gemini CLI 실행 헬퍼
# ──────────────────────────────────────────────
def _run_cmd(cmd: list[str], timeout: int) -> tuple[bool, str]:
    """subprocess 실행 → (성공여부, 출력텍스트)"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            err = (result.stderr or result.stdout).strip()
            return False, f"[EXIT {result.returncode}] {err}"
    except subprocess.TimeoutExpired:
        return False, f"[TIMEOUT after {timeout}s]"
    except FileNotFoundError:
        return False, f"[ERROR] gemini CLI not found at: {GEMINI_CLI}"


def run_warmup(model: str, lang: str, timeout: int) -> tuple[bool, str]:
    """
    페르소나 확립 워밍업 호출.
    성공하면 이후 -r "latest" 로 세션 재개 가능.
    """
    warmup = WARMUP_ZH if lang == "zh" else WARMUP_EN
    cmd = [
        GEMINI_CLI,
        "-p", warmup,
        "--approval-mode=yolo",
        "-m", model,
        "--output-format", "text",
    ]
    return _run_cmd(cmd, timeout)


def run_gemini_session(image_path: Path, model: str, lang: str, timeout: int) -> tuple[bool, str]:
    """
    세션 재개(-r latest) + 최소 이미지 태스크 호출.
    워밍업 이후에 사용합니다.
    """
    task = build_image_task(image_path, lang)
    cmd = [
        GEMINI_CLI,
        "-r", "latest",
        "-p", task,
        "--approval-mode=yolo",
        "-m", model,
        "--output-format", "text",
    ]
    return _run_cmd(cmd, timeout)


def run_gemini_full(image_path: Path, model: str, lang: str, timeout: int) -> tuple[bool, str]:
    """
    no-session 모드: 전체 프롬프트를 포함한 독립 호출.
    """
    prompt = build_full_prompt(image_path, lang)
    cmd = [
        GEMINI_CLI,
        "-p", prompt,
        "--approval-mode=yolo",
        "-m", model,
        "--output-format", "text",
    ]
    return _run_cmd(cmd, timeout)


# ──────────────────────────────────────────────
# 유틸
# ──────────────────────────────────────────────
def collect_images(input_dir: Path) -> list[Path]:
    images = []
    for ext in IMAGE_EXTENSIONS:
        images.extend(input_dir.glob(f"*{ext}"))
        images.extend(input_dir.glob(f"*{ext.upper()}"))
    return sorted(set(images), key=lambda p: p.name)


def output_path_for(image: Path, output_dir: Path | None) -> Path:
    base = output_dir if output_dir else image.parent
    return base / (image.stem + ".txt")


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Gemini CLI 헤드리스 배치 이미지 분석",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input_dir", type=Path, help="이미지 폴더 경로")
    parser.add_argument("-o", "--output-dir", type=Path, default=None,
                        help="프롬프트 txt 저장 폴더 (기본: 이미지와 같은 폴더)")
    parser.add_argument("--lang", choices=["en", "zh"], default="en",
                        help="출력 언어 (기본: en)")
    parser.add_argument("-m", "--model", choices=list(MODEL_ALIASES.keys()), default="flash",
                        help="Gemini 모델 별칭 (기본: flash)")
    parser.add_argument("--delay", type=float, default=3.0,
                        help="이미지 간 대기 시간(초) (기본: 3)")
    parser.add_argument("--timeout", type=int, default=120,
                        help="이미지당 최대 대기 시간(초) (기본: 120)")
    parser.add_argument("--skip-existing", action="store_true",
                        help="이미 txt 파일이 존재하면 건너뜀")
    parser.add_argument("--dry-run", action="store_true",
                        help="실제 실행 없이 처리 목록만 출력")
    parser.add_argument("--collect-file", type=str, default="prompts.txt",
                        help="누적 프롬프트 파일명 (기본: prompts.txt). 빈 문자열로 비활성화")
    parser.add_argument("--no-session", action="store_true",
                        help="세션 없이 매 이미지마다 전체 프롬프트 전달 (기존 방식)")
    parser.add_argument("--reset-every", type=int, default=25,
                        help="세션 모드: N장마다 세션 리셋 (기본: 25, 0=리셋 없음)")
    args = parser.parse_args()

    # 입력 폴더 확인
    if not args.input_dir.is_dir():
        print(f"[ERROR] 입력 폴더 없음: {args.input_dir}", file=sys.stderr)
        sys.exit(1)

    # 출력 폴더 생성
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)

    # gemini CLI 확인
    if not Path(GEMINI_CLI).exists():
        print(f"[ERROR] gemini CLI를 찾을 수 없습니다: {GEMINI_CLI}", file=sys.stderr)
        print("  설치 확인: which gemini", file=sys.stderr)
        sys.exit(1)

    # 이미지 목록
    images = collect_images(args.input_dir)
    if not images:
        print(f"[WARN] 이미지가 없습니다: {args.input_dir}")
        sys.exit(0)

    model = MODEL_ALIASES[args.model]
    total = len(images)
    skipped = 0
    success = 0
    failed = 0
    session_active = False  # 워밍업 성공 여부 추적

    # 누적 파일 경로 결정
    collect_path: Path | None = None
    if args.collect_file:
        collect_base = args.output_dir if args.output_dir else args.input_dir
        collect_path = collect_base / args.collect_file

    session_mode = not args.no_session
    reset_every = args.reset_every

    print(f"Gemini CLI 배치 시작")
    print(f"  입력폴더 : {args.input_dir.resolve()}")
    print(f"  출력폴더 : {args.output_dir.resolve() if args.output_dir else '(이미지 옆)'}")
    print(f"  누적파일 : {collect_path.resolve() if collect_path else '(비활성화)'}")
    print(f"  모델     : {args.model} ({model})")
    print(f"  언어     : {args.lang}")
    print(f"  총 이미지: {total}장")
    print(f"  대기시간 : {args.delay}초")
    print(f"  세션모드 : {'ON (리셋 ' + (str(reset_every) + '장마다)' if reset_every > 0 else '없음)') if session_mode else 'OFF (전체 프롬프트)'}")
    print()

    def do_warmup(idx: int) -> bool:
        """워밍업 실행 후 결과 출력. 성공하면 True."""
        print(f"  [WARMUP] 세션 초기화 중...", end="", flush=True)
        ok, text = run_warmup(model, args.lang, args.timeout)
        if ok:
            preview = text[:50].replace("\n", " ")
            print(f" OK  ({preview})")
        else:
            print(f" FAIL  {text}")
            print(f"  [WARN] 워밍업 실패 — 전체 프롬프트 방식으로 폴백합니다.")
        return ok

    for idx, image in enumerate(images, 1):
        out_txt = output_path_for(image, args.output_dir)
        prefix = f"[{idx:3d}/{total}]"

        # skip-existing
        if args.skip_existing and out_txt.exists() and out_txt.stat().st_size > 0:
            print(f"{prefix} SKIP  {image.name}")
            skipped += 1
            continue

        if args.dry_run:
            print(f"{prefix} DRY   {image.name} -> {out_txt}")
            continue

        # 세션 모드: 워밍업 / 리셋 타이밍 결정
        if session_mode:
            need_warmup = (
                not session_active                                    # 첫 이미지
                or (reset_every > 0 and (idx - 1) % reset_every == 0 and idx > 1)  # N장마다
            )
            if need_warmup:
                if idx > 1:
                    print()  # 줄바꿈 후 워밍업 구분
                session_active = do_warmup(idx)

        print(f"{prefix} ...   {image.name}", end="", flush=True)

        # 이미지 분석 호출
        if session_mode and session_active:
            ok, text = run_gemini_session(image, model, args.lang, args.timeout)
        else:
            ok, text = run_gemini_full(image, model, args.lang, args.timeout)

        if ok:
            out_txt.write_text(text, encoding="utf-8")
            # 누적 파일에 추가: 줄바꿈 압축 → 한 줄 = 한 프롬프트
            if collect_path:
                single_line = " ".join(text.split())
                with collect_path.open("a", encoding="utf-8") as cf:
                    cf.write(single_line + "\n")
            # 첫 60자만 미리보기
            preview = text[:60].replace("\n", " ")
            print(f"\r{prefix} OK    {image.name}  |  {preview}...")
            success += 1
        else:
            print(f"\r{prefix} FAIL  {image.name}  |  {text}")
            # 세션 실패 시 세션 상태 초기화 (다음 이미지에서 재워밍업)
            if session_mode:
                session_active = False
            # 실패 로그 저장 (재처리 판단용)
            out_txt.with_suffix(".err").write_text(text, encoding="utf-8")
            failed += 1

        # 마지막 이미지가 아닐 때만 대기
        if idx < total and args.delay > 0:
            time.sleep(args.delay)

    # 결과 요약
    print()
    print(f"완료: 성공 {success} / 실패 {failed} / 건너뜀 {skipped} / 전체 {total}")
    if collect_path and success > 0:
        print(f"누적파일: {collect_path.resolve()}")
    if failed > 0:
        print(f"실패한 이미지의 에러는 .err 파일로 저장됩니다.")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
