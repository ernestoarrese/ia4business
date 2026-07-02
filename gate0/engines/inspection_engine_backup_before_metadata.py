"""
Inspection Engine

Motor técnico de inspección.
En v1 es una fachada preparada para adaptar el pipeline legacy.
"""

from gate0.models.inspection_result import InspectionResult


class InspectionEngine:
    def inspect(self, input_file):
        return InspectionResult(
            file=str(input_file),
            metadata={
                "engine": "InspectionEngine",
                "mode": "legacy_adapter_pending"
            }
        )
