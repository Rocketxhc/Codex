#!/usr/bin/env python3
"""Generate an editable 16:9 presentation from explicit JSON content."""
import argparse
import json
from pathlib import Path
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt


def textbox(slide, x, y, w, h, text, size, color, bold=False):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.word_wrap = True
    p = frame.paragraphs[0]
    p.text = text
    for run in p.runs:
        run.font.name = 'Noto Sans CJK SC'
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = RGBColor.from_string(color)
    return box


def create(content, output):
    deck = Presentation()
    deck.slide_width, deck.slide_height = Inches(13.333), Inches(7.5)
    slide = deck.slides.add_slide(deck.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = RGBColor.from_string('16425B')
    textbox(slide, 0.85, 2.0, 11.6, 2.3, content['title'], 38, 'FFFFFF', True)
    textbox(slide, 0.9, 5.8, 10.5, 0.7, content.get('subtitle', ''), 18, 'CDE7E8')
    for index, block in enumerate(content.get('slides', []), 1):
        slide = deck.slides.add_slide(deck.slide_layouts[6])
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = RGBColor.from_string('F4F7F8')
        textbox(slide, 0.8, 0.6, 11.5, 1.0, block['title'], 30, '16425B', True)
        panel = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.7), Inches(4.6))
        panel.fill.solid()
        panel.fill.fore_color.rgb = RGBColor.from_string('FFFFFF')
        panel.line.fill.background()
        lines = []
        if block.get('body'):
            lines.append(block['body'])
        lines.extend(block.get('bullets', []))
        box = slide.shapes.add_textbox(Inches(1.2), Inches(2.15), Inches(10.9), Inches(3.8))
        frame = box.text_frame
        frame.word_wrap = True
        for i, text in enumerate(lines):
            p = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
            p.text = str(text)
            p.space_after = Pt(20)
            for run in p.runs:
                run.font.name = 'Noto Sans CJK SC'
                run.font.size = Pt(23)
                run.font.color.rgb = RGBColor.from_string('263D49')
        textbox(slide, 11.8, 6.8, 0.7, 0.4, str(index), 12, '667C86')
        if block.get('notes'):
            slide.notes_slide.notes_text_frame.text = block['notes']
    deck.core_properties.title = content['title']
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    deck.save(path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('content_json', type=Path)
    parser.add_argument('output_pptx', type=Path)
    args = parser.parse_args()
    create(json.loads(args.content_json.read_text(encoding='utf-8')), args.output_pptx)
    print(args.output_pptx)
