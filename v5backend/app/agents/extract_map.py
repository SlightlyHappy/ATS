from __future__ import annotations
from typing import List, Dict, Any
from app.services.llm import SCHEMA, score_confidence
from app.services.ollama_client import ollama
from app.core.config import settings
import hashlib

# Simple per-process cache for chunk extractions
_CACHE: dict[str, Dict[str, Any]] = {}
_MAX = 5000


def _key(text: str) -> str:
    return hashlib.md5(text[:4000].encode("utf-8", errors="ignore")).hexdigest()


async def map_extract_chunks(chunks: List[str], max_chunks: int = 30) -> List[Dict[str, Any]]:
    """Run lightweight JSON extraction per chunk. Returns list of {idx, data, confidence}."""
    out: List[Dict[str, Any]] = []
    model_fast = "qwen2.5:3b-instruct-q5_0"
    options = {"num_ctx": settings.OLLAMA_NUM_CTX}
    for idx, ch in enumerate(chunks[:max_chunks]):
        k = _key(ch)
        cached = _CACHE.get(k)
        if cached is not None:
            out.append({"idx": idx, **cached})
            continue
        prompt = (
            "Extract any structured resume facts present in this excerpt as JSON. "
            "If a field isn't present, omit it. Return only JSON.\n\nExcerpt:\n" + ch[:4000]
        )
        try:
            data = await ollama.generate_json(model_fast, prompt, SCHEMA, options=options)
            conf = float(score_confidence(data))
            item = {"data": data, "confidence": conf}
            out.append({"idx": idx, **item})
            if len(_CACHE) > _MAX:
                _CACHE.clear()
            _CACHE[k] = item
        except Exception:
            out.append({"idx": idx, "data": {}, "confidence": 0.0})
    return out
