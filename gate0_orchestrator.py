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

    def resolve_output_dir(self, output_dir=None):
        """
        Resolve output directory for the legacy subprocess.

        Sprint 27B:
        - Default remains data/output for CLI/backward compatibility.
        - Web flow passes a session-specific output_dir.
        """
        if output_dir is None:
            output_path = self.root_path / "data" / "output"
        else:
            output_path = Path(output_dir)
            if not output_path.is_absolute():
                output_path = self.root_path / output_path

        output_path.mkdir(parents=True, exist_ok=True)
        return output_path

    def run_legacy_pipeline(self, input_file, output_dir=None):
        """
        Ejecuta el pipeline actual usando gate0_check.py.

        Sprint 27B:
        - output_dir allows session-specific reports.
        - If omitted, keeps legacy data/output behavior.
        """
        input_file = Path(input_file)
        output_path = self.resolve_output_dir(output_dir)
        output_json = output_path / "gate0_report.json"

        cmd = [
            sys.executable,
            "gate0_check.py",
            str(input_file),
            str(output_path),
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

        if not output_json.exists():
            raise FileNotFoundError(
                f"No se encontró el reporte esperado: {output_json}"
            )

        with output_json.open("r", encoding="utf-8") as f:
            return json.load(f)

    def run(self, input_file, output_dir=None):
        """
        Punto de entrada principal del orquestador.

        En v1:
        - Ejecuta el pipeline legacy completo.
        - Devuelve el report_data final como dict.

        Sprint 27B:
        - output_dir enables runtime isolation by session.

        En versiones futuras:
        - InspectionAgent.inspect()
        - QADecisionAgent.evaluate()
        - PackagingExpertAgent.explain()
        - ReportingAgent.report()
        """
        return self.run_legacy_pipeline(input_file, output_dir=output_dir)
