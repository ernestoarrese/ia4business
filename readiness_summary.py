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
    Ordena hallazgos por prioridad de negocio, evitando repetir el mismo check.

    Regla:
    - Deduplica por check.
    - Conserva el mejor hallazgo por prioridad/peso/severidad.
    - Agrega occurrence_count.
    - Prioriza CRITICAL/WARNING.
    - INFO solo aparece si no existen riesgos CRITICAL/WARNING suficientes.
    """
    if not findings:
        return []

    grouped = {}

    severity_rank = {
        "PASS": 0,
        "INFO": 1,
        "LOW": 1,
        "WARNING": 2,
        "MEDIUM": 2,
        "CRITICAL": 3,
        "HIGH": 3,
    }

    for finding in findings:
        check = finding.get("check", "UNKNOWN")

        business_severity = (
            finding.get("business_severity")
            or finding.get("severity")
            or "INFO"
        )

        priority = finding.get("priority", 99)
        score_weight = finding.get("score_weight", 0)
        severity_score = severity_rank.get(str(business_severity).upper(), 1)

        candidate_sort_key = (
            priority,
            -score_weight,
            -severity_score
        )

        if check not in grouped:
            grouped[check] = {
                "best": finding,
                "occurrence_count": 1,
                "max_score_weight": score_weight,
                "max_severity_score": severity_score,
            }
            continue

        grouped[check]["occurrence_count"] += 1
        grouped[check]["max_score_weight"] = max(
            grouped[check]["max_score_weight"],
            score_weight
        )
        grouped[check]["max_severity_score"] = max(
            grouped[check]["max_severity_score"],
            severity_score
        )

        current = grouped[check]["best"]
        current_business_severity = (
            current.get("business_severity")
            or current.get("severity")
            or "INFO"
        )

        current_sort_key = (
            current.get("priority", 99),
            -current.get("score_weight", 0),
            -severity_rank.get(str(current_business_severity).upper(), 1)
        )

        if candidate_sort_key < current_sort_key:
            grouped[check]["best"] = finding

    deduped = []

    for check, data in grouped.items():
        item = dict(data["best"])
        item["occurrence_count"] = data["occurrence_count"]
        item["max_score_weight"] = data["max_score_weight"]
        item["max_severity_score"] = data["max_severity_score"]
        deduped.append(item)

    deduped = sorted(
        deduped,
        key=lambda f: (
            -severity_rank.get(str(f.get("business_severity") or f.get("severity") or "INFO").upper(), 1),
            f.get("priority", 99),
            -f.get("score_weight", 0),
            -f.get("occurrence_count", 1)
        )
    )

    # Primero riesgos reales: WARNING / CRITICAL
    actionable = [
        f for f in deduped
        if severity_rank.get(str(f.get("business_severity") or f.get("severity") or "INFO").upper(), 1) >= 2
    ]

    # Luego observaciones INFO solo si faltan slots
    informational = [
        f for f in deduped
        if severity_rank.get(str(f.get("business_severity") or f.get("severity") or "INFO").upper(), 1) == 1
    ]

    return actionable[:limit]



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
        "BARCODE_RISK": "Puede generar problemas de lectura o rechazo de calidad.",
        "FONT_NOT_EMBEDDED": "Puede modificar texto o apariencia aprobada.",
        "SMALL_TEXT_RISK": "Puede generar problemas de legibilidad.",
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

