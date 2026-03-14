#!/usr/bin/env python3
"""
Qwen3-VL-8B-Instruct 단독 테스트 스크립트
이미지 1장을 분석하여 프롬프트를 생성하고 속도 및 품질을 확인한다.

사용법:
  python3 test_qwen3vl.py <이미지_경로> [--quant {nf4,bf16}]

참고:
  - 모델: Qwen/Qwen3-VL-8B-Instruct
  - 클래스: Qwen3VLForConditionalGeneration (transformers >= 4.57.0 필요)
  - API: processor.apply_chat_template(..., return_dict=True) 방식 (Qwen2.5-VL과 다름)
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

MODEL_ID = "Qwen/Qwen3-VL-8B-Instruct"

SYSTEM_PROMPT_EN = """You are an expert in interpreting precise visual scenes. Analyze the image and produce a refined, high-fidelity English prompt tailored to its primary subject (person, architectural space, natural landscape, or still-life object).

Follow these rules carefully:

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


def _bnb_config_nf4():
    from transformers import BitsAndBytesConfig
    import torch
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )


def _bnb_config_int8():
    from transformers import BitsAndBytesConfig
    return BitsAndBytesConfig(load_in_8bit=True)


def load_model(quant: str):
    import torch
    from transformers import Qwen3VLForConditionalGeneration, AutoProcessor

    print(f"[로드] {MODEL_ID} ({quant}) ...")
    t = time.time()

    load_kwargs = {"device_map": "auto"}
    if quant == "nf4":
        load_kwargs["quantization_config"] = _bnb_config_nf4()
    elif quant == "int8":
        load_kwargs["quantization_config"] = _bnb_config_int8()
    else:
        load_kwargs["torch_dtype"] = torch.bfloat16

    model = Qwen3VLForConditionalGeneration.from_pretrained(MODEL_ID, **load_kwargs)
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model.eval()

    print(f"  로드 완료 ({time.time() - t:.1f}초)")
    return model, processor


def run(image_path: str, model, processor, lang: str = "en") -> str:
    import torch
    from PIL import Image

    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
    except ImportError:
        pass

    # PIL Image로 직접 로드 (공식 방식: file:// URI 미지원)
    pil_image = Image.open(image_path).convert("RGB")

    prompt = SYSTEM_PROMPT_ZH if lang == "zh" else SYSTEM_PROMPT_EN

    # system prompt를 user 메시지에 직접 통합 (ComfyUI-QwenVL 노드 방식)
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": pil_image},
                {"type": "text", "text": prompt},
            ],
        },
    ]

    # 공식 API: apply_chat_template(return_dict=True) + inputs.to(device)
    inputs = processor.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt",
    )
    inputs = inputs.to(model.device)

    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=1024,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
        )

    generated_ids_trimmed = [
        out_ids[len(in_ids):]
        for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    return processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0].strip()


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif", ".heic", ".heif"}


def main():
    parser = argparse.ArgumentParser(description="Qwen3-VL-8B 단독 테스트 (단일 이미지 또는 폴더)")
    parser.add_argument("input", help="이미지 파일 또는 폴더 경로")
    parser.add_argument("--quant", default="bf16", choices=["nf4", "int8", "bf16"], help="양자화 방식 (기본: bf16)")
    parser.add_argument("--lang", default="en", choices=["en", "zh"], help="출력 언어 (기본: en)")
    parser.add_argument("--output", "-o", help="결과 저장 파일 경로 (미지정 시 콘솔 출력만)")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if input_path.is_file():
        images = [input_path]
    elif input_path.is_dir():
        images = sorted(p for p in input_path.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS)
    else:
        print(f"오류: {input_path} 가 존재하지 않습니다.")
        sys.exit(1)

    if not images:
        print(f"오류: 이미지를 찾을 수 없습니다.")
        sys.exit(1)

    print(f"\n=== Qwen3-VL-8B-Instruct 테스트 ===")
    print(f"입력   : {input_path}")
    print(f"이미지 : {len(images)}장")
    print(f"양자화 : {args.quant}")
    print(f"언어   : {args.lang}")
    if args.output:
        print(f"출력   : {args.output}")
    print()

    model, processor = load_model(args.quant)

    import torch
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1024**3
        print(f"VRAM 사용 (모델 로드 후): {allocated:.1f} GB\n")

    out_file = open(args.output, "w", encoding="utf-8") if args.output else None
    timings = []
    total_start = time.time()

    try:
        for i, img_path in enumerate(images, 1):
            print(f"[{i}/{len(images)}] {img_path.name}")
            t = time.time()
            try:
                result = run(str(img_path), model, processor, lang=args.lang)
                elapsed = time.time() - t
                timings.append(elapsed)
                print(f"  완료 ({elapsed:.1f}초)  |  {len(result.split())}단어")
                print(f"  {result[:120]}{'...' if len(result) > 120 else ''}")
                if out_file:
                    if i > 1:
                        out_file.write("\n")
                    out_file.write(result + "\n")
                    out_file.flush()
            except Exception as e:
                print(f"  오류: {e}")
    finally:
        if out_file:
            out_file.close()

    total = time.time() - total_start
    if timings:
        print(f"\n{'═' * 60}")
        print(f"완료: {len(timings)}/{len(images)}장  |  총 {total:.1f}초")
        print(f"평균: {sum(timings)/len(timings):.1f}초/장  |  최소: {min(timings):.1f}초  |  최대: {max(timings):.1f}초")
        if args.output:
            print(f"저장: {args.output}")

    del model, processor
    gc.collect()
    try:
        torch.cuda.empty_cache()
        free = torch.cuda.mem_get_info()[0] / 1024**3
        print(f"VRAM 해제 후 여유: {free:.1f} GB")
    except Exception:
        pass


if __name__ == "__main__":
    main()
