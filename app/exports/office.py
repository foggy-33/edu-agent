from __future__ import annotations

import re
from io import BytesIO
from typing import Iterable

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from pptx import Presentation
from pptx.dml.color import RGBColor as PptRGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches as PptInches, Pt as PptPt


ACCENT = "6D5DE7"
INK = "202123"
MUTED = "6B7280"


def _plain(text: str) -> str:
    text = re.sub(r"!\[([^]]*)]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^]]+)]\([^)]+\)", r"\1", text)
    return re.sub(r"[*_`~]", "", text).strip()


def _safe_lines(content: str) -> list[str]:
    return [line.rstrip() for line in content.replace("\r\n", "\n").replace("\r", "\n").split("\n")]


def _presentation_sections(content: str, fallback_title: str) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    current_title = "核心内容"
    current_items: list[str] = []

    def flush() -> None:
        nonlocal current_items
        if current_items:
            sections.append((current_title, current_items))
            current_items = []

    for raw in _safe_lines(content):
        line = raw.strip()
        if not line or line.startswith("```"):
            continue
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            flush()
            current_title = _plain(line[3:]) or fallback_title
            continue
        if line.startswith("### "):
            current_items.append(_plain(line[4:]))
            continue
        match = re.match(r"^(?:[-*+]\s+|\d+[.)]\s+)(.+)$", line)
        current_items.append(_plain(match.group(1) if match else line))
    flush()
    return sections or [(fallback_title, ["围绕主题梳理核心概念、关键方法与应用。"])]


def _chunks(items: list[str], size: int = 6) -> Iterable[list[str]]:
    for index in range(0, len(items), size):
        yield items[index:index + size]


def _ppt_text(
    slide,
    text: str,
    left: float,
    top: float,
    width: float,
    height: float,
    *,
    size: int,
    color: tuple[int, int, int] = (32, 33, 35),
    bold: bool = False,
    align=PP_ALIGN.LEFT,
    anchor=MSO_ANCHOR.TOP,
):
    box = slide.shapes.add_textbox(PptInches(left), PptInches(top), PptInches(width), PptInches(height))
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = 0
    frame.margin_right = 0
    frame.margin_top = 0
    frame.margin_bottom = 0
    frame.vertical_anchor = anchor
    paragraph = frame.paragraphs[0]
    paragraph.alignment = align
    run = paragraph.add_run()
    run.text = text
    run.font.name = "Microsoft YaHei"
    run.font.size = PptPt(size)
    run.font.bold = bold
    run.font.color.rgb = PptRGBColor(*color)
    return box


def _ppt_rule(slide, left: float, top: float, width: float, color: tuple[int, int, int] = (184, 188, 196)) -> None:
    line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        PptInches(left),
        PptInches(top),
        PptInches(width),
        PptInches(0.018),
    )
    line.fill.solid()
    line.fill.fore_color.rgb = PptRGBColor(*color)
    line.line.fill.background()


def _ppt_vertical_rule(slide, left: float, top: float, height: float, color: tuple[int, int, int] = (184, 188, 196)) -> None:
    line = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        PptInches(left),
        PptInches(top),
        PptInches(0.018),
        PptInches(height),
    )
    line.fill.solid()
    line.fill.fore_color.rgb = PptRGBColor(*color)
    line.line.fill.background()


def _ppt_chrome(slide, page_number: int, section_label: str) -> None:
    _ppt_text(slide, "智学 AI  /  PPT 讲解", 0.58, 0.32, 4.2, 0.28, size=10, color=(109, 93, 231), bold=True)
    _ppt_text(slide, f"{page_number:02d}", 11.95, 0.31, 0.75, 0.28, size=10, color=(112, 116, 126), align=PP_ALIGN.RIGHT)
    _ppt_rule(slide, 0.58, 0.82, 12.15)
    _ppt_text(slide, section_label[:48], 0.58, 7.02, 8.6, 0.22, size=8, color=(142, 145, 154))


def _ppt_bullet_column(slide, items: list[str], left: float, top: float, width: float, height: float, size: int = 19) -> None:
    box = slide.shapes.add_textbox(PptInches(left), PptInches(top), PptInches(width), PptInches(height))
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = 0
    frame.margin_right = 0
    frame.margin_top = 0
    frame.margin_bottom = 0
    for index, item in enumerate(items):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.text = f"—  {item[:150]}"
        paragraph.font.name = "Microsoft YaHei"
        paragraph.font.size = PptPt(size)
        paragraph.font.color.rgb = PptRGBColor(52, 54, 61)
        paragraph.space_after = PptPt(15)
        paragraph.line_spacing = 1.08


def build_pptx(title: str, subtitle: str, content: str) -> BytesIO:
    deck = Presentation()
    deck.slide_width = PptInches(13.333)
    deck.slide_height = PptInches(7.5)
    blank = deck.slide_layouts[6]
    sections = _presentation_sections(content, title)

    cover = deck.slides.add_slide(blank)
    cover.background.fill.solid()
    cover.background.fill.fore_color.rgb = PptRGBColor(255, 255, 255)
    _ppt_text(cover, "智学 AI  ·  课程讲解", 0.62, 0.48, 4.5, 0.36, size=13, color=(109, 93, 231), bold=True)
    _ppt_text(
        cover,
        title[:72],
        0.62,
        1.48,
        11.7,
        2.2,
        size=48 if len(title) <= 22 else 40,
        bold=True,
        anchor=MSO_ANCHOR.MIDDLE,
    )
    _ppt_rule(cover, 0.62, 4.24, 2.05, (109, 93, 231))
    _ppt_text(cover, subtitle[:140], 0.62, 4.62, 8.6, 0.72, size=20, color=(103, 107, 116))
    _ppt_text(cover, "理解  ·  连接  ·  应用", 0.62, 6.72, 4.8, 0.28, size=11, color=(130, 133, 142))
    _ppt_text(cover, "01", 11.45, 5.72, 1.25, 0.8, size=36, color=(225, 222, 249), bold=True, align=PP_ALIGN.RIGHT)

    page_number = 2
    overview = deck.slides.add_slide(blank)
    overview.background.fill.solid()
    overview.background.fill.fore_color.rgb = PptRGBColor(255, 255, 255)
    _ppt_chrome(overview, page_number, title)
    _ppt_text(overview, "这次讲解将解决什么", 0.62, 1.18, 8.8, 0.7, size=35, bold=True)
    _ppt_text(overview, "沿着问题逐步建立理解，最后落实到应用。", 0.62, 1.95, 7.4, 0.42, size=16, color=(103, 107, 116))
    route_titles = [section_title for section_title, _ in sections][:10]
    split_at = (len(route_titles) + 1) // 2
    for column, column_items in enumerate((route_titles[:split_at], route_titles[split_at:])):
        left = 0.68 + column * 6.05
        for index, item in enumerate(column_items):
            top = 2.72 + index * 0.72
            number = index + 1 + (split_at if column else 0)
            _ppt_text(overview, f"{number:02d}", left, top, 0.48, 0.3, size=11, color=(109, 93, 231), bold=True)
            _ppt_text(overview, item[:34], left + 0.62, top - 0.03, 5.12, 0.42, size=17, bold=True)
            _ppt_rule(overview, left + 0.62, top + 0.47, 4.92, (232, 232, 236))

    content_slide_index = 0
    for section_title, items in sections:
        for part_index, part in enumerate(_chunks(items)):
            page_number += 1
            content_slide_index += 1
            slide = deck.slides.add_slide(blank)
            slide.background.fill.solid()
            slide.background.fill.fore_color.rgb = PptRGBColor(255, 255, 255)
            suffix = "（续）" if part_index else ""
            display_title = f"{section_title}{suffix}"[:54]
            _ppt_chrome(slide, page_number, title)
            _ppt_text(slide, display_title, 0.62, 1.12, 11.6, 0.78, size=34 if len(display_title) <= 24 else 29, bold=True)

            layout = content_slide_index % 4
            if layout == 1 and len(part) >= 2:
                _ppt_text(slide, part[0][:150], 0.68, 2.22, 5.35, 2.7, size=28, bold=True, anchor=MSO_ANCHOR.MIDDLE)
                _ppt_vertical_rule(slide, 6.31, 2.24, 3.72, (109, 93, 231))
                _ppt_bullet_column(slide, part[1:], 6.72, 2.22, 5.85, 3.7, 18)
            elif layout == 2 and len(part) >= 4:
                midpoint = (len(part) + 1) // 2
                _ppt_text(slide, "先理解", 0.68, 2.22, 5.5, 0.36, size=14, color=(109, 93, 231), bold=True)
                _ppt_bullet_column(slide, part[:midpoint], 0.68, 2.82, 5.45, 3.25, 18)
                _ppt_text(slide, "再应用", 6.78, 2.22, 5.5, 0.36, size=14, color=(109, 93, 231), bold=True)
                _ppt_bullet_column(slide, part[midpoint:], 6.78, 2.82, 5.45, 3.25, 18)
            elif layout == 3 and len(part) >= 3:
                for index, item in enumerate(part[:3]):
                    left = 0.68 + index * 4.08
                    _ppt_text(slide, f"0{index + 1}", left, 2.34, 0.7, 0.35, size=13, color=(109, 93, 231), bold=True)
                    _ppt_rule(slide, left, 2.85, 3.6, (215, 212, 238))
                    _ppt_text(slide, item[:125], left, 3.18, 3.58, 2.25, size=20, bold=True, anchor=MSO_ANCHOR.MIDDLE)
                if len(part) > 3:
                    _ppt_text(slide, "补充：" + "；".join(part[3:])[:150], 0.68, 5.76, 11.8, 0.52, size=14, color=(100, 104, 113))
            else:
                first = part[0] if part else section_title
                _ppt_text(slide, first[:165], 0.68, 2.22, 11.4, 1.62, size=30, bold=True, anchor=MSO_ANCHOR.MIDDLE)
                _ppt_rule(slide, 0.68, 4.18, 11.75, (109, 93, 231))
                _ppt_bullet_column(slide, part[1:] or ["用自己的语言复述这一点，并尝试连接到一个具体问题。"], 0.68, 4.62, 11.45, 1.55, 18)

    page_number += 1
    close = deck.slides.add_slide(blank)
    close.background.fill.solid()
    close.background.fill.fore_color.rgb = PptRGBColor(248, 247, 255)
    last_items = sections[-1][1][:3] if sections else []
    _ppt_text(close, "智学 AI  ·  讲解总结", 0.62, 0.48, 4.5, 0.34, size=12, color=(109, 93, 231), bold=True)
    _ppt_text(close, "现在，把理解变成行动", 0.62, 1.58, 10.8, 1.2, size=43, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    _ppt_text(close, "回到题目或实践场景，完成一次独立解释与应用。", 0.62, 3.02, 9.6, 0.5, size=19, color=(96, 100, 109))
    for index, item in enumerate(last_items or ["复述核心概念", "完成一道变式题", "记录并订正易错点"]):
        _ppt_text(close, f"{index + 1}", 0.68 + index * 4.04, 4.42, 0.35, 0.36, size=13, color=(109, 93, 231), bold=True)
        _ppt_text(close, item[:72], 1.12 + index * 4.04, 4.36, 3.25, 1.15, size=17, bold=True)
    _ppt_text(close, f"{page_number:02d}", 11.45, 6.34, 1.25, 0.7, size=32, color=(215, 211, 242), bold=True, align=PP_ALIGN.RIGHT)

    output = BytesIO()
    deck.save(output)
    output.seek(0)
    return output


def _set_run_font(run, name: str, size: int, color: str = INK, bold: bool = False) -> None:
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = RGBColor.from_string(color)
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), name)


def _shade_paragraph(paragraph, fill: str) -> None:
    properties = paragraph._p.get_or_add_pPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), fill)
    properties.append(shading)


def build_docx(title: str, subtitle: str, content: str) -> BytesIO:
    document = Document()
    section = document.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(0.9)
    section.right_margin = Inches(1)
    section.bottom_margin = Inches(0.9)
    section.left_margin = Inches(1)
    section.header_distance = Inches(0.45)
    section.footer_distance = Inches(0.45)

    normal = document.styles["Normal"]
    normal.font.name = "Microsoft YaHei"
    normal.font.size = Pt(10.5)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.2
    for style_name, size, color, before, after in (
        ("Heading 1", 18, ACCENT, 16, 8),
        ("Heading 2", 14, ACCENT, 12, 6),
        ("Heading 3", 12, "403A72", 9, 4),
    ):
        style = document.styles[style_name]
        style.font.name = "Microsoft YaHei"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string(color)
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True

    title_paragraph = document.add_paragraph()
    title_paragraph.paragraph_format.space_after = Pt(7)
    title_run = title_paragraph.add_run(title[:120])
    _set_run_font(title_run, "Microsoft YaHei", 26, INK, True)
    subtitle_paragraph = document.add_paragraph()
    subtitle_paragraph.paragraph_format.space_after = Pt(18)
    subtitle_run = subtitle_paragraph.add_run(subtitle[:180])
    _set_run_font(subtitle_run, "Microsoft YaHei", 10, MUTED)

    in_code = False
    code_lines: list[str] = []
    for raw in _safe_lines(content):
        line = raw.rstrip()
        if line.strip().startswith("```"):
            if in_code:
                paragraph = document.add_paragraph()
                paragraph.paragraph_format.left_indent = Inches(0.18)
                paragraph.paragraph_format.right_indent = Inches(0.18)
                paragraph.paragraph_format.space_before = Pt(4)
                paragraph.paragraph_format.space_after = Pt(9)
                _shade_paragraph(paragraph, "F4F3FA")
                run = paragraph.add_run("\n".join(code_lines))
                _set_run_font(run, "Consolas", 9, "303038")
                code_lines = []
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("# "):
            continue
        if stripped.startswith("### "):
            document.add_paragraph(_plain(stripped[4:]), style="Heading 3")
        elif stripped.startswith("## "):
            document.add_paragraph(_plain(stripped[3:]), style="Heading 2")
        elif re.match(r"^[-*+]\s+", stripped):
            paragraph = document.add_paragraph(style="List Bullet")
            paragraph.paragraph_format.space_after = Pt(4)
            paragraph.add_run(_plain(re.sub(r"^[-*+]\s+", "", stripped)))
        elif re.match(r"^\d+[.)]\s+", stripped):
            paragraph = document.add_paragraph(style="List Number")
            paragraph.paragraph_format.space_after = Pt(4)
            paragraph.add_run(_plain(re.sub(r"^\d+[.)]\s+", "", stripped)))
        else:
            paragraph = document.add_paragraph()
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
            paragraph.add_run(_plain(stripped))

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer_run = footer.add_run(subtitle[:70])
    _set_run_font(footer_run, "Microsoft YaHei", 8, "8A8D96")

    output = BytesIO()
    document.save(output)
    output.seek(0)
    return output
