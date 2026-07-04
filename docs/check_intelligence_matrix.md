# Gate0 — Check Intelligence Matrix v2

Matriz maestra de inteligencia por check.

Esta matriz consolida criterio aplicado, contexto operativo, impacto, acción recomendada, tipo de fix, limitaciones actuales y evolución futura.

No reemplaza todavía la lógica del motor. Su objetivo es evitar pérdida de conocimiento y servir como referencia para Business Rules, Expert Comments, Fix Plan y futuro AutoFix.

---

## Clasificación de fix

| Tipo | Significado |
|---|---|
| manual | Requiere criterio humano o intervención directa en preprensa. |
| assisted | Gate0 puede guiar la corrección, pero el usuario debe validar antes de liberar. |
| autofix_candidate | A futuro podría corregirse automáticamente bajo reglas controladas. |
| blocked | No debe corregirse automáticamente sin información adicional. |

---

## 1. RGB_OBJECT

**Criterio aplicado**  
Detecta objetos definidos en RGB dentro del PDF.

**Contexto operativo**  
En packaging, un objeto RGB puede convertirse de forma no controlada durante RIP, edición o exportación, generando desviación de color frente al objetivo aprobado.

**Impacto posible**  
Cambio de color, diferencia contra prueba, retrabajo de preprensa o reclamo por apariencia final.

**Acción recomendada**  
Convertir RGB a CMYK o spot validado según perfil de impresión y proceso.

**Fix type v1**  
assisted

**Limitación actual**  
No clasifica intención del objeto ni decide automáticamente el perfil correcto de conversión.

**Futuro**  
Conversión asistida con perfil aprobado por cliente/proceso y validación visual antes/después.

---

## 2. LOW_IMAGE_RESOLUTION

**Criterio aplicado**  
Evalúa resolución efectiva de imágenes al tamaño final de uso.

**Contexto operativo**  
Una imagen con baja resolución puede verse pixelada o perder detalle al imprimirse, especialmente si ocupa un área relevante del diseño.

**Impacto posible**  
Pérdida visible de calidad, reclamo visual, rechazo interno o necesidad de reemplazar imagen.

**Acción recomendada**  
Solicitar imagen de mayor resolución, reducir tamaño de uso o validar si la baja resolución es intencional/no crítica.

**Fix type v1**  
assisted

**Limitación actual**  
No distingue completamente rol de la imagen: producto, fondo, textura, logo, barcode, elemento decorativo.

**Futuro**  
Clasificar rol visual del objeto y ajustar severidad según zona crítica del arte.

---

## 3. BARCODE_RISK

**Criterio aplicado**  
Detecta candidatos barcode/QR como imagen de bajo DPI mediante geometría, tamaño y resolución efectiva.

**Contexto operativo**  
Barcode y QR son elementos funcionales. No basta con que se vean bien; deben poder leerse correctamente en control de calidad, logística y uso final.

**Impacto posible**  
Código ilegible, rechazo de calidad, bloqueo de lote, reproceso, reclamo o problema comercial/logístico.

**Acción recomendada**  
Validar escaneo. Preferir código vectorial o imagen de alta resolución. Confirmar que esté construido a una sola tinta cuando aplique; evitar códigos multitinta por riesgo de registro y lectura.

**Fix type v1**  
assisted

**Limitación actual**  
No decodifica, no valida GS1, quiet zone, magnificación, contraste ni si está a una sola tinta.

**Futuro**  
Validación de single ink, quiet zone, magnificación, decodificación y cumplimiento GS1 cuando aplique.

---

## 4. SMALL_TEXT_RISK

**Criterio aplicado**  
Evalúa texto vivo por debajo del tamaño mínimo configurado en el perfil operativo.

**Contexto operativo**  
Texto pequeño puede perder legibilidad, más aún si está en negativo, sobre fondos cargados, en varias tintas o en procesos exigentes.

**Impacto posible**  
Texto ilegible, incumplimiento legal/regulatorio, reclamo de marca o rechazo por calidad.

**Acción recomendada**  
Aumentar tamaño, simplificar tipografía, revisar contraste o validar mínimo técnico según proceso y condición de impresión.

**Fix type v1**  
assisted

**Limitación actual**  
No clasifica todavía texto positivo, negativo, multitinta, sobre fondo complejo o texto legal crítico.

**Futuro**  
Small Text v2: clasificación positivo/negativo/multitinta/fondo. Small Text v3: propuesta asistida de corrección.

---

## 5. FONT_NOT_EMBEDDED

**Criterio aplicado**  
Detecta fuentes no embebidas en el PDF.

**Contexto operativo**  
Si una fuente no está embebida, puede sustituirse al abrir, procesar, ripear o editar el archivo, alterando textos, medidas y apariencia.

**Impacto posible**  
Cambio tipográfico, texto corrido, errores de layout, incumplimiento legal o diferencia frente al arte aprobado.

**Acción recomendada**  
Incrustar fuentes en el PDF o convertir texto a curvas antes de liberar.

**Fix type v1**  
manual

**Limitación actual**  
Gate0 no corrige ni convierte fuentes automáticamente.

**Futuro**  
Guía asistida de corrección y validación post-conversión.

---

## 6. HIGH_TAC_RISK

**Criterio aplicado**  
Evalúa cobertura total de tinta contra el límite configurado en el perfil operativo.

**Contexto operativo**  
TAC alto puede generar problemas de secado, repinte, ganancia, trapping, transferencia o inestabilidad de color.

**Impacto posible**  
Problemas en prensa, defectos de impresión, variabilidad, rechazo interno o necesidad de reprocesar separación.

**Acción recomendada**  
Reducir cobertura total revisando separación, perfil de conversión, curvas, negro enriquecido o estrategia cromática.

**Fix type v1**  
assisted

**Limitación actual**  
No modifica separaciones ni propone receta exacta de reducción.

**Futuro**  
Sugerir estrategia de reducción por perfil, zona, proceso y objetivo visual.

---

## 7. OVERPRINT_RISK

**Criterio aplicado**  
Detecta condiciones de sobreimpresión que requieren validación.

**Contexto operativo**  
Una sobreimpresión mal aplicada puede hacer desaparecer elementos, alterar apariencia o generar resultados no visibles en una revisión superficial.

**Impacto posible**  
Elementos perdidos, textos invisibles, cambios de color, error en blanco o diferencia frente al arte aprobado.

**Acción recomendada**  
Verificar intención de diseño, revisar separaciones y validar visualmente contra arte aprobado.

**Fix type v1**  
assisted

**Limitación actual**  
Detección parcial. No siempre identifica sobreimpresión por objeto ni combina totalmente con color/rol del objeto.

**Futuro**  
Comparación visual, mapa por objeto y fix asistido para casos seguros.

---

## 8. SPOT_COLOR_RISK

**Criterio aplicado**  
Evalúa tintas spot, blancos, nombres genéricos, duplicidades y separaciones técnicas.

**Contexto operativo**  
Spots mal nombrados, duplicados o genéricos pueden generar tintas adicionales, errores de formulación o confusión en separación.

**Impacto posible**  
Tinta incorrecta, costo adicional, error de formulación, separación duplicada, problemas de aprobación o setup innecesario.

**Acción recomendada**  
Normalizar nombres, validar duplicidades, confirmar intención de blancos y racionalizar spots cuando corresponda.

**Fix type v1**  
assisted

**Limitación actual**  
No conoce todavía intención completa del diseño ni decide automáticamente qué spot debe eliminarse o consolidarse.

**Futuro**  
Normalización asistida, detección de equivalencias y sugerencia de racionalización.

---

## 9. SEPARATION_COUNT_RISK

**Criterio aplicado**  
Evalúa cantidad de separaciones imprimibles contra umbrales del perfil operativo.

**Contexto operativo**  
Más separaciones implican mayor complejidad, más estaciones, más setup, mayor costo y más riesgo operativo.

**Impacto posible**  
Trabajo difícil de producir, necesidad de racionalizar tintas, mayor tiempo de preparación o incompatibilidad con prensa disponible.

**Acción recomendada**  
Validar capacidad de prensa, secuencia y necesidad real de cada separación. Evaluar conversión de colores secundarios a CMYK o consolidación de spots.

**Fix type v1**  
assisted

**Limitación actual**  
No decide qué tinta eliminar ni conoce automáticamente restricciones reales de cada prensa.

**Futuro**  
Sugerir candidatos de racionalización o conversión según cliente, prensa y perfil.

---

## 10. PDF_STRUCTURE_RISK

**Criterio aplicado**  
Evalúa páginas vacías, tamaño de archivo, cantidad de objetos, imágenes y complejidad estructural.

**Contexto operativo**  
PDFs vacíos, pesados o muy complejos pueden fallar en RIP, trapping, imposición, edición o procesamiento automático.

**Impacto posible**  
Error de procesamiento, lentitud, archivo corrupto, fallo en producción o necesidad de reconstrucción.

**Acción recomendada**  
Optimizar, reconstruir o validar el PDF antes de procesos pesados.

**Fix type v1**  
manual

**Limitación actual**  
No repara estructura PDF automáticamente.

**Futuro**  
Limpieza estructural asistida y validación antes/después.

---

## Principio de evolución

Cada check debe avanzar en este orden:

1. Detectar.
2. Explicar.
3. Priorizar.
4. Recomendar.
5. Clasificar tipo de fix.
6. Guiar corrección.
7. Automatizar solo si es seguro.

