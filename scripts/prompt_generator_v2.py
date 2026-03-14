#!/usr/bin/env python3
"""
prompt_generator_v2.py — Z-Image Turbo 프롬프트 생성 (v2)

사용법:
  python3 prompt_generator_v2.py <입력폴더> -o <출력폴더> [옵션]

메소드:
  1 - JoyCaption (영어 전용, raw 캡션)
  2 - Qwen3-VL-8B 직접 이미지 분석
  3 - Qwen3.5-9B 직접 이미지 분석
  4 - JoyCaption raw → Qwen3-VL-8B 정제 (2-pass)
  5 - JoyCaption raw → Qwen3.5-9B 정제 (2-pass)

출력:
  <출력폴더>/prompts_raw.txt  - JoyCaption raw 캡션 (method 1, 4, 5)
  <출력폴더>/prompts.txt      - 최종 프롬프트 (전 method)
"""

import sys
import os
from pathlib import Path

_VENV_DIR = Path(__file__).resolve().parent.parent / "venv-prompt"
if _VENV_DIR.exists() and Path(sys.prefix) != _VENV_DIR:
    _VENV_PYTHON = _VENV_DIR / "bin" / "python3"
    os.execv(str(_VENV_PYTHON), [str(_VENV_PYTHON)] + sys.argv)

import argparse
import time
import gc

# ──────────────────────────────────────────────
# 모델 ID
# ──────────────────────────────────────────────
MODEL_JOYCAPTION = "fancyfeast/llama-joycaption-beta-one-hf-llava"
MODEL_QWEN3VL    = "Qwen/Qwen3-VL-8B-Instruct"
MODEL_QWEN35     = "Qwen/Qwen3.5-9B"
MODEL_QWEN3VL_AB = "huihui-ai/Huihui-Qwen3-VL-8B-Instruct-abliterated"
MODEL_QWEN35_AB  = "huihui-ai/Huihui-Qwen3.5-9B-abliterated"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif", ".heic", ".heif"}

# ──────────────────────────────────────────────
# 시스템 프롬프트 — 직접 이미지 분석 (method 2, 3)
# ──────────────────────────────────────────────
SYSTEM_PROMPT_EN = """You are an expert in interpreting precise visual scenes. Analyze the image and produce a refined, high-fidelity English prompt tailored to its primary subject (person, architectural space, natural landscape, or still-life object).

If the scene depicts architecture or interior space, describe the architectural style, structural elements, materials, and spatial depth accurately. Do not invent human presence.

If the image represents a product or still-life object, emphasize surface qualities, material reflections, textures, color harmony, and physical arrangement.

Only if people are clearly visible should you describe the following in detail. If no people exist, omit all human-related language entirely.

For clothing: garment type and style, neckline shape and depth, sleeve length and cut, hemline length, any cutouts or sheer and transparent panels, areas of bare skin exposure, fabric texture and material (e.g., satin, lace, cotton), colors and patterns, and all accessories including shoes, bags, jewelry, and hair accessories.

For pose: overall body orientation (facing camera, angled, turned away), head tilt and exact gaze direction, shoulder position, arm and hand placement (e.g., arms raised, hands on hips, holding an object), leg stance (standing straight, one leg forward, seated, crossed), and any body lean or weight shift.

Explain the lighting conditions, including the type of light source, shadow behavior, contrast, and atmospheric mood.

Describe composition and camera perspective, such as framing balance, lens choice, depth of field, and viewpoint.

Write a single, natural English paragraph of 80–250 words. Avoid references to watermarks, symbols, or irrelevant text."""

SYSTEM_PROMPT_ZH = """你是专业的图像视觉分析专家，为文生图模型生成精准的中文提示词。分析图像，根据主要主题（人物、建筑空间、自然风景或静物）输出高保真提示词。

若为建筑或室内空间：描述建筑风格、结构元素、材质及空间层次感，不虚构人物。
若为产品或静物：重点描述表面质感、材质反光、纹理、色彩搭配及物品排列。
若画面中有清晰可见的人物，详细描述以下内容；若无人物则完全省略人物描述：

服装细节：服装类型与款式、领口形状与深度、袖长与剪裁、裙摆或裤腿长度、镂空或透视薄纱区域、裸露肌肤范围（含腿部丝袜或裸腿的区分）、面料质感与材质（缎面、蕾丝、棉质、针织、丝袜等）、颜色与花纹、全部配饰（鞋履、包袋、耳环、项链、手链、脚链、发饰等）。

姿势与体态：整体身体朝向（正对/侧身/背对镜头）、头部倾斜角度与视线方向、肩部位置与角度、手臂及手部动作（上举、叉腰、持物、触碰身体部位等）、腿部姿态（站立、坐姿、交叉腿、单腿前伸）、身体重心偏移方向、体态曲线与轮廓走势。

光线：光源类型与方向、阴影形态、色温、对比度与氛围。
构图：景别（特写/近景/半身/全身）、拍摄角度、景深与背景虚化。

用单段流畅自然的中文输出，字数150至400字，不提及水印、符号或无关文字。"""

# ──────────────────────────────────────────────
# 정제 프롬프트 — JoyCaption raw → 최종 프롬프트 (method 4, 5)
# ──────────────────────────────────────────────
REFINE_PROMPT_EN = """Below is a detailed image description. Based on this description, generate a refined English prompt for the Z-Image Turbo text-to-image model.

Requirements:
- Preserve all clothing details, pose descriptions, skin exposure, and accessories exactly as described
- Order by importance: subject → clothing & skin exposure → pose & body orientation → lighting & composition
- Write a single, natural English paragraph of 80–250 words
- Avoid references to watermarks, symbols, or irrelevant text

[Image Description]
{raw}"""

REFINE_PROMPT_ZH = """以下是对图像的详细英文描述。基于此描述，生成一段精准的中文提示词，用于文生图模型Z-Image Turbo。

要求：
- 完整保留所有服装细节、皮肤裸露程度、姿势描述和配饰信息
- 按重要性排序：主体 → 服装与裸露区域 → 姿势体态 → 光线构图
- 用单段流畅自然的中文输出，字数150至400字
- 不提及水印、符号或无关文字

[图像描述]
{raw}"""


# ──────────────────────────────────────────────
# 양자화 설정
# ──────────────────────────────────────────────
def _bnb_nf4():
    from transformers import BitsAndBytesConfig
    import torch
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

def _bnb_int8():
    from transformers import BitsAndBytesConfig
    return BitsAndBytesConfig(load_in_8bit=True)


# ──────────────────────────────────────────────
# JoyCaption 로더 / 추론
# ──────────────────────────────────────────────
def load_joycaption(quant: str = "bf16"):
    import torch
    from transformers import AutoProcessor, LlavaForConditionalGeneration

    print(f"[로드] JoyCaption ({quant}) ...")
    t = time.time()
    kwargs = {"device_map": "auto"}
    if quant == "nf4":
        kwargs["quantization_config"] = _bnb_nf4()
    elif quant == "int8":
        kwargs["quantization_config"] = _bnb_int8()
    else:
        kwargs["torch_dtype"] = torch.bfloat16

    model = LlavaForConditionalGeneration.from_pretrained(MODEL_JOYCAPTION, **kwargs)
    processor = AutoProcessor.from_pretrained(MODEL_JOYCAPTION, use_fast=False)
    model.eval()

    # nf4: MultiheadAttention.out_proj 패치
    if quant == "nf4":
        import torch.nn as nn
        from bitsandbytes.nn import Linear4bit
        for module in model.modules():
            if isinstance(module, nn.MultiheadAttention):
                op = module.out_proj
                if isinstance(op, Linear4bit):
                    new = nn.Linear(op.in_features, op.out_features, bias=op.bias is not None)
                    new.weight = nn.Parameter(op.weight.dequantize().to(torch.bfloat16))
                    if op.bias is not None:
                        new.bias = nn.Parameter(op.bias.to(torch.bfloat16))
                    module.out_proj = new.to(next(model.parameters()).device)

    print(f"  로드 완료 ({time.time() - t:.1f}초)")
    return model, processor


def run_joycaption(image_path: str, model, processor) -> str:
    import torch
    from PIL import Image

    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
    except ImportError:
        pass

    pil_image = Image.open(image_path).convert("RGB")
    # v1 검증 방식: content는 plain str, processor에 text=list로 전달
    convo = [
        {"role": "system", "content": "You are a helpful image captioner."},
        {"role": "user", "content": (
            "Write a descriptive caption for this image in a formal tone. "
            "Describe the subject, clothing (including neckline, fabric, skin exposure), "
            "pose and body orientation, accessories, lighting, and composition."
        )},
    ]
    convo_str = processor.apply_chat_template(convo, tokenize=False, add_generation_prompt=True)
    inputs = processor(text=[convo_str], images=[pil_image], return_tensors="pt")
    inputs = {k: v.to(model.device) if hasattr(v, "to") else v for k, v in inputs.items()}

    with torch.no_grad():
        output = model.generate(**inputs, max_new_tokens=512, do_sample=True, temperature=0.6, top_p=0.9)[0]

    output = output[inputs["input_ids"].shape[1]:]
    return processor.tokenizer.decode(output, skip_special_tokens=True).strip()


# ──────────────────────────────────────────────
# Qwen3-VL-8B 로더 / 추론
# ──────────────────────────────────────────────
def load_qwen3vl(quant: str = "bf16", model_id: str = MODEL_QWEN3VL):
    import torch
    from transformers import Qwen3VLForConditionalGeneration, AutoProcessor

    label = model_id.split("/")[-1]
    print(f"[로드] {label} ({quant}) ...")
    t = time.time()
    kwargs = {"device_map": "auto"}
    if quant == "nf4":
        kwargs["quantization_config"] = _bnb_nf4()
    elif quant == "int8":
        kwargs["quantization_config"] = _bnb_int8()
    else:
        kwargs["torch_dtype"] = torch.bfloat16

    model = Qwen3VLForConditionalGeneration.from_pretrained(model_id, **kwargs)
    processor = AutoProcessor.from_pretrained(model_id)
    model.eval()
    print(f"  로드 완료 ({time.time() - t:.1f}초)")
    return model, processor


def run_qwen3vl_image(image_path: str, model, processor, lang: str = "en") -> str:
    """이미지 직접 분석 (method 2)"""
    import torch
    from PIL import Image

    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
    except ImportError:
        pass

    pil_image = Image.open(image_path).convert("RGB")
    prompt = SYSTEM_PROMPT_ZH if lang == "zh" else SYSTEM_PROMPT_EN
    messages = [{"role": "user", "content": [
        {"type": "image", "image": pil_image},
        {"type": "text", "text": prompt},
    ]}]

    inputs = processor.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True,
        return_dict=True, return_tensors="pt",
    )
    inputs = inputs.to(model.device)

    with torch.no_grad():
        generated_ids = model.generate(
            **inputs, max_new_tokens=1024, do_sample=True, temperature=0.7, top_p=0.9,
        )

    trimmed = [out[len(inp):] for inp, out in zip(inputs.input_ids, generated_ids)]
    return processor.batch_decode(trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0].strip()


def run_qwen3vl_refine(raw_text: str, model, processor, lang: str = "en") -> str:
    """JoyCaption raw → 정제 (method 4, 이미지 없음)"""
    import torch

    template = REFINE_PROMPT_ZH if lang == "zh" else REFINE_PROMPT_EN
    prompt = template.format(raw=raw_text)
    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]

    inputs = processor.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True,
        return_dict=True, return_tensors="pt",
    )
    inputs = inputs.to(model.device)

    with torch.no_grad():
        generated_ids = model.generate(
            **inputs, max_new_tokens=1024, do_sample=True, temperature=0.7, top_p=0.9,
        )

    trimmed = [out[len(inp):] for inp, out in zip(inputs.input_ids, generated_ids)]
    return processor.batch_decode(trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0].strip()


# ──────────────────────────────────────────────
# Qwen3.5-9B 로더 / 추론
# ──────────────────────────────────────────────
def load_qwen35(quant: str = "bf16", model_id: str = MODEL_QWEN35):
    import torch
    from transformers import Qwen3_5ForConditionalGeneration, AutoProcessor

    label = model_id.split("/")[-1]
    print(f"[로드] {label} ({quant}) ...")
    t = time.time()
    kwargs = {"device_map": "auto"}
    if quant == "nf4":
        kwargs["quantization_config"] = _bnb_nf4()
    elif quant == "int8":
        kwargs["quantization_config"] = _bnb_int8()
    else:
        kwargs["torch_dtype"] = torch.bfloat16

    model = Qwen3_5ForConditionalGeneration.from_pretrained(model_id, **kwargs)
    processor = AutoProcessor.from_pretrained(model_id)
    model.eval()
    print(f"  로드 완료 ({time.time() - t:.1f}초)")
    return model, processor


def _qwen35_inputs(messages, processor, model):
    import torch
    inputs = processor.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True,
        return_dict=True, enable_thinking=False, return_tensors="pt",
    )
    return {k: v.to(model.device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}


def run_qwen35_image(image_path: str, model, processor, lang: str = "en") -> str:
    """이미지 직접 분석 (method 3)"""
    import torch
    from PIL import Image

    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
    except ImportError:
        pass

    pil_image = Image.open(image_path).convert("RGB")
    prompt = SYSTEM_PROMPT_ZH if lang == "zh" else SYSTEM_PROMPT_EN
    messages = [{"role": "user", "content": [
        {"type": "image", "image": pil_image},
        {"type": "text", "text": prompt},
    ]}]

    inputs = _qwen35_inputs(messages, processor, model)
    with torch.no_grad():
        generated_ids = model.generate(
            **inputs, max_new_tokens=1024, do_sample=True, temperature=0.7, top_p=0.9,
        )

    trimmed = [out[len(inp):] for inp, out in zip(inputs["input_ids"], generated_ids)]
    result = processor.batch_decode(trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0].strip()

    import re
    if "<think>" in result:
        result = re.sub(r"<think>.*?</think>", "", result, flags=re.DOTALL).strip()
    return result


def run_qwen35_refine(raw_text: str, model, processor, lang: str = "en") -> str:
    """JoyCaption raw → 정제 (method 5, 이미지 없음)"""
    import torch

    template = REFINE_PROMPT_ZH if lang == "zh" else REFINE_PROMPT_EN
    prompt = template.format(raw=raw_text)
    messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]

    inputs = _qwen35_inputs(messages, processor, model)
    with torch.no_grad():
        generated_ids = model.generate(
            **inputs, max_new_tokens=1024, do_sample=True, temperature=0.7, top_p=0.9,
        )

    trimmed = [out[len(inp):] for inp, out in zip(inputs["input_ids"], generated_ids)]
    result = processor.batch_decode(trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0].strip()

    import re
    if "<think>" in result:
        result = re.sub(r"<think>.*?</think>", "", result, flags=re.DOTALL).strip()
    return result


# ──────────────────────────────────────────────
# 모델 해제
# ──────────────────────────────────────────────
def unload(model, processor):
    import torch
    del model, processor
    gc.collect()
    try:
        torch.cuda.empty_cache()
        free = torch.cuda.mem_get_info()[0] / 1024**3
        print(f"[해제] VRAM 여유: {free:.1f} GB")
    except Exception:
        pass


# ──────────────────────────────────────────────
# 누적/재개 헬퍼
# ──────────────────────────────────────────────
def _count_prompts(filepath: Path) -> int:
    if not filepath.exists():
        return 0
    text = filepath.read_text(encoding="utf-8").strip()
    if not text:
        return 0
    return len([p for p in text.split("\n\n") if p.strip()])


def _read_prompts(filepath: Path) -> list:
    text = filepath.read_text(encoding="utf-8").strip()
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def _clear_file(filepath: Path):
    """비-accumulate 모드: 기존 파일 초기화"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text("", encoding="utf-8")


def _append_prompt(filepath: Path, prompt: str, index: int):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "a", encoding="utf-8") as f:
        if index > 0:
            f.write("\n")
        f.write(prompt + "\n")


def _vram_info() -> str:
    try:
        import torch
        used = torch.cuda.memory_allocated() / 1024**3
        return f"{used:.1f} GB"
    except Exception:
        return "N/A"


# ──────────────────────────────────────────────
# 메소드 실행기
# ──────────────────────────────────────────────
def run_method1(images: list, args):
    """JoyCaption → prompts.txt (영어 전용)"""
    out_dir = Path(args.output_dir)
    out_file = out_dir / "prompts.txt"
    raw_file = out_dir / "prompts_raw.txt"

    if not args.accumulate:
        _clear_file(out_file)
        _clear_file(raw_file)
    done = _count_prompts(out_file) if args.accumulate else 0
    if done:
        print(f"[재개] {done}/{len(images)}장 완료 — {Path(images[done]).name}부터 재개")
    images = images[done:]

    model, processor = load_joycaption(args.quant)
    print(f"VRAM: {_vram_info()}\n")

    timings = []
    for i, img_path in enumerate(images, done):
        print(f"[{i+1}/{len(images)+done}] {Path(img_path).name}")
        t = time.time()
        try:
            result = run_joycaption(img_path, model, processor)
            elapsed = time.time() - t
            timings.append(elapsed)
            print(f"  완료 ({elapsed:.1f}초) | {len(result.split())}단어")
            print(f"  {result[:120]}{'...' if len(result) > 120 else ''}")
            _append_prompt(out_file, result, i)
            _append_prompt(raw_file, result, i)
        except Exception as e:
            print(f"  오류: {e}")

    unload(model, processor)
    _print_stats(timings, len(images) + done)


def run_method2(images: list, args):
    """Qwen3-VL-8B 직접 이미지 분석 → prompts.txt"""
    out_dir = Path(args.output_dir)
    out_file = out_dir / "prompts.txt"

    if not args.accumulate:
        _clear_file(out_file)
    done = _count_prompts(out_file) if args.accumulate else 0
    if done:
        print(f"[재개] {done}/{len(images)}장 완료 — {Path(images[done]).name}부터 재개")
    images = images[done:]

    model, processor = load_qwen3vl(args.quant)
    print(f"VRAM: {_vram_info()}\n")

    timings = []
    for i, img_path in enumerate(images, done):
        print(f"[{i+1}/{len(images)+done}] {Path(img_path).name}")
        t = time.time()
        try:
            result = run_qwen3vl_image(img_path, model, processor, lang=args.lang)
            elapsed = time.time() - t
            timings.append(elapsed)
            print(f"  완료 ({elapsed:.1f}초) | {len(result.split())}단어")
            print(f"  {result[:120]}{'...' if len(result) > 120 else ''}")
            _append_prompt(out_file, result, i)
        except Exception as e:
            print(f"  오류: {e}")

    unload(model, processor)
    _print_stats(timings, len(images) + done)


def run_method3(images: list, args):
    """Qwen3.5-9B 직접 이미지 분석 → prompts.txt"""
    out_dir = Path(args.output_dir)
    out_file = out_dir / "prompts.txt"

    if not args.accumulate:
        _clear_file(out_file)
    done = _count_prompts(out_file) if args.accumulate else 0
    if done:
        print(f"[재개] {done}/{len(images)}장 완료 — {Path(images[done]).name}부터 재개")
    images = images[done:]

    model, processor = load_qwen35(args.quant)
    print(f"VRAM: {_vram_info()}\n")

    timings = []
    for i, img_path in enumerate(images, done):
        print(f"[{i+1}/{len(images)+done}] {Path(img_path).name}")
        t = time.time()
        try:
            result = run_qwen35_image(img_path, model, processor, lang=args.lang)
            elapsed = time.time() - t
            timings.append(elapsed)
            print(f"  완료 ({elapsed:.1f}초) | {len(result.split())}단어")
            print(f"  {result[:120]}{'...' if len(result) > 120 else ''}")
            _append_prompt(out_file, result, i)
        except Exception as e:
            print(f"  오류: {e}")

    unload(model, processor)
    _print_stats(timings, len(images) + done)


def run_method4(images: list, args):
    """JoyCaption raw → Qwen3-VL-8B 정제 (2-pass)"""
    out_dir = Path(args.output_dir)
    raw_file = out_dir / "prompts_raw.txt"
    out_file = out_dir / "prompts.txt"
    total = len(images)

    if not args.accumulate:
        _clear_file(raw_file)
        _clear_file(out_file)
    # ── Pass 1: JoyCaption raw 생성 ──
    raw_done = _count_prompts(raw_file) if args.accumulate else 0
    if raw_done < total:
        print(f"\n[Pass 1/2] JoyCaption raw 생성 ({raw_done}/{total} 완료)")
        imgs_p1 = images[raw_done:]
        joy_model, joy_proc = load_joycaption(args.quant)
        print(f"VRAM: {_vram_info()}\n")

        timings = []
        for i, img_path in enumerate(imgs_p1, raw_done):
            print(f"  [{i+1}/{total}] {Path(img_path).name}")
            t = time.time()
            try:
                raw = run_joycaption(img_path, joy_model, joy_proc)
                elapsed = time.time() - t
                timings.append(elapsed)
                print(f"    완료 ({elapsed:.1f}초)")
                _append_prompt(raw_file, raw, i)
            except Exception as e:
                print(f"    오류: {e}")

        unload(joy_model, joy_proc)
        _print_stats(timings, total, label="Pass 1")
    else:
        print(f"\n[Pass 1/2] 완료 — prompts_raw.txt {total}개 복원")

    # ── Pass 2: Qwen3-VL 정제 ──
    raws = _read_prompts(raw_file)
    final_done = _count_prompts(out_file) if args.accumulate else 0
    if final_done >= total:
        print(f"[Pass 2/2] 이미 완료 ({total}개)")
        return

    print(f"\n[Pass 2/2] Qwen3-VL-8B 정제 ({final_done}/{total} 완료)")
    pairs = list(zip(images, raws))[final_done:]
    qvl_model, qvl_proc = load_qwen3vl(args.quant)
    print(f"VRAM: {_vram_info()}\n")

    timings = []
    for i, (img_path, raw) in enumerate(pairs, final_done):
        print(f"  [{i+1}/{total}] {Path(img_path).name}")
        t = time.time()
        try:
            result = run_qwen3vl_refine(raw, qvl_model, qvl_proc, lang=args.lang)
            elapsed = time.time() - t
            timings.append(elapsed)
            print(f"    완료 ({elapsed:.1f}초) | {len(result.split())}단어")
            print(f"    {result[:120]}{'...' if len(result) > 120 else ''}")
            _append_prompt(out_file, result, i)
        except Exception as e:
            print(f"    오류: {e}")

    unload(qvl_model, qvl_proc)
    _print_stats(timings, total, label="Pass 2")


def run_method5(images: list, args):
    """JoyCaption raw → Qwen3.5-9B 정제 (2-pass)"""
    out_dir = Path(args.output_dir)
    raw_file = out_dir / "prompts_raw.txt"
    out_file = out_dir / "prompts.txt"
    total = len(images)

    if not args.accumulate:
        _clear_file(raw_file)
        _clear_file(out_file)
    # ── Pass 1: JoyCaption raw 생성 ──
    raw_done = _count_prompts(raw_file) if args.accumulate else 0
    if raw_done < total:
        print(f"\n[Pass 1/2] JoyCaption raw 생성 ({raw_done}/{total} 완료)")
        imgs_p1 = images[raw_done:]
        joy_model, joy_proc = load_joycaption(args.quant)
        print(f"VRAM: {_vram_info()}\n")

        timings = []
        for i, img_path in enumerate(imgs_p1, raw_done):
            print(f"  [{i+1}/{total}] {Path(img_path).name}")
            t = time.time()
            try:
                raw = run_joycaption(img_path, joy_model, joy_proc)
                elapsed = time.time() - t
                timings.append(elapsed)
                print(f"    완료 ({elapsed:.1f}초)")
                _append_prompt(raw_file, raw, i)
            except Exception as e:
                print(f"    오류: {e}")

        unload(joy_model, joy_proc)
        _print_stats(timings, total, label="Pass 1")
    else:
        print(f"\n[Pass 1/2] 완료 — prompts_raw.txt {total}개 복원")

    # ── Pass 2: Qwen3.5 정제 ──
    raws = _read_prompts(raw_file)
    final_done = _count_prompts(out_file) if args.accumulate else 0
    if final_done >= total:
        print(f"[Pass 2/2] 이미 완료 ({total}개)")
        return

    print(f"\n[Pass 2/2] Qwen3.5-9B 정제 ({final_done}/{total} 완료)")
    pairs = list(zip(images, raws))[final_done:]
    q35_model, q35_proc = load_qwen35(args.quant)
    print(f"VRAM: {_vram_info()}\n")

    timings = []
    for i, (img_path, raw) in enumerate(pairs, final_done):
        print(f"  [{i+1}/{total}] {Path(img_path).name}")
        t = time.time()
        try:
            result = run_qwen35_refine(raw, q35_model, q35_proc, lang=args.lang)
            elapsed = time.time() - t
            timings.append(elapsed)
            print(f"    완료 ({elapsed:.1f}초) | {len(result.split())}단어")
            print(f"    {result[:120]}{'...' if len(result) > 120 else ''}")
            _append_prompt(out_file, result, i)
        except Exception as e:
            print(f"    오류: {e}")

    unload(q35_model, q35_proc)
    _print_stats(timings, total, label="Pass 2")


# ──────────────────────────────────────────────
# 통계 출력
# ──────────────────────────────────────────────
def _print_stats(timings: list, total: int, label: str = ""):
    if not timings:
        return
    tag = f" [{label}]" if label else ""
    print(f"\n{'═' * 60}")
    print(f"완료{tag}: {len(timings)}/{total}장 | 총 {sum(timings):.1f}초")
    print(f"평균: {sum(timings)/len(timings):.1f}초/장 | 최소: {min(timings):.1f}초 | 최대: {max(timings):.1f}초")


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────

def run_method6(images: list, args):
    """Huihui-Qwen3-VL-8B abliterated 직접 이미지 분석 → prompts.txt"""
    out_dir = Path(args.output_dir)
    out_file = out_dir / "prompts.txt"

    if not args.accumulate:
        _clear_file(out_file)
    done = _count_prompts(out_file) if args.accumulate else 0
    if done:
        print(f"[재개] {done}/{len(images)}장 완료 — {Path(images[done]).name}부터 재개")
    images = images[done:]

    model, processor = load_qwen3vl(args.quant, MODEL_QWEN3VL_AB)
    print(f"VRAM: {_vram_info()}\n")

    timings = []
    for i, img_path in enumerate(images, done):
        print(f"[{i+1}/{len(images)+done}] {Path(img_path).name}")
        t = time.time()
        try:
            result = run_qwen3vl_image(img_path, model, processor, lang=args.lang)
            elapsed = time.time() - t
            timings.append(elapsed)
            print(f"  완료 ({elapsed:.1f}초) | {len(result.split())}단어")
            print(f"  {result[:120]}{'...' if len(result) > 120 else ''}")
            _append_prompt(out_file, result, i)
        except Exception as e:
            print(f"  오류: {e}")

    unload(model, processor)
    _print_stats(timings, len(images) + done)


def run_method7(images: list, args):
    """Huihui-Qwen3.5-9B abliterated 직접 이미지 분석 → prompts.txt"""
    out_dir = Path(args.output_dir)
    out_file = out_dir / "prompts.txt"

    if not args.accumulate:
        _clear_file(out_file)
    done = _count_prompts(out_file) if args.accumulate else 0
    if done:
        print(f"[재개] {done}/{len(images)}장 완료 — {Path(images[done]).name}부터 재개")
    images = images[done:]

    model, processor = load_qwen35(args.quant, MODEL_QWEN35_AB)
    print(f"VRAM: {_vram_info()}\n")

    timings = []
    for i, img_path in enumerate(images, done):
        print(f"[{i+1}/{len(images)+done}] {Path(img_path).name}")
        t = time.time()
        try:
            result = run_qwen35_image(img_path, model, processor, lang=args.lang)
            elapsed = time.time() - t
            timings.append(elapsed)
            print(f"  완료 ({elapsed:.1f}초) | {len(result.split())}단어")
            print(f"  {result[:120]}{'...' if len(result) > 120 else ''}")
            _append_prompt(out_file, result, i)
        except Exception as e:
            print(f"  오류: {e}")

    unload(model, processor)
    _print_stats(timings, len(images) + done)

def main():
    parser = argparse.ArgumentParser(
        description="Z-Image Turbo 프롬프트 생성 v2",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("input", help="이미지 파일 또는 폴더 경로")
    parser.add_argument("--output-dir", "-o", required=True, help="출력 폴더 경로")
    parser.add_argument(
        "--method", "-m", type=int, default=2, choices=[1, 2, 3, 4, 5, 6, 7],
        help=(
            "1: JoyCaption (영어 전용)\n"
            "2: Qwen3-VL-8B 직접 분석\n"
            "3: Qwen3.5-9B 직접 분석\n"
            "4: JoyCaption → Qwen3-VL-8B 정제\n"
            "5: JoyCaption → Qwen3.5-9B 정제\n"
            "6: Huihui-Qwen3-VL-8B abliterated 직접 분석\n"
            "7: Huihui-Qwen3.5-9B abliterated 직접 분석"
        ),
    )
    parser.add_argument(
        "--quant", default="bf16", choices=["nf4", "int8", "bf16"],
        help="양자화 방식 (기본: bf16)",
    )
    parser.add_argument(
        "--lang", default="en", choices=["en", "zh"],
        help="출력 언어 (기본: en, method 1은 항상 en)",
    )
    parser.add_argument(
        "--accumulate", "-a", action="store_true",
        help="중단된 작업 이어서 처리",
    )
    args = parser.parse_args()

    # 입력 이미지 수집
    input_path = Path(args.input).resolve()
    if input_path.is_file():
        images = [str(input_path)]
    elif input_path.is_dir():
        images = [
            str(p) for p in sorted(
                (p for p in input_path.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS),
                key=lambda p: p.name
            )
        ]
    else:
        print(f"오류: {input_path} 가 존재하지 않습니다.")
        sys.exit(1)

    if not images:
        print("오류: 이미지를 찾을 수 없습니다.")
        sys.exit(1)

    # method 1은 항상 영어
    lang = args.lang
    if args.method in (1,):
        lang = "en"
        if args.lang != "en":
            print("※ method 1(JoyCaption)은 영어 전용입니다. --lang 옵션 무시.")

    method_names = {
        1: "JoyCaption (영어 전용)",
        2: "Qwen3-VL-8B 직접 분석",
        3: "Qwen3.5-9B 직접 분석",
        4: "JoyCaption → Qwen3-VL-8B 정제",
        5: "JoyCaption → Qwen3.5-9B 정제",
        6: "Huihui-Qwen3-VL-8B abliterated 직접 분석",
        7: "Huihui-Qwen3.5-9B abliterated 직접 분석",
    }

    print(f"\n=== Z-Image Turbo 프롬프트 생성 v2 ===")
    print(f"방식  : {args.method} - {method_names[args.method]}")
    print(f"입력  : {input_path}")
    print(f"이미지: {len(images)}장")
    print(f"출력  : {args.output_dir}")
    print(f"양자화: {args.quant}")
    print(f"언어  : {lang}")
    print(f"누적  : {'활성화' if args.accumulate else '비활성화'}")
    print()

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    dispatch = {
        1: run_method1,
        2: run_method2,
        3: run_method3,
        4: run_method4,
        5: run_method5,
        6: run_method6,
        7: run_method7,
    }
    dispatch[args.method](images, args)

    print(f"\n저장 완료: {args.output_dir}/prompts.txt")


if __name__ == "__main__":
    main()
