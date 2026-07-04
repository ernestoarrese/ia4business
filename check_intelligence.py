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
        "operational_context": "Una fuente no embebida puede sustituirse al abrir, procesar o ripear el archivo.",
        "possible_impact": "Cambio tipográfico, texto corrido, error de layout o diferencia frente al arte aprobado.",
        "fix_type": "manual",
        "current_limitation": "Gate0 no corrige ni convierte fuentes automáticamente.",
        "future_evolution": "Guía asistida y validación post-conversión.",
    },
    "HIGH_TAC_RISK": {
        "criteria": "Evalúa cobertura total de tinta contra el límite del perfil operativo.",
        "operational_context": "TAC alto puede causar secado deficiente, repinte, ganancia o inestabilidad en prensa.",
        "possible_impact": "Defectos de impresión, variabilidad, rechazo interno o necesidad de reprocesar separación.",
        "fix_type": "assisted",
        "current_limitation": "No modifica separaciones ni propone receta exacta de reducción.",
        "future_evolution": "Sugerir estrategia de reducción por perfil, zona, proceso y objetivo visual.",
    },
    "OVERPRINT_RISK": {
        "criteria": "Detecta condiciones de sobreimpresión que requieren validación.",
        "operational_context": "Una sobreimpresión incorrecta puede hacer desaparecer elementos o cambiar apariencia.",
        "possible_impact": "Elementos perdidos, textos invisibles, cambio de color o error en blanco.",
        "fix_type": "assisted",
        "current_limitation": "Detección parcial; no siempre identifica sobreimpresión por objeto.",
        "future_evolution": "Comparación visual, mapa por objeto y fix asistido para casos seguros.",
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
        "criteria": "Evalúa cantidad de separaciones imprimibles contra umbrales del perfil.",
        "operational_context": "Más separaciones aumentan complejidad, costo, setup y riesgo operativo.",
        "possible_impact": "Trabajo difícil de producir, mayor tiempo de preparación o incompatibilidad con prensa.",
        "fix_type": "assisted",
        "current_limitation": "No decide qué tinta eliminar ni conoce restricciones reales de cada prensa.",
        "future_evolution": "Sugerir candidatos de racionalización o conversión según cliente, prensa y perfil.",
    },
    "PDF_STRUCTURE_RISK": {
        "criteria": "Evalúa páginas vacías, tamaño de archivo, objetos, imágenes y complejidad estructural.",
        "operational_context": "PDFs vacíos, pesados o complejos pueden fallar en RIP, trapping, imposición o edición.",
        "possible_impact": "Error de procesamiento, lentitud, archivo corrupto o necesidad de reconstrucción.",
        "fix_type": "manual",
        "current_limitation": "No repara estructura PDF automáticamente.",
        "future_evolution": "Limpieza estructural asistida y validación antes/después.",
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
