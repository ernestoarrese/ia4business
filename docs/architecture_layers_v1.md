# Gate0 — Architecture Layers v1

Este documento define la arquitectura actual de Gate0, su arquitectura objetivo y el criterio para evolucionar hacia un orchestrator formal.

Prioridad: Producto 80% / Arquitectura 20%.

La arquitectura debe crecer solo cuando habilite una capacidad visible para el usuario o reduzca complejidad real.

---

## 1. Arquitectura actual

| Capa | Archivo / módulo actual | Responsabilidad |
|---|---|---|
| Input / Intake | app.py | Recibir PDF, AI, ZIP y preparar análisis. |
| Detection Layer | gate0_check.py | Detectar hallazgos técnicos: RGB, DPI, fuentes, TAC, overprint, spots, separaciones, estructura, texto pequeño, barcode/QR. |
| Context Layer | context_engine.py | Enriquecer hallazgos con contexto técnico disponible. |
| Business Rules Layer | business_rules.py | Convertir hallazgos técnicos en severidad de negocio, prioridad, riesgo y acción. |
| Readiness Layer | readiness_engine.py / readiness_summary.py | Calcular score, status, decisión, top risks y fix plan. |
| Expert Layer | expert_comment_engine.py | Explicar qué se encontró, por qué importa, impacto y recomendación. |
| Profile Layer | profiles/flexo_pet_bopp_default.json | Centralizar criterios operativos del proceso. |
| Presentation Layer | dashboard/index.html | Mostrar resultado, top risks, evidencia, operational profile y fix plan. |
| Product Intelligence Reference | docs/check_intelligence_matrix.md | Documentar criterio, contexto, acción, fix type, limitaciones y futuro por check. |

---

## 2. Flujo actual

PDF / AI / ZIP → Detection → Context → Business Rules → Readiness → Expert Layer → Fix Plan → JSON / Dashboard

Actualmente el flujo principal vive principalmente en gate0_check.py → analyze_pdf().

Esto es aceptable para MVP mientras el producto siga siendo simple y estable.

---

## 3. Arquitectura objetivo

A futuro, Gate0 debería evolucionar hacia un orchestrator formal, por ejemplo:

gate0/orchestrator/analysis_orchestrator.py

El orchestrator debe coordinar el flujo, no contener reglas técnicas ni lógica de negocio pesada.

---

## 4. Qué NO mover todavía

- analyze_pdf() fuera de gate0_check.py solo por orden.
- reglas individuales si todavía cambian mucho.
- expert comments si todavía estamos aprendiendo el wording.
- fix plan si todavía está en v1.
- profile selection si aún no existe cliente, login o perfiles múltiples.

Regla: no refactorizar si no desbloquea una capacidad visible de producto.

---

## 5. Cuándo crear el orchestrator real

Crear orchestrator cuando exista complejidad real:

1. varios flujos: PDF, AI, ZIP, comparación, histórico.
2. múltiples perfiles por cliente, planta, proceso o usuario.
3. Fix Plan con fix asistido o autofix.
4. agentes especializados.
5. gate0_check.py sea difícil de mantener.

---

## 6. Principio de diseño

Cada check debe evolucionar así:

Detectar → Explicar → Priorizar → Recomendar → Clasificar tipo de fix → Guiar corrección → Automatizar solo si es seguro.

---

## 7. Estado recomendado actual

Mantener arquitectura actual, documentar capas y seguir construyendo capacidades visibles.

No crear orchestrator formal todavía.

---

## 8. Próxima evolución probable

Antes del orchestrator, conviene separar gradualmente:

- Fix Plan Engine.
- Check Intelligence Matrix consumible por código.
- Profile selector.
- History / Learning layer.
