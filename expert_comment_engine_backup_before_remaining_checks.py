def _fmt(value, decimals=0):
    try:
        value = float(value)
        if decimals == 0:
            return str(int(round(value)))
        return f"{value:.{decimals}f}"
    except Exception:
        return str(value) if value is not None else "-"


def _severity_to_urgency(severity):
    severity = str(severity or "").upper()

    if severity in ["CRITICAL", "HIGH"]:
        return "Alta"
    if severity in ["WARNING", "MEDIUM"]:
        return "Media"
    if severity in ["INFO", "LOW"]:
        return "Baja"

    return "Media"


def _find_related_findings(report_data, check):
    return [
        f for f in report_data.get("business_assessment", {}).get("priority_findings", [])
        if f.get("check") == check
    ]


def _build_rgb_insight(top_risk, related_findings):
    count = top_risk.get("occurrence_count") or len(related_findings) or 1

    area_values = [
        f.get("object_area_percent")
        for f in related_findings
        if f.get("object_area_percent") is not None
    ]

    max_area = max(area_values) if area_values else None

    if max_area is not None:
        what_found = f"Se detectaron {count} objetos RGB imprimibles; el principal ocupa cerca del {_fmt(max_area, 1)}% del área evaluada."
        brief = (
            f"Hay {count} objetos RGB imprimibles y el principal ocupa cerca del {_fmt(max_area, 1)}% del área. "
            "Esto puede generar variación de color al convertir a CMYK. Conviene convertirlos con el perfil correcto antes de liberar."
        )
    else:
        what_found = f"Se detectaron {count} objetos RGB imprimibles."
        brief = (
            f"Hay {count} objetos RGB imprimibles. Esto puede generar variación de color al convertir a CMYK. "
            "Conviene convertirlos con el perfil correcto antes de liberar."
        )

    return {
        "brief_comment": brief,
        "what_found": what_found,
        "why_it_matters": "Los objetos RGB requieren conversión a CMYK o a una tinta validada para impresión.",
        "possible_impact": "La conversión no controlada puede provocar diferencias entre el color aprobado y el resultado impreso.",
        "recommended_action": "Convertir los elementos RGB usando el perfil de color definido para el trabajo antes de liberar.",
        "urgency": _severity_to_urgency(top_risk.get("business_severity") or top_risk.get("severity")),
        "evidence": {
            "occurrence_count": count,
            "max_object_area_percent": max_area,
            "page": top_risk.get("page"),
            "rule_applied": "RGB_OBJECT",
            "confidence": "Alta"
        }
    }


def _build_lowres_insight(top_risk, related_findings):
    selected = related_findings[0] if related_findings else {}

    dpi = selected.get("effective_dpi") or top_risk.get("effective_dpi")
    area = selected.get("object_area_percent") or top_risk.get("object_area_percent")
    image_role = selected.get("image_role") or top_risk.get("image_role") or "unknown"

    minimum = 250
    recommended = 300

    if dpi is not None and area is not None:
        what_found = f"Se detectó una imagen con resolución efectiva de {_fmt(dpi)} dpi y área aproximada de {_fmt(area, 1)}%."
        brief = (
            f"La imagen tiene {_fmt(dpi)} dpi efectivos; el mínimo sugerido es {minimum} dpi y lo ideal suele estar cerca de {recommended} dpi. "
            f"Además ocupa cerca del {_fmt(area, 1)}% del área, por lo que el riesgo visual es relevante. "
            "Conviene reemplazarla por una imagen de mayor resolución."
        )
    elif dpi is not None:
        what_found = f"Se detectó una imagen con resolución efectiva de {_fmt(dpi)} dpi."
        brief = (
            f"La imagen tiene {_fmt(dpi)} dpi efectivos; el mínimo sugerido es {minimum} dpi y lo ideal suele estar cerca de {recommended} dpi. "
            "Puede perder nitidez o verse pixelada. Conviene reemplazarla por una imagen de mayor resolución."
        )
    else:
        what_found = "Se detectó una imagen con resolución efectiva baja."
        brief = (
            "Hay una imagen con resolución efectiva baja. Puede perder nitidez o verse pixelada si está en una zona visible. "
            "Conviene revisar el tamaño final de uso o solicitar una imagen mejor."
        )

    return {
        "brief_comment": brief,
        "what_found": what_found,
        "why_it_matters": "La resolución efectiva depende del tamaño real al que la imagen se usa dentro del arte.",
        "possible_impact": "Una imagen con baja resolución puede verse pixelada, borrosa o con pérdida de detalle en impresión.",
        "recommended_action": "Solicitar una imagen de mayor resolución o reducir el tamaño de uso si el diseño lo permite.",
        "urgency": _severity_to_urgency(top_risk.get("business_severity") or top_risk.get("severity")),
        "evidence": {
            "effective_dpi": dpi,
            "minimum_suggested_dpi": minimum,
            "recommended_dpi": recommended,
            "object_area_percent": area,
            "image_role": image_role,
            "page": top_risk.get("page"),
            "rule_applied": "LOW_IMAGE_RESOLUTION",
            "confidence": "Alta"
        }
    }


def _build_tac_insight(top_risk, related_findings):
    selected = related_findings[0] if related_findings else {}

    tac = selected.get("detected_tac") or selected.get("tac") or selected.get("max_tac") or top_risk.get("detected_tac")
    limit = selected.get("tac_limit") or selected.get("limit") or top_risk.get("tac_limit") or 280

    try:
        excess = float(tac) - float(limit) if tac is not None else None
    except Exception:
        excess = None

    if tac is not None and excess is not None:
        what_found = f"Se detectó un TAC máximo de {_fmt(tac)}% frente a un límite de {_fmt(limit)}%."
        brief = (
            f"El TAC detectado es {_fmt(tac)}% frente a un límite de {_fmt(limit)}%. "
            f"El exceso es de {_fmt(excess)} puntos, lo que puede generar secado lento, repinte o inestabilidad en prensa. "
            "Conviene revisar separación, perfil de conversión y negro enriquecido."
        )
    else:
        what_found = "Se detectó carga total de tinta por encima del límite del proceso."
        brief = (
            "La carga total de tinta está por encima del límite esperado. "
            "Esto puede generar secado lento, repinte o inestabilidad en prensa. "
            "Conviene revisar separación, perfil de conversión y negro enriquecido."
        )

    return {
        "brief_comment": brief,
        "what_found": what_found,
        "why_it_matters": "La cobertura total de tinta debe mantenerse dentro del límite definido por el proceso, tinta y sustrato.",
        "possible_impact": "Un TAC alto puede generar secado lento, repinte, bloqueo, ganancia o inestabilidad durante impresión.",
        "recommended_action": "Reducir la cobertura total revisando separación, perfil de conversión, curvas o negro enriquecido.",
        "urgency": _severity_to_urgency(top_risk.get("business_severity") or top_risk.get("severity")),
        "evidence": {
            "detected_tac": tac,
            "tac_limit": limit,
            "excess": excess,
            "page": top_risk.get("page"),
            "rule_applied": "HIGH_TAC_RISK",
            "confidence": "Alta"
        }
    }


def build_expert_insight(top_risk, report_data):
    check = top_risk.get("check")
    related_findings = _find_related_findings(report_data, check)

    if check == "RGB_OBJECT":
        return _build_rgb_insight(top_risk, related_findings)

    if check == "LOW_IMAGE_RESOLUTION":
        return _build_lowres_insight(top_risk, related_findings)

    if check == "HIGH_TAC_RISK":
        return _build_tac_insight(top_risk, related_findings)

    return {
        "brief_comment": (
            top_risk.get("risk_reason")
            or top_risk.get("detail")
            or "Se detectó un hallazgo que requiere revisión."
        ),
        "what_found": top_risk.get("detail") or "Se detectó un hallazgo relevante.",
        "why_it_matters": "Puede afectar el flujo de preprensa o producción.",
        "possible_impact": top_risk.get("risk_reason") or "Puede generar riesgo operativo.",
        "recommended_action": top_risk.get("action") or top_risk.get("recommendation") or "Revisar antes de liberar.",
        "urgency": _severity_to_urgency(top_risk.get("business_severity") or top_risk.get("severity")),
        "evidence": {
            "page": top_risk.get("page"),
            "rule_applied": top_risk.get("check"),
            "confidence": "Media"
        }
    }


def enrich_report_with_expert_insights(report_data):
    summary = report_data.get("readiness_summary", {})
    top_risks = summary.get("top_risks", [])

    if not isinstance(top_risks, list):
        return report_data

    for risk in top_risks:
        if not isinstance(risk, dict):
            continue

        insight = build_expert_insight(risk, report_data)
        risk["expert_insight"] = insight
        risk["expert_comment"] = insight.get("brief_comment")

    return report_data
