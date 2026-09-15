"""PDF text extraction with a free OCR fallback.

Approach per PDF_TEXT_EXTRACTION_APPROACH.md: try PyMuPDF's native text layer
first; only pay the OCR cost on pages that actually need it (scanned/
image-only pages return close to zero characters from a real text layer).
"""
from __future__ import annotations

import pymupdf  # PyMuPDF

from app.config import MIN_CHARS_PER_PAGE

_rapidocr_engine = None  # lazy singleton: loading OCR models is the expensive part


def extract_text(pdf_path: str, min_chars_per_page: int = MIN_CHARS_PER_PAGE) -> tuple[str, bool]:
    """Returns (text, used_ocr)."""
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


def _ocr_page(page: "pymupdf.Page", dpi: int = 200) -> str:
    global _rapidocr_engine
    from rapidocr import RapidOCR

    if _rapidocr_engine is None:
        _rapidocr_engine = RapidOCR()

    pix = page.get_pixmap(matrix=pymupdf.Matrix(dpi / 72, dpi / 72))
    result = _rapidocr_engine(pix.tobytes("png"))
    return "\n".join(result.txts) if result and result.txts else ""
