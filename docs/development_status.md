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


## Risk Preview Crop + Separation Count Correction v1

- `/api/risk-preview` ahora devuelve un recorte ampliado alrededor del `bbox`, no la página completa.
- El objetivo es que el usuario vea la zona específica del riesgo.
- El dashboard debe mostrar umbrales reales por check en vez de “Regla definida por Gate0”.
- `C PERU`, `M PERU`, `Y PERU`, `K PERU` se clasifican como separaciones de plano/no imprimibles.
- El conteo de `SEPARATION_COUNT_RISK` debe alinearse con Color Separation Summary.

---


## Risk Visual Evidence Stabilization v1

- Se endurece `BARCODE_RISK` para evitar falsos positivos por logos o íconos cuadrados de baja resolución.
- QR ya no se detecta solo por geometría cuadrada; requiere evidencia adicional.
- Se limita ruido de candidatos barcode/QR.
- El detalle de riesgo debe mostrar umbral operativo real, no “Regla definida por Gate0”.
- `SEPARATION_COUNT_RISK` ahora explicita conteo operativo, proceso y spots para facilitar cruce con Color Separation Summary.

---


## Risk Preview Final Stabilization v1

- `BARCODE_RISK` ahora valida patrón visual de barras 1D para reducir falsos positivos con logos o etiquetas rectangulares.
- QR queda conservador en v1: no se marca solo por geometría cuadrada.
- `SEPARATION_COUNT_RISK` usa la misma clasificación base que `Color Separation Summary` cuando existen separaciones explícitas.
- El dashboard fuerza el reemplazo visual de “Regla definida por Gate0” por umbrales operativos reales.
- Objetivo: estabilizar Risk Visual Evidence antes de commitear.

---


## Safe Sep Count + Barcode Stabilization v1

- `SEPARATION_COUNT_RISK` usa como fuente principal la misma clasificación de `Color Separation Summary`.
- Esto evita diferencias entre el conteo visual operativo y el Top Risk de separaciones.
- `BARCODE_RISK` de baja confianza se degrada a INFO para evitar falsos positivos críticos.
- Objetivo: estabilizar MVP antes de avanzar a validaciones más sofisticadas de barcode/QR.

---


## Barcode Risk Disabled by Default v1

- `BARCODE_RISK` queda desactivado por defecto en el MVP.
- Motivo: la detección por geometría/DPI puede generar falsos positivos en logos, íconos o etiquetas técnicas.
- Puede activarse para pruebas controladas con `GATE0_ENABLE_BARCODE_RISK=true`.
- El check debe evolucionar a una versión más confiable antes de volver a Top Risks:
    - decodificación real cuando sea posible,
    - validación de patrón visual,
    - quiet zone,
    - ubicación probable,
    - exclusión de logos/claims/etiquetas no funcionales.

---


## Printable Area Guard v1

- Se agrega enriquecimiento de findings con `bbox` contra cajas PDF de página.
- Prioridad de área útil:
    1. TrimBox confirmado
    2. ArtBox fallback
    3. CropBox fallback
    4. Página completa no confirmada
- Se agregan campos:
    - `printable_area_source`
    - `printable_area_confidence`
    - `is_inside_printable_area`
    - `printable_area_overlap_percent`
- `SMALL_TEXT_RISK` y `LOW_IMAGE_RESOLUTION` fuera del área útil confirmada se degradan a INFO.
- El dashboard muestra si el hallazgo está dentro/fuera del área imprimible confirmada.
- Si no hay caja confiable, Gate0 mantiene comportamiento actual.

---

## Backlog — Risk Visual Evidence Occurrence Navigation

Cuando un Top Risk tenga múltiples ocurrencias detectadas, el panel de Riesgo seleccionado debería permitir navegar entre ocurrencias.

Ejemplo:

- Texto pequeño / legibilidad: 25 ocurrencias detectadas.
- Mostrar navegación: Anterior / Siguiente.
- Mostrar contador: 1 / 25.
- Al cambiar ocurrencia, actualizar:
    - preview ampliada,
    - bbox,
    - evidencia técnica,
    - texto detectado,
    - área imprimible,
    - solape con área útil.

Prioridad inicial:

1. SMALL_TEXT_RISK
2. LOW_IMAGE_RESOLUTION
3. Otros riesgos con bbox confiable

Objetivo: que Gate0 no solo diga que existen 25 ocurrencias, sino que permita revisarlas una por una desde el dashboard.

---


## Risk Evidence Quality v1

- Se mejora el bloque `Riesgo seleccionado` del dashboard.
- Se agrega resumen ejecutivo del riesgo:
    - Tipo de riesgo
    - Confianza
    - Alcance
    - Área imprimible
    - Umbral / criterio
    - Tipo de corrección
- El umbral visible usa `thresholdLabel(r, insight)` en vez de depender solo de `risk_evidence.threshold`.
- Se mantiene la preview visual ampliada para riesgos con `bbox`.
- Se mantiene evidencia técnica desplegable, inteligencia del check, guías específicas y feedback.

---


## Risk Occurrence Navigation v1

- `top_risks` ahora puede incluir `occurrences[]` para riesgos agrupados.
- Cada ocurrencia conserva datos útiles:
    - `page`
    - `bbox`
    - `value`
    - `sample_text`
    - `font_size_pt`
    - `effective_dpi`
    - `printable_area_source`
    - `is_inside_printable_area`
    - `printable_area_overlap_percent`
- El dashboard permite navegar ocurrencias dentro de `Riesgo seleccionado`.
- La preview ampliada y la evidencia técnica se actualizan al cambiar de ocurrencia.
- Prioridad inicial: `SMALL_TEXT_RISK` y `LOW_IMAGE_RESOLUTION`.

---

## Backlog — Risk Visual Evidence Clustering v2

Durante la validación de Risk Occurrence Navigation v1 se observó que algunos riesgos, especialmente `SMALL_TEXT_RISK`, pueden mostrar muchas ocurrencias dentro del mismo párrafo o bloque visual.

Desde el punto de vista de diseño/preprensa, varias ocurrencias cercanas deberían tratarse como una sola zona problemática.

Objetivo futuro:

- Agrupar ocurrencias cercanas por página y proximidad visual.
- Mostrar navegación por zona, no solo por ocurrencia individual.
- Mantener conteo interno de textos/objetos detectados.
- Mostrar algo como: `6 zonas / 25 textos pequeños`.
- Generar preview ampliada con el bbox unido de toda la zona o párrafo.
- Prioridad inicial: `SMALL_TEXT_RISK`.
- Segunda prioridad: `LOW_IMAGE_RESOLUTION` cuando varias imágenes/fragmentos correspondan a una misma zona visual.

---


## Hotfix — Spot Count Alignment + Occurrence Navigation Guard

Se corrigen dos inconsistencias detectadas en validación visual:

1. `SPOT_COLOR_RISK` debe usar la misma clasificación que `Color Separation Summary`.
    - Cuenta solo tintas `Spot` y `Blanco` imprimibles.
    - Excluye process colors.
    - Excluye separaciones `Plano` / `Technical`.
    - El conteo total operativo queda reservado para `SEPARATION_COUNT_RISK`.

2. La navegación de ocurrencias solo debe mostrarse para riesgos visuales con `bbox`.
    - Aplica a `SMALL_TEXT_RISK`.
    - Aplica a `LOW_IMAGE_RESOLUTION`.
    - Aplica a `BARCODE_RISK` solo cuando se reactive y tenga bbox confiable.
    - No aplica a `SPOT_COLOR_RISK`, porque es un riesgo global/configuración.

---


## Hotfix — Material as Technical Separation

Se clasifica `Material` / `Materials` / `Materiales` como separación no imprimible/técnica.

Criterio:

- `Material` representa información de sustrato, referencia técnica o plano.
- No debe contarse como tinta imprimible.
- No debe sumar en `SPOT_COLOR_RISK`.
- No debe sumar en `SEPARATION_COUNT_RISK`.
- Debe aparecer en el bloque de separaciones no imprimibles/técnicas del dashboard.

---


## Sprint 20A — Separation Classification Contract

Se define `SeparationIntelligenceService` como fuente oficial de clasificación de separaciones.

Tipos oficiales:

- `Process`: imprimible / operativo.
- `Spot`: imprimible / operativo.
- `Blanco`: imprimible / operativo.
- `Barniz`: imprimible / operativo.
- `Plano`: no imprimible / técnico.
- `Technical`: no imprimible / técnico.

Reglas clave:

- `C`, `M`, `Y`, `K` puros se clasifican como `Process`.
- `C PERU`, `M PERU`, `Y PERU`, `K PERU` se clasifican como `Plano`.
- `Material`, `Sustrato`, `Substrate`, `Dimensions`, `Mechanical Artwork`, `Technical Drawing` se clasifican como `Technical`.
- `White`, `Blanco`, `Opaque White` se clasifican como `Blanco`.
- `Barniz`, `Varnish`, `Lacquer`, `Coating` se clasifican como `Barniz`.
- Todo lo demás se clasifica como `Spot`.

Uso por ubicación:

- Si una separación imprimible aparece 100% fuera del `TrimBox` confirmado y no hay `BleedBox` útil, puede reclasificarse como `Technical` por ubicación.
- Si está fuera del `TrimBox` pero dentro del `BleedBox`, sigue siendo imprimible.
- Si no existe información de uso por ubicación, no se reclasifica.

Nota:

- Sprint 20A deja el contrato y el soporte de datos.
- Sprint 20B debe extraer el uso real por separación dentro/fuera de `TrimBox` / `BleedBox`.

---


## Sprint 20B1 — Separation Usage Capability Probe

Se agrega un probe experimental para evaluar si el PDF trae señales de bajo nivel suficientes para mapear uso de separaciones.

El probe reporta:

- separaciones detectadas,
- presencia de recursos `/Separation`,
- presencia de operadores `cs` / `CS`,
- presencia de operadores `scn` / `SCN`,
- páginas con señales de uso de color space,
- limitaciones actuales.

Decisión importante:

- `safe_for_reclassification` queda en `false`.
- `can_compute_bbox_by_separation` queda en `false`.
- Este bloque no cambia conteos ni decisiones operativas.
- La reclasificación por ubicación queda reservada para una etapa posterior, cuando pueda asociarse separación específica con geometría/bbox confiable.

---


## Sprint 20C — Dashboard Separation Consistency

Se ajusta `Color Separation Summary` para que el dashboard no reclasifique separaciones por nombre.

Regla:

- El backend clasifica usando `SeparationIntelligenceService`.
- El dashboard usa `item.is_printable` como fuente oficial.
- Fallback solo para reportes antiguos:
    - `Process`, `Spot`, `Blanco`, `Barniz` → imprimibles.
    - `Plano`, `Technical` → no imprimibles / técnicas.
- Se evita que el frontend mantenga una lógica propia con nombres como `Sustrato`, `Material`, `Technical Drawing`, etc.
- Objetivo: alinear visualmente `Color Separation Summary`, `SPOT_COLOR_RISK` y `SEPARATION_COUNT_RISK`.

---
