from __future__ import annotations
import asyncio
import json
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings


class OllamaClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.OLLAMA_HOST
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=300)

    async def close(self):
        await self._client.aclose()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def embeddings(self, model: str, input: str) -> list[float]:
        r = await self._client.post("/api/embeddings", json={"model": model, "input": input})
        r.raise_for_status()
        return r.json()["embedding"]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate_json(self, model: str, prompt: str, json_schema: dict, options: dict | None = None) -> dict:
        body = {
            "model": model,
            "prompt": prompt,
            "format": {"type": "json_schema", "json_schema": json_schema},
            "options": options or {"num_ctx": settings.OLLAMA_NUM_CTX},
            "stream": False,
        }
        r = await self._client.post("/api/generate", json=body)
        r.raise_for_status()
        data = r.json()
        resp = data.get("response", {})
        if isinstance(resp, str):
            try:
                return json.loads(resp)
            except Exception:
                return {}
        return resp if isinstance(resp, dict) else {}

    async def chat_stream(self, model: str, messages: list[dict], options: dict | None = None):
        body = {"model": model, "messages": messages, "stream": True, "options": options or {"num_ctx": settings.OLLAMA_NUM_CTX}}
        async with self._client.stream("POST", "/api/chat", json=body) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line:
                    continue
                yield line


ollama = OllamaClient()
