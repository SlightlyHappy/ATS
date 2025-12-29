from __future__ import annotations
from typing import Dict, Any


def basic_consistency_checks(facts: Dict[str, Any]) -> Dict[str, Any]:
    issues = []
    # Example: missing name but has email/phone
    ident = facts.get("identity") or {}
    if not ident.get("name") and (ident.get("email") or ident.get("phone")):
        issues.append({"type": "missing_name", "severity": "low"})
    # Example: experience with no company or title
    for i, exp in enumerate(facts.get("experience") or []):
        if not exp.get("company") or not exp.get("title"):
            issues.append({"type": "incomplete_experience", "idx": i, "severity": "medium"})
    return {"ok": len(issues) == 0, "issues": issues}
