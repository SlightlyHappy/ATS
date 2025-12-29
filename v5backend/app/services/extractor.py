from __future__ import annotations
import io
from typing import Tuple
import pdfplumber
from pypdf import PdfReader
from docx import Document
from PIL import Image  # noqa: F401
import pytesseract
try:
    from langdetect import detect, LangDetectException
except Exception:  # pragma: no cover - optional dep at runtime
    detect = None  # type: ignore
    class LangDetectException(Exception):
        pass
from app.core.config import settings
from app.monitoring.metrics import OCR_USED

# Configure tesseract executable if provided
if settings.TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD


def extract_text_from_pdf(data: bytes) -> str:
    # Prefer pdfplumber for layout, fallback to pypdf
    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            ocr_applied = False
            if not (text and text.strip()):
                # OCR any page with no text
                ocr_texts = []
                for page in pdf.pages:
                    if (page.extract_text() or "").strip():
                        continue
                    try:
                        im = page.to_image(resolution=200).original
                        ocr_texts.append(pytesseract.image_to_string(im))
                    except Exception:
                        continue
                if ocr_texts:
                    text = (text or "") + "\n" + "\n".join(ocr_texts)
                    ocr_applied = True
            if ocr_applied:
                try:
                    OCR_USED.inc()
                except Exception:
                    pass
            if text and text.strip():
                return text
    except Exception as pdfplumber_error:
        # Log pdfplumber failure but continue with pypdf fallback
        pass
    
    # Fallback to pypdf with better error handling
    try:
        reader = PdfReader(io.BytesIO(data))
        out = []
        for page in reader.pages:
            try:
                t = page.extract_text() or ""
                out.append(t)
            except Exception:
                # Skip corrupted pages
                continue
        extracted_text = "\n".join(out)
        if extracted_text.strip():
            return extracted_text
        else:
            # If no text extracted, return empty string instead of failing
            return ""
    except Exception as pdf_error:
        # Handle specific PDF errors more gracefully
        error_msg = str(pdf_error)
        if "startxref not found" in error_msg:
            raise ValueError(f"PDF appears to be corrupted or malformed: {error_msg}")
        else:
            raise ValueError(f"Failed to process PDF: {error_msg}")


def extract_text_from_docx(data: bytes) -> str:
    f = io.BytesIO(data)
    doc = Document(f)
    return "\n".join(p.text for p in doc.paragraphs)


def detect_language(text: str) -> str:
    try:
        if not detect:
            return "unknown"
        return detect(text)
    except LangDetectException:
        return "unknown"
    except Exception:
        return "unknown"


def extract_text(mime: str, data: bytes) -> Tuple[str, str]:
    if mime.endswith("pdf"):
        text = extract_text_from_pdf(data)
    elif mime.endswith("docx"):
        text = extract_text_from_docx(data)
    else:
        raise ValueError("Unsupported mime type")
    lang = detect_language(text)
    return text, lang
