"""
Inspection Agent

Coordina la inspección técnica del archivo.
No decide, no explica y no reporta.
"""

from gate0.engines.inspection_engine import InspectionEngine


class InspectionAgent:
    def __init__(self, engine=None):
        self.engine = engine or InspectionEngine()

    def inspect(self, input_file):
        return self.engine.inspect(input_file)
