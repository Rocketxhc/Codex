---
name: presentation-creator
description: Create, read and edit PowerPoint PPTX slide decks, presentations, pitch decks and slide templates. Use for PPT/PPTX requests and producing editable slides with visual quality checks.
---

# PowerPoint presentation creation

This original cloud workflow uses the open source `python-pptx` library. No proprietary artifact service is required.

## Runtime

Use `/workspace/skill-platform/documents-venv/bin/python`. The environment also provides `pptxgenjs` through Node's configured module path, for advanced native PowerPoint charts. No credential or background service is needed.

## Workflow

1. Derive the audience, purpose, language, outline and desired deck length from the request. If a template is supplied, inspect its slides and layouts first; preserve the original.
2. Build an outline with one clear claim per slide. Choose a coherent type scale and palette, and vary layouts according to content. Do not invent data or sources.
3. Create/edit PPTX using `python-pptx` or `pptxgenjs`. For a simple starting deck, run `python scripts/create_presentation.py content.json output.pptx`. JSON accepts `title` and `slides`; each slide accepts `title`, optional `body`, `bullets`, and `notes`. The helper produces an editable title slide and content slides.
4. Prefer editable text, shapes and charts. Validate slide count and expected text by reopening with `python-pptx`. Check ZIP member integrity with `zipfile.ZipFile(...).testzip()`.
5. Convert to PDF using `soffice --headless --convert-to pdf --outdir <preview-dir> output.pptx`. Render every page with `pdftoppm -png -r 110 preview.pdf <page-prefix>` and open the images. Check clipped text, overlap, contrast, alignment and missing glyphs; revise until satisfactory.
6. Deliver the PPTX and any requested PDF export. Label external media and data sources truthfully.

## Design and editing notes

Use a 16:9 canvas unless the template or user specifies otherwise. Keep text away from slide edges, use short lines, and split overcrowded slides. Use installed Chinese fonts for Chinese content; check availability with `fc-match`. Text extraction alone does not validate layout.

For existing decks, edit text runs when preserving rich formatting matters. Do not assume `python-pptx` preserves every proprietary feature, animation, SmartArt, embedded object, macro or template behavior. Retain source files and disclose limitations that affect the requested output. LibreOffice rendering is a useful cloud check but may differ from Microsoft PowerPoint.
