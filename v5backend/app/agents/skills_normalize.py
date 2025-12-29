from __future__ import annotations
from typing import Dict, Any, List
import json
import os
from rapidfuzz import fuzz

_ONT: Dict[str, List[str]] | None = None


def _load_ontology() -> Dict[str, List[str]]:
    global _ONT
    if _ONT is not None:
        return _ONT
    path = os.path.join(os.path.dirname(__file__), "..", "data", "skills_ontology.json")
    path = os.path.abspath(path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    mapping: Dict[str, List[str]] = {}
    for item in data.get("skills", []):
        name = item.get("name", "").strip().lower()
        aliases = [a.strip().lower() for a in item.get("aliases", [])]
        if name:
            mapping[name] = [name] + aliases
    _ONT = mapping
    return mapping


def normalize_skills(skills: Dict[str, List[str]]) -> Dict[str, List[str]]:
    if not skills:
        return {"hard": [], "soft": [], "tools": []}
    ont = _load_ontology()
    def _norm(listing: List[str]) -> List[str]:
        out: List[str] = []
        for s in listing or []:
            s1 = s.strip().lower()
            best = None
            best_score = 0
            for canon, aliases in ont.items():
                for alias in aliases:
                    sc = fuzz.partial_ratio(s1, alias)
                    if sc > best_score:
                        best_score = sc
                        best = canon
            # Threshold avoid bad matches
            if best and best_score >= 85:
                if best not in out:
                    out.append(best)
            else:
                if s1 and s1 not in out:
                    out.append(s1)
        return out
    return {
        "hard": _norm(skills.get("hard") or []),
        "soft": _norm(skills.get("soft") or []),
        "tools": _norm(skills.get("tools") or []),
    }
