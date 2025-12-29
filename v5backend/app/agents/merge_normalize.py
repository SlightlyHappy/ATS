from __future__ import annotations
from typing import Dict, Any, List
from collections import defaultdict
from app.schemas.resume_facts import ResumeFactsModel, ExperienceItem, EducationItem, Skills, Identity, Culture
from .skills_normalize import normalize_skills


def _merge_lists(unique_key: str, items: List[dict]) -> List[dict]:
    seen = {}
    for it in items:
        key = (it.get(unique_key) or "").strip().lower()
        if not key:
            key = str(hash(str(sorted(it.items()))))
        if key not in seen:
            seen[key] = it
        else:
            # simple merge: extend highlights
            if "highlights" in it and isinstance(it["highlights"], list):
                base = seen[key].setdefault("highlights", [])
                base.extend([h for h in it["highlights"] if h not in base])
    return list(seen.values())


def merge_partial_facts(partials: List[Dict[str, Any]]) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    exps: List[dict] = []
    edus: List[dict] = []
    hard, soft, tools = set(), set(), set()
    domains = set()

    identity = {}
    summaries = []

    for p in partials:
        d = p.get("data") or {}
        if not isinstance(d, dict):
            continue
        if d.get("identity"):
            identity |= {k: v for k, v in d["identity"].items() if v}
        if d.get("summary_short"):
            summaries.append(d["summary_short"])  
        if d.get("experience"):
            exps.extend([x for x in d["experience"] if isinstance(x, dict)])
        if d.get("education"):
            edus.extend([x for x in d["education"] if isinstance(x, dict)])
        if d.get("skills"):
            sk = d["skills"]
            hard |= set(sk.get("hard") or [])
            soft |= set(sk.get("soft") or [])
            tools |= set(sk.get("tools") or [])
        if d.get("domain"):
            domains |= set(d["domain"]) if isinstance(d["domain"], list) else set()

    merged["identity"] = identity
    if summaries:
        merged["summary_short"] = max(summaries, key=len)  # pick richest for now
    merged["experience"] = _merge_lists("company", exps)
    merged["education"] = _merge_lists("institution", edus)
    merged["skills"] = normalize_skills({"hard": sorted(hard), "soft": sorted(soft), "tools": sorted(tools)})
    merged["domain"] = sorted(domains)
    return merged


def to_validated_model(merged: Dict[str, Any]) -> ResumeFactsModel:
    return ResumeFactsModel(**merged)
