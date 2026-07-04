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

