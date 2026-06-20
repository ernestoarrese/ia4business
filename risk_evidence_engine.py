def _find_related_findings(report_data, check):
    return [
        f for f in report_data.get("business_assessment", {}).get("priority_findings", [])
        if f.get("check") == check
    ]


def _get_decision_impact(decision, severity):
    severity = str(severity or "").upper()
    decision = str(decision or "").upper()

    if decision == "NO_GO" and severity in ["CRITICAL", "HIGH"]:
        return "Contribuye directamente al NO_GO."

    if decision == "HOLD" and severity in ["CRITICAL", "HIGH", "WARNING", "MEDIUM"]:
        return "Contribuye a mantener el archivo en revisión antes de avanzar."

    if decision == "GO_WITH_NOTES":
        return "No bloquea el avance, pero debe quedar registrado como observación."

    if decision == "GO":
        return "No afecta la liberación del archivo."

    return "Contribuye a la evaluación general del archivo."


def _build_rgb_evidence(top_risk, related):
    count = top_risk.get("occurrence_count") or len(related) or 1
    areas = [f.get("object_area_percent") for f in related if f.get("object_area_percent") is not None]
    max_area = max(areas) if areas else None

    detected = f"{count} objeto(s) RGB imprimibles"
    if max_area is not None:
        detected += f"; mayor área aproximada {round(max_area, 1)}%"

    return {
        "detected_value": detected,
        "threshold": "RGB no recomendado en arte final imprimible",
        "page": top_risk.get("page"),
        "confidence": "Alta"
    }


def _build_lowres_evidence(top_risk, related):
    selected = related[0] if related else {}

    dpi = selected.get("effective_dpi") or top_risk.get("effective_dpi")
    area = selected.get("object_area_percent") or top_risk.get("object_area_percent")

    detected = "Imagen con resolución efectiva baja"
    if dpi is not None:
        detected = f"{round(float(dpi), 1)} dpi efectivos"
    if area is not None:
        detected += f"; área aproximada {round(float(area), 1)}%"

    return {
        "detected_value": detected,
        "threshold": "Mínimo sugerido 250 dpi / recomendado cercano a 300 dpi",
        "page": top_risk.get("page"),
        "confidence": "Alta"
    }


def _build_tac_evidence(top_risk, related):
    selected = related[0] if related else {}

    tac = (
        selected.get("detected_tac")
        or selected.get("tac")
        or selected.get("max_tac")
        or top_risk.get("detected_tac")
    )

    limit = (
        selected.get("tac_limit")
        or selected.get("limit")
        or top_risk.get("tac_limit")
        or 280
    )

    detected = "TAC por encima del límite"
    if tac is not None:
        detected = f"TAC detectado {round(float(tac), 1)}%"

    return {
        "detected_value": detected,
        "threshold": f"Límite configurado {limit}%",
        "page": top_risk.get("page"),
        "confidence": "Alta"
    }


def _build_font_evidence(top_risk, related):
    count = top_risk.get("occurrence_count") or len(related) or 1
    fonts = [
        f.get("font_name") or f.get("value")
        for f in related
        if f.get("font_name") or f.get("value")
    ]

    detected = f"{count} fuente(s) no embebida(s)"
    if fonts:
        detected += f"; ejemplo: {', '.join(str(x) for x in fonts[:2])}"

    return {
        "detected_value": detected,
        "threshold": "Todas las fuentes deben estar embebidas o convertidas a curvas",
        "page": top_risk.get("page"),
        "confidence": "Alta"
    }


def _build_spot_evidence(top_risk, related):
    selected = related[0] if related else {}

    spot_count = selected.get("printable_spot_count") or selected.get("spot_count")
    categories = selected.get("spot_category") or []
    if isinstance(categories, str):
        categories = [categories]

    names = selected.get("spot_names") or []

    detected = "Observación en tintas spot"
    if spot_count is not None:
        detected = f"{spot_count} tinta(s) spot imprimible(s)"
    if names:
        detected += f"; ejemplo: {', '.join(str(x) for x in names[:3])}"

    return {
        "detected_value": detected,
        "threshold": "Más de 12 spots imprimibles se considera crítico en el perfil MVP",
        "page": top_risk.get("page"),
        "confidence": "Media",
        "categories": categories
    }


def _build_separation_evidence(top_risk, related):
    selected = related[0] if related else {}

    count = selected.get("printable_separation_count") or top_risk.get("printable_separation_count")

    detected = "Complejidad de separaciones"
    if count is not None:
        detected = f"{count} separación(es) imprimible(s)"

    return {
        "detected_value": detected,
        "threshold": "≤8 normal | 9–10 elevado | 11–12 alto | >12 crítico",
        "page": top_risk.get("page"),
        "confidence": "Alta"
    }


def build_risk_evidence(top_risk, report_data):
    check = top_risk.get("check")
    related = _find_related_findings(report_data, check)

    if check == "RGB_OBJECT":
        return _build_rgb_evidence(top_risk, related)

    if check == "LOW_IMAGE_RESOLUTION":
        return _build_lowres_evidence(top_risk, related)

    if check == "HIGH_TAC_RISK":
        return _build_tac_evidence(top_risk, related)

    if check == "FONT_NOT_EMBEDDED":
        return _build_font_evidence(top_risk, related)

    if check == "SPOT_COLOR_RISK":
        return _build_spot_evidence(top_risk, related)

    if check == "SEPARATION_COUNT_RISK":
        return _build_separation_evidence(top_risk, related)

    return {
        "detected_value": top_risk.get("value") or top_risk.get("detail"),
        "threshold": "Regla definida por Gate0",
        "page": top_risk.get("page"),
        "confidence": "Media"
    }


def enrich_report_with_risk_evidence(report_data):
    summary = report_data.get("readiness_summary", {})
    top_risks = summary.get("top_risks", [])

    decision = summary.get("decision") or report_data.get("readiness_assessment", {}).get("readiness_decision")

    if not isinstance(top_risks, list):
        return report_data

    for risk in top_risks:
        if not isinstance(risk, dict):
            continue

        severity = risk.get("business_severity") or risk.get("severity")
        risk["risk_evidence"] = build_risk_evidence(risk, report_data)
        risk["decision_impact"] = _get_decision_impact(decision, severity)

    return report_data
