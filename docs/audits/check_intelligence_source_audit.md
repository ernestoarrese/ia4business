# Gate0 — Check Intelligence Source Audit

Auditoría de fuentes actuales de inteligencia por check.

---

## 1. Checks detectados en business_rules.py

141:def apply_business_fields(finding, severity, risk_area, risk_reason, priority, action, score_weight):
146:    finding["risk_area"] = risk_area
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

---

## 2. Comentarios expertos actuales

33:def _build_rgb_insight(top_risk, related):
46:        "brief_comment": brief,
47:        "what_found": found,
48:        "why_it_matters": "Los elementos RGB están pensados para pantalla y normalmente deben convertirse a CMYK o a una tinta validada antes de impresión.",
49:        "possible_impact": "La conversión no controlada puede provocar diferencias entre el color aprobado y el resultado impreso.",
50:        "recommended_action": "Convertir los elementos RGB usando el perfil de color definido para el trabajo antes de liberar.",
52:        "evidence": {"occurrence_count": count, "max_object_area_percent": max_area, "page": top_risk.get("page"), "rule_applied": "RGB_OBJECT", "confidence": "Alta"}
57:def _build_barcode_insight(top_risk, related):
79:        "brief_comment": brief,
80:        "what_found": found,
81:        "why_it_matters": "Los códigos de barras y QR son elementos funcionales. No basta con que se vean bien; deben poder leerse de forma confiable en control de calidad y uso final.",
82:        "possible_impact": "Un código pixelado, rasterizado a baja resolución o construido con varias tintas puede generar problemas de registro, lectura deficiente, rechazo de calidad, reproceso o bloqueo de lote.",
83:        "recommended_action": selected.get("action") or selected.get("recommendation") or "Validar lectura del código. Preferir código vectorial o imagen de alta resolución. Confirmar que esté construido a una sola tinta cuando aplique y evitar códigos multitinta por riesgo de registro.",
92:            "rule_applied": "BARCODE_RISK",
97:def _build_lowres_insight(top_risk, related):
115:        "brief_comment": brief,
116:        "what_found": found,
117:        "why_it_matters": "Una imagen puede verse bien en pantalla, pero perder calidad cuando se amplía dentro del diseño o se imprime.",
118:        "possible_impact": "Puede verse pixelada, borrosa o con pérdida de detalle en impresión.",
119:        "recommended_action": "Solicitar una imagen de mayor resolución o reducir el tamaño de uso si el diseño lo permite.",
121:        "evidence": {"effective_dpi": dpi, "minimum_suggested_dpi": minimum, "recommended_dpi": recommended, "object_area_percent": area, "image_role": role, "page": top_risk.get("page"), "rule_applied": "LOW_IMAGE_RESOLUTION", "confidence": "Alta"}
125:def _build_tac_insight(top_risk, related):
143:        "brief_comment": brief,
144:        "what_found": found,
145:        "why_it_matters": "La cobertura total de tinta debe mantenerse dentro del límite definido por proceso, tinta y sustrato.",
146:        "possible_impact": "Un TAC alto puede generar secado lento, repinte, bloqueo, ganancia o inestabilidad durante impresión.",
147:        "recommended_action": "Reducir la cobertura total revisando separación, perfil de conversión, curvas o negro enriquecido.",
149:        "evidence": {"detected_tac": tac, "tac_limit": limit, "excess": excess, "page": top_risk.get("page"), "rule_applied": "HIGH_TAC_RISK", "confidence": "Alta"}
154:def _build_small_text_insight(top_risk, related):
172:        "brief_comment": brief,
173:        "what_found": found,
174:        "why_it_matters": "En packaging, textos muy pequeños pueden perder definición por ganancia, registro, sustrato, anilox, cilindro, trama o condición de impresión.",
175:        "possible_impact": "Puede afectar legibilidad de legales, ingredientes, advertencias, claims o información regulatoria.",
176:        "recommended_action": selected.get("action") or selected.get("recommendation") or "Aumentar tamaño, simplificar tipografía o validar mínimo técnico según proceso y condición de impresión.",
185:            "rule_applied": "SMALL_TEXT_RISK",
190:def _build_font_insight(top_risk, related):
210:        "brief_comment": brief,
211:        "what_found": found,
212:        "why_it_matters": "Si una fuente no está embebida, el sistema que procese el archivo puede sustituirla por otra.",
213:        "possible_impact": "Puede cambiar el texto, la composición, los legales, ingredientes, códigos o elementos aprobados del diseño.",
214:        "recommended_action": "Incrustar las fuentes en el PDF o convertir el texto a curvas antes de enviar a producción.",
216:        "evidence": {"occurrence_count": count, "sample_fonts": font_names[:3], "page": top_risk.get("page"), "rule_applied": "FONT_NOT_EMBEDDED", "confidence": "Alta"}
221:def _build_spot_insight(top_risk, related):
257:        "brief_comment": brief,
258:        "what_found": found,
259:        "why_it_matters": "Las tintas spot definen separaciones adicionales que deben formularse, asignarse y controlarse correctamente en preprensa y prensa.",
260:        "possible_impact": "Nombres incorrectos, duplicados o exceso de spots pueden generar errores de separación, tintas innecesarias, mayor setup o riesgo operativo.",
261:        "recommended_action": selected.get("action") or selected.get("recommendation") or "Validar nombres, duplicados y necesidad real de cada tinta spot.",
263:        "evidence": {"printable_spot_count": spot_count, "spot_category": categories, "sample_spot_names": names[:5], "page": top_risk.get("page"), "rule_applied": "SPOT_COLOR_RISK", "confidence": "Media"}
267:def _build_separation_insight(top_risk, related):
291:        "brief_comment": brief,
292:        "what_found": found,
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
324:        "what_found": top_risk.get("detail") or "Se detectó un hallazgo relevante.",
325:        "why_it_matters": "Puede afectar el flujo de preprensa o producción.",
326:        "possible_impact": top_risk.get("risk_reason") or "Puede generar riesgo operativo.",
327:        "recommended_action": top_risk.get("action") or top_risk.get("recommendation") or "Revisar antes de liberar.",
344:            risk["expert_comment"] = insight.get("brief_comment")

---

## 3. Readiness Summary / simple risks / next action

10:- Identificar top risks.
14:def sort_top_risks(findings, limit=3):
129:def get_main_reason(top_risks):
130:    if not top_risks:
133:    top = top_risks[0]
136:        top.get("risk_reason")
142:def get_simple_risk(top_risks):
143:    if not top_risks:
146:    top = top_risks[0]
149:    simple_map = {
150:        "RGB_OBJECT": "Puede generar variación de color.",
151:        "LOW_IMAGE_RESOLUTION": "Puede generar pérdida visible de calidad.",
152:        "BARCODE_RISK": "Puede generar problemas de lectura o rechazo de calidad.",
153:        "FONT_NOT_EMBEDDED": "Puede modificar texto o apariencia aprobada.",
154:        "SMALL_TEXT_RISK": "Puede generar problemas de legibilidad.",
155:        "HIGH_TAC_RISK": "Puede generar problemas de impresión, secado o estabilidad.",
156:        "OVERPRINT_RISK": "Puede alterar el resultado visual por sobreimpresión.",
158:        "SPOT_COLOR_RISK": "Puede generar confusión o complejidad en separaciones spot.",
159:        "SEPARATION_COUNT_RISK": "Puede aumentar la complejidad operativa de impresión.",
160:        "PDF_STRUCTURE_RISK": "Puede afectar procesamiento, RIP o preprensa."
163:    return simple_map.get(
169:def get_next_action(decision, top_risks):
177:        if top_risks:
178:            return top_risks[0].get(
185:        if top_risks:
186:            return top_risks[0].get(
227:def build_user_message(decision, main_reason, next_action):
230:        f"Siguiente acción recomendada: {next_action}"
243:    top_risks = sort_top_risks(findings)
245:    main_reason = get_main_reason(top_risks)
246:    simple_risk = get_simple_risk(top_risks)
247:    next_action = get_next_action(decision, top_risks)
250:    user_message = build_user_message(decision, main_reason, next_action)
259:        "simple_risk": simple_risk,
260:        "next_action": next_action,
262:        "top_risks": top_risks
268:        "RGB_OBJECT",
269:        "LOW_IMAGE_RESOLUTION",
270:        "SMALL_TEXT_RISK",
271:        "BARCODE_RISK",
272:        "SPOT_COLOR_RISK",
273:        "SEPARATION_COUNT_RISK",
277:        "FONT_NOT_EMBEDDED",
278:        "PDF_STRUCTURE_RISK",
330:                finding.get("risk_reason")

---

## 4. Matrix actual

# Gate0 — Check Intelligence Matrix v1

Esta matriz define la inteligencia base de cada check: criterio, contexto operativo, acción recomendada y tipo de corrección.

No reemplaza todavía la lógica del motor. Es una referencia de producto para ordenar la evolución de Gate0 hacia fix asistido y futuro autofix.

---

## Clasificación de fix

| Tipo | Significado |
|---|---|
| manual | Requiere criterio humano o intervención directa en preprensa. |
| assisted | Gate0 puede guiar la corrección, pero el usuario debe validar antes de liberar. |
| autofix_candidate | A futuro podría corregirse automáticamente bajo reglas controladas. |
| blocked | No debe corregirse automáticamente sin información adicional. |

---

## Matriz por check

| Check | Criterio aplicado | Contexto operativo | Acción recomendada | Fix type v1 | Limitación actual | Futuro |
|---|---|---|---|---|---|---|
| RGB_OBJECT | Detecta operadores RGB en el PDF. | En impresión packaging, RGB puede convertirse de forma no controlada y alterar color final. | Convertir a CMYK o spot validado según perfil de impresión. | assisted | No clasifica intención del objeto. | Conversión asistida con perfil aprobado. |
| LOW_IMAGE_RESOLUTION | Evalúa DPI efectivo de imágenes. | Imágenes de baja resolución pueden pixelarse al tamaño final. | Reemplazar imagen, reducir tamaño de uso o validar si es intencional. | assisted | No distingue completamente rol visual del objeto. | Sugerir reemplazo o alerta por zona crítica. |
| BARCODE_RISK | Detecta candidato barcode/QR como imagen de bajo DPI. | Barcode/QR es funcional: debe leerse, no solo verse bien. | Validar escaneo, usar vector o alta resolución, confirmar una sola tinta cuando aplique. | assisted | No decodifica, no valida GS1, quiet zone ni multitinta. | Validar single ink, quiet zone, magnificación y lectura. |
| SMALL_TEXT_RISK | Evalúa texto vivo por tamaño en puntos. | Texto pequeño puede perder legibilidad, más aún en negativo o multitinta. | Aumentar tamaño, simplificar fuente o validar mínimo técnico. | assisted | No clasifica aún positivo/negativo/multitinta. | Clasificar contexto visual y proponer ajuste. |
| FONT_NOT_EMBEDDED | Detecta fuentes no embebidas. | Puede haber sustitución tipográfica o cambios de texto al abrir/procesar. | Incrustar fuentes o convertir texto a curvas. | manual | No corrige ni convierte fuentes. | Guía asistida o validación post-conversión. |
| HIGH_TAC_RISK | Evalúa cobertura total de tinta contra límite de perfil. | TAC alto puede generar secado deficiente, repinte, ganancia o inestabilidad. | Reducir TAC revisando separación, perfil, curvas o negro enriquecido. | assisted | No modifica separaciones. | Sugerir estrategia de reducción por perfil. |
| OVERPRINT_RISK | Detecta riesgo de sobreimpresión. | Una sobreimpresión mal aplicada puede desaparecer elementos o cambiar apariencia. | Verificar intención y validar visualmente contra arte aprobado. | assisted | Detección parcial, no siempre por objeto. | Comparación visual y fix asistido. |
| SPOT_COLOR_RISK | Evalúa spots, blancos, nombres genéricos y duplicidades. | Spots mal nombrados o duplicados generan tintas extra, errores de formulación o separación. | Normalizar nombres y validar necesidad real de cada spot. | assisted | No sabe aún intención completa del diseño. | Normalización asistida y sugerencia de racionalización. |
| SEPARATION_COUNT_RISK | Evalúa cantidad de separaciones imprimibles. | Muchas separaciones aumentan complejidad, costo y riesgo operativo. | Racionalizar spots y validar capacidad de prensa. | assisted | No decide qué tinta eliminar. | Sugerir candidatos a conversión CMYK o consolidación. |
| PDF_STRUCTURE_RISK | Evalúa páginas vacías, tamaño, objetos y complejidad. | PDFs pesados o corruptos pueden fallar en RIP, trapping o imposición. | Optimizar, reconstruir o validar archivo antes de procesos pesados. | manual | No repara estructura PDF. | Limpieza estructural asistida. |

---

## Principio de evolución

Cada check debe avanzar en este orden:

1. Detectar.
2. Explicar.
3. Priorizar.
4. Guiar corrección.
5. Clasificar fix.
6. Ejecutar fix asistido o automático solo cuando sea seguro.


---

## 5. Dashboard criterio/contexto actual

297:  "RGB_OBJECT": "Objetos RGB detectados",
298:  "LOW_IMAGE_RESOLUTION": "Resolución de imagen insuficiente",
299:  "BARCODE_RISK": "Código de barras / QR",
300:  "FONT_NOT_EMBEDDED": "Fuentes no embebidas",
301:  "SMALL_TEXT_RISK": "Texto pequeño / legibilidad",
302:  "HIGH_TAC_RISK": "Cobertura total de tinta elevada",
303:  "OVERPRINT_RISK": "Observación de sobreimpresión",
305:  "SPOT_COLOR_RISK": "Observación en tintas spot",
306:  "SEPARATION_COUNT_RISK": "Complejidad de separaciones",
307:  "PDF_STRUCTURE_RISK": "Estructura PDF"
471:function riskCriteria(check){
473:    RGB_OBJECT:"Detecta objetos definidos en RGB dentro del PDF.",
474:    LOW_IMAGE_RESOLUTION:"Evalúa la resolución efectiva de imágenes contra el mínimo operativo del perfil.",
475:    BARCODE_RISK:"Detecta candidatos barcode/QR como imagen de bajo DPI.",
476:    SMALL_TEXT_RISK:"Evalúa texto vivo por debajo del tamaño mínimo configurado.",
477:    FONT_NOT_EMBEDDED:"Detecta fuentes no embebidas en el PDF.",
478:    HIGH_TAC_RISK:"Evalúa cobertura total de tinta contra el límite del perfil.",
479:    OVERPRINT_RISK:"Detecta condiciones de sobreimpresión que requieren validación.",
480:    SPOT_COLOR_RISK:"Evalúa tintas spot, blancos, nombres genéricos y posibles duplicidades.",
481:    SEPARATION_COUNT_RISK:"Evalúa cantidad de separaciones imprimibles contra capacidad operativa.",
482:    PDF_STRUCTURE_RISK:"Evalúa páginas vacías, tamaño, cantidad de objetos y complejidad del PDF."
487:function riskOperationalContext(check){
489:    RGB_OBJECT:"En packaging, RGB puede convertirse de forma no controlada y alterar el color final.",
490:    LOW_IMAGE_RESOLUTION:"Una imagen de baja resolución puede pixelarse al tamaño final de impresión.",
491:    BARCODE_RISK:"Barcode/QR es un elemento funcional: debe leerse, no solo verse bien.",
492:    SMALL_TEXT_RISK:"Texto pequeño puede perder legibilidad, especialmente en negativo, multitinta o procesos exigentes.",
493:    FONT_NOT_EMBEDDED:"Una fuente no embebida puede sustituirse y modificar textos, medidas o apariencia.",
494:    HIGH_TAC_RISK:"TAC alto puede causar secado deficiente, repinte, ganancia o inestabilidad en prensa.",
495:    OVERPRINT_RISK:"Una sobreimpresión incorrecta puede hacer desaparecer elementos o cambiar el resultado visual.",
496:    SPOT_COLOR_RISK:"Spots mal nombrados o duplicados pueden generar tintas extra, errores de formulación o separaciones incorrectas.",
497:    SEPARATION_COUNT_RISK:"Muchas separaciones aumentan complejidad, costo, setup y riesgo operativo.",
498:    PDF_STRUCTURE_RISK:"Un PDF muy pesado, vacío o complejo puede fallar en RIP, trapping, imposición o procesamiento."
552:        <div>${esc(riskCriteria(r.check))}</div>
556:        <div>${esc(riskOperationalContext(r.check))}</div>
