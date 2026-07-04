"""
Gate0 Check Intelligence v1

Fuente central liviana para criterio, contexto, impacto, fix type,
limitación actual y evolución futura por check.

No reemplaza business_rules ni expert_comment_engine.
Enriquece el JSON para dashboard, reportes y futuros agentes.
"""

CHECK_INTELLIGENCE = {
    "RGB_OBJECT": {
        "criteria": "Detecta objetos definidos en RGB dentro del PDF.",
        "operational_context": "En packaging, RGB puede convertirse de forma no controlada y alterar el color final.",
        "possible_impact": "Cambio de color, diferencia contra prueba, retrabajo o reclamo visual.",
        "fix_type": "assisted",
        "current_limitation": "No clasifica intención del objeto ni decide automáticamente el perfil correcto.",
        "future_evolution": "Conversión asistida con perfil aprobado y validación visual antes/después.",
    },
    "LOW_IMAGE_RESOLUTION": {
        "criteria": "Evalúa resolución efectiva de imágenes al tamaño final de uso.",
        "operational_context": "Una imagen de baja resolución puede pixelarse o perder detalle al imprimirse.",
        "possible_impact": "Pérdida visible de calidad, reclamo visual o necesidad de reemplazar imagen.",
        "fix_type": "assisted",
        "current_limitation": "No distingue completamente rol de imagen: producto, fondo, textura, logo o elemento decorativo.",
        "future_evolution": "Clasificar rol visual y ajustar severidad según zona crítica del arte.",
    },
    "BARCODE_RISK": {
        "criteria": "Detecta candidatos barcode/QR como imagen de bajo DPI mediante geometría, tamaño y resolución efectiva.",
        "operational_context": "Barcode y QR son elementos funcionales. No basta con que se vean bien; deben poder leerse correctamente en control de calidad, logística y uso final.",
        "possible_impact": "Un código pixelado, rasterizado a baja resolución o construido con varias tintas puede generar problemas de registro, lectura deficiente, rechazo de calidad, reproceso, bloqueo de lote o problema logístico/comercial.",
        "fix_type": "assisted",
        "current_limitation": "No decodifica, no valida GS1, quiet zone, magnificación, contraste ni confirma si el código está construido a una sola tinta.",
        "future_evolution": "Validar single ink, quiet zone, magnificación, contraste, decodificación y cumplimiento GS1 cuando aplique.",
        "prepress_guidance": "Validar escaneo antes de liberar. Preferir código vectorial o imagen de alta resolución.",
        "single_ink_guidance": "Confirmar que el código esté construido a una sola tinta cuando aplique; evitar códigos multitinta por riesgo de registro y lectura.",
        "do_not_claim": "Barcode Intelligence v1 detecta riesgo técnico del candidato; no certifica lectura ni cumplimiento GS1.",
    },
    "SMALL_TEXT_RISK": {
        "criteria": "Evalúa texto vivo por debajo del tamaño mínimo configurado en el perfil operativo.",
        "operational_context": "Texto pequeño puede perder legibilidad en impresión, especialmente cuando está en negativo, sobre fondos cargados, en varias tintas o en procesos exigentes.",
        "possible_impact": "Texto ilegible, pérdida de información crítica, incumplimiento legal/regulatorio, reclamo de marca, rechazo de calidad o necesidad de rediseño.",
        "fix_type": "assisted",
        "current_limitation": "No clasifica todavía texto positivo, negativo, multitinta, sobre fondo complejo ni distingue texto legal crítico de texto decorativo.",
        "future_evolution": "Small Text v2 debe clasificar positivo/negativo/multitinta/fondo. Small Text v3 debe proponer correcciones asistidas según proceso, contraste y criticidad.",
        "prepress_guidance": "Validar tamaño mínimo, legibilidad real y condición de impresión antes de liberar.",
        "negative_text_guidance": "Si el texto es negativo o va sobre fondo cargado, usar un criterio más conservador que para texto positivo.",
        "multicolor_guidance": "Evitar texto pequeño construido en varias tintas cuando pueda generar problemas de registro o borde sucio.",
        "do_not_claim": "Small Text v1 mide tamaño de texto vivo; no certifica legibilidad final ni clasifica todavía positivo/negativo/multitinta.",
    },
    "FONT_NOT_EMBEDDED": {
        "criteria": "Detecta fuentes no embebidas en el PDF.",
        "operational_context": "Una fuente no embebida puede sustituirse al abrir, editar, procesar, ripear o convertir el archivo, alterando textos, medidas, legales y apariencia.",
        "possible_impact": "Cambio tipográfico, texto corrido, variación de layout, pérdida de caracteres especiales, incumplimiento legal, diferencia frente al arte aprobado o rechazo de calidad.",
        "fix_type": "manual",
        "current_limitation": "Gate0 no incrusta ni convierte fuentes automáticamente. Solo alerta el riesgo y recomienda corrección antes de liberar.",
        "future_evolution": "Guía asistida de corrección, validación post-conversión a curvas y comparación visual antes/después.",
        "prepress_guidance": "Incrustar fuentes en el PDF o convertir texto a curvas antes de liberar a producción.",
        "legal_text_guidance": "Prestar especial atención si la fuente afecta textos legales, ingredientes, advertencias, códigos, claims o información obligatoria.",
        "do_not_claim": "Font v1 detecta riesgo de fuente no embebida; no garantiza que el texto haya cambiado ni corrige la fuente automáticamente.",
    },
    "HIGH_TAC_RISK": {
        "criteria": "Evalúa cobertura total de tinta contra el límite configurado en el perfil operativo.",
        "operational_context": "TAC alto puede generar problemas de secado, repinte, ganancia, trapping, transferencia, bloqueo o inestabilidad de color en prensa.",
        "possible_impact": "Defectos de impresión, demora de secado, repinte, variabilidad, rechazo interno, reclamo de calidad o necesidad de reprocesar la separación.",
        "fix_type": "assisted",
        "current_limitation": "No modifica separaciones ni propone una receta exacta de reducción. No distingue todavía con precisión entre negro enriquecido intencional, imagen, fondo o zona crítica.",
        "future_evolution": "Sugerir estrategia de reducción por perfil, zona, proceso, tipo de objeto, área afectada y objetivo visual.",
        "area_guidance": "La severidad debe considerar no solo el TAC detectado, sino también el área afectada. Un exceso pequeño puede ser informativo; un exceso alto en área grande puede ser crítico.",
        "rich_black_guidance": "Cuando el TAC alto provenga de negro enriquecido, revisar si la construcción es intencional y compatible con el perfil de impresión.",
        "profile_guidance": "El límite de TAC debe venir del perfil operativo del proceso, no de un valor genérico oculto en código.",
        "do_not_claim": "High TAC v1 alerta riesgo de cobertura total; no corrige separaciones automáticamente ni garantiza desempeño en prensa.",
    },
    "OVERPRINT_RISK": {
        "criteria": "Detecta condiciones de sobreimpresión que requieren validación técnica y visual.",
        "operational_context": "La sobreimpresión puede ser una intención válida de preprensa, como trapping manual o refuerzo, pero si está mal aplicada puede hacer desaparecer elementos o alterar el resultado impreso.",
        "possible_impact": "Elementos perdidos, textos invisibles, cambios de color, errores con blanco, diferencias frente al arte aprobado, reproceso o rechazo de calidad.",
        "fix_type": "assisted",
        "current_limitation": "La detección actual es parcial. No siempre identifica sobreimpresión por objeto ni confirma intención visual del diseñador o preprensa.",
        "future_evolution": "Mapa por objeto, comparación visual antes/después, validación por separaciones y fix asistido solo para casos seguros.",
        "white_overprint_guidance": "Blanco con sobreimpresión requiere atención especial. Puede ser intencional, pero también puede anular reservas o producir un resultado inesperado.",
        "visual_validation_guidance": "Validar separaciones y previsualización de overprint antes de liberar. No confiar solo en la vista normal del PDF.",
        "intent_guidance": "Confirmar si la sobreimpresión corresponde a intención de diseño, trapping manual, refuerzo cromático o error.",
        "do_not_claim": "Overprint v1 alerta riesgo contextual; no certifica intención ni corrige sobreimpresiones automáticamente.",
    },
    "SPOT_COLOR_RISK": {
        "criteria": "Evalúa tintas spot, blancos, nombres genéricos, duplicidades y separaciones técnicas.",
        "operational_context": "Las tintas spot son separaciones productivas. Si están mal nombradas, duplicadas o mezcladas con separaciones técnicas, pueden generar errores de formulación, tintas adicionales o confusión en preprensa/prensa.",
        "possible_impact": "Tinta incorrecta, costo adicional, separación duplicada, error de formulación, blanco mal interpretado, setup innecesario, reproceso o riesgo de producir con una separación no prevista.",
        "fix_type": "assisted",
        "current_limitation": "No conoce todavía la intención completa del diseño ni decide automáticamente qué spot debe eliminarse, consolidarse o mantenerse.",
        "future_evolution": "Normalización asistida de nombres, detección de equivalencias, sugerencia de racionalización y validación contra especificación de cliente/prensa.",
        "white_ink_guidance": "Validar que las separaciones de blanco correspondan a la intención del arte. Si hay múltiples blancos, confirmar si son necesarios por opacidad, reserva o estrategia técnica.",
        "generic_name_guidance": "Evitar nombres genéricos como Spot 1, Spot 2 o nombres poco claros. Renombrar con nombre técnico o tinta real antes de liberar.",
        "duplicate_guidance": "Revisar posibles duplicidades por diferencias menores de nomenclatura, por ejemplo 485C vs 485 C, White vs Blanco o variantes similares.",
        "technical_separation_guidance": "Validar que separaciones técnicas como troquel, barniz, corte, guía o dieline no sean tratadas como tintas imprimibles.",
        "rationalization_guidance": "Cuando existan muchas tintas spot, revisar si alguna puede racionalizarse, consolidarse o convertirse a CMYK según estrategia de impresión.",
        "do_not_claim": "Spot Color Intelligence v1 alerta riesgos de nomenclatura, duplicidad y complejidad; no decide automáticamente la intención del diseño ni elimina tintas.",
    },
    "SEPARATION_COUNT_RISK": {
        "criteria": "Evalúa cantidad de separaciones imprimibles contra los umbrales definidos en el perfil operativo.",
        "operational_context": "Cada separación imprimible puede representar una tinta, estación, formulación o control adicional. Muchas separaciones aumentan complejidad, setup, costo y riesgo operativo.",
        "possible_impact": "Trabajo difícil de producir, mayor tiempo de preparación, mayor probabilidad de error de secuencia, incompatibilidad con prensa disponible, costo adicional o necesidad de racionalizar tintas.",
        "fix_type": "assisted",
        "current_limitation": "No decide automáticamente qué separación eliminar, consolidar o convertir a CMYK. Tampoco conoce todavía la configuración real de cada prensa o cliente.",
        "future_evolution": "Sugerir candidatos de racionalización, consolidación o conversión según cliente, prensa, perfil, secuencia de impresión y objetivo visual.",
        "press_capacity_guidance": "Validar capacidad real de prensa, número de estaciones disponibles, secuencia de impresión y necesidad productiva de cada separación.",
        "rationalization_guidance": "Revisar si alguna separación spot puede consolidarse, eliminarse o convertirse a CMYK sin afectar intención visual o requerimiento técnico.",
        "technical_separation_guidance": "Diferenciar separaciones imprimibles de separaciones técnicas como troquel, guía, corte, barniz técnico o referencias no productivas.",
        "do_not_claim": "Separation Count v1 alerta complejidad por cantidad de separaciones; no decide automáticamente la estrategia de reducción ni garantiza producibilidad.",
    },
    "PDF_STRUCTURE_RISK": {
        "criteria": "Evalúa páginas vacías, tamaño de archivo, cantidad de objetos, imágenes y complejidad estructural del PDF.",
        "operational_context": "Un PDF vacío, pesado, corrupto o excesivamente complejo puede fallar durante RIP, trapping, imposición, edición, comparación o automatización.",
        "possible_impact": "Lentitud, error de procesamiento, archivo no procesable, pérdida de elementos, fallo en RIP, bloqueo del flujo o necesidad de reconstruir el arte.",
        "fix_type": "manual",
        "current_limitation": "Gate0 no repara estructura PDF automáticamente. Solo alerta complejidad, páginas vacías o señales de riesgo estructural.",
        "future_evolution": "Limpieza estructural asistida, validación antes/después, reducción de complejidad y clasificación de objetos problemáticos.",
        "empty_page_guidance": "Si existen páginas vacías, validar si son intencionales. Una página vacía no esperada puede indicar exportación incorrecta o archivo incompleto.",
        "complexity_guidance": "Si el archivo tiene demasiados objetos, imágenes o peso excesivo, revisar optimización antes de procesos pesados como RIP, trapping o imposición.",
        "workflow_guidance": "Cuando el PDF sea estructuralmente crítico, conviene reconstruir, optimizar o solicitar nuevo archivo antes de liberar a producción.",
        "do_not_claim": "PDF Structure v1 alerta riesgo estructural; no corrige, optimiza ni garantiza integridad completa del PDF.",
    },
}


def get_check_intelligence(check):
    return CHECK_INTELLIGENCE.get(check, {
        "criteria": "Criterio técnico definido por Gate0.",
        "operational_context": "Este hallazgo puede impactar calidad, producción o liberación del archivo.",
        "possible_impact": "Riesgo operativo o de calidad pendiente de clasificación.",
        "fix_type": "manual",
        "current_limitation": "Inteligencia específica pendiente de consolidar.",
        "future_evolution": "Definir evolución del check según validación de producto.",
    })


def enrich_finding_with_check_intelligence(finding):
    enriched = finding.copy()
    intelligence = get_check_intelligence(enriched.get("check"))

    for key, value in intelligence.items():
        enriched.setdefault(key, value)

    return enriched


def enrich_findings_with_check_intelligence(findings):
    return [enrich_finding_with_check_intelligence(f) for f in findings]
