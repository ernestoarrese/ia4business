"""
readiness_summary.py

Genera resumen ejecutivo del resultado Gate0.

Responsabilidad:
- Convertir readiness assessment + findings en mensaje entendible.
- Crear headline.
- Definir tono.
- Identificar top risks.
- Sugerir siguiente acción.
"""


def sort_top_risks(findings, limit=3):
    """
    Ordena hallazgos por prioridad y peso.
    """
    if not findings:
        return []

    return sorted(
        findings,
        key=lambda f: (
            f.get("priority", 99),
            -f.get("score_weight", 0)
        )
    )[:limit]


def get_main_reason(top_risks):
    if not top_risks:
        return "No se detectaron riesgos relevantes."

    top = top_risks[0]

    return (
        top.get("risk_reason")
        or top.get("detail")
        or "Se detectó un riesgo relevante que requiere revisión."
    )


def get_simple_risk(top_risks):
    if not top_risks:
        return "El archivo no presenta alertas relevantes para el flujo inicial."

    top = top_risks[0]
    check = top.get("check", "UNKNOWN")

    simple_map = {
        "RGB_OBJECT": "Puede generar variación de color.",
        "LOW_IMAGE_RESOLUTION": "Puede generar pérdida visible de calidad.",
        "FONT_NOT_EMBEDDED": "Puede modificar texto o apariencia aprobada.",
        "HIGH_TAC_RISK": "Puede generar problemas de impresión, secado o estabilidad.",
        "OVERPRINT_RISK": "Puede alterar el resultado visual por sobreimpresión.",
        "WHITE_INK_RISK": "Puede afectar la gestión de tinta blanca.",
        "SPOT_COLOR_RISK": "Puede generar confusión o complejidad en separaciones spot.",
        "SEPARATION_COUNT_RISK": "Puede aumentar la complejidad operativa de impresión.",
        "PDF_STRUCTURE_RISK": "Puede afectar procesamiento, RIP o preprensa."
    }

    return simple_map.get(
        check,
        "Puede generar riesgo operativo durante preprensa o producción."
    )


def get_next_action(decision, top_risks):
    if decision == "GO":
        return "Continuar con el flujo normal."

    if decision == "GO_WITH_NOTES":
        return "Continuar, dejando registradas las observaciones detectadas."

    if decision == "HOLD":
        if top_risks:
            return top_risks[0].get(
                "action",
                "Revisar el riesgo principal antes de continuar."
            )
        return "Revisar el archivo antes de continuar."

    if decision == "NO_GO":
        if top_risks:
            return top_risks[0].get(
                "action",
                "Corregir el archivo antes de avanzar."
            )
        return "Corregir el archivo antes de avanzar."

    return "Revisar resultado del análisis."


def get_tone(decision):
    if decision == "GO":
        return "positive"

    if decision == "GO_WITH_NOTES":
        return "caution"

    if decision == "HOLD":
        return "review"

    if decision == "NO_GO":
        return "critical"

    return "neutral"


def build_headline(status, decision, score):
    if decision == "GO":
        return f"Archivo listo para continuar. Score {score}/100."

    if decision == "GO_WITH_NOTES":
        return f"Archivo puede continuar con observaciones. Score {score}/100."

    if decision == "HOLD":
        return f"Archivo requiere revisión antes de avanzar. Score {score}/100."

    if decision == "NO_GO":
        return f"Archivo no debe avanzar sin corrección. Score {score}/100."

    return f"Resultado de análisis Gate0. Score {score}/100."


def build_user_message(decision, main_reason, next_action):
    return (
        f"{main_reason} "
        f"Siguiente acción recomendada: {next_action}"
    )


def build_readiness_summary(readiness_assessment, findings):
    """
    Construye resumen ejecutivo final.
    """

    score = readiness_assessment.get("readiness_score")
    status = readiness_assessment.get("readiness_status")
    decision = readiness_assessment.get("readiness_decision")

    top_risks = sort_top_risks(findings)

    main_reason = get_main_reason(top_risks)
    simple_risk = get_simple_risk(top_risks)
    next_action = get_next_action(decision, top_risks)
    tone = get_tone(decision)
    headline = build_headline(status, decision, score)
    user_message = build_user_message(decision, main_reason, next_action)

    return {
        "headline": headline,
        "decision": decision,
        "tone": tone,
        "score": score,
        "status": status,
        "main_reason": main_reason,
        "simple_risk": simple_risk,
        "next_action": next_action,
        "user_message": user_message,
        "top_risks": top_risks
    }

