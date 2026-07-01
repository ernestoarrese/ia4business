# Gate0 Architecture v1 — Agent-Ready Modular MVP

Gate0 v1 no implementa aún un sistema multiagente complejo. La arquitectura actual se organiza como módulos con responsabilidad clara, preparados para evolucionar hacia agentes especializados.

## 1. Inspection Agent

Responsabilidad:
- Leer archivo PDF/AI compatible.
- Extraer hallazgos técnicos.
- Detectar riesgos base.

Archivos actuales:
- gate0_check.py
- context_engine.py
- parser_capability_audit.py

## 2. QA Decision Agent

Responsabilidad:
- Aplicar reglas de negocio.
- Asignar severidad.
- Calcular readiness score.
- Definir decisión GO / GO_WITH_NOTES / HOLD / NO_GO.

Archivos actuales:
- business_rules.py
- readiness_engine.py

## 3. Packaging Expert Agent

Responsabilidad:
- Convertir hallazgos técnicos en explicación experta.
- Explicar qué se encontró, por qué importa, qué problema genera y qué hacer.
- Agregar evidencia e impacto en decisión.

Archivos actuales:
- readiness_summary.py
- expert_comment_engine.py
- risk_evidence_engine.py

## 4. Reporting / History Agent

Responsabilidad:
- Exponer resultado en dashboard.
- Gestionar carga PDF/ZIP.
- Guardar histórico.
- Capturar feedback.

Archivos actuales:
- app.py
- dashboard/
- data/history/analysis_history.csv

## Flujo objetivo

PDF / AI / ZIP
↓
Inspection Agent
↓
QA Decision Agent
↓
Packaging Expert Agent
↓
Reporting / History Agent
↓
Dashboard + histórico + feedback

## Regla de evolución

Por ahora no se agregan nuevos checks.  
La prioridad es consolidar Gate0 v1 como MVP técnico funcional, auditable y modular.
