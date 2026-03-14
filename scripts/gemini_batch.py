#!/usr/bin/env python3
"""
gemini_batch.py — Gemini CLI 헤드리스 배치 이미지 분석

Gemini CLI를 subprocess로 호출하여 이미지 폴더를 배치 처리합니다.
API 키 없이 Gemini CLI의 OAuth 인증(Google AI Pro 등)을 그대로 사용합니다.

사용법:
  python3 gemini_batch.py <입력폴더> [옵션]

예시:
  python3 gemini_batch.py ./photos
  python3 gemini_batch.py ./photos -o ./prompts --lang zh --model flash-lite
  python3 gemini_batch.py ./photos --delay 5 --skip-existing
  python3 gemini_batch.py ./photos --collect-file all_prompts.txt
"""

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

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
# 프롬프트
# ──────────────────────────────────────────────
PROMPT_EN = (
    "You are an expert in interpreting precise visual scenes. "
    "Analyze the image at @{{IMAGE_PATH}} and produce a refined, high-fidelity English prompt "
    "tailored to its primary subject (person, architectural space, natural landscape, or still-life object).\n\n"
    "If the scene depicts architecture or interior space, describe the architectural style, "
    "structural elements, materials, and spatial depth accurately. Do not invent human presence.\n\n"
    "If the image represents a product or still-life object, emphasize surface qualities, "
    "material reflections, textures, color harmony, and physical arrangement.\n\n"
    "Only if people are clearly visible should you describe the following in detail. "
    "If no people exist, omit all human-related language entirely.\n\n"
    "For clothing: garment type and style, neckline shape and depth, sleeve length and cut, "
    "hemline length, any cutouts or sheer and transparent panels, areas of bare skin exposure, "
    "fabric texture and material (e.g., satin, lace, cotton), colors and patterns, "
    "and all accessories including shoes, bags, jewelry, and hair accessories.\n\n"
    "For pose: overall body orientation (facing camera, angled, turned away), head tilt and exact gaze direction, "
    "shoulder position, arm and hand placement (e.g., arms raised, hands on hips, holding an object), "
    "leg stance (standing straight, one leg forward, seated, crossed), and any body lean or weight shift.\n\n"
    "Explain the lighting conditions, including the type of light source, shadow behavior, contrast, and atmospheric mood.\n\n"
    "Describe composition and camera perspective, such as framing balance, lens choice, depth of field, and viewpoint.\n\n"
    "Write a single, natural English paragraph of 80-250 words. "
    "Avoid references to watermarks, symbols, or irrelevant text. "
    "Output ONLY the prompt text with no preamble or explanation."
)

PROMPT_ZH = (
    "你是专业的图像视觉分析专家，为文生图模型生成精准的中文提示词。"
    "分析图像 @{{IMAGE_PATH}} ，根据主要主题（人物、建筑空间、自然风景或静物）输出高保真提示词。\n\n"
    "若为建筑或室内空间：描述建筑风格、结构元素、材质及空间层次感，不虚构人物。\n"
    "若为产品或静物：重点描述表面质感、材质反光、纹理、色彩搭配及物品排列。\n"
    "若画面中有清晰可见的人物，详细描述以下内容；若无人物则完全省略人物描述：\n\n"
    "服装细节：服装类型与款式、领口形状与深度、袖长与剪裁、裙摆或裤腿长度、"
    "镂空或透视薄纱区域、裸露肌肤范围、面料质感与材质（缎面、蕾丝、棉质、针织等）、"
    "颜色与花纹、全部配饰（鞋履、包袋、耳环、项链、手链、脚链、发饰等）。\n\n"
    "姿势与体态：整体身体朝向（正对/侧身/背对镜头）、头部倾斜角度与视线方向、"
    "肩部位置与角度、手臂及手部动作、腿部姿态、身体重心偏移方向、体态曲线与轮廓走势。\n\n"
    "光线：光源类型与方向、阴影形态、色温、对比度与氛围。\n"
    "构图：景别（特写/近景/半身/全身）、拍摄角度、景深与背景虚化。\n\n"
    "用单段流畅自然的中文输出，字数150至400字，不提及水印、符号或无关文字。"
    "只输出提示词本身，不加任何前言或说明。"
)


def build_prompt(image_path: Path, lang: str) -> str:
    """이미지 절대경로를 @{...} 문법으로 삽입한 프롬프트 생성."""
    abs_path = str(image_path.resolve())
    template = PROMPT_ZH if lang == "zh" else PROMPT_EN
    # {IMAGE_PATH} 자리에 실제 경로 삽입 (이중 중괄호로 이스케이프한 부분)
    return template.replace("{IMAGE_PATH}", abs_path)


def run_gemini(prompt: str, model: str, timeout: int) -> tuple[bool, str]:
    """
    gemini -p "<prompt>" --approval-mode=yolo -m <model> 를 실행하고
    (성공여부, 출력텍스트) 를 반환합니다.
    """
    cmd = [
        GEMINI_CLI,
        "-p", prompt,
        "--approval-mode=yolo",   # 헤드리스 배치에서 툴 승인 프롬프트 자동 통과
        "-m", model,
        "--output-format", "text",
    ]
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


def collect_images(input_dir: Path) -> list[Path]:
    images = []
    for ext in IMAGE_EXTENSIONS:
        images.extend(input_dir.glob(f"*{ext}"))
        images.extend(input_dir.glob(f"*{ext.upper()}"))
    return sorted(set(images))


def output_path_for(image: Path, output_dir: Path | None) -> Path:
    base = output_dir if output_dir else image.parent
    return base / (image.stem + ".txt")


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

    # 누적 파일 경로 결정
    collect_path: Path | None = None
    if args.collect_file:
        collect_base = args.output_dir if args.output_dir else args.input_dir
        collect_path = collect_base / args.collect_file

    print(f"Gemini CLI 배치 시작")
    print(f"  입력폴더 : {args.input_dir.resolve()}")
    print(f"  출력폴더 : {args.output_dir.resolve() if args.output_dir else '(이미지 옆)'}")
    print(f"  누적파일 : {collect_path.resolve() if collect_path else '(비활성화)'}")
    print(f"  모델     : {args.model} ({model})")
    print(f"  언어     : {args.lang}")
    print(f"  총 이미지: {total}장")
    print(f"  대기시간 : {args.delay}초")
    print()

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

        print(f"{prefix} ...   {image.name}", end="", flush=True)

        prompt = build_prompt(image, args.lang)
        ok, text = run_gemini(prompt, model, args.timeout)

        if ok:
            out_txt.write_text(text, encoding="utf-8")
            # 누적 파일에 이미지명 헤더와 함께 추가
            if collect_path:
                with collect_path.open("a", encoding="utf-8") as cf:
                    cf.write(f"# {image.name}\n{text}\n\n")
            # 첫 60자만 미리보기
            preview = text[:60].replace("\n", " ")
            print(f"\r{prefix} OK    {image.name}  |  {preview}...")
            success += 1
        else:
            print(f"\r{prefix} FAIL  {image.name}  |  {text}")
            # 실패 로그도 저장 (재처리 판단용)
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
