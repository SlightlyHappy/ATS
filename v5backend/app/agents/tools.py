from __future__ import annotations
from typing import List, Dict, Any
from app.services.extractor import extract_text
from app.services.chunker import simple_chunk
from app.services.embeddings import embed_chunks
from app.services.retriever import ensure_fulltext

# Thin wrappers to be expanded later (OCR, header-aware chunking, MMR, etc.)

class TextExtractorTool:
    def run(self, mime: str, data: bytes) -> str:
        text, _ = extract_text(mime, data)
        return text


class SectionChunkerTool:
    def run(self, text: str) -> List[Dict[str, Any]]:
        # For now, map simple_chunk into section-agnostic parts
        chunks = simple_chunk(text)
        return [{"section": "unknown", "idx": i, "text": ch} for i, ch in enumerate(chunks)]


class EmbedderTool:
    async def run(self, chunks: List[str]) -> List[List[float]]:
        return await embed_chunks(chunks)


class RetrieverTool:
    def ensure(self, session):
        ensure_fulltext(session)
