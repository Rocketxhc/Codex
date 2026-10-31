#!/usr/bin/env python3
"""Generate an editable DOCX from a small, explicit JSON content structure."""
import argparse
import json
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def create(content, output):
    doc = Document()
    section = doc.sections[0]
    section.top_margin = section.bottom_margin = Inches(0.8)
    section.left_margin = section.right_margin = Inches(0.85)
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)
    style.paragraph_format.space_after = Pt(7)
    style.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), 'Noto Sans CJK SC')
    title = doc.add_heading(content['title'], 0)
    for run in title.runs:
        run.font.color.rgb = RGBColor.from_string('16425B')
    if content.get('subtitle'):
        doc.add_paragraph(content['subtitle'], 'Subtitle')
    for block in content.get('sections', []):
        if block.get('heading'):
            doc.add_heading(block['heading'], 1)
        for text in block.get('paragraphs', []):
            doc.add_paragraph(str(text))
        for text in block.get('bullets', []):
            doc.add_paragraph(str(text), 'List Bullet')
        rows = block.get('table', [])
        if rows:
            if any(len(row) != len(rows[0]) for row in rows):
                raise ValueError('Every table row must have the same number of cells')
            table = doc.add_table(rows=1, cols=len(rows[0]))
            table.style = 'Light Shading Accent 1'
            for cell, value in zip(table.rows[0].cells, rows[0]):
                cell.text = str(value)
            header = OxmlElement('w:tblHeader')
            table.rows[0]._tr.get_or_add_trPr().append(header)
            for values in rows[1:]:
                for cell, value in zip(table.add_row().cells, values):
                    cell.text = str(value)
    doc.core_properties.title = content['title']
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('content_json', type=Path)
    parser.add_argument('output_docx', type=Path)
    args = parser.parse_args()
    create(json.loads(args.content_json.read_text(encoding='utf-8')), args.output_docx)
    print(args.output_docx)
