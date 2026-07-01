from dataclasses import dataclass, field
from typing import Any


@dataclass
class AnalysisRecord:
    session_id: str
    file: str
    client: str = "Sin cliente"
    input_type: str = "PDF"
    score: int | None = None
    status: str | None = None
    decision: str | None = None
    top_risk: str | None = None
    history_metadata: dict[str, Any] = field(default_factory=dict)
    dashboard_payload: dict[str, Any] = field(default_factory=dict)
