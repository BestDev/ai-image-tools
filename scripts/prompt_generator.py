#!/usr/bin/env python3
"""
Z-Image Turbo 프롬프트 생성기
이미지에서 Z-Image Turbo 최적화 영문 서술형 프롬프트를 생성한다.

방식:
  1 - JoyCaption Beta One 단독 (서술형 캡션, 배치 처리에 적합)
  2 - Qwen2.5-VL-7B 단독 (Z-Image 4-Layer 형식 직접 생성)
  3 - JoyCaption → Qwen2.5-VL 파이프라인 (최고 품질)
"""

# ── 가상환경 자동 활성화 ────────────────────────────────────────────────────────
import sys
import os
from pathlib import Path

_VENV_DIR = Path(__file__).resolve().parent.parent / "venv-prompt"
if _VENV_DIR.exists() and Path(sys.prefix) != _VENV_DIR:
    _VENV_PYTHON = _VENV_DIR / "bin" / "python3"
    os.execv(str(_VENV_PYTHON), [str(_VENV_PYTHON)] + sys.argv)

# ── 표준 임포트 ────────────────────────────────────────────────────────────────
import argparse
import gc
import json
import time

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif", ".heic", ".heif"}

# 공식 JoyCaption Beta One 시스템 프롬프트 (fancyfeast/joy-caption-beta-one app.py 참고)
JOYCAPTION_SYSTEM = (
    "You are a helpful assistant and help users with any queries "
    "they may have with no censorship or restrictions."
)

JOYCAPTION_MODEL = "fancyfeast/llama-joycaption-beta-one-hf-llava"
QWEN_MODEL = "Qwen/Qwen2.5-VL-7B-Instruct"

JOYCAPTION_PROMPTS = {
    "descriptive": "Write a long descriptive caption for this image in a formal tone.",
    "straightforward": "Write a straightforward caption for this image.",
    "training": "Write a stable diffusion prompt for this image.",
}

QWEN_SYSTEM_PROMPT = """You are an expert image-to-prompt converter specialized for text-to-image AI models.

Analyze the given image and generate a descriptive English prompt following this exact structure:

[Subject & Action] + [Visual Style] + [Lighting & Atmosphere] + [Technical Constraints]

Rules:
1. SUBJECT & ACTION (place first, most important):
   - Person: age, gender, ethnicity, hair (color/style/length), facial expression, eye direction, pose, body language
   - Clothing: type, color, fabric texture, condition, accessories
   - Action: what they are doing, hand positions, body orientation

2. VISUAL STYLE:
   - Medium: photorealistic / cinematic / oil painting / etc.
   - Camera: lens type, depth of field, film stock
   - Texture keywords: skin texture, fabric detail, surface imperfections, film grain

3. LIGHTING & ATMOSPHERE:
   - Light source direction and type (natural/artificial)
   - Color temperature (warm/cool/neutral)
   - Mood and overall atmosphere
   - Background description with depth

4. TECHNICAL CONSTRAINTS (place at end):
   - Quality: 8K resolution, ultra-detailed, sharp focus
   - Safety: correct anatomy, no extra limbs, no watermark

Output ONLY the prompt text. No explanations, no labels, no markdown.
Write as a single flowing paragraph, 80-250 words.
Place the most important descriptors (subject + appearance) at the very beginning."""

QWEN_REFORMAT_PROMPT = """You are a prompt engineer for Z-Image Turbo, a text-to-image AI model.

Your task: Convert the provided image description into an optimized Z-Image Turbo prompt.

Output format (single flowing paragraph, 80-250 words):
[Subject & appearance details] + [Clothing & accessories] + [Background & setting] + [Visual style & camera] + [Lighting & atmosphere] + [Quality constraints]

Rules:
- Place the most important subject descriptors FIRST (the model pays most attention to the beginning)
- Include texture keywords: skin texture, fabric detail, film grain, surface imperfections
- Include quality keywords at end: 8K resolution, sharp focus, correct anatomy, no watermark
- Use ONLY positive descriptions (no "no ugly", instead say "beautiful")
- Write as natural English prose, NOT comma-separated tags
- Do NOT use contradictory styles (e.g., "photorealistic cartoon")

Output ONLY the final prompt. No explanations."""

QWEN_SYSTEM_PROMPT_ZH = """你是一位专为文本生成图像AI模型设计的图像提示词专家。

分析给定图像，按照以下结构生成中文描述提示词：

【主体与动作】+【视觉风格】+【光线与氛围】+【技术约束】

规则：
1. 主体与动作（放在最前，最重要）：
   - 人物：年龄、性别、民族、发型（颜色/风格/长度）、面部表情、视线方向、姿势、肢体语言
   - 服装：类型、颜色、面料质感、状态、配饰
   - 动作：正在做什么、手的位置、身体朝向

2. 视觉风格：
   - 媒介：写实摄影 / 电影感 / 油画 / 等
   - 相机：镜头类型、景深、胶片种类
   - 质感关键词：皮肤质感、面料细节、表面瑕疵、胶片颗粒

3. 光线与氛围：
   - 光源方向与类型（自然光/人造光）
   - 色温（暖/冷/中性）
   - 整体情绪与氛围
   - 带有景深的背景描述

4. 技术约束（放在最后）：
   - 质量：8K分辨率、超精细、锐利对焦
   - 安全：正确解剖结构、无多余肢体、无水印

仅输出提示词文本，无需解释、无标签、无Markdown格式。
以单段连续文字书写，80-250字。
将最重要的描述词（主体+外貌）放在最前面。"""

QWEN_REFORMAT_PROMPT_ZH = """你是Z-Image Turbo文本生成图像模型的提示词工程师。

任务：将提供的图像描述转换为优化的Z-Image Turbo中文提示词。

输出格式（单段连续文字，80-250字）：
【主体与外貌细节】+【服装与配饰】+【背景与场景】+【视觉风格与相机】+【光线与氛围】+【质量约束】

规则：
- 将最重要的主体描述词放在最前（模型对开头内容关注度最高）
- 包含质感关键词：皮肤质感、面料细节、胶片颗粒、表面瑕疵
- 结尾包含质量关键词：8K分辨率、锐利对焦、正确解剖结构、无水印
- 仅使用正面描述（不用"不丑陋"，而用"美丽"）
- 以自然中文散文书写，不使用逗号分隔的标签
- 不使用矛盾风格（如"写实风格卡通"）

仅输出最终提示词，无需解释。"""

QWEN_SYSTEM_PROMPTS = {"en": QWEN_SYSTEM_PROMPT, "zh": QWEN_SYSTEM_PROMPT_ZH}
QWEN_REFORMAT_PROMPTS = {"en": QWEN_REFORMAT_PROMPT, "zh": QWEN_REFORMAT_PROMPT_ZH}


# ── 모델 로드 / 해제 ──────────────────────────────────────────────────────────

def _bnb_config(quant: str):
    from transformers import BitsAndBytesConfig
    import torch
    if quant == "nf4":
        return BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
        )
    return None  # bf16


def _local_model_path(repo_id: str) -> str:
    from huggingface_hub import snapshot_download

    return snapshot_download(repo_id=repo_id, local_files_only=True)


def _materialize_chat_template(snapshot_path: str):
    snapshot_dir = Path(snapshot_path)
    jinja_path = snapshot_dir / "chat_template.jinja"
    if jinja_path.exists():
        return

    json_path = snapshot_dir / "chat_template.json"
    if not json_path.exists():
        return

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception:
        return

    template = data.get("chat_template")
    if isinstance(template, str) and template.strip():
        jinja_path.write_text(template, encoding="utf-8")


def _model_device(model):
    try:
        return next(model.parameters()).device
    except StopIteration:
        import torch
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _move_inputs_to_model(inputs, model):
    import torch

    device = _model_device(model)
    dtype = None
    if device.type == "cuda":
        dtype = torch.bfloat16

    moved = {}
    for key, value in inputs.items():
        if hasattr(value, "to"):
            kwargs = {"device": device}
            if dtype is not None and torch.is_floating_point(value):
                kwargs["dtype"] = dtype
            moved[key] = value.to(**kwargs)
        else:
            moved[key] = value
    return moved


def _fix_mha_quantization(model):
    """nf4 양자화 후 nn.MultiheadAttention.out_proj 수정.

    F.multi_head_attention_forward는 out_proj.weight를 직접 접근하여
    Linear4bit의 역양자화 경로를 우회한다. 해당 레이어를 bf16으로 교체한다.
    (transformers 5.x + bitsandbytes 0.49.x 호환 픽스)
    """
    import torch
    try:
        import bitsandbytes as bnb
        import bitsandbytes.functional as bnb_F
    except ImportError:
        return

    for module in model.modules():
        if not isinstance(module, torch.nn.MultiheadAttention):
            continue
        proj = module.out_proj
        if not isinstance(proj, bnb.nn.Linear4bit):
            continue
        with torch.no_grad():
            w = bnb_F.dequantize_4bit(proj.weight, proj.weight.quant_state).to(torch.bfloat16)
            device = w.device
            bias = proj.bias
            new = torch.nn.Linear(
                proj.in_features, proj.out_features,
                bias=bias is not None, dtype=torch.bfloat16, device=device,
            )
            new.weight = torch.nn.Parameter(w)
            if bias is not None:
                new.bias = torch.nn.Parameter(bias.to(torch.bfloat16))
            module.out_proj = new


def load_joycaption(quant: str = "nf4"):
    import torch
    from transformers import AutoProcessor, LlavaForConditionalGeneration

    print(f"[로드] JoyCaption Beta One ({quant}) ...")
    model_path = _local_model_path(JOYCAPTION_MODEL)
    _materialize_chat_template(model_path)
    kwargs = {"device_map": "auto", "local_files_only": True}
    if quant == "nf4":
        kwargs["quantization_config"] = _bnb_config("nf4")
    else:
        kwargs["torch_dtype"] = torch.bfloat16

    processor = AutoProcessor.from_pretrained(model_path, local_files_only=True, use_fast=False)
    model = LlavaForConditionalGeneration.from_pretrained(model_path, **kwargs)
    if quant == "nf4":
        _fix_mha_quantization(model)
    model.eval()
    return model, processor


def load_qwen(quant: str = "nf4"):
    import torch
    from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor

    print(f"[로드] Qwen2.5-VL-7B ({quant}) ...")
    model_path = _local_model_path(QWEN_MODEL)
    _materialize_chat_template(model_path)
    kwargs = {"device_map": "auto", "local_files_only": True}
    if quant == "nf4":
        kwargs["quantization_config"] = _bnb_config("nf4")
    else:
        kwargs["torch_dtype"] = torch.bfloat16

    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(model_path, **kwargs)
    processor = AutoProcessor.from_pretrained(
        model_path,
        local_files_only=True,
        min_pixels=256 * 28 * 28,
        max_pixels=1280 * 28 * 28,
    )
    return model, processor


def unload(model, processor):
    del model, processor
    gc.collect()
    try:
        import torch
        torch.cuda.empty_cache()
    except Exception:
        pass
    print("[해제] 모델 VRAM 해제 완료")


# ── 방식 1: JoyCaption ────────────────────────────────────────────────────────

def run_joycaption(image_path: str, model, processor, mode: str = "descriptive") -> str:
    import torch
    from PIL import Image

    image = Image.open(image_path).convert("RGB")
    prompt_text = JOYCAPTION_PROMPTS.get(mode, JOYCAPTION_PROMPTS["descriptive"])

    convo = [
        {"role": "system", "content": JOYCAPTION_SYSTEM},
        {"role": "user", "content": prompt_text},
    ]
    convo_str = processor.apply_chat_template(convo, tokenize=False, add_generation_prompt=True)
    inputs = processor(text=[convo_str], images=[image], return_tensors="pt")
    inputs = _move_inputs_to_model(inputs, model)

    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=True,
            temperature=0.6,
            top_p=0.9,
        )[0]

    output = output[inputs["input_ids"].shape[1]:]
    return processor.tokenizer.decode(output, skip_special_tokens=True).strip()


# ── 방식 2: Qwen2.5-VL ───────────────────────────────────────────────────────

def run_qwen(image_path: str, model, processor, lang: str = "en") -> str:
    import os
    import tempfile
    import torch
    from PIL import Image
    from qwen_vl_utils import process_vision_info

    # HEIC는 file:// URI로 처리 불가 → 임시 JPEG로 변환
    suffix = Path(image_path).suffix.lower()
    tmp_path = None
    if suffix in {".heic", ".heif"}:
        pil_img = Image.open(image_path).convert("RGB")
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        pil_img.save(tmp.name, "JPEG", quality=95)
        tmp_path = tmp.name
        actual_path = tmp_path
    else:
        actual_path = image_path

    user_text = "为这张图像生成Z-Image Turbo提示词。" if lang == "zh" else "Generate a Z-Image Turbo prompt for this image."
    try:
        messages = [
            {"role": "system", "content": QWEN_SYSTEM_PROMPTS[lang]},
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": f"file://{actual_path}"},
                    {"type": "text", "text": user_text},
                ],
            },
        ]

        text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )
        inputs = _move_inputs_to_model(inputs, model)

        with torch.no_grad():
            generated_ids = model.generate(
                **inputs,
                max_new_tokens=512,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
            )

        trimmed = [out[len(inp):] for inp, out in zip(inputs["input_ids"], generated_ids)]
        return processor.batch_decode(trimmed, skip_special_tokens=True)[0].strip()
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


# ── 방식 3 Step2: Qwen 재형식화 ──────────────────────────────────────────────

def run_qwen_reformat(raw_caption: str, model, processor, lang: str = "en") -> str:
    import torch

    user_text = (
        f"将以下图像描述转换为Z-Image Turbo提示词：\n\n{raw_caption}"
        if lang == "zh"
        else f"Convert this image description into a Z-Image Turbo prompt:\n\n{raw_caption}"
    )
    messages = [
        {"role": "system", "content": QWEN_REFORMAT_PROMPTS[lang]},
        {"role": "user", "content": user_text},
    ]

    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(text=[text], return_tensors="pt")
    inputs = _move_inputs_to_model(inputs, model)

    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=True,
            temperature=0.5,
            top_p=0.9,
        )

    trimmed = [out[len(inp):] for inp, out in zip(inputs["input_ids"], generated_ids)]
    return processor.batch_decode(trimmed, skip_special_tokens=True)[0].strip()


# ── 결과 저장 ─────────────────────────────────────────────────────────────────

def save_prompt(image_path: str, prompt: str, output_dir: Path, suffix: str = ""):
    """이미지별 개별 .txt 저장"""
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(image_path).stem
    fname = f"{stem}{suffix}.txt"
    (output_dir / fname).write_text(prompt, encoding="utf-8")
    return output_dir / fname


def append_prompt(image_path: str, prompt: str, accum_file: Path):
    """누적 .txt 에 프롬프트 추가 (프롬프트 사이 빈 줄 한 줄)"""
    accum_file.parent.mkdir(parents=True, exist_ok=True)
    is_empty = not accum_file.exists() or accum_file.stat().st_size == 0
    with accum_file.open("a", encoding="utf-8") as f:
        if not is_empty:
            f.write("\n")
        f.write(prompt + "\n")
    return accum_file


def print_result(image_path: str, prompt: str, label: str = "프롬프트"):
    print(f"\n{'─'*60}")
    print(f"[{label}] {Path(image_path).name}")
    print('─'*60)
    print(prompt)
    print('─'*60)


# ── 재개 지원 헬퍼 ────────────────────────────────────────────────────────────

def _count_prompts(accum_file: Path) -> int:
    """누적 파일에 저장된 프롬프트 수 반환. 파일이 없으면 0."""
    if not accum_file.exists() or accum_file.stat().st_size == 0:
        return 0
    lines = accum_file.read_text(encoding="utf-8").splitlines()
    return (len(lines) + 1) // 2


def _read_prompts(accum_file: Path) -> list:
    """누적 파일에서 프롬프트 목록을 순서대로 반환."""
    if not accum_file.exists() or accum_file.stat().st_size == 0:
        return []
    content = accum_file.read_text(encoding="utf-8")
    return [p.strip() for p in content.split("\n\n") if p.strip()]


def _already_done(img: str, args, suffix: str = "") -> bool:
    """개별 저장 모드에서 출력 파일이 이미 존재하는지 확인."""
    if not args.output_dir or args.accumulate:
        return False
    return (Path(args.output_dir) / f"{Path(img).stem}{suffix}.txt").exists()


def _read_individual(img: str, args, suffix: str = "") -> str:
    """개별 저장 모드에서 이미 저장된 프롬프트를 읽어 반환."""
    return (Path(args.output_dir) / f"{Path(img).stem}{suffix}.txt").read_text(encoding="utf-8").strip()


# ── 방식별 실행 ───────────────────────────────────────────────────────────────

def _save(img: str, prompt: str, args, suffix: str = ""):
    """개별 저장 또는 누적 저장 분기"""
    if not args.output_dir:
        return
    out = Path(args.output_dir)
    if args.accumulate:
        fname = f"prompts{suffix}.txt"
        p = append_prompt(img, prompt, out / fname)
        print(f"  누적: {p}")
    else:
        p = save_prompt(img, prompt, out, suffix)
        print(f"  저장: {p}")


def run_method1(images: list[str], args):
    total = len(images)

    # 누적 모드: 완료된 이미지 수만큼 건너뜀
    if args.output_dir and args.accumulate:
        done = _count_prompts(Path(args.output_dir) / "prompts.txt")
        if done:
            print(f"[재개] {done}/{total}개 완료 — {Path(images[done]).name}부터 재개")
            images = images[done:]

    model, processor = load_joycaption(args.quant)
    for i, img in enumerate(images, total - len(images) + 1):
        # 개별 모드: 파일이 이미 존재하면 건너뜀
        if _already_done(img, args):
            print(f"\n[건너뜀 {i}/{total}] {Path(img).name}")
            continue
        print(f"\n[{i}/{total}] {Path(img).name}")
        t = time.time()
        prompt = run_joycaption(img, model, processor, mode=args.mode)
        print(f"  완료 ({time.time()-t:.1f}초)")
        print_result(img, prompt, label="JoyCaption")
        _save(img, prompt, args)
    unload(model, processor)


def run_method2(images: list[str], args):
    total = len(images)

    # 누적 모드: 완료된 이미지 수만큼 건너뜀
    if args.output_dir and args.accumulate:
        done = _count_prompts(Path(args.output_dir) / "prompts.txt")
        if done:
            print(f"[재개] {done}/{total}개 완료 — {Path(images[done]).name}부터 재개")
            images = images[done:]

    model, processor = load_qwen(args.quant)
    for i, img in enumerate(images, total - len(images) + 1):
        # 개별 모드: 파일이 이미 존재하면 건너뜀
        if _already_done(img, args):
            print(f"\n[건너뜀 {i}/{total}] {Path(img).name}")
            continue
        print(f"\n[{i}/{total}] {Path(img).name}")
        t = time.time()
        prompt = run_qwen(img, model, processor, lang=args.lang)
        print(f"  완료 ({time.time()-t:.1f}초)")
        print_result(img, prompt, label="Qwen → Z-Image")
        _save(img, prompt, args)
    unload(model, processor)


def run_method3(images: list[str], args):
    total = len(images)
    out = Path(args.output_dir) if args.output_dir else None

    # ── 재개 지점 계산 ──────────────────────────────────────────────────────
    raw_done, final_done = 0, 0
    if out and args.accumulate:
        raw_done = _count_prompts(out / "prompts_raw.txt")
        final_done = _count_prompts(out / "prompts_final.txt")
        if raw_done:
            print(f"[재개] prompts_raw.txt: {raw_done}/{total}개 완료")
        if final_done:
            print(f"[재개] prompts_final.txt: {final_done}/{total}개 완료")

    # ── Pass 1: JoyCaption ──────────────────────────────────────────────────
    raws = []  # (img, raw) 전체 목록 — Pass 2에서 사용

    if out and args.accumulate and raw_done >= total:
        # Pass 1 완전 완료 → 파일에서 복원, 모델 로드 불필요
        print(f"\n[Pass 1/2] 완료 — prompts_raw.txt에서 {total}개 복원")
        raws = list(zip(images, _read_prompts(out / "prompts_raw.txt")))
    else:
        print(f"\n[Pass 1/2] JoyCaption — {total}개 이미지")
        # 누적 모드: 이미 완료된 부분을 파일에서 복원
        if raw_done:
            raws = list(zip(images[:raw_done], _read_prompts(out / "prompts_raw.txt")))
            print(f"  → {raw_done}개 복원, {Path(images[raw_done]).name}부터 재개")

        joy_model, joy_proc = load_joycaption(args.quant)
        for i, img in enumerate(images[raw_done:] if raw_done else images, raw_done + 1):
            # 개별 모드: _raw.txt 존재 시 파일에서 읽고 건너뜀
            if _already_done(img, args, suffix="_raw"):
                raw = _read_individual(img, args, suffix="_raw")
                raws.append((img, raw))
                print(f"\n[건너뜀 {i}/{total}] {Path(img).name}")
                continue
            print(f"\n[{i}/{total}] {Path(img).name}")
            t = time.time()
            raw = run_joycaption(img, joy_model, joy_proc, mode=args.mode)
            print(f"  완료 ({time.time()-t:.1f}초)")
            print_result(img, raw, label="1차 캡션 (JoyCaption)")
            _save(img, raw, args, suffix="_raw")
            raws.append((img, raw))
        unload(joy_model, joy_proc)

    # ── Pass 2: Qwen 변환 ───────────────────────────────────────────────────
    pass2_raws = raws[final_done:] if final_done else raws
    print(f"\n[Pass 2/2] Qwen 변환 — {total}개")
    if final_done:
        print(f"  → {final_done}개 완료, {Path(pass2_raws[0][0]).name}부터 재개")

    qwen_model, qwen_proc = load_qwen(args.quant)
    for i, (img, raw) in enumerate(pass2_raws, final_done + 1):
        # 개별 모드: _final.txt 존재 시 건너뜀
        if _already_done(img, args, suffix="_final"):
            print(f"\n[건너뜀 {i}/{total}] {Path(img).name}")
            continue
        print(f"\n[{i}/{total}] {Path(img).name}")
        t = time.time()
        final = run_qwen_reformat(raw, qwen_model, qwen_proc, lang=args.lang)
        print(f"  완료 ({time.time()-t:.1f}초)")
        print_result(img, final, label="최종 프롬프트 (Z-Image Turbo)")
        _save(img, final, args, suffix="_final")
    unload(qwen_model, qwen_proc)


# ── 메인 ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Z-Image Turbo 프롬프트 생성기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
방식 설명:
  1  JoyCaption Beta One 단독   -- 안정적, 배치 처리에 적합
  2  Qwen2.5-VL-7B 단독        -- Z-Image 4-Layer 형식 직접 지정 (기본값)
  3  JoyCaption + Qwen 파이프라인 -- 최고 품질, 속도 느림
        """
    )
    parser.add_argument("input", help="이미지 파일 또는 폴더 경로")
    parser.add_argument(
        "--method", "-m", type=int, choices=[1, 2, 3], default=2,
        help="생성 방식 선택 (기본: 2)"
    )
    parser.add_argument(
        "--mode", default="descriptive",
        choices=["descriptive", "straightforward", "training"],
        help="JoyCaption 캡션 타입 (방식 1·3, 기본: descriptive)"
    )
    parser.add_argument(
        "--quant", default="nf4", choices=["nf4", "bf16"],
        help="양자화 방식 (기본: nf4 / bf16은 VRAM 17GB+ 필요)"
    )
    parser.add_argument(
        "--output-dir", "-o",
        help="프롬프트 .txt 저장 폴더 (미지정 시 출력만)"
    )
    parser.add_argument(
        "--accumulate", "-a", action="store_true",
        help="폴더 처리 시 개별 저장 대신 하나의 .txt 에 누적 (프롬프트 사이 빈 줄)"
    )
    parser.add_argument(
        "--lang", default="en", choices=["en", "zh"],
        help="출력 언어 (기본: en / zh: 중국어, 방식 2·3에서만 적용)"
    )
    args = parser.parse_args()

    # 입력 경로 처리
    input_path = Path(args.input)
    if input_path.is_file():
        images = [str(input_path)]
    elif input_path.is_dir():
        images = sorted(
            str(f) for f in input_path.iterdir()
            if f.suffix.lower() in IMAGE_EXTENSIONS
        )
        if not images:
            print(f"오류: {input_path} 에서 이미지를 찾을 수 없습니다.")
            return
    else:
        print(f"오류: {input_path} 가 존재하지 않습니다.")
        return

    method_names = {1: "JoyCaption Beta One", 2: "Qwen2.5-VL-7B", 3: "JoyCaption + Qwen 파이프라인"}
    lang_names = {"en": "영어", "zh": "중국어"}
    print(f"=== Z-Image Turbo 프롬프트 생성 ===")
    print(f"방식  : {args.method} - {method_names[args.method]}")
    print(f"양자화: {args.quant}")
    print(f"언어  : {lang_names[args.lang]}" + (" (방식 1은 항상 영어)" if args.method == 1 and args.lang != "en" else ""))
    print(f"이미지: {len(images)}개")
    if args.output_dir:
        save_mode = "누적 (prompts.txt)" if args.accumulate else "개별 (.txt per image)"
        print(f"저장  : {args.output_dir}  [{save_mode}]")
    print()

    start = time.time()

    if args.method == 1:
        run_method1(images, args)
    elif args.method == 2:
        run_method2(images, args)
    else:
        run_method3(images, args)

    elapsed = time.time() - start
    print(f"\n=== 완료: 총 {len(images)}개, {elapsed:.1f}초 ({elapsed/len(images):.1f}초/이미지) ===")


if __name__ == "__main__":
    main()
