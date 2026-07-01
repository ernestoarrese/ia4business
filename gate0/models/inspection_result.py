from dataclasses import dataclass, field
from typing import Any


@dataclass
class InspectionResult:
    file: str
    pages: int = 0
    technical_findings: list[dict[str, Any]] = field(default_factory=list)
    separations: list[str] = field(default_factory=list)
    page_boxes: list[dict[str, Any]] = field(default_factory=list)
    pdf_structure: dict[str, Any] = field(default_factory=dict)
    live_fonts: list[dict[str, Any]] = field(default_factory=list)
    parser_capabilities: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
