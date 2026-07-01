from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExpertReport:
    summary: dict[str, Any] = field(default_factory=dict)
    expert_comments: list[dict[str, Any]] = field(default_factory=list)
    risk_evidence: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[dict[str, Any]] = field(default_factory=list)
    decision_impact: list[dict[str, Any]] = field(default_factory=list)
