# PDF Text Extraction — Recommended Approach

**Recommendation: use PyMuPDF for normal (digitally-born) PDFs; fall back to
RapidOCR when a page has no extractable text (scanned/photographed PDFs).
Both are free, open-source, run fully local, and need no API key.**

This is the conclusion of a benchmark run against real-world resume PDFs
(2,489 real resumes + 36 purpose-built hard-layout resumes + 15 scanned/
image-only PDFs), scoring every library with token-level F1 (Normalized
Levenshtein similarity, threshold 0.7), BLEU-4, and Smith-Waterman local
alignment against independently-sourced ground truth. Full methodology,
every number, and every caveat are in this repo's `README.md` and
`Resume_PDF_Parser_Benchmark_Report_v2.docx` — this file is the distilled,
implementation-ready version for reuse in another project.

---

## 1. Decision logic

Try PyMuPDF first. If it returns effectively no text (a real PDF with a text
layer will always return far more than a few dozen characters per page —
only a scanned/image-only page returns close to zero), fall back to OCR.

```python
"""pdf_text.py — drop-in text extraction with a free OCR fallback.

pip install pymupdf rapidocr
"""
from __future__ import annotations

import pymupdf  # PyMuPDF

MIN_CHARS_PER_PAGE = 20  # a real text layer returns far more than this;
                          # a scanned page with no text layer returns ~0


def extract_text(pdf_path: str, min_chars_per_page: int = MIN_CHARS_PER_PAGE) -> tuple[str, bool]:
    """Returns (text, used_ocr). Tries the fast native text layer first;
    only pays the OCR cost on pages that actually need it."""
    doc = pymupdf.open(pdf_path)
    try:
        parts: list[str] = []
        used_ocr = False
        for page in doc:
            page_text = page.get_text()
            if len(page_text.strip()) < min_chars_per_page:
                page_text = _ocr_page(page)
                used_ocr = True
            parts.append(page_text)
        return "\n".join(parts), used_ocr
    finally:
        doc.close()


_rapidocr_engine = None  # lazy singleton: loading OCR models is the expensive part


def _ocr_page(page: "pymupdf.Page", dpi: int = 200) -> str:
    global _rapidocr_engine
    from rapidocr import RapidOCR

    if _rapidocr_engine is None:
        _rapidocr_engine = RapidOCR()

    pix = page.get_pixmap(matrix=pymupdf.Matrix(dpi / 72, dpi / 72))
    result = _rapidocr_engine(pix.tobytes("png"))
    return "\n".join(result.txts) if result and result.txts else ""
```

Usage:

```python
text, used_ocr = extract_text("resume.pdf")
```

Tune `min_chars_per_page` down (e.g. to 5-10) if you expect pages that are
legitimately mostly-blank with a little real text (e.g. a cover page); tune
it up if you're seeing false negatives on pages with a tiny broken text layer
(some scanners/printers embed a handful of junk characters).

### If a page has *both* real text and images that need OCR (rare for
resumes, common for some document types)

The function above OCRs a whole page only if its native text layer is nearly
empty. If you need per-region OCR (e.g. a photo caption on an otherwise
text-rich page), that's a materially bigger job — use **Docling** instead
(see §4), which does real layout analysis and only OCRs image regions it
detects.

---

## 2. Install

```bash
pip install pymupdf rapidocr
```

Both are free, MIT/Apache-family licensed, pure enough to run in a normal
Python environment (RapidOCR uses `onnxruntime`, no GPU or external
Tesseract binary required, no network calls after the first run — model
weights download once to a local cache).

---

## 3. Evidence

### Non-OCR extraction (digitally-born PDFs) — 2,483-document corpus, real resumes, 24 job categories

| Library | F1 | Precision | Recall | BLEU-4 | Local alignment | Avg time/doc |
|---|---|---|---|---|---|---|
| **PyMuPDF** | **0.9917** | 0.9906 | 0.9931 | **0.9766** | **0.9824** | **11 ms** |
| pypdf | 0.9916 | 0.9904 | 0.9932 | 0.9764 | 0.9825 | 235 ms |
| pdfminer.six | 0.9916 | 0.9904 | 0.9932 | 0.9758 | 0.9782 | 359 ms |
| pdfplumber | 0.9916 | 0.9904 | 0.9931 | 0.9682 | 0.9491 | 613 ms |
| pymupdf4llm | 0.9911 | 0.9903 | 0.9922 | 0.9658 | 0.9563 | 1,303 ms |
| pypdfium2 | 0.7062 | 0.8220 | 0.6195 | 0.4817 | 0.3354 | 23 ms |

PyMuPDF wins on every accuracy metric *and* is 20-150x faster than every
alternative except pypdfium2 (which fails badly on this corpus — see
Caveats). Zero extraction failures across the corpus.

### OCR fallback (scanned/image-only PDFs, no text layer) — 15-document set

| Library | F1 | Precision | Recall | BLEU-4 | Local alignment |
|---|---|---|---|---|---|
| pymupdf4llm (built-in OCR fallback) | 0.9426 | 0.9419 | 0.9442 | 0.8754 | 0.8112 |
| **RapidOCR (direct)** | **0.9291** | 0.9205 | 0.9387 | 0.8224 | 0.7487 |
| Docling (full layout+OCR pipeline) | 0.9235 | 0.9401 | 0.9079 | 0.8159 | 0.7105 |
| PyMuPDF, pypdf, pdfminer.six, pdfplumber, pypdfium2 (no OCR) | **0.0000** | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

Every plain rule-based library scores **exactly zero** on scanned PDFs — none
of them do OCR, so this isn't a close call. RapidOCR direct is the
recommended fallback here because it's the leanest dependency (no full
layout-model stack); `pymupdf4llm` scored marginally higher in this test but
pulls in a heavier pipeline for a small gain, and its OCR behavior is
undocumented/implicit rather than a deliberate API you call.

---

## 4. Caveats

- **pypdfium2's failure above is corpus-specific, not universal.** On a
  different PDF source (Chromium-print-to-PDF resumes in the same
  benchmark), pypdfium2 was competitive-to-best. Its weakness is that its
  raw text API (`FPDFText_GetText`) does no gap-based space reconstruction,
  so it concatenates words together (`"successfulat"`) on PDFs whose text
  streams omit explicit space characters — some PDF generators do this,
  others don't. **Validate against a sample of your actual production PDF
  source before ruling it in or out**; don't take the table above as a
  universal verdict on pypdfium2.
- **If you need structured table extraction** (not just flattened text —
  e.g. reconstructing a skills table as rows/columns), none of the libraries
  above were tested for that here; consider **Docling** (IBM Research, MIT
  license), which includes a dedicated table-structure model (TableFormer).
  It's also the most capable option if you need real document layout
  understanding beyond text order.
- **The scanned-PDF test set here is simulated**, not real scans: existing
  digitally-born PDFs were rasterized to images with mild degradation
  (grayscale, ±1.2° rotation, slight blur, JPEG compression), not sourced
  from an actual scanner or camera. If your real documents are noisier,
  more skewed, lower-resolution, or handwritten, treat the ~0.92-0.94 F1
  OCR numbers above as an optimistic ceiling, not a guarantee — validate
  against your own sample.
- **Multi-column layouts, tables, embedded photos, and multi-page documents
  did not meaningfully change which library wins**, once tested at a
  reasonable sample size (36 documents spanning 5 distinct layout
  structures): every library landed within ~0.5 F1 points of every other on
  those specifically. Don't over-engineer a layout-detection branch in your
  pipeline on the assumption that "hard" layouts need a different tool —
  the evidence here doesn't support that.
- **Marker** (a GPL-licensed PDF→Markdown ML tool, similar to Docling) was
  not tested in this benchmark; if you evaluate it, note its license is
  copyleft, unlike everything else listed here.
