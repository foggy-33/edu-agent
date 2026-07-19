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


def build_pptx(title: str, subtitle: str, content: str) -> BytesIO:
    deck = Presentation()
    deck.slide_width = PptInches(13.333)
    deck.slide_height = PptInches(7.5)
    blank = deck.slide_layouts[6]

    cover = deck.slides.add_slide(blank)
    cover.background.fill.solid()
    cover.background.fill.fore_color.rgb = PptRGBColor(248, 247, 255)
    accent = cover.shapes.add_shape(MSO_SHAPE.RECTANGLE, PptInches(0.72), PptInches(1.22), PptInches(0.12), PptInches(4.1))
    accent.fill.solid()
    accent.fill.fore_color.rgb = PptRGBColor(109, 93, 231)
    accent.line.fill.background()
    title_box = cover.shapes.add_textbox(PptInches(1.12), PptInches(1.45), PptInches(10.9), PptInches(1.65))
    title_frame = title_box.text_frame
    title_frame.clear()
    title_frame.word_wrap = True
    title_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    title_run = title_frame.paragraphs[0].add_run()
    title_run.text = title[:80]
    title_run.font.name = "Microsoft YaHei"
    title_run.font.size = PptPt(50)
    title_run.font.bold = True
    title_run.font.color.rgb = PptRGBColor(32, 33, 35)
    sub_box = cover.shapes.add_textbox(PptInches(1.15), PptInches(3.35), PptInches(10.4), PptInches(1.2))
    sub_frame = sub_box.text_frame
    sub_frame.clear()
    sub_run = sub_frame.paragraphs[0].add_run()
    sub_run.text = subtitle[:140]
    sub_run.font.name = "Microsoft YaHei"
    sub_run.font.size = PptPt(22)
    sub_run.font.color.rgb = PptRGBColor(107, 114, 128)

    page_number = 1
    for section_title, items in _presentation_sections(content, title):
        for part_index, part in enumerate(_chunks(items)):
            page_number += 1
            slide = deck.slides.add_slide(blank)
            slide.background.fill.solid()
            slide.background.fill.fore_color.rgb = PptRGBColor(255, 255, 255)
            header = slide.shapes.add_textbox(PptInches(0.78), PptInches(0.55), PptInches(11.6), PptInches(0.72))
            header_frame = header.text_frame
            header_frame.clear()
            header_run = header_frame.paragraphs[0].add_run()
            suffix = "（续）" if part_index else ""
            header_run.text = f"{section_title}{suffix}"[:70]
            header_run.font.name = "Microsoft YaHei"
            header_run.font.size = PptPt(36)
            header_run.font.bold = True
            header_run.font.color.rgb = PptRGBColor(32, 33, 35)
            rule = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, PptInches(0.8), PptInches(1.42), PptInches(1.15), PptInches(0.07))
            rule.fill.solid()
            rule.fill.fore_color.rgb = PptRGBColor(109, 93, 231)
            rule.line.fill.background()

            body = slide.shapes.add_textbox(PptInches(1.02), PptInches(1.72), PptInches(11.25), PptInches(4.85))
            frame = body.text_frame
            frame.clear()
            frame.word_wrap = True
            frame.margin_left = PptInches(0.08)
            frame.margin_right = PptInches(0.08)
            for index, item in enumerate(part):
                paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
                paragraph.text = item[:180]
                paragraph.level = 0
                paragraph.font.name = "Microsoft YaHei"
                paragraph.font.size = PptPt(21)
                paragraph.font.color.rgb = PptRGBColor(55, 58, 65)
                paragraph.space_after = PptPt(14)
                paragraph.line_spacing = 1.1
            footer = slide.shapes.add_textbox(PptInches(0.82), PptInches(6.91), PptInches(11.65), PptInches(0.28))
            footer_frame = footer.text_frame
            footer_frame.clear()
            footer_frame.paragraphs[0].alignment = PP_ALIGN.RIGHT
            footer_run = footer_frame.paragraphs[0].add_run()
            footer_run.text = f"{subtitle[:45]}  ·  {page_number}"
            footer_run.font.name = "Microsoft YaHei"
            footer_run.font.size = PptPt(10)
            footer_run.font.color.rgb = PptRGBColor(148, 151, 160)

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
