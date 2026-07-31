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


## Sprint 22 — Risk Detail UX Compact Mode

Se compacta el panel `Riesgo seleccionado` para reducir saturación visual.

Nueva jerarquía:

Visible por defecto:

- Qué se encontró.
- Por qué importa.
- Qué hacer.

Colapsado:

- Resumen técnico.
- Evidencia técnica.
- Criterio, contexto y alcance.
- Guías específicas del check.
- Limitaciones de la versión actual.

Ajustes realizados:

- `renderRiskQualitySummary()` pasa a mostrarse dentro de un bloque colapsable.
- `renderRiskVisualEvidence()` deja de mostrar mensaje vacío cuando el riesgo es global y no tiene bbox.
- El bloque principal pasa de 4 tarjetas visibles a 3 tarjetas ejecutivas.
- `Alcance v1` deja de competir visualmente con la acción recomendada y queda disponible en el detalle técnico/guías cuando aplica.

Objetivo:

- Gate0 no debe mostrar todo lo que sabe al mismo tiempo.
- Primero debe ayudar a decidir.
- El detalle técnico debe quedar disponible, pero no saturar la lectura principal.

---


## Sprint 22A — Risk Detail Executive Language

Se mejora el lenguaje del panel `Riesgo seleccionado`.

Ajustes:

- Los 3 bloques ejecutivos usan lenguaje más cotidiano:
    - Qué se encontró.
    - Por qué importa.
    - Qué hacer.
- Se evita mostrar valores técnicos crudos como `has_overprint_fill=True`.
- Para `OVERPRINT_RISK`, el dashboard diferencia:
    - sobreimpresión genérica,
    - sobreimpresión con contexto de blanco.
- Los 3 bloques se muestran en una sola columna para mejorar lectura en el panel derecho.

Criterio de producto:

- Overprint debe sentirse como validación contextual.
- Si hay blanco, `WARNING` es correcto, pero no significa defecto confirmado.
- Gate0 no debe afirmar que el blanco está sobreimprimiendo hasta tener evidencia por objeto/separación.

---


## Sprint 23A — Production Readiness v2 Foundation

Se agrega una nueva capa ejecutiva `production_readiness_v2`.

Objetivo:

- Convertir hallazgos técnicos en una decisión de producción más clara.
- Responder si el archivo está listo para producir.
- Explicar motivo principal.
- Estimar tiempo de revisión.
- Listar qué revisar primero.

Estados:

- `READY`: listo para producir.
- `READY_WITH_NOTES`: liberable con observaciones.
- `REVIEW_REQUIRED`: requiere revisión antes de liberar.
- `HIGH_RISK`: alto riesgo.
- `NO_GO`: no liberar sin corrección o revisión técnica.

Criterio:

- Esta capa no reemplaza todavía el readiness engine original.
- Se agrega como capa producto/ejectutiva encima de `readiness_assessment` y `priority_findings`.
- Overprint genérico INFO no empuja revisión requerida.
- Riesgos WARNING/CRITICAL con peso operativo sí aparecen como revisión prioritaria.

Dashboard:

- Se agrega bloque `Production Readiness` en el hero.
- Muestra decisión sugerida, riesgo principal, tiempo estimado y qué revisar primero.

---


## Sprint 23B — Production Readiness v2 Language & Decision Quality

Se refina la capa `production_readiness_v2` para que el output sea más cercano al criterio operativo de preprensa.

Cambios:

- Se agrega pregunta ejecutiva: `¿Está este archivo listo para producir?`
- Se agrega `answer` en lenguaje simple.
- Se agrega `supervisor_summary`.
- Se agrega `next_step`.
- Se mejora el nombre de riesgos en `what_to_review_first`.
- Se mejora lenguaje para sobreimpresión con blanco:
  - No se comunica como defecto confirmado.
  - Se comunica como validación requerida.
  - Se sugiere revisar con Overprint Preview.
- El dashboard muestra una lectura más ejecutiva dentro del bloque Production Readiness.

Objetivo de producto:

- Que Gate0 no solo liste riesgos técnicos.
- Que Gate0 ayude a decidir si el archivo puede liberarse, debe revisarse o debe retenerse.

---


## Sprint 23C — Hide Legacy Hero Summary

Se oculta el resumen legacy del hero cuando existe `production_readiness_v2`.

Motivo:

- El resumen antiguo repetía información que ahora aparece mejor explicada en Production Readiness.
- Se mantiene como fallback para reportes antiguos que no tengan `production_readiness_v2`.

Resultado esperado:

- El bloque superior queda más limpio.
- La decisión ejecutiva principal vive en Production Readiness.
- Se reduce redundancia visual.

---


## Sprint 23D — Production Readiness Priority Logic

Se mejora la priorización interna de `production_readiness_v2`.

Objetivo:

- Que `primary_risk` represente mejor lo que preprensa revisaría primero.
- Que `what_to_review_first` quede ordenado por prioridad operativa, no solo por orden de aparición.
- Alinear el bloque Production Readiness con Top Risks.

Criterios agregados:

- Severidad.
- Riesgo bloqueante.
- Peso de score.
- Tipo de check.
- Sobreimpresión con blanco.
- Área imprimible / solape visual.
- Necesidad de validación visual.

Regla importante:

- Un riesgo CRITICAL bloqueante sigue teniendo prioridad sobre cualquier WARNING.
- Sobreimpresión WARNING, especialmente con blanco o alto solape visual, debe aparecer antes que riesgos menores de revisión.
- Overprint INFO contextual no debe subir artificialmente.

---


## Sprint 23D.1 — Overprint Priority Hotfix

Se ajusta la priorización de `production_readiness_v2`.

Motivo:

- En un caso real, Top Risks mostraba sobreimpresión primero, pero Production Readiness seguía mostrando texto pequeño como riesgo principal.
- Esto generaba inconsistencia de lectura.

Ajuste:

- `OVERPRINT_RISK` en `WARNING` sube prioridad.
- Si el texto del hallazgo indica área visual significativa o 100% de impacto visual, sube prioridad adicional.
- `OVERPRINT_RISK` en `INFO` sigue sin escalar artificialmente.
- Riesgos `CRITICAL` o bloqueantes siguen ganando prioridad.

Resultado esperado:

- Production Readiness debe priorizar sobreimpresión visual significativa antes que texto pequeño.
- Se mantiene la lógica de que no es defecto confirmado, sino validación requerida.

---


## Sprint 23D.2 — Deduplicate Production Readiness Review Items

Se ajusta `production_readiness_v2` para evitar redundancia visual.

Cambios:

- `what_to_review_first` agrupa ocurrencias repetidas del mismo check.
- Si hay dos textos pequeños, se muestra una sola línea con `occurrence_count`.
- El dashboard puede mostrar `(2 ocurrencias)` junto al riesgo agrupado.
- Se oculta el comentario libre superior del panel de riesgo seleccionado porque repetía el contenido de las tarjetas ejecutivas.

Resultado esperado:

- Production Readiness deja de listar dos veces `Revisar texto pequeño`.
- Riesgo seleccionado queda más limpio: título, severidad, navegación de ocurrencias, tarjetas ejecutivas y evidencia visual.

---


## Sprint 24A.1 — Visible Production Readiness Drilldown

Se ajusta el bloque `Production Readiness`:

- Se oculta el título redundante `Production Readiness`.
- Se mantiene la pregunta ejecutiva `¿Está este archivo listo para producir?`.
- Cada item de `Qué revisar primero` muestra `Ver evidencia y detalle`.
- Los items son clickeables y seleccionan automáticamente el Top Risk correspondiente.
- Se hace scroll hacia el panel de riesgo seleccionado.

Objetivo:

- Hacer evidente el acceso directo.
- Evitar agregar más texto explicativo.
- Conectar decisión ejecutiva con evidencia visual.

---


## Sprint 24A.2 — Drilldown Click Fix

Se corrige el acceso directo desde `Production Readiness`.

Cambios:

- Se elimina el texto redundante `Ver evidencia y detalle`.
- El nombre del hallazgo queda clickeable.
- El click selecciona automáticamente el Top Risk correspondiente.
- Se agrega fallback por nombre del hallazgo si el código del check no llega correctamente.
- Se hace scroll hacia `Riesgo seleccionado`.

Resultado esperado:

- Click en `Validar sobreimpresión` abre el detalle de sobreimpresión.
- Click en `Revisar texto pequeño` abre el detalle de texto pequeño y sus ocurrencias.

---


## Sprint 24A.3 — Drilldown Event Delegation

Se corrige el click desde `Production Readiness`.

Cambios:

- Se agrega event delegation global para `.pr2-review-link`.
- Se mantiene `onclick` directo como respaldo.
- El click busca el Top Risk por `check`.
- Si el `check` no llega, infiere el check desde el título del item.
- Al encontrar el riesgo, ejecuta `selectRisk(idx, 0)` y hace scroll hacia `Riesgo seleccionado`.

Resultado esperado:

- Click en `Validar sobreimpresión` selecciona el riesgo de sobreimpresión.
- Click en `Revisar texto pequeño` selecciona texto pequeño y muestra ocurrencias.

---


## Sprint 25A — Risk Visual Evidence Clustering

Se agrega agrupación visual de ocurrencias para riesgos con bbox.

Alcance inicial:

- `SMALL_TEXT_RISK`
- `LOW_IMAGE_RESOLUTION`

Cambios backend:

- `sort_top_risks()` conserva `occurrences`.
- Se agrega `visual_zones` cuando hay ocurrencias cercanas o solapadas.
- Cada zona contiene:
  - `zone_index`
  - `page`
  - `bbox` unido
  - `occurrence_count`
  - `occurrences`
- Se mantiene compatibilidad con navegación antigua por `occurrences`.

Cambios dashboard:

- Si existen `visual_zones`, la navegación usa zonas.
- Muestra `Zona X / N`.
- Muestra cuántas ocurrencias contiene la zona.
- La evidencia visual usa el bbox unido de la zona.
- Top Risks puede mostrar cantidad de ocurrencias y zonas.

Criterio:

- No se aplica todavía a `OVERPRINT_RISK`.
- No infiere intención de diseño.
- Solo agrupa por cercanía geométrica en la misma página.

---


## Sprint 25A.1 — Safe BBox Helper

Se corrige error JavaScript en navegación de zonas visuales.

Problema:

- El dashboard usaba `hasRenderableBbox()` dentro de la navegación por `visual_zones`.
- La función no estaba definida en el bundle final.
- Al seleccionar un riesgo con zonas visuales, el panel `Riesgo seleccionado` fallaba.

Corrección:

- Se agrega helper global `hasRenderableBbox(item)`.
- Soporta bbox como array `[x0,y0,x1,y1]` o string `"x0,y0,x1,y1"`.
- Permite que `riskVisualZones()` filtre zonas renderizables sin romper `selectRisk()`.

---


## Sprint 25B — Printable Area Priority Filter

Se agrega filtro de prioridad por área imprimible dentro de `production_readiness_v2`.

Objetivo:

- Reducir falsos positivos operativos.
- Bajar prioridad cuando un hallazgo visual está fuera del área imprimible confirmada.
- Mantener prioridad cuando el hallazgo está dentro de TrimBox/área imprimible.
- No bajar prioridad cuando el área imprimible no está confirmada.

Aplica inicialmente a:

- `RGB_OBJECT`
- `LOW_IMAGE_RESOLUTION`
- `SMALL_TEXT_RISK`
- `HIGH_TAC_RISK`
- `BARCODE_RISK`

Reglas:

- Fuera de área imprimible confirmada con overlap 0–1% → observación contextual.
- Dentro de área imprimible confirmada → riesgo efectivo.
- Área no confirmada → no se degrada automáticamente.

Campos agregados en `production_readiness_v2`:

- `primary_printable_area_status`
- `printable_area_status` por item de `what_to_review_first`

Estados posibles:

- `OUTSIDE_CONFIRMED_PRINTABLE_AREA`
- `INSIDE_CONFIRMED_PRINTABLE_AREA`
- `PARTIAL_OR_UNCLEAR_PRINTABLE_AREA`
- `PRINTABLE_AREA_NOT_CONFIRMED`

---


## Sprint 25B.1 — Unconfirmed Printable Area Fix

Se corrige la validación de área imprimible confirmada.

Problema:

- `UNCONFIRMED_FULL_PAGE` estaba siendo interpretado como confirmado porque contiene la palabra `CONFIRMED`.
- Esto hacía que hallazgos con área imprimible no confirmada pudieran degradarse incorrectamente a observación contextual.

Corrección:

- Se evita usar búsqueda parcial de texto.
- `UNCONFIRMED_FULL_PAGE` ahora se trata correctamente como no confirmado.
- Solo fuentes explícitas como `TRIMBOX_CONFIRMED`, `ARTBOX_CONFIRMED`, `CROPBOX_CONFIRMED` o confianza `CONFIRMED/HIGH` se consideran confirmadas.

Resultado esperado:

- Si el área no está confirmada, Gate0 no baja automáticamente la prioridad.
- Si el hallazgo está fuera de TrimBox confirmado, sí puede pasar a observación contextual.

---


## Sprint 25C.1 — RGB_OBJECT Evidence Depth

Se mejora la evidencia de `RGB_OBJECT`.

Hallazgo del audit:

- El detector actual identifica operadores RGB simples en content stream:
  - `rg` para relleno/fill.
  - `RG` para trazo/stroke.
- No existe todavía bbox ni ubicación visual del objeto RGB.
- Por tanto, no se puede confirmar si el RGB está dentro/fuera del TrimBox.

Cambios:

- `check_rgb_objects()` agrega evidencia técnica:
  - `rgb_values`
  - `rgb_operator`
  - `rgb_mode`
  - `color_space`
  - `detection_method`
  - `bbox_available`
  - `location_confidence`
  - `object_location_status`
  - `printable_area_status`
  - `requires_manual_location_review`
- `evaluate_rgb_object()` deja de inventar área `0.00%` cuando no hay bbox ni área.
- El dashboard muestra evidencia específica para RGB:
  - espacio de color
  - operador
  - modo
  - método de detección
  - ubicación visual no disponible
  - área imprimible no evaluable sin bbox

Criterio de producto:

- RGB detectado sin bbox queda como observación contextual.
- Si en el futuro RGB tiene bbox/área, la regla puede escalar a WARNING/CRITICAL según tamaño, tipo de objeto y área imprimible.
- No se afirma que el color final será incorrecto; se indica riesgo de conversión no controlada.

Backlog:

- `RGB_OBJECT v2`: asociar RGB a objeto visual, bbox, área imprimible y tipo de objeto.

---


## Sprint 25C.2 — HIGH_TAC_RISK Evidence Depth

Se mejora la evidencia de `HIGH_TAC_RISK`.

Hallazgo del audit:

- El detector actual identifica operadores CMYK simples en content stream.
- Calcula TAC sumando C+M+Y+K.
- Genera `detected_tac`, pero no existe todavía bbox ni ubicación visual exacta.
- Por tanto, no se puede confirmar todavía si el TAC alto está dentro/fuera del TrimBox ni el área afectada.

Cambios:

- `check_high_tac()` agrega evidencia técnica:
  - `detected_tac`
  - `tac_limit`
  - `tac_excess`
  - `cmyk_values`
  - `cmyk_operator`
  - `cmyk_mode`
  - `color_space`
  - `detection_method`
  - `bbox_available`
  - `location_confidence`
  - `object_location_status`
  - `printable_area_status`
  - `requires_manual_location_review`
- `evaluate_high_tac_risk()` deja de inventar área `0.00%` cuando no hay bbox ni área.
- El dashboard muestra evidencia específica para TAC:
  - TAC detectado
  - límite TAC
  - exceso TAC
  - CMYK detectado
  - operador
  - modo
  - ubicación visual no disponible
  - área imprimible no evaluable sin bbox

Criterio de producto:

- TAC alto detectado sin bbox queda como observación contextual.
- Si en el futuro TAC tiene bbox/área, la regla puede escalar a WARNING/CRITICAL según exceso, área y perfil operativo.
- No se afirma ubicación exacta si el motor no puede probarla.

Backlog:

- `HIGH_TAC_RISK v2`: asociar TAC alto a objeto visual, bbox, área imprimible y tipo de construcción, por ejemplo negro enriquecido.

---


## Sprint 25C.3 — FONT_NOT_EMBEDDED Evidence Depth

Se mejora la evidencia de `FONT_NOT_EMBEDDED`.

Hallazgo del audit:

- `detect_live_fonts()` usa `page.get_fonts(full=True)`.
- Hoy detecta fuente no embebida a nivel de recurso PDF:
  - página
  - xref
  - nombre base
  - nombre interno
  - tipo
  - extensión
  - estado de embebido
- Todavía no asocia de forma confiable qué texto específico usa esa fuente.

Cambios:

- `check_font_embedding()` agrega:
  - `font_name`
  - `font_name_raw`
  - `font_type`
  - `font_ext`
  - `font_embedding_status`
  - `detection_method`
  - `text_association_status`
  - `affected_text_available`
  - `bbox_available`
  - `requires_manual_text_review`
- `evaluate_font_not_embedded()` mantiene severidad crítica.
- Dashboard muestra evidencia específica de fuente.
- No se afirma texto afectado si no está asociado.

Criterio de producto:

- Fuente no embebida sigue siendo riesgo crítico.
- Gate0 debe ser honesto: detecta la fuente, pero no confirma todavía el texto exacto afectado.
- Acción recomendada: incrustar fuente, convertir texto a curvas o corregir el recurso.

Backlog:

- `FONT_NOT_EMBEDDED v2`: cruzar fuente no embebida con spans de texto para identificar texto, bbox y criticidad contextual.

---


## Sprint 26A — Separation Usage v2 Foundation

Se agrega una capa informativa `separation_usage_v2`.

Objetivo:

- Transformar `separation_summary` + `separation_usage_capability` en una lectura más clara por separación.
- Mostrar si hay señales de presencia/uso a nivel de recursos PDF.
- Mantener explícitamente que la capa es informativa.

No cambia:

- `operational_total`
- clasificación de separaciones
- `SPOT_COLOR_RISK`
- `SEPARATION_COUNT_RISK`
- `Production Readiness`

Campos principales:

- `version`
- `safe_for_operational_decision`
- `safe_for_reclassification`
- `can_compute_bbox_by_separation`
- `summary`
- `items`

Cada item incluye:

- `name`
- `type`
- `is_printable`
- `classification_source`
- `usage_signal_status`
- `resource_mention_count`
- `bbox_available`
- `decision_impact`
- `operational_count_impact`

Criterio de producto:

- `RESOURCE_SIGNAL_FOUND` confirma señal técnica/presencia, no uso visual.
- `NO_DIRECT_RESOURCE_SIGNAL` no significa que la separación no se use.
- Sin bbox por separación, no debe afectar decisión operativa.

Backlog:

- `Separation Usage v2.1`: asociar separación a objetos reales.
- `Separation Usage v2.2`: calcular bbox por separación.
- `Separation Usage v2.3`: cruzar bbox con TrimBox/BleedBox.
- `Separation Usage v3`: permitir impacto seguro en conteo operativo y readiness.

---


## Sprint 26A.1 — Separation Usage Function Order Fix

Se corrige error de ejecución del pipeline legacy.

Problema:

- `build_report()` llamaba a `build_separation_usage_v2()`.
- La función estaba definida después del flujo de ejecución principal.
- Al ejecutar `gate0_check.py` como script, Python llegaba a la llamada antes de haber definido la función.

Corrección:

- Se mueve el bloque `build_separation_usage_v2()` antes de `build_report()`.
- No cambia lógica de producto.
- `separation_usage_v2` sigue siendo informativo y no decisorio.

---


## Sprint 26A.2 — Separation Summary Definition Fix

Se corrige error de ejecución en `build_report()`.

Problema:

- `separation_usage_v2` recibía `separation_summary`.
- `separation_summary` no estaba definido dentro de `build_report()`.
- Esto generaba `NameError` durante el análisis.

Corrección:

- Se construye `separation_summary` antes de `report_data`.
- Se expone `separation_summary` en el JSON del reporte.
- `separation_usage_v2` usa esa misma base.
- No cambia clasificación ni conteos de riesgo.

---


## Sprint 26A.3 — Compact UX Copy

Se ajusta copy del dashboard para reducir repetición y evitar lenguaje técnico innecesario.

Cambios:

- En `Production Readiness`, se elimina la línea superior de `next_step` cuando repite lo mismo que `Qué revisar primero`.
- En `Separation Usage v2`, se cambia el lenguaje:
  - `con señales` → `con señal técnica`
  - `sin señal directa` → `sin señal confirmada`
  - `Sin bbox por separación` → `Sin ubicación visual por separación`
- Se ocultan métricas demasiado técnicas en UI:
  - `tint ops`
  - `cs/CS`

Criterio de producto:

- El bloque debe ser resumen ejecutivo, no diagnóstico técnico profundo.
- Debe aclarar que detecta señales técnicas, pero no confirma uso visual.
- No cambia conteo operativo ni decisión de liberación.

---


## Sprint 26B — Inline Separation Usage Signal Marker

Se integra `separation_usage_v2` dentro de la lista existente de separaciones.

Objetivo:

- Evitar un panel adicional.
- Mostrar una marca compacta por separación:
  - `✓` = señal técnica encontrada.
  - `—` = sin señal directa confirmada por el análisis actual.
- Mantener el mensaje como informativo, no decisorio.

Criterio de producto:

- `✓` no significa aprobado.
- `✓` no confirma uso visual ni ubicación exacta.
- `—` no significa que la separación no se use.
- La marca no cambia conteo operativo, clasificación, riesgos ni Production Readiness.

---


## Sprint 26B.1 — Separation Summary UI Fallback

Se agrega fallback visual para `Color Separation Summary`.

Problema:

- En algunos reportes el dashboard podía mostrar “Sin información de separaciones”
  aunque el JSON tuviera `separations`.
- Esto podía ocurrir si `separation_summary.items` venía vacío o no era consumido correctamente.

Corrección:

- Si `separation_summary.items` está vacío pero `data.separations` tiene datos,
  el dashboard crea una vista fallback mínima.
- El fallback no cambia conteo operativo real ni clasificación backend.
- Solo evita perder visibilidad de separaciones en la UI.

---


## Sprint 26B.2 — Inline Signal Runtime Helper Fix

Se corrige error visual en `Color Separation Summary`.

Problema:

- El dashboard llamaba a `separationUsageSignalMap(data)`.
- La función helper no quedó definida en runtime.
- El render de separaciones se interrumpía y quedaba visible el mensaje:
  `Sin información de separaciones.`

Corrección:

- Se agregan explícitamente los helpers:
  - `separationUsageSignalMap`
  - `separationUsageSignalForItem`
  - `renderSeparationUsageSignal`
- Se agrega prueba estática para evitar regresión.
- No cambia backend ni lógica de conteo.

---


## Sprint 26B.3 — Hide Redundant Separation Usage Block

Se elimina visualmente el bloque inferior `Uso de separaciones v2`.

Motivo:

- La señal de uso ya se muestra inline junto a cada separación.
- El bloque inferior repetía contexto y ocupaba espacio.
- La UI queda más compacta y más fácil de leer.

Se mantiene:

- `separation_usage_v2` en el JSON.
- Marcador inline por separación:
  - `✓` = señal técnica encontrada.
  - `—` = sin señal directa confirmada.
- Tooltips explicativos.
- Sin impacto en conteo operativo, clasificación, riesgos ni Production Readiness.

---


## Sprint 27A.1 — Compare File Card Layout Fix

Se corrige layout de la página de comparación AI/PDF.

Problema:

- Las tarjetas `AI inspeccionado` y `PDF inspeccionado` mostraban rutas completas.
- Los nombres largos rompían el ancho de página.
- La tabla de comparación podía generar scroll horizontal excesivo.

Corrección:

- Se muestra solo el nombre del archivo, no la ruta completa.
- Se reduce tamaño visual de las tarjetas de archivo.
- Se fuerza `overflow-wrap:anywhere`.
- Se usa `table-layout:fixed` para estabilizar la tabla.
- Se mantiene la lógica de comparación sin cambios.

---


## Sprint 27A.2 — Compare CSS F-string Fix

Se corrige error que impedía levantar la web.

Problema:

- El hotfix 27A.1 insertó CSS dentro de un HTML construido con `f-string`.
- En Python, las llaves `{}` dentro de un `f-string` deben escaparse como `{{}}`.
- Esto podía generar error de importación en `app.py` y evitar que `uvicorn` levantara.

Corrección:

- Se escapan las llaves del bloque CSS agregado en Sprint 27A.1.
- No cambia lógica de comparación.
- Solo corrige arranque de la web.

---


## Sprint 27A.4.1 — Runtime Function Order Guard

Se recupera parte del hardening perdido del commit local `c735bd9`.

Problema:

- `gate0_check.py` tenía `if __name__ == "__main__"` antes de funciones redefinidas en sprints posteriores.
- Los tests por import podían usar las versiones nuevas.
- La ejecución real como script/subprocess podía usar versiones antiguas.

Corrección:

- Se mueve el guard `if __name__ == "__main__"` al final del archivo.
- Se agrega prueba de contrato para evitar que vuelva a quedar antes de:
  - `check_rgb_objects`
  - `check_high_tac`
  - `check_font_embedding`

No cambia:

- reglas de negocio;
- severidades;
- dashboard;
- rutas runtime.

---


## Sprint 27A.4.2 — Business Rule Regression Contracts

Nota de ajuste 27A.4.2b:

- Los hallazgos contextuales `INFO` pueden omitir `readiness_weight`; en contrato se interpreta ausencia como peso `0`.
- El contrato de readiness no fuerza `HIGH_RISK` con un hallazgo crítico manual aislado, porque la decisión final depende de criticidad/clase/bloqueo según `readiness_engine`.
- Los tests específicos existentes de `readiness_engine.py` siguen protegiendo `NO_GO` para críticos Clase A.



Se recupera parte del hardening perdido del commit local `c735bd9`.

Objetivo:

- Proteger reglas de negocio antes de iniciar Runtime Isolation.
- Evitar regresiones silenciosas en severidades, umbrales y readiness.
- No cambiar comportamiento funcional ni UI.

Contratos protegidos:

- RGB sin bbox debe permanecer contextual.
- RGB con área debe respetar umbrales 3% / 15%.
- TAC igual o menor al límite no debe generar `HIGH_TAC_RISK`.
- TAC sin bbox no debe escalar por área inventada.
- Small Text debe respetar umbrales 4 pt / 5 pt.
- Separaciones deben respetar 8 / 10 / 12.
- Readiness debe mantener sus bandas operativas.

No cambia:

- Detection.
- Dashboard.
- Production Readiness.
- Runtime paths.
- Compare Engine.

---


## Sprint 27C.2 — Consolidate gate0_check.py Single Definitions

Se reduce deuda técnica en `gate0_check.py`.

Problema:

- Existían definiciones antiguas y nuevas de:
  - `check_font_embedding`
  - `check_rgb_objects`
  - `check_high_tac`
- La ejecución real ya usaba las versiones nuevas porque el `main` está al final.
- Aun así, mantener funciones duplicadas generaba riesgo de editar una versión inactiva.

Corrección:

- Se eliminan las definiciones antiguas.
- Se mantiene una sola definición activa para cada función.
- Se agregan pruebas de contrato para proteger:
  - definición única;
  - orden antes del `main`;
  - campos de evidencia enriquecida de RGB, TAC y fuentes.

No cambia:

- reglas de negocio;
- severidades;
- Production Readiness;
- Runtime Isolation;
- dashboard.

---


## Sprint 27C.3 — Consolidate business_rules.py Single Definitions

Se reduce deuda técnica en `business_rules.py`.

Problema:

- Existían definiciones antiguas y nuevas de:
  - `evaluate_rgb_object`
  - `evaluate_high_tac_risk`
- Las versiones nuevas 25C eran las efectivas al final del módulo.
- Mantener duplicados generaba riesgo de editar una función inactiva.

Corrección:

- Se eliminan las definiciones antiguas.
- Se mantiene una sola definición activa por función.
- Se agregan pruebas de contrato para proteger:
  - definición única;
  - RGB sin bbox como riesgo contextual;
  - umbrales RGB 3% / 15%;
  - TAC sin bbox como riesgo contextual;
  - umbrales TAC por exceso.

No cambia:

- severidades;
- umbrales;
- Production Readiness;
- Runtime Isolation;
- dashboard.

---


## Sprint 27C.4A — PR2 Active Behavior Guardrails

Se agregan pruebas de contrato antes de consolidar `readiness_summary.py`.

Contexto:

- `readiness_summary.py` conserva varias generaciones de `Production Readiness v2`.
- La función activa es la última definición de `build_production_readiness_v2`.
- La versión activa esperada es `v2_printable_area_priority`.
- El helper `_pr2_printable_area_confidence_confirmed` debe ser estricto:
  - `CONFIRMED` real permite tratar hallazgos fuera del área imprimible como contextuales.
  - `UNCONFIRMED` no debe degradar riesgos efectivos.

Se protege:

- versión activa de PR2;
- área imprimible confirmada fuera como nota contextual;
- área imprimible no confirmada sin downgrade;
- prioridad de sobreimpresión con blanco;
- deduplicación de texto pequeño repetido.

No cambia:

- `readiness_summary.py`;
- reglas de negocio;
- severidades;
- dashboard;
- runtime isolation.

---


## Sprint 27C.4B — Consolidate readiness_summary.py Single Definitions

Se consolida deuda técnica en `readiness_summary.py`.

Problema:

- Existían múltiples generaciones de funciones PR2 en el mismo archivo.
- `build_production_readiness_v2` tenía varias definiciones históricas.
- Python usaba la última definición activa, pero las anteriores generaban riesgo de mantenimiento.

Corrección:

- Se eliminan definiciones antiguas duplicadas.
- Se mantiene una sola definición activa para:
  - `sort_top_risks`
  - `_pr2_title`
  - `_pr2_is_contextual_non_blocking`
  - `_pr2_next_step`
  - `_pr2_priority_score`
  - `_pr2_make_review_item`
  - `_pr2_plain_reason`
  - `_pr2_printable_area_confidence_confirmed`
  - `build_production_readiness_v2`
- Se agregan pruebas de contrato para proteger definición única y comportamiento activo.

No cambia:

- lógica activa de Production Readiness;
- versión `v2_printable_area_priority`;
- severidades;
- reglas de negocio;
- dashboard;
- runtime isolation.

---


## Sprint 27C.5A — Clean remaining business_rules duplicates

Se eliminan duplicados remanentes en `business_rules.py`.

Problema detectado en audit 27C.5:

- `severity_meta` tenía dos definiciones.
- `evaluate_font_not_embedded` tenía dos definiciones.
- Python usaba la última definición, pero mantener versiones antiguas generaba riesgo de mantenimiento.

Corrección:

- Se elimina la definición antigua de cada función.
- Se mantiene la última definición activa.
- Se agregan pruebas de contrato para proteger:
  - definición única;
  - shape esperado de `severity_meta`;
  - comportamiento crítico de `FONT_NOT_EMBEDDED`.

No cambia:

- umbrales;
- severidades activas;
- Production Readiness;
- dashboard;
- Runtime Isolation.

---


## Sprint 27C.5B — Consolidate spot_utils build_spot_inventory

Se elimina duplicación remanente en `config/spot_utils.py`.

Problema detectado en audit 27C.5:

- `build_spot_inventory` existía dos veces.
- La segunda definición envolvía a la primera mediante `_GATE0_ORIGINAL_BUILD_SPOT_INVENTORY`.
- Python usaba la segunda definición activa, pero el patrón generaba deuda técnica y riesgo de mantenimiento.

Corrección:

- Se consolida `build_spot_inventory` en una sola función.
- Se conserva la clasificación activa:
  - spots imprimibles;
  - blanco;
  - barniz;
  - separaciones técnicas/no imprimibles;
  - exclusión de plano/material/técnicas del conteo operativo imprimible.
- Se agregan pruebas de contrato para proteger definición única y conteo operativo.

No cambia:

- lógica activa de separación;
- reglas de negocio;
- Production Readiness;
- dashboard;
- Runtime Isolation.

---


## Sprint 28A — Product Validation Pass

Se valida funcionalmente el flujo real después de la fase de limpieza técnica 27C.

Validación realizada:

- Landing `/` responde correctamente.
- Upload/análisis PDF responde con redirect a dashboard.
- Dashboard carga con `sid`.
- `/api/report` responde correctamente.
- `/api/pdf` responde correctamente.
- `/api/risk-preview` responde correctamente.
- El visor PDF y la evidencia visual siguen operativos.
- Production Readiness, Top Risks y navegación de riesgo seleccionado siguen funcionando.

Resultado:

- La limpieza técnica no rompió el flujo principal.
- Runtime Isolation sigue funcionando por sesión.
- El producto queda estable para continuar con nuevos sprints de producto/UX.

---


## Sprint 28B.1 — Dashboard copy compact pass

Se realiza una mejora menor de copy en el dashboard.

Cambios:

- `Top Risks` pasa a `Riesgos principales`.
- `Riesgo seleccionado` pasa a `Detalle del riesgo`.
- El título accesible del iframe pasa de `PDF analizado` a `Archivo PDF analizado`.
- Se protege que no reaparezcan textos redundantes como `Vista del archivo` o `Preview de producción`.

No cambia:

- motor de análisis;
- reglas de negocio;
- Production Readiness;
- separación de colores;
- runtime isolation;
- compare engine.

---


## Sprint 28B.2 — Compact selected risk detail labels

Se compacta el copy del bloque `Detalle del riesgo`.

Cambios:

- `Tipo de riesgo` pasa a `Riesgo`.
- `Área imprimible` pasa a `Área útil`.
- `Umbral / criterio` pasa a `Criterio`.
- `Por qué importa` pasa a `Impacto`.
- `Qué hacer` pasa a `Acción sugerida`.
- El empty state del detalle se orienta a prioridad, evidencia y acción sugerida.

No cambia:

- motor de análisis;
- reglas de negocio;
- Production Readiness;
- evidencias;
- separaciones;
- runtime isolation;
- compare engine.

---


## Sprint 28C.1 — Dashboard JS Guardrails

Se agregan pruebas de contrato antes de limpiar duplicados JavaScript en `dashboard/index.html`.

Contexto:

- El dashboard funciona y `node --check` pasa.
- El audit detectó nombres duplicados en JS.
- Algunos duplicados son funciones top-level antiguas sobrescritas por versiones nuevas.
- Otros son variables locales repetidas y no representan riesgo real.

Se protege:

- sintaxis JS del dashboard;
- copy UX actual;
- ausencia de copy redundante antiguo;
- hooks de Production Readiness drilldown;
- navegación visual de ocurrencias/zonas;
- soporte inline de Separation Usage v2.

No cambia:

- dashboard productivo;
- motor;
- reglas de negocio;
- Production Readiness;
- Runtime Isolation;
- Compare Engine.

---


## Sprint 28C.2 — Remove obsolete dashboard JS duplicate definitions

Se eliminan definiciones JavaScript antiguas duplicadas en `dashboard/index.html`.

Problema:

- El audit detectó funciones top-level duplicadas.
- Python/JS usaba la última definición activa por sobrescritura.
- Mantener versiones antiguas generaba riesgo de editar una función inactiva.

Funciones consolidadas:

- `bindProductionReadinessDrilldown`
- `clampOccurrenceIndex`
- `renderOccurrenceNav`
- `renderSeparationUsageV2`
- `riskDataForActiveOccurrence`
- `selectProductionReadinessRisk`

Se mantiene:

- la última definición activa;
- Production Readiness drilldown con `data-pr2-check` y `data-pr2-title`;
- navegación visual por zonas/ocurrencias;
- renderer compacto de Separation Usage v2.

No se toca:

- variables locales repetidas como `check`, `fromRisk`, `pushUnique` o `compact`;
- motor de análisis;
- reglas de negocio;
- Production Readiness backend;
- Runtime Isolation;
- Compare Engine.

---


## Sprint 28 — UX and Dashboard Stabilization Closure

Se cierra la fase Sprint 28 enfocada en validación funcional, limpieza UX y estabilización del dashboard.

Incluye:

- Sprint 28A: Product Validation Pass.
- Sprint 28B.1: compact dashboard risk copy.
- Sprint 28B.2: compact selected risk detail copy.
- Sprint 28C.1: dashboard JS guardrails.
- Sprint 28C.2: eliminación de definiciones JavaScript obsoletas duplicadas.

Resultado:

- Dashboard validado funcionalmente.
- Copy principal más claro y consistente.
- Production Readiness drilldown protegido.
- Navegación visual por zonas/ocurrencias protegida.
- Separation Usage v2 inline protegido.
- JavaScript del dashboard con guardrails antes y después de limpieza.
- Sin cambios en motor, reglas de negocio, Production Readiness backend, Runtime Isolation o Compare Engine.

Estado de cierre esperado:

- `node --check` OK.
- `pytest` OK.
- repo limpio después del commit.
- backup final creado.

---


## Sprint 28D — Codex Working Protocol for Gate0

Se prepara el repositorio para trabajar con Codex de manera segura.

Entregables:

- AGENTS.md con reglas de trabajo para agentes.
- docs/codex/gate0_codex_prompt.md con prompt base para Codex.
- Pruebas de contrato para proteger que el protocolo incluya:
  - flujo seguro;
  - validación con tests;
  - protección del dashboard;
  - protección de reglas de negocio;
  - protección de Runtime Isolation;
  - política audit-first para la primera tarea Codex.

Objetivo:

- Usar Codex como apoyo de ingeniería, no como piloto automático.
- Empezar con tareas de auditoría antes de permitir cambios.
- Mantener el flujo Gate0:
  - status;
  - diff;
  - tests;
  - commit;
  - push;
  - backup.

No cambia:

- motor de análisis;
- dashboard;
- reglas de negocio;
- Production Readiness;
- Compare Engine;
- Runtime Isolation.

---
