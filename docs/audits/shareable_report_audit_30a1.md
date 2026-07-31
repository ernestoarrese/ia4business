# Sprint 30A.1 — Shareable Report Audit

## Objetivo

Auditar el estado actual de Gate0 para definir la forma mínima y segura de crear un reporte compartible.

## Estado confirmado

Gate0 ya tiene:

- dashboard funcional;
- `report_data` completo desde `gate0_check.py`;
- `production_readiness_v2`;
- `operational_profile`;
- `production_readiness_v2.operational_context`;
- endpoint `/api/report`;
- endpoint `/api/pdf`;
- dashboard con `sid`;
- pruebas de dashboard y rutas pasando.

## Hallazgo principal

El producto ya tiene los datos necesarios para un reporte ejecutivo.

No hace falta duplicar la lógica del dashboard ni generar PDF todavía.

## Opción recomendada

Implementar:

### A) Ruta imprimible

Crear una ruta:

- `/report/print?sid=...`

Debe renderizar HTML simple, imprimible y compartible.

### B) Botón en dashboard

Agregar un botón compacto:

- `Reporte ejecutivo`

Debe abrir `/report/print?sid=...` en nueva pestaña.

## Contenido mínimo del reporte

El reporte debe ser una hoja ejecutiva con:

1. Decisión Gate0.
2. Readiness Score.
3. Perfil productivo usado.
4. Top 3 riesgos.
5. Acción recomendada.
6. Limitaciones del análisis.

## Qué NO debe incluir

No incluir:

- todo el JSON;
- todos los hallazgos técnicos;
- evidencia visual completa;
- visor PDF;
- feedback;
- tablas extensas;
- bloques duplicados del dashboard.

## Principio UX

El reporte no debe ser otro dashboard.

Debe responder rápidamente:

- ¿Se puede liberar?
- ¿Contra qué perfil fue evaluado?
- ¿Qué debo revisar primero?
- ¿Qué limitación debo tener presente?

## Riesgos

- Crear un reporte demasiado largo y poco accionable.
- Duplicar contenido del dashboard.
- Mostrar detalles técnicos que distraigan de la decisión.
- Generar PDF prematuramente antes de validar el contenido ejecutivo.

## Plan recomendado

### Sprint 30A.2 — Shareable Report Presenter

Crear una función backend que transforme `report_data` en un resumen ejecutivo.

### Sprint 30A.3 — Printable Report Route

Crear `/report/print?sid=...`.

### Sprint 30A.4 — Dashboard Button

Agregar botón compacto desde dashboard.

### Sprint 30A.5 — Functional Validation & Closure

Validar flujo real y cerrar sprint.

