# Gate0 — Intelligence Reconciliation v1

Objetivo: comparar las fuentes actuales de inteligencia por check para evitar pérdida de conocimiento, duplicidad o simplificación excesiva.

Este documento no modifica lógica. Sirve como control antes de consolidar una fuente maestra consumible por el motor.

---

## Fuentes revisadas

| Fuente | Rol actual | ¿Debe ser fuente maestra? |
|---|---|---|
| business_rules.py | Severidad, prioridad, risk_reason, action | Parcial |
| expert_comment_engine.py | Comentario experto, impacto, recomendación | Parcial |
| check_intelligence.py | Criterio/contexto/fix type en JSON | Candidata futura |
| docs/check_intelligence_matrix.md | Matriz documental consolidada | Referencia producto |
| dashboard/index.html | Visualización | No |

---

## Decisión base

- El dashboard no debe ser fuente maestra.
- expert_comment_engine.py no debe ser reemplazado por textos más simples.
- business_rules.py mantiene la lógica de severidad y prioridad.
- check_intelligence.py debe enriquecerse gradualmente usando lo ya trabajado, no inventando desde cero.
- docs/check_intelligence_matrix.md debe ser la referencia documental de producto.

---

## Reconciliation por check

| Check | Business Rules | Expert Comment | JSON Intelligence | Matrix | Dashboard | Acción recomendada |
|---|---|---|---|---|---|---|
| RGB_OBJECT | Sí | Sí | Sí | Sí | Sí | Revisar consistencia y evitar simplificación. |
| LOW_IMAGE_RESOLUTION | Sí | Sí | Sí | Sí | Sí | Revisar consistencia y evitar simplificación. |
| BARCODE_RISK | Sí | Sí | Sí | Sí | Sí | Revisar consistencia y evitar simplificación. |
| SMALL_TEXT_RISK | Sí | Sí | Sí | Sí | Sí | Revisar consistencia y evitar simplificación. |
| FONT_NOT_EMBEDDED | Sí | Sí | Sí | Sí | Sí | Revisar consistencia y evitar simplificación. |
| HIGH_TAC_RISK | Sí | Sí | Sí | Sí | Sí | Revisar consistencia y evitar simplificación. |
| OVERPRINT_RISK | Sí | No | Sí | Sí | Sí | Revisar consistencia y evitar simplificación. |
| SPOT_COLOR_RISK | Sí | Sí | Sí | Sí | Sí | Revisar consistencia y evitar simplificación. |
| SEPARATION_COUNT_RISK | Sí | Sí | Sí | Sí | Sí | Revisar consistencia y evitar simplificación. |
| PDF_STRUCTURE_RISK | Sí | No | Sí | Sí | Sí | Revisar consistencia y evitar simplificación. |

---

## Evidencia por fuente

### business_rules.py

```text
141:def apply_business_fields(finding, severity, risk_area, risk_reason, priority, action, score_weight):
147:    finding["risk_reason"] = risk_reason
187:def evaluate_rgb_object(finding, profile):
211:    return apply_business_fields(finding, sev, "Color / Separaciones", reason, p, "Convertir RGB a CMYK o spot validado según perfil.", w)
215:def evaluate_barcode_risk(finding, profile):
241:    action = (
248:    result = apply_business_fields(finding, sev, "Código de barras / QR", reason, p, action, w)
255:def evaluate_low_image_resolution(finding, profile):
284:    return apply_business_fields(finding, sev, "Resolución / Imagen", reason, p, "Revisar resolución efectiva y solicitar imagen en mayor resolución si aplica.", w)
288:def evaluate_small_text_risk(finding, profile):
317:    action = (
323:    result = apply_business_fields(finding, sev, "Texto / Legibilidad", reason, p, action, w)
332:def evaluate_font_not_embedded(finding, profile):
333:    return apply_business_fields(
344:def evaluate_high_tac_risk(finding, profile):
361:    return apply_business_fields(finding, sev, "Carga de tinta / Impresión", reason, p, "Reducir TAC según estándar del proceso/sustrato.", w)
364:def evaluate_overprint_risk(finding, profile):
369:        sev, reason, action = "PASS", "Objeto sin sobreimpresión activa.", "Sin acción requerida."
373:        action = "Verificar si el blanco tiene sobreimpresión activa y si genera reserva correctamente."
377:        action = "Verificar intención de diseño y efecto visual."
381:        action = "Confirmar si corresponde a trapping manual, refuerzo cromático o estrategia normal."
384:    return apply_business_fields(finding, sev, "Sobreimpresión", reason, p, action, w)
387:def evaluate_white_ink_risk(finding, profile):
394:        action = "Unificar nomenclatura de blanco y validar separación correcta."
398:        action = "Normalizar nombre de blanco."
402:        action = "Confirmar uso de blanco según especificación."
405:    return apply_business_fields(finding, sev, "Tinta blanca / Separaciones", reason, p, action, w)
408:def evaluate_spot_color_risk(finding, profile):
415:        action = "Racionalizar separaciones spot antes de liberar."
419:        action = finding.get("recommendation", "Revisar y normalizar separaciones spot.")
423:        action = finding.get("recommendation", "Validar separaciones spot.")
426:    return apply_business_fields(finding, sev, "Separaciones spot", reason, p, action, w)
429:def evaluate_separation_count_risk(finding, profile):
436:        action = "Sin acción requerida."
440:        action = "Verificar complejidad operativa y disponibilidad de estaciones."
444:        action = "Revisar racionalización de spots."
448:        action = "Validar capacidad de prensa y racionalización de separaciones."
451:    return apply_business_fields(finding, sev, "Complejidad de separaciones", reason, p, action, w)
454:def evaluate_pdf_structure_risk(finding, profile):
460:        action = "Optimizar, reconstruir o validar archivo."
464:        action = "Revisar optimización antes de RIP/trapping/imposición."
468:        action = "Sin acción requerida."
471:    return apply_business_fields(finding, sev, "Estructura PDF", reason, p, action, w)
477:    if check == "RGB_OBJECT":
479:    if check == "BARCODE_RISK":
481:    if check == "LOW_IMAGE_RESOLUTION":
483:    if check == "SMALL_TEXT_RISK":
485:    if check == "FONT_NOT_EMBEDDED":
487:    if check == "HIGH_TAC_RISK":
489:    if check == "OVERPRINT_RISK":
493:    if check == "SPOT_COLOR_RISK":
495:    if check == "SEPARATION_COUNT_RISK":
497:    if check == "PDF_STRUCTURE_RISK":
500:    return apply_business_fields(
```

### expert_comment_engine.py

```text
33:def _build_rgb_insight(top_risk, related):
46:        "brief_comment": brief,
48:        "why_it_matters": "Los elementos RGB están pensados para pantalla y normalmente deben convertirse a CMYK o a una tinta validada antes de impresión.",
49:        "possible_impact": "La conversión no controlada puede provocar diferencias entre el color aprobado y el resultado impreso.",
50:        "recommended_action": "Convertir los elementos RGB usando el perfil de color definido para el trabajo antes de liberar.",
52:        "evidence": {"occurrence_count": count, "max_object_area_percent": max_area, "page": top_risk.get("page"), "rule_applied": "RGB_OBJECT", "confidence": "Alta"}
57:def _build_barcode_insight(top_risk, related):
79:        "brief_comment": brief,
81:        "why_it_matters": "Los códigos de barras y QR son elementos funcionales. No basta con que se vean bien; deben poder leerse de forma confiable en control de calidad y uso final.",
82:        "possible_impact": "Un código pixelado, rasterizado a baja resolución o construido con varias tintas puede generar problemas de registro, lectura deficiente, rechazo de calidad, reproceso o bloqueo de lote.",
83:        "recommended_action": selected.get("action") or selected.get("recommendation") or "Validar lectura del código. Preferir código vectorial o imagen de alta resolución. Confirmar que esté construido a una sola tinta cuando aplique y evitar códigos multitinta por riesgo de registro.",
92:            "rule_applied": "BARCODE_RISK",
97:def _build_lowres_insight(top_risk, related):
115:        "brief_comment": brief,
117:        "why_it_matters": "Una imagen puede verse bien en pantalla, pero perder calidad cuando se amplía dentro del diseño o se imprime.",
118:        "possible_impact": "Puede verse pixelada, borrosa o con pérdida de detalle en impresión.",
119:        "recommended_action": "Solicitar una imagen de mayor resolución o reducir el tamaño de uso si el diseño lo permite.",
121:        "evidence": {"effective_dpi": dpi, "minimum_suggested_dpi": minimum, "recommended_dpi": recommended, "object_area_percent": area, "image_role": role, "page": top_risk.get("page"), "rule_applied": "LOW_IMAGE_RESOLUTION", "confidence": "Alta"}
125:def _build_tac_insight(top_risk, related):
143:        "brief_comment": brief,
145:        "why_it_matters": "La cobertura total de tinta debe mantenerse dentro del límite definido por proceso, tinta y sustrato.",
146:        "possible_impact": "Un TAC alto puede generar secado lento, repinte, bloqueo, ganancia o inestabilidad durante impresión.",
147:        "recommended_action": "Reducir la cobertura total revisando separación, perfil de conversión, curvas o negro enriquecido.",
149:        "evidence": {"detected_tac": tac, "tac_limit": limit, "excess": excess, "page": top_risk.get("page"), "rule_applied": "HIGH_TAC_RISK", "confidence": "Alta"}
154:def _build_small_text_insight(top_risk, related):
172:        "brief_comment": brief,
174:        "why_it_matters": "En packaging, textos muy pequeños pueden perder definición por ganancia, registro, sustrato, anilox, cilindro, trama o condición de impresión.",
175:        "possible_impact": "Puede afectar legibilidad de legales, ingredientes, advertencias, claims o información regulatoria.",
176:        "recommended_action": selected.get("action") or selected.get("recommendation") or "Aumentar tamaño, simplificar tipografía o validar mínimo técnico según proceso y condición de impresión.",
185:            "rule_applied": "SMALL_TEXT_RISK",
190:def _build_font_insight(top_risk, related):
210:        "brief_comment": brief,
212:        "why_it_matters": "Si una fuente no está embebida, el sistema que procese el archivo puede sustituirla por otra.",
213:        "possible_impact": "Puede cambiar el texto, la composición, los legales, ingredientes, códigos o elementos aprobados del diseño.",
214:        "recommended_action": "Incrustar las fuentes en el PDF o convertir el texto a curvas antes de enviar a producción.",
216:        "evidence": {"occurrence_count": count, "sample_fonts": font_names[:3], "page": top_risk.get("page"), "rule_applied": "FONT_NOT_EMBEDDED", "confidence": "Alta"}
221:def _build_spot_insight(top_risk, related):
257:        "brief_comment": brief,
259:        "why_it_matters": "Las tintas spot definen separaciones adicionales que deben formularse, asignarse y controlarse correctamente en preprensa y prensa.",
260:        "possible_impact": "Nombres incorrectos, duplicados o exceso de spots pueden generar errores de separación, tintas innecesarias, mayor setup o riesgo operativo.",
261:        "recommended_action": selected.get("action") or selected.get("recommendation") or "Validar nombres, duplicados y necesidad real de cada tinta spot.",
263:        "evidence": {"printable_spot_count": spot_count, "spot_category": categories, "sample_spot_names": names[:5], "page": top_risk.get("page"), "rule_applied": "SPOT_COLOR_RISK", "confidence": "Media"}
267:def _build_separation_insight(top_risk, related):
291:        "brief_comment": brief,
293:        "why_it_matters": "Cada separación imprimible implica una tinta, estación o control adicional dentro del flujo de impresión.",
294:        "possible_impact": "Una cantidad alta de separaciones puede aumentar setup, complejidad, riesgo de error, tiempo de preparación y dificultad de control.",
295:        "recommended_action": selected.get("action") or selected.get("recommendation") or "Validar capacidad de prensa, secuencia y necesidad real de cada separación.",
297:        "evidence": {"printable_separation_count": count, "white_detected": white, "varnish_detected": varnish, "technical_separations_detected": technical, "page": top_risk.get("page"), "rule_applied": "SEPARATION_COUNT_RISK", "confidence": "Alta"}
305:    if check == "RGB_OBJECT":
307:    if check == "BARCODE_RISK":
309:    if check == "LOW_IMAGE_RESOLUTION":
311:    if check == "HIGH_TAC_RISK":
313:    if check == "SMALL_TEXT_RISK":
315:    if check == "FONT_NOT_EMBEDDED":
317:    if check == "SPOT_COLOR_RISK":
319:    if check == "SEPARATION_COUNT_RISK":
323:        "brief_comment": top_risk.get("risk_reason") or top_risk.get("detail") or "Se detectó un hallazgo que requiere revisión.",
325:        "why_it_matters": "Puede afectar el flujo de preprensa o producción.",
326:        "possible_impact": top_risk.get("risk_reason") or "Puede generar riesgo operativo.",
327:        "recommended_action": top_risk.get("action") or top_risk.get("recommendation") or "Revisar antes de liberar.",
344:            risk["expert_comment"] = insight.get("brief_comment")
```

### check_intelligence.py

```text
12:    "RGB_OBJECT": {
13:        "criteria": "Detecta objetos definidos en RGB dentro del PDF.",
14:        "operational_context": "En packaging, RGB puede convertirse de forma no controlada y alterar el color final.",
15:        "possible_impact": "Cambio de color, diferencia contra prueba, retrabajo o reclamo visual.",
16:        "fix_type": "assisted",
17:        "current_limitation": "No clasifica intención del objeto ni decide automáticamente el perfil correcto.",
18:        "future_evolution": "Conversión asistida con perfil aprobado y validación visual antes/después.",
20:    "LOW_IMAGE_RESOLUTION": {
21:        "criteria": "Evalúa resolución efectiva de imágenes al tamaño final de uso.",
22:        "operational_context": "Una imagen de baja resolución puede pixelarse o perder detalle al imprimirse.",
23:        "possible_impact": "Pérdida visible de calidad, reclamo visual o necesidad de reemplazar imagen.",
24:        "fix_type": "assisted",
25:        "current_limitation": "No distingue completamente rol de imagen: producto, fondo, textura, logo o elemento decorativo.",
26:        "future_evolution": "Clasificar rol visual y ajustar severidad según zona crítica del arte.",
28:    "BARCODE_RISK": {
29:        "criteria": "Detecta candidatos barcode/QR como imagen de bajo DPI.",
30:        "operational_context": "Barcode y QR son elementos funcionales: deben poder leerse, no solo verse bien.",
31:        "possible_impact": "Código ilegible, rechazo de calidad, bloqueo de lote, reproceso o problema logístico.",
32:        "fix_type": "assisted",
33:        "current_limitation": "No decodifica, no valida GS1, quiet zone, magnificación, contraste ni single ink.",
34:        "future_evolution": "Validar single ink, quiet zone, magnificación, decodificación y cumplimiento GS1.",
36:    "SMALL_TEXT_RISK": {
37:        "criteria": "Evalúa texto vivo por debajo del tamaño mínimo configurado.",
38:        "operational_context": "Texto pequeño puede perder legibilidad, más aún en negativo, multitinta o fondos complejos.",
39:        "possible_impact": "Texto ilegible, incumplimiento legal, reclamo de marca o rechazo por calidad.",
40:        "fix_type": "assisted",
41:        "current_limitation": "No clasifica positivo, negativo, multitinta, fondo complejo o texto legal crítico.",
42:        "future_evolution": "Clasificar contexto visual y proponer ajustes asistidos.",
44:    "FONT_NOT_EMBEDDED": {
45:        "criteria": "Detecta fuentes no embebidas en el PDF.",
46:        "operational_context": "Una fuente no embebida puede sustituirse al abrir, procesar o ripear el archivo.",
47:        "possible_impact": "Cambio tipográfico, texto corrido, error de layout o diferencia frente al arte aprobado.",
48:        "fix_type": "manual",
49:        "current_limitation": "Gate0 no corrige ni convierte fuentes automáticamente.",
50:        "future_evolution": "Guía asistida y validación post-conversión.",
52:    "HIGH_TAC_RISK": {
53:        "criteria": "Evalúa cobertura total de tinta contra el límite del perfil operativo.",
54:        "operational_context": "TAC alto puede causar secado deficiente, repinte, ganancia o inestabilidad en prensa.",
55:        "possible_impact": "Defectos de impresión, variabilidad, rechazo interno o necesidad de reprocesar separación.",
56:        "fix_type": "assisted",
57:        "current_limitation": "No modifica separaciones ni propone receta exacta de reducción.",
58:        "future_evolution": "Sugerir estrategia de reducción por perfil, zona, proceso y objetivo visual.",
60:    "OVERPRINT_RISK": {
61:        "criteria": "Detecta condiciones de sobreimpresión que requieren validación.",
62:        "operational_context": "Una sobreimpresión incorrecta puede hacer desaparecer elementos o cambiar apariencia.",
63:        "possible_impact": "Elementos perdidos, textos invisibles, cambio de color o error en blanco.",
64:        "fix_type": "assisted",
65:        "current_limitation": "Detección parcial; no siempre identifica sobreimpresión por objeto.",
66:        "future_evolution": "Comparación visual, mapa por objeto y fix asistido para casos seguros.",
68:    "SPOT_COLOR_RISK": {
69:        "criteria": "Evalúa tintas spot, blancos, nombres genéricos, duplicidades y separaciones técnicas.",
70:        "operational_context": "Spots mal nombrados o duplicados pueden generar tintas extra o errores de formulación.",
71:        "possible_impact": "Tinta incorrecta, costo adicional, separación duplicada o setup innecesario.",
72:        "fix_type": "assisted",
73:        "current_limitation": "No conoce intención completa del diseño ni decide qué spot eliminar.",
74:        "future_evolution": "Normalización asistida, equivalencias y sugerencia de racionalización.",
76:    "SEPARATION_COUNT_RISK": {
77:        "criteria": "Evalúa cantidad de separaciones imprimibles contra umbrales del perfil.",
78:        "operational_context": "Más separaciones aumentan complejidad, costo, setup y riesgo operativo.",
79:        "possible_impact": "Trabajo difícil de producir, mayor tiempo de preparación o incompatibilidad con prensa.",
80:        "fix_type": "assisted",
81:        "current_limitation": "No decide qué tinta eliminar ni conoce restricciones reales de cada prensa.",
82:        "future_evolution": "Sugerir candidatos de racionalización o conversión según cliente, prensa y perfil.",
84:    "PDF_STRUCTURE_RISK": {
85:        "criteria": "Evalúa páginas vacías, tamaño de archivo, objetos, imágenes y complejidad estructural.",
86:        "operational_context": "PDFs vacíos, pesados o complejos pueden fallar en RIP, trapping, imposición o edición.",
87:        "possible_impact": "Error de procesamiento, lentitud, archivo corrupto o necesidad de reconstrucción.",
88:        "fix_type": "manual",
89:        "current_limitation": "No repara estructura PDF automáticamente.",
90:        "future_evolution": "Limpieza estructural asistida y validación antes/después.",
97:        "criteria": "Criterio técnico definido por Gate0.",
98:        "operational_context": "Este hallazgo puede impactar calidad, producción o liberación del archivo.",
99:        "possible_impact": "Riesgo operativo o de calidad pendiente de clasificación.",
100:        "fix_type": "manual",
101:        "current_limitation": "Inteligencia específica pendiente de consolidar.",
102:        "future_evolution": "Definir evolución del check según validación de producto.",
```

### docs/check_intelligence_matrix.md

```text
22:## 1. RGB_OBJECT
24:**Criterio aplicado**  
27:**Contexto operativo**  
30:**Impacto posible**  
33:**Acción recomendada**  
39:**Limitación actual**  
42:**Futuro**  
47:## 2. LOW_IMAGE_RESOLUTION
49:**Criterio aplicado**  
52:**Contexto operativo**  
55:**Impacto posible**  
58:**Acción recomendada**  
64:**Limitación actual**  
67:**Futuro**  
72:## 3. BARCODE_RISK
74:**Criterio aplicado**  
77:**Contexto operativo**  
80:**Impacto posible**  
83:**Acción recomendada**  
89:**Limitación actual**  
92:**Futuro**  
97:## 4. SMALL_TEXT_RISK
99:**Criterio aplicado**  
102:**Contexto operativo**  
105:**Impacto posible**  
108:**Acción recomendada**  
114:**Limitación actual**  
117:**Futuro**  
122:## 5. FONT_NOT_EMBEDDED
124:**Criterio aplicado**  
127:**Contexto operativo**  
130:**Impacto posible**  
133:**Acción recomendada**  
139:**Limitación actual**  
142:**Futuro**  
147:## 6. HIGH_TAC_RISK
149:**Criterio aplicado**  
152:**Contexto operativo**  
155:**Impacto posible**  
158:**Acción recomendada**  
164:**Limitación actual**  
167:**Futuro**  
172:## 7. OVERPRINT_RISK
174:**Criterio aplicado**  
177:**Contexto operativo**  
180:**Impacto posible**  
183:**Acción recomendada**  
189:**Limitación actual**  
192:**Futuro**  
197:## 8. SPOT_COLOR_RISK
199:**Criterio aplicado**  
202:**Contexto operativo**  
205:**Impacto posible**  
208:**Acción recomendada**  
214:**Limitación actual**  
217:**Futuro**  
222:## 9. SEPARATION_COUNT_RISK
224:**Criterio aplicado**  
227:**Contexto operativo**  
230:**Impacto posible**  
233:**Acción recomendada**  
239:**Limitación actual**  
242:**Futuro**  
247:## 10. PDF_STRUCTURE_RISK
249:**Criterio aplicado**  
252:**Contexto operativo**  
255:**Impacto posible**  
258:**Acción recomendada**  
264:**Limitación actual**  
267:**Futuro**  
```

### dashboard/index.html

```text
306:  "RGB_OBJECT": "Objetos RGB detectados",
307:  "LOW_IMAGE_RESOLUTION": "Resolución de imagen insuficiente",
308:  "BARCODE_RISK": "Código de barras / QR",
309:  "FONT_NOT_EMBEDDED": "Fuentes no embebidas",
310:  "SMALL_TEXT_RISK": "Texto pequeño / legibilidad",
311:  "HIGH_TAC_RISK": "Cobertura total de tinta elevada",
312:  "OVERPRINT_RISK": "Observación de sobreimpresión",
314:  "SPOT_COLOR_RISK": "Observación en tintas spot",
315:  "SEPARATION_COUNT_RISK": "Complejidad de separaciones",
316:  "PDF_STRUCTURE_RISK": "Estructura PDF"
546:function riskCriteria(input){
551:    RGB_OBJECT:"Detecta objetos definidos en RGB dentro del PDF.",
552:    LOW_IMAGE_RESOLUTION:"Evalúa la resolución efectiva de imágenes contra el mínimo operativo del perfil.",
553:    BARCODE_RISK:"Detecta candidatos barcode/QR como imagen de bajo DPI.",
554:    SMALL_TEXT_RISK:"Evalúa texto vivo por debajo del tamaño mínimo configurado.",
555:    FONT_NOT_EMBEDDED:"Detecta fuentes no embebidas en el PDF.",
556:    HIGH_TAC_RISK:"Evalúa cobertura total de tinta contra el límite del perfil.",
557:    OVERPRINT_RISK:"Detecta condiciones de sobreimpresión que requieren validación.",
558:    SPOT_COLOR_RISK:"Evalúa tintas spot, blancos, nombres genéricos y posibles duplicidades.",
559:    SEPARATION_COUNT_RISK:"Evalúa cantidad de separaciones imprimibles contra capacidad operativa.",
560:    PDF_STRUCTURE_RISK:"Evalúa páginas vacías, tamaño, cantidad de objetos y complejidad del PDF."
565:function riskOperationalContext(input){
570:    RGB_OBJECT:"En packaging, RGB puede convertirse de forma no controlada y alterar el color final.",
571:    LOW_IMAGE_RESOLUTION:"Una imagen de baja resolución puede pixelarse al tamaño final de impresión.",
572:    BARCODE_RISK:"Barcode/QR es un elemento funcional: debe leerse, no solo verse bien.",
573:    SMALL_TEXT_RISK:"Texto pequeño puede perder legibilidad, especialmente en negativo, multitinta o procesos exigentes.",
574:    FONT_NOT_EMBEDDED:"Una fuente no embebida puede sustituirse y modificar textos, medidas o apariencia.",
575:    HIGH_TAC_RISK:"TAC alto puede causar secado deficiente, repinte, ganancia o inestabilidad en prensa.",
576:    OVERPRINT_RISK:"Una sobreimpresión incorrecta puede hacer desaparecer elementos o cambiar el resultado visual.",
577:    SPOT_COLOR_RISK:"Spots mal nombrados o duplicados pueden generar tintas extra, errores de formulación o separaciones incorrectas.",
578:    SEPARATION_COUNT_RISK:"Muchas separaciones aumentan complejidad, costo, setup y riesgo operativo.",
579:    PDF_STRUCTURE_RISK:"Un PDF muy pesado, vacío o complejo puede fallar en RIP, trapping, imposición o procesamiento."
636:        <div>${esc(riskCriteria(r))}</div>
640:        <div>${esc(riskOperationalContext(r))}</div>
```

---

## Conclusión operativa

La próxima consolidación debe hacerse check por check, tomando como base:

1. Severidad y acción desde business_rules.py.
2. Explicación rica desde expert_comment_engine.py.
3. Estructura consumible desde check_intelligence.py.
4. Visión producto desde docs/check_intelligence_matrix.md.

No se debe eliminar ni reemplazar comentario experto existente sin compararlo contra esta auditoría.
