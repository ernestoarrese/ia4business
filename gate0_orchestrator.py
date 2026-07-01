"""
gate0_orchestrator.py

Orquestador principal de Gate0.

Objetivo:
- Crear un punto único de entrada futuro para Gate0.
- Mantener compatibilidad con el pipeline actual.
- No modificar checks, reglas, dashboard ni histórico.
- En v1 usa el pipeline legacy existente: gate0_check.py.
"""

import json
import subprocess
import sys
from pathlib import Path


class Gate0Orchestrator:
    """
    Director de orquesta de Gate0.

    En esta versión inicial, no reimplementa el flujo completo por agentes.
    Envuelve el pipeline actual para preparar la transición futura.
    """

    def __init__(self, root_path=None):
        self.root_path = Path(root_path or Path(__file__).parent).resolve()
        self.output_json = self.root_path / "data" / "output" / "gate0_report.json"

    def run_legacy_pipeline(self, input_file):
        """
        Ejecuta el pipeline actual usando gate0_check.py.

        Este método mantiene vivo el MVP mientras migramos gradualmente hacia:
        InspectionAgent → QADecisionAgent → PackagingExpertAgent → ReportingAgent.
        """
        input_file = Path(input_file)

        cmd = [
            sys.executable,
            "gate0_check.py",
            str(input_file)
        ]

        result = subprocess.run(
            cmd,
            cwd=str(self.root_path),
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(
                "Gate0 legacy pipeline failed.\n\n"
                f"STDOUT:\n{result.stdout}\n\n"
                f"STDERR:\n{result.stderr}"
            )

        if not self.output_json.exists():
            raise FileNotFoundError(
                f"No se encontró el reporte esperado: {self.output_json}"
            )

        with self.output_json.open("r", encoding="utf-8") as f:
            return json.load(f)

    def run(self, input_file):
        """
        Punto de entrada principal del orquestador.

        En v1:
        - Ejecuta el pipeline legacy completo.
        - Devuelve el report_data final como dict.

        En versiones futuras:
        - InspectionAgent.inspect()
        - QADecisionAgent.evaluate()
        - PackagingExpertAgent.explain()
        - ReportingAgent.report()
        """
        return self.run_legacy_pipeline(input_file)
