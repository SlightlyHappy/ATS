from __future__ import annotations
import asyncio
import hashlib
from app.services.ollama_client import ollama
from app.core.config import settings

# Simple in-process cache keyed by md5(text[:2000])
_EMB_CACHE: dict[str, list[float]] = {}
_MAX_CACHE = 5000


def _key(text: str) -> str:
    return hashlib.md5(text[:2000].encode("utf-8", errors="ignore")).hexdigest()


def _get_cache(k: str):
    return _EMB_CACHE.get(k)


def _set_cache(k: str, v: list[float]):
    if len(_EMB_CACHE) > _MAX_CACHE:
        _EMB_CACHE.clear()
    _EMB_CACHE[k] = v


async def embed_text(text: str) -> list[float]:
    model = settings.EMBEDDING_MODEL
    k = _key(text)
    cached = _get_cache(k)
    if cached is not None:
        return cached
    vec = await ollama.embeddings(model, text[:2000])
    _set_cache(k, vec)
    return vec


async def _embed_one(sema: asyncio.Semaphore, model: str, text: str) -> list[float]:
    k = _key(text)
    cached = _get_cache(k)
    if cached is not None:
        return cached
    async with sema:
        vec = await ollama.embeddings(model, text[:2000])
    _set_cache(k, vec)
    return vec


async def embed_chunks(chunks: list[str]) -> list[list[float]]:
    model = settings.EMBEDDING_MODEL
    # Concurrency limited to avoid CPU overload
    parallel = max(1, int(getattr(settings, "OLLAMA_NUM_PARALLEL", 1)))
    sema = asyncio.Semaphore(parallel)
    tasks = [asyncio.create_task(_embed_one(sema, model, ch)) for ch in chunks]
    return await asyncio.gather(*tasks)
