from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from app.core.logging import get_logger

log = get_logger("agents.supervisor")


@dataclass
class AgentTrace:
    resume_id: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "pending"
    confidence: float = 0.0

    def add_step(self, name: str, ok: bool, meta: Optional[Dict[str, Any]] = None):
        self.steps.append({"step": name, "ok": ok, "meta": meta or {}})


class Supervisor:
    """Thin orchestrator placeholder. Will plan and route tasks to agents.
    This keeps state minimal and serializable for Celery retries.
    """

    def __init__(self, resume_id: str):
        self.trace = AgentTrace(resume_id=resume_id)

    def plan(self) -> List[str]:
        # Initial linear plan; can become dynamic later
        return [
            "ingest",
            "section",
            "embed",
            "extract_map",
            "merge_normalize",
            "consistency",
            "summarize",
            "score",
        ]

    def finalize(self, confidence: float):
        self.trace.status = "done"
        self.trace.confidence = confidence
        log.info("agent_plan_complete", resume_id=self.trace.resume_id, confidence=confidence)
        return self.trace
