# Gate0 Development Status

## Estado del proyecto

Gate0 es una plataforma de inspección técnica para archivos de packaging que evoluciona hacia un sistema experto de decisión y, posteriormente, hacia una plataforma de acondicionamiento técnico (Prepress Conditioner).

La arquitectura base se considera estable (v1). A partir de este punto el foco principal pasa a ser el desarrollo de capacidades visibles para el usuario.

---

# Principio de desarrollo

Cada sprint debe entregar SIEMPRE dos resultados:

## Producto (80%)

Una mejora visible para el usuario.

Debe responder:

> ¿Qué nueva capacidad tiene Gate0 esta semana?

---

## Arquitectura (20%)

Solo la mejora mínima necesaria para soportar esa capacidad.

La arquitectura nunca lidera al producto.

La arquitectura habilita al producto.

No se crearán nuevas capas ni componentes "por si acaso".

---

# Metodología de trabajo

Todo desarrollo seguirá este flujo:

1. Backup
2. Cambio mediante Bash siempre que sea posible.
3. Compilación.
4. Tests.
5. Validación funcional.
6. Commit.
7. Push.
8. Working tree clean.

Siempre se priorizará Bash sobre edición manual para reducir errores.

---

# Arquitectura actual

## Agentes

- Inspection Agent
- QA Decision Agent
- Packaging Expert Agent
- Reporting Agent

---

## Engines

- Inspection Engine
- Reasoning Engine
- Expert Comment Engine
- Readiness Engine
- Readiness Summary
- Business Rules

---

## Services

- Runtime Service
- History Service
- ZIP Inventory Service
- Separation Intelligence Service
- Comparison Service

---

## Operational Profile compacto en cabecera

- El perfil operativo se muestra en la cabecera como `Perfil usado`.
- El detalle técnico del perfil se despliega bajo demanda con click.
- Se evita desplazar los Top Risks hacia abajo.
- Por ahora se mantiene un solo perfil default.
- Backlog futuro: selector de perfil por cliente/usuario cuando exista login y múltiples perfiles.

---

## Operational Profile visible en Dashboard

- Dashboard muestra el perfil operativo usado en el análisis.
- Se exponen thresholds clave:
    - TAC máximo.
    - Small Text WARNING.
    - Small Text CRITICAL.
- Por ahora Gate0 usa un solo perfil default.
- Backlog futuro:
    - perfil por cliente,
    - perfil por usuario logueado,
    - selector de perfil,
    - perfil default editable por cliente/planta/proceso.

---

## Profile Hardening v1

- Gate0 expone el perfil operativo usado en cada análisis.
- `business_assessment.operational_profile` contiene thresholds clave.
- El reporte principal incluye `operational_profile`.
- Si el archivo de profile no existe, Gate0 usa fallback explícito y trazable.
- Esta capacidad fortalece la confianza comercial sin crear una Knowledge Layer formal todavía.

---

## Operational Profile

- `profiles/flexo_pet_bopp_default.json`
- Funciona como semilla operativa de futura Knowledge Layer.
- Contiene límites configurables de proceso.
- Small Text v1.1 usa umbrales desde profile:
    - warning_threshold_pt
    - critical_threshold_pt
- Reglas positivo / negativo / multitinta quedan reservadas para Small Text v2.

---

## Domain Models

- InspectionResult
- ComparisonResult

---

## Capacidades implementadas

### Intake

- PDF
- AI
- ZIP
- ZIP local

---

### Dashboard

- Readiness
- Top Risks
- Expert Comment
- PDF Viewer

---

### Color Intelligence

- Spot Colors
- White
- Separations
- Separation Summary
- Clasificación:
    - Process
    - Spot
    - Blanco
    - Barniz
    - Plano
    - Technical

---

### Text Intelligence

- Small Text Intelligence v1
- Small Text thresholds by profile v1.1
- Detección de texto vivo menor a 5 pt
- Clasificación inicial:
    - < 4 pt: CRITICAL
    - < 5 pt: WARNING
- Evidencia:
    - página
    - muestra de texto
    - tamaño en pt
    - altura aproximada en mm
    - fuente
    - bbox

---

### Artwork Consistency

- Detección AI/PDF
- Candidate Pair
- ComparisonResult
- Comparación estructural inicial
- Normalización de prefijos PDF Font Subset

---

# Backlog priorizado

## Muy Alta

- Artwork Consistency v2
- Rich Black Intelligence
- Small Text Intelligence
- Barcode Intelligence

---

## Alta

- Fix Plan Foundation
- AutoFix Classification
- Object Cleaning

---

## Media

- UX Intake
- Dashboard refinements

---

# Visión futura

Gate0 evolucionará en esta secuencia:

Inspection

↓

Reasoning

↓

Expert Decision

↓

Fix Plan

↓

AutoFix

↓

Before/After Compare

↓

Experience

↓

Knowledge

---

# Regla de oro

Cada funcionalidad nueva debe dejar:

- una mejora visible para el usuario.

- una mejora arquitectónica mínima.

Nunca una sin la otra.

## Check Intelligence Matrix v1

- Se creó `docs/check_intelligence_matrix.md`.
- Define criterio, contexto operativo, acción recomendada, fix type, limitación actual y futuro por check.
- No reemplaza todavía la lógica del motor.
- Sirve como referencia de producto para evolucionar Gate0 hacia fix asistido y futuro autofix.

---


## Architecture Layers v1

- Se creó docs/architecture_layers_v1.md.
- Documenta arquitectura actual, arquitectura objetivo y criterio para futuro orchestrator.
- Confirma que Gate0 ya opera por capas, aunque el flujo principal siga coordinado desde analyze_pdf().
- Define que no se debe refactorizar hacia orchestrator hasta que exista complejidad real de producto.

---


## Top Risk Criteria Context v1

- Cada Top Risk muestra criterio aplicado y contexto operativo.
- Esta mejora conecta la matriz de inteligencia con la experiencia visible del dashboard.
- No mueve lógica al motor todavía; es una mejora de explicación y usabilidad.

---

## Check Intelligence Matrix v2

- Se consolidó docs/check_intelligence_matrix.md como matriz maestra de inteligencia por check.
- Incluye criterio, contexto operativo, impacto, acción recomendada, fix type, limitaciones actuales y futuro.
- Mantiene la inteligencia del producto documentada antes de moverla al motor.

---


## Check Intelligence JSON v1

- Se creó `check_intelligence.py` como fuente central liviana de criterio, contexto, impacto, fix type, limitación y futuro por check.
- El reporte JSON enriquece `priority_findings` con esta inteligencia.
- El dashboard ahora puede leer criterio y contexto desde el JSON, manteniendo fallback visual.
- Esto prepara la transición futura hacia una matriz consumible por motor/agentes.

---


## Evidence Panel v1

- Cada Top Risk muestra evidencia técnica disponible desde el JSON.
- Evidencia posible:
    - página
    - severidad
    - DPI efectivo
    - TAC detectado
    - tamaño de texto
    - área de objeto
    - barcode confidence
    - método de detección
    - separaciones
    - bbox
- Mejora la confianza del usuario en el diagnóstico sin modificar el motor.

---

## Intelligence Reconciliation v1

- Se creó docs/audits/intelligence_reconciliation_v1.md.
- Compara business_rules.py, expert_comment_engine.py, check_intelligence.py, check_intelligence_matrix.md y dashboard.
- Objetivo: proteger la inteligencia ya trabajada antes de consolidar una fuente maestra.
- No modifica lógica ni comentarios expertos.

---


## Barcode Intelligence Consolidation v1

- Se consolidó `BARCODE_RISK` como primer check piloto de inteligencia protegida.
- `check_intelligence.py` ahora conserva:
    - criterio aplicado
    - contexto operativo
    - impacto posible
    - limitación actual
    - evolución futura
    - guía de preprensa
    - recomendación de una sola tinta
    - advertencia explícita de no certificar lectura/GS1 en v1
- No se reemplazaron comentarios expertos existentes.

---


## Small Text Intelligence Consolidation v1

- Se consolidó `SMALL_TEXT_RISK` como segundo check piloto de inteligencia protegida.
- `check_intelligence.py` conserva:
    - criterio aplicado por perfil operativo
    - contexto de legibilidad
    - impacto legal/regulatorio
    - guía para texto negativo
    - guía para texto multitinta
    - limitación explícita de v1
    - evolución hacia clasificación positivo/negativo/multitinta/fondo
- No se reemplazaron comentarios expertos existentes.

---


## Spot Color Intelligence Consolidation v1

- Se consolidó `SPOT_COLOR_RISK` como check de inteligencia protegida.
- `check_intelligence.py` conserva:
    - white ink / múltiples blancos
    - nombres genéricos
    - duplicidades de nomenclatura
    - separaciones técnicas
    - racionalización de spots
    - limitación explícita de v1
- No se reemplazaron comentarios expertos existentes.

---


## High TAC Intelligence Consolidation v1

- Se consolidó `HIGH_TAC_RISK` como check de inteligencia protegida.
- `check_intelligence.py` conserva:
    - límite TAC por perfil operativo
    - impacto de secado, repinte, ganancia y estabilidad
    - importancia del área afectada
    - relación con negro enriquecido
    - limitación explícita de v1
- No se reemplazaron comentarios expertos existentes.

---


## Overprint Intelligence Consolidation v1

- Se consolidó `OVERPRINT_RISK` como check de inteligencia protegida.
- `check_intelligence.py` conserva:
    - sobreimpresión intencional vs error
    - riesgo especial de blanco + overprint
    - necesidad de validación visual y separaciones
    - limitación explícita de detección parcial v1
    - no prometer corrección automática
- No se reemplazaron comentarios expertos existentes.

---


## Separation Count Intelligence Consolidation v1

- Se consolidó `SEPARATION_COUNT_RISK` como check de inteligencia protegida.
- `check_intelligence.py` conserva:
    - criterio por perfil operativo
    - complejidad por número de separaciones imprimibles
    - validación de capacidad de prensa
    - racionalización de spots
    - diferencia entre separaciones imprimibles y técnicas
    - limitación explícita de v1
- No se reemplazaron comentarios expertos existentes.

---


## Font Intelligence Consolidation v1

- Se consolidó `FONT_NOT_EMBEDDED` como check de inteligencia protegida.
- `check_intelligence.py` conserva:
    - riesgo de sustitución tipográfica
    - impacto en layout, legales y apariencia
    - recomendación de incrustar o convertir a curvas
    - atención especial a textos legales/obligatorios
    - limitación explícita de v1
- No se reemplazaron comentarios expertos existentes.

---


## PDF Structure Intelligence Consolidation v1

- Se consolidó `PDF_STRUCTURE_RISK` como check de inteligencia protegida.
- `check_intelligence.py` conserva:
    - páginas vacías
    - tamaño de archivo
    - cantidad de objetos/imágenes
    - complejidad estructural
    - impacto en RIP, trapping, imposición y automatización
    - recomendación de optimizar/reconstruir/solicitar nuevo archivo
    - limitación explícita de v1
- No se reemplazaron comentarios expertos existentes.

---


## Low Image Resolution Intelligence Consolidation v1

- Se consolidó `LOW_IMAGE_RESOLUTION` como check de inteligencia protegida.
- `check_intelligence.py` conserva:
    - DPI efectivo al tamaño final
    - mínimos del perfil operativo
    - importancia del área afectada
    - rol visual de imagen como limitación actual
    - relación con barcode dedupe
    - limitación explícita de v1
- No se reemplazaron comentarios expertos existentes.

---


## RGB Object Intelligence Consolidation v1

- Se consolidó `RGB_OBJECT` como check de inteligencia protegida.
- `check_intelligence.py` conserva:
    - riesgo de conversión RGB no controlada
    - impacto en color aprobado / prueba de color
    - necesidad de perfil aprobado
    - limitación explícita de v1
    - no prometer corrección automática
- Con esto queda consolidada la inteligencia base de los checks actuales.

---


## Dashboard Check Intelligence Full v1

- El dashboard consume más campos enriquecidos desde `check_intelligence.py` vía JSON:
    - criterio aplicado
    - contexto operativo
    - impacto posible
    - limitación actual
    - evolución futura
    - guías específicas por check
    - alcance / do_not_claim
- El dashboard mantiene fallback visual, pero deja de ser la fuente maestra de inteligencia.
- Esto protege los comentarios y criterios ya trabajados sin duplicarlos manualmente en UI.

---

## Backlog UX — Top Risk Detail compacto

- El detalle de Top Risk ya muestra inteligencia completa, evidencia, criterio, contexto, impacto, limitación, evolución futura, guías específicas y acción.
- Para primera etapa se mantiene así porque aporta trazabilidad completa.
- Backlog futuro:
    - compactar visualmente la vista.
    - reducir redundancia.
    - dejar visible solo resumen, evidencia clave, criterio/contexto y acción.
    - mover impacto, limitación, evolución futura y guías específicas a secciones expandibles.
- No implementar ahora; validar primero con uso real.

---


## Compact Top Risk UX v1

- Se compactó el detalle de Top Risk para reducir saturación visual.
- La evidencia técnica queda en desplegable.
- Criterio, contexto, impacto, limitación y evolución futura quedan en desplegable.
- Las guías específicas del check quedan en desplegable.
- El bloque de acción recomendada y tipo de corrección se mantiene visible.
- Categorías técnicas como Technical / Dimensions / Mechanical Artwork / Substrate bajan protagonismo visual cuando aparecen en el dashboard.
- No se modificó motor ni inteligencia; solo presentación.

---


## Process Color Detection v1

- Gate0 deja de asumir CMYK completo para el conteo operativo de separaciones.
- `SEPARATION_COUNT_RISK` ahora calcula:
    - colores de proceso detectados
    - spots imprimibles
    - total operativo = proceso detectado + spots imprimibles
- Nuevos campos:
    - `process_colors_detected`
    - `process_color_count`
    - `process_count_source`
    - `process_detection_confidence`
    - `printable_spot_count`
- Si no se detectan colores de proceso, no se suman 4 automáticamente.
- Limitación v1: detección basada en operadores CMYK de content stream; no certifica todos los casos complejos ni imágenes raster.

---


## Non-printable Separation Classification v1

- Gate0 excluye separaciones de plano/técnicas del conteo operativo.
- Ejemplos no productivos:
    - All
    - Pie
    - Sustrato / Substrate
    - Texto / Text
    - Plano
    - Technical / Technical Drawing
    - Dimensions
    - Mechanical Artwork
    - Dieline / Troquel / Corte / Guía
- `Detectadas por parser` puede ser mayor que `Conteo operativo`.
- `Conteo operativo` debe contar solo proceso detectado + spots imprimibles.
- Se corrige fallback para que cero sea valor válido y no caiga a total detectado.

---


## Dashboard Layout UX v2

- Se amplía el visor PDF para hacerlo más protagonista.
- Se reordena el panel derecho:
    1. Color Separation Summary
    2. Top Risks
    3. Riesgo seleccionado
- Color Separation Summary se compacta en tabla/lista densa.
- Se mantiene la diferenciación visual de Spot / Blanco / Plano / Technical.

---


## Compact Separation Summary v1

- Color Separation Summary se compacta para no desplazar Top Risks.
- La tabla de separaciones usa scroll interno.
- Separaciones técnicas/plano como Dimensions, Mechanical Artwork, Technical Drawing y Sustrato deben clasificarse como no productivas.
- Objetivo UX: mantener Top Risks y Riesgo seleccionado visibles junto al visor PDF.

---


## Separation Summary Below Viewer v1

- Color Separation Summary se mueve debajo del visor PDF.
- El panel derecho queda enfocado en Top Risks y Riesgo seleccionado.
- Las separaciones se dividen en dos grupos:
    - Imprimibles
    - No imprimibles / técnicas
- Objetivo UX: permitir seleccionar riesgos y leer el detalle mientras el visor PDF sigue visible.

---
