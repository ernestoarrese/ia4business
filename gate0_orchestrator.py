"""
gate0_orchestrator.py

Fachada de arquitectura Gate0 v1.

Objetivo:
- Preparar Gate0 para una arquitectura modular tipo agentes.
- No reemplaza todavía gate0_check.py.
- No cambia reglas, checks ni dashboard.
- Sirve como punto de entrada futuro para coordinar módulos.
"""


class Gate0Orchestrator:
    """
    Orquestador lógico de Gate0.

    Bloques:
    1. Inspection Agent
    2. QA Decision Agent
    3. Packaging Expert Agent
    4. Reporting / History Agent
    """

    def inspect(self, input_file):
        """
        Futuro punto de entrada para inspección técnica.
        Hoy la lógica vive principalmente en gate0_check.py.
        """
        raise NotImplementedError("Inspection Agent todavía usa gate0_check.py")

    def evaluate(self, findings):
        """
        Futuro punto de entrada para reglas de negocio y readiness.
        """
        raise NotImplementedError("QA Decision Agent todavía usa business_rules.py/readiness_engine.py")

    def explain(self, report_data):
        """
        Futuro punto de entrada para interpretación experta.
        """
        raise NotImplementedError("Packaging Expert Agent todavía usa readiness_summary/expert engines")

    def report(self, report_data):
        """
        Futuro punto de entrada para reporting, histórico y dashboard.
        """
        raise NotImplementedError("Reporting/History Agent todavía vive en app.py")

    def run(self, input_file):
        """
        Futuro flujo completo:
        inspect → evaluate → explain → report
        """
        raise NotImplementedError("Gate0Orchestrator es una fachada inicial; no ejecuta aún el pipeline.")
