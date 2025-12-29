from __future__ import annotations
from typing import Dict, Any
from app.services.ollama_client import ollama
from app.core.config import settings


async def generate_summaries(facts: Dict[str, Any]) -> Dict[str, str]:
    model = "qwen2.5:7b-instruct-q4_K_M"
    prompt = (
        "Given the structured resume facts below, write a 2-3 sentence concise summary and a detailed 6-8 sentence summary. "
        "Return JSON with keys summary_short and summary_detailed.\n\nFacts:\n" + str(facts)
    )
    data = await ollama.generate_json(model, prompt, {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "summary_short": {"type": "string"},
            "summary_detailed": {"type": "string"}
        }
    })
    return {"summary_short": data.get("summary_short") or "", "summary_detailed": data.get("summary_detailed") or ""}


def compute_scores(facts: Dict[str, Any]) -> Dict[str, float]:
    score = 0.0
    if facts.get("experience"):
        score += 0.4
    if (facts.get("skills") or {}).get("hard"):
        score += 0.2
    if facts.get("education"):
        score += 0.2
    if (facts.get("identity") or {}).get("name"):
        score += 0.1
    return {"confidence": min(1.0, score)}
