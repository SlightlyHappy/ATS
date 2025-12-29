from __future__ import annotations
from app.services.ollama_client import ollama
from app.core.config import settings

SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "identity": {"type": "object", "properties": {
            "name": {"type": "string"},
            "email": {"type": "string"},
            "phone": {"type": "string"},
            "location": {"type": "string"}
        }},
        "summary_short": {"type": "string"},
        "summary_detailed": {"type": "string"},
        "experience": {"type": "array", "items": {"type": "object", "properties": {
            "company": {"type": "string"},
            "title": {"type": "string"},
            "start": {"type": "string"},
            "end": {"type": "string"},
            "highlights": {"type": "array", "items": {"type": "string"}}
        }}}
        ,
        "education": {"type": "array", "items": {"type": "object", "properties": {
            "institution": {"type": "string"},
            "degree": {"type": "string"},
            "year": {"type": "string"}
        }}}
        ,
        "skills": {"type": "object", "properties": {
            "hard": {"type": "array", "items": {"type": "string"}},
            "soft": {"type": "array", "items": {"type": "string"}},
            "tools": {"type": "array", "items": {"type": "string"}}
        }},
        "culture": {"type": "object", "properties": {
            "leadership": {"type": "string"},
            "teamwork": {"type": "string"},
            "communication": {"type": "string"},
            "values": {"type": "string"}
        }},
        "domain": {"type": "array", "items": {"type": "string"}},
        "seniority": {"type": "string"}
    }
}


async def extract_facts_with_cascade(text: str) -> tuple[dict, float]:
    prompt = (
        "Extract structured JSON from the following resume text. Return only valid JSON.\n"
        "Text:\n" + text[:6000]
    )
    # Fast pass
    data3 = await ollama.generate_json("qwen2.5:3b-instruct-q5_0", prompt, SCHEMA)
    conf3 = score_confidence(data3)
    if conf3 >= 0.7:
        return data3, conf3
    # Fallback to 7B
    data7 = await ollama.generate_json("qwen2.5:7b-instruct-q4_K_M", prompt, SCHEMA)
    conf7 = score_confidence(data7)
    return data7, conf7


def score_confidence(data: dict) -> float:
    # Simple heuristic confidence scorer
    score = 0.0
    if data.get("identity", {}).get("name"):
        score += 0.2
    if data.get("experience"):
        score += 0.3
    if data.get("skills", {}).get("hard"):
        score += 0.2
    if data.get("summary_short"):
        score += 0.1
    if data.get("education"):
        score += 0.2
    return min(1.0, score)


async def rag_chat_stream(query: str, context: str, citations: list[dict]):
    system = (
        "You are a helpful recruiting assistant. Use only the provided context to answer. "
        "Cite resume and chunk ids in brackets when relevant."
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
    ]
    # Send prelude with citations
    yield {"type": "meta", "citations": citations}
    async for line in ollama.chat_stream("qwen2.5:7b-instruct-q4_K_M", messages):
        yield {"type": "delta", "delta": line}
    yield {"type": "done"}
