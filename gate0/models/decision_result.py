from dataclasses import dataclass, field
from typing import Any


@dataclass
class DecisionResult:
    gate_status: str
    readiness_score: int
    readiness_status: str
    readiness_decision: str
    business_assessment: dict[str, Any] = field(default_factory=dict)
    readiness_assessment: dict[str, Any] = field(default_factory=dict)
    readiness_summary: dict[str, Any] = field(default_factory=dict)
    top_risks: list[dict[str, Any]] = field(default_factory=list)
