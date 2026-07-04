from dataclasses import dataclass, field
from typing import Any


@dataclass
class ComparisonResult:
    left_file: str
    right_file: str
    overall_status: str
    score: int
    checks: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
