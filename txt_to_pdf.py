#!/usr/bin/env python3
"""TXT 파일을 PDF로 변환하는 스크립트"""

import sys
import os
import glob
import argparse
from pathlib import Path

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# NotoSansCJK-VF.ttf.ttc: 한중일 통합 폰트 (한글/CJK기본/확장A 100%, 히라가나 97%)
# 서브폰트 인덱스: 0=JP, 1=KR, 2=SC(간체), 3=TC(번체), 4=HK
_USER_FONTS = os.path.expandvars(r'%USERPROFILE%\AppData\Local\Microsoft\Windows\Fonts')
NOTO_CJK_TTC = os.path.join(_USER_FONTS, 'NotoSansCJK-VF.ttf.ttc')

FONT_PRESETS = {
    # (경로, subfontIndex 또는 None)
    "kr": [
        (NOTO_CJK_TTC, 1),                                    # Noto Sans CJK KR - 한중일 통합
        ("C:/Windows/Fonts/NotoSansKR-VF.ttf", None),         # 한글+일본어
        ("C:/Windows/Fonts/malgun.ttf", None),                 # Windows 기본
    ],
    "jp": [
        (NOTO_CJK_TTC, 0),                                    # Noto Sans CJK JP - 한중일 통합
        ("C:/Windows/Fonts/NotoSansJP-VF.ttf", None),         # 일본어+한자
        ("C:/Windows/Fonts/malgun.ttf", None),                 # Windows 기본
    ],
}

FONT_NAME = "Primary"
PAGE_W, PAGE_H = A4
MARGIN = 20 * mm
LINE_HEIGHT = 5.5 * mm
FONT_SIZE = 11


def _make_regular_ttf(ttc_path: str, subfont_idx: int) -> str:
    """Variable TTC에서 Regular(wght=400) static 인스턴스를 추출해 임시 TTF로 저장"""
    import tempfile, copy
    from fontTools.ttLib import TTCollection
    from fontTools.varLib import instancer

    ttc = TTCollection(ttc_path)
    font = copy.deepcopy(ttc.fonts[subfont_idx])
    instancer.instantiateVariableFont(font, {"wght": 400}, inplace=True)
    tmp = tempfile.NamedTemporaryFile(suffix=".ttf", delete=False)
    font.save(tmp.name)
    return tmp.name


def register_font(preset: str) -> bool:
    for path, subfont_idx in FONT_PRESETS.get(preset, FONT_PRESETS["kr"]):
        if os.path.exists(path):
            try:
                if subfont_idx is not None:
                    # Variable TTC → Regular(400) 인스턴스 추출
                    ttf_path = _make_regular_ttf(path, subfont_idx)
                    pdfmetrics.registerFont(TTFont(FONT_NAME, ttf_path))
                else:
                    pdfmetrics.registerFont(TTFont(FONT_NAME, path))
                return True
            except Exception:
                continue
    return False


def txt_to_pdf(input_path: str, output_path: str = None, font_preset: str = "kr") -> bool:
    input_file = Path(input_path)
    if not input_file.exists():
        print(f"오류: 파일을 찾을 수 없습니다 - {input_path}")
        return False

    if output_path is None:
        output_path = str(input_file.with_suffix(".pdf"))

    # 인코딩 자동 감지
    text = None
    for encoding in ["utf-8", "utf-8-sig", "cp949", "euc-kr"]:
        try:
            text = input_file.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue

    if text is None:
        print(f"오류: 파일 인코딩을 인식할 수 없습니다 - {input_path}")
        return False

    has_font = register_font(font_preset)
    font_name = FONT_NAME if has_font else "Helvetica"
    if not has_font:
        print("경고: 폰트를 찾을 수 없습니다. 기본 폰트를 사용합니다.")

    c = canvas.Canvas(output_path, pagesize=A4)
    c.setFont(font_name, FONT_SIZE)

    text_width = PAGE_W - 2 * MARGIN
    x = MARGIN
    y = PAGE_H - MARGIN

    def new_page():
        nonlocal y
        c.showPage()
        c.setFont(font_name, FONT_SIZE)
        y = PAGE_H - MARGIN

    for line in text.splitlines():
        if not line.strip():
            y -= LINE_HEIGHT
            if y < MARGIN:
                new_page()
            continue

        # 긴 줄 자동 줄바꿈
        current_line = ""
        for char in line:
            test_line = current_line + char
            if c.stringWidth(test_line, font_name, FONT_SIZE) > text_width:
                if y < MARGIN:
                    new_page()
                c.drawString(x, y, current_line)
                y -= LINE_HEIGHT
                current_line = char
            else:
                current_line = test_line

        if current_line:
            if y < MARGIN:
                new_page()
            c.drawString(x, y, current_line)
            y -= LINE_HEIGHT

    c.save()
    print(f"변환 완료: {output_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description="TXT 파일을 PDF로 변환")
    parser.add_argument("input", help="입력 txt 파일 (와일드카드 지원: *.txt)")
    parser.add_argument("output", nargs="?", help="출력 pdf 파일 (생략 시 같은 이름으로 생성)")
    parser.add_argument(
        "--font",
        choices=["kr", "jp"],
        default="kr",
        help="폰트 프리셋: kr=한국어 글리프 기준 (기본), jp=일본어 글리프 기준 (동일 문자도 나라별 자형 차이 있음)",
    )
    args = parser.parse_args()

    if "*" in args.input or "?" in args.input:
        files = glob.glob(args.input)
        if not files:
            print(f"일치하는 파일이 없습니다: {args.input}")
            sys.exit(1)
        results = [txt_to_pdf(f, font_preset=args.font) for f in files]
        sys.exit(0 if all(results) else 1)
    else:
        success = txt_to_pdf(args.input, args.output, font_preset=args.font)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
