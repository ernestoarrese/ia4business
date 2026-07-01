"""
inspection_agent.py

Inspection Agent de Gate0.

Responsabilidad:
- Encapsular la inspección técnica.
- Preparar arquitectura modular agent-ready.
- No decide GO / HOLD / NO_GO.
- No interpreta riesgos para usuario.
- No modifica reglas de negocio.

Nota:
Por ahora actúa como fachada. La lógica principal sigue viviendo en gate0_check.py.
"""


class InspectionAgent:
    """
    Agente responsable de inspección técnica del archivo.
    """

    def inspect(self, input_file):
        """
        Futuro punto de entrada para detección técnica.

        En v1 todavía no ejecuta directamente la lógica,
        porque gate0_check.py sigue siendo el entrypoint operativo.
        """
        raise NotImplementedError(
            "InspectionAgent todavía no reemplaza gate0_check.py. "
            "Esta clase prepara la arquitectura modular."
        )
