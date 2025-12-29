from __future__ import annotations
from typing import List, Dict
import re


def simple_chunk(text: str, max_chars: int = 2000, overlap: int = 200) -> List[str]:
    chunks: List[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        chunks.append(text[start:end])
        if end == n:
            break
        start = max(0, end - overlap)
    return chunks


def section_aware_chunks(text: str, max_chars: int = 1800, overlap: int = 150) -> List[Dict[str, str | int]]:
    """Very light heuristic to segment resumes into sections before chunking.
    Returns list of {section, idx, text}.
    """
    # Simple headers
    headers = [
        r"^\s*(summary|profile|about)\b:?.*$",
        r"^\s*(experience|work experience|employment)\b:?.*$",
        r"^\s*(education|qualifications)\b:?.*$",
        r"^\s*(skills|technical skills|tools|technologies)\b:?.*$",
        r"^\s*(projects)\b:?.*$",
        r"^\s*(certifications)\b:?.*$",
    ]
    pattern = re.compile("|".join(headers), flags=re.IGNORECASE | re.MULTILINE)
    parts: List[Dict[str, str | int]] = []
    matches = list(pattern.finditer(text))
    if not matches:
        # Fallback to uniform chunking
        return [{"section": "unknown", "idx": i, "text": ch} for i, ch in enumerate(simple_chunk(text, max_chars, overlap))]

    # Collect ranges
    spans = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        header = m.group(0).strip().lower()
        sec = "unknown"
        if "experience" in header:
            sec = "experience"
        elif "education" in header:
            sec = "education"
        elif "skill" in header or "technolog" in header or "tool" in header:
            sec = "skills"
        elif "project" in header:
            sec = "projects"
        elif "certification" in header:
            sec = "certifications"
        elif "summary" in header or "profile" in header or "about" in header:
            sec = "summary"
        spans.append((sec, start, end))

    # Chunk within sections
    out: List[Dict[str, str | int]] = []
    for sec, s, e in spans:
        body = text[s:e]
        subs = simple_chunk(body, max_chars=max_chars, overlap=overlap)
        for i, ch in enumerate(subs):
            out.append({"section": sec, "idx": i, "text": ch})
    return out
