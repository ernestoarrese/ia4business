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


def _get_severity(top_risk):
    return top_risk.get("business_severity") or top_risk.get("severity")


def _build_rgb_insight(top_risk, related):
    count = top_risk.get("occurrence_count") or len(related) or 1
    areas = [f.get("object_area_percent") for f in related if f.get("object_area_percent") is not None]
    max_area = max(areas) if areas else None

    if max_area is not None:
        brief = f"Hay {count} objetos RGB imprimibles y el principal ocupa cerca del {_fmt(max_area,1)}% del área. Esto puede generar variación de color al convertir a CMYK. Conviene convertirlos con el perfil correcto antes de liberar."
        found = f"Se detectaron {count} objetos RGB imprimibles; el principal ocupa cerca del {_fmt(max_area,1)}% del área evaluada."
    else:
        brief = f"Hay {count} objetos RGB imprimibles. Esto puede generar variación de color al convertir a CMYK. Conviene convertirlos con el perfil correcto antes de liberar."
        found = f"Se detectaron {count} objetos RGB imprimibles."

    return {
        "brief_comment": brief,
        "what_found": found,
        "why_it_matters": "Los elementos RGB están pensados para pantalla y normalmente deben convertirse a CMYK o a una tinta validada antes de impresión.",
        "possible_impact": "La conversión no controlada puede provocar diferencias entre el color aprobado y el resultado impreso.",
        "recommended_action": "Convertir los elementos RGB usando el perfil de color definido para el trabajo antes de liberar.",
        "urgency": _severity_to_urgency(_get_severity(top_risk)),
        "evidence": {"occurrence_count": count, "max_object_area_percent": max_area, "page": top_risk.get("page"), "rule_applied": "RGB_OBJECT", "confidence": "Alta"}
    }


def _build_lowres_insight(top_risk, related):
    selected = related[0] if related else {}
    dpi = selected.get("effective_dpi") or top_risk.get("effective_dpi")
    area = selected.get("object_area_percent") or top_risk.get("object_area_percent")
    role = selected.get("image_role") or top_risk.get("image_role") or "unknown"
    minimum, recommended = 250, 300

    if dpi is not None and area is not None:
        brief = f"La imagen tiene {_fmt(dpi)} dpi efectivos; el mínimo sugerido es {minimum} dpi y lo ideal suele estar cerca de {recommended} dpi. Además ocupa cerca del {_fmt(area,1)}% del área, por lo que el riesgo visual es relevante. Conviene reemplazarla por una imagen de mayor resolución."
        found = f"Se detectó una imagen con resolución efectiva de {_fmt(dpi)} dpi y área aproximada de {_fmt(area,1)}%."
    elif dpi is not None:
        brief = f"La imagen tiene {_fmt(dpi)} dpi efectivos; el mínimo sugerido es {minimum} dpi y lo ideal suele estar cerca de {recommended} dpi. Puede perder nitidez o verse pixelada. Conviene reemplazarla por una imagen de mayor resolución."
        found = f"Se detectó una imagen con resolución efectiva de {_fmt(dpi)} dpi."
    else:
        brief = "Hay una imagen con resolución efectiva baja. Puede perder nitidez o verse pixelada si está en una zona visible. Conviene revisar el tamaño final de uso o solicitar una imagen mejor."
        found = "Se detectó una imagen con resolución efectiva baja."

    return {
        "brief_comment": brief,
        "what_found": found,
        "why_it_matters": "Una imagen puede verse bien en pantalla, pero perder calidad cuando se amplía dentro del diseño o se imprime.",
        "possible_impact": "Puede verse pixelada, borrosa o con pérdida de detalle en impresión.",
        "recommended_action": "Solicitar una imagen de mayor resolución o reducir el tamaño de uso si el diseño lo permite.",
        "urgency": _severity_to_urgency(_get_severity(top_risk)),
        "evidence": {"effective_dpi": dpi, "minimum_suggested_dpi": minimum, "recommended_dpi": recommended, "object_area_percent": area, "image_role": role, "page": top_risk.get("page"), "rule_applied": "LOW_IMAGE_RESOLUTION", "confidence": "Alta"}
    }


def _build_tac_insight(top_risk, related):
    selected = related[0] if related else {}
    tac = selected.get("detected_tac") or selected.get("tac") or selected.get("max_tac") or top_risk.get("detected_tac")
    limit = selected.get("tac_limit") or selected.get("limit") or top_risk.get("tac_limit") or 280

    try:
        excess = float(tac) - float(limit) if tac is not None else None
    except Exception:
        excess = None

    if tac is not None and excess is not None:
        brief = f"El TAC detectado es {_fmt(tac)}% frente a un límite de {_fmt(limit)}%. El exceso es de {_fmt(excess)} puntos, lo que puede generar secado lento, repinte o inestabilidad en prensa. Conviene revisar separación, perfil de conversión y negro enriquecido."
        found = f"Se detectó un TAC máximo de {_fmt(tac)}% frente a un límite de {_fmt(limit)}%."
    else:
        brief = "La carga total de tinta está por encima del límite esperado. Esto puede generar secado lento, repinte o inestabilidad en prensa. Conviene revisar separación, perfil de conversión y negro enriquecido."
        found = "Se detectó carga total de tinta por encima del límite del proceso."

    return {
        "brief_comment": brief,
        "what_found": found,
        "why_it_matters": "La cobertura total de tinta debe mantenerse dentro del límite definido por proceso, tinta y sustrato.",
        "possible_impact": "Un TAC alto puede generar secado lento, repinte, bloqueo, ganancia o inestabilidad durante impresión.",
        "recommended_action": "Reducir la cobertura total revisando separación, perfil de conversión, curvas o negro enriquecido.",
        "urgency": _severity_to_urgency(_get_severity(top_risk)),
        "evidence": {"detected_tac": tac, "tac_limit": limit, "excess": excess, "page": top_risk.get("page"), "rule_applied": "HIGH_TAC_RISK", "confidence": "Alta"}
    }


def _build_font_insight(top_risk, related):
    count = top_risk.get("occurrence_count") or len(related) or 1
    font_names = [f.get("font_name") or f.get("value") for f in related if f.get("font_name") or f.get("value")]
    sample = ", ".join(str(x) for x in font_names[:2])

    if count == 1:
        font_label = "1 fuente no embebida"
        found_prefix = "Se detectó"
    else:
        font_label = f"{count} fuentes no embebidas"
        found_prefix = "Se detectaron"

    if sample:
        found = f"{found_prefix} {font_label}, incluyendo {sample}."
        brief = f"Hay {font_label}, incluyendo {sample}. Esto puede hacer que el texto cambie o se reemplace al procesar el PDF. Conviene incrustar las fuentes o convertir el texto a curvas antes de liberar."
    else:
        found = f"{found_prefix} {font_label}."
        brief = f"Hay {font_label}. Esto puede hacer que el texto cambie o se reemplace al procesar el PDF. Conviene incrustar las fuentes o convertir el texto a curvas antes de liberar."

    return {
        "brief_comment": brief,
        "what_found": found,
        "why_it_matters": "Si una fuente no está embebida, el sistema que procese el archivo puede sustituirla por otra.",
        "possible_impact": "Puede cambiar el texto, la composición, los legales, ingredientes, códigos o elementos aprobados del diseño.",
        "recommended_action": "Incrustar las fuentes en el PDF o convertir el texto a curvas antes de enviar a producción.",
        "urgency": _severity_to_urgency(_get_severity(top_risk)),
        "evidence": {"occurrence_count": count, "sample_fonts": font_names[:3], "page": top_risk.get("page"), "rule_applied": "FONT_NOT_EMBEDDED", "confidence": "Alta"}
    }



def _build_spot_insight(top_risk, related):
    selected = related[0] if related else {}
    spot_count = selected.get("printable_spot_count") or selected.get("spot_count")
    categories = selected.get("spot_category") or []
    if isinstance(categories, str):
        categories = [categories]
    categories = [str(c).upper() for c in categories]
    names = selected.get("spot_names") or []
    sample = ", ".join(str(x) for x in names[:3])

    if spot_count == 0:
        found = "No se detectaron tintas spot imprimibles."
        brief = "No se identificaron tintas spot imprimibles en el archivo. No se requieren acciones asociadas a separaciones spot."
    elif spot_count and spot_count > 12:
        found = f"Se detectaron {spot_count} tintas spot imprimibles."
        brief = f"Se detectaron {spot_count} tintas spot imprimibles; para este perfil, más de 12 ya se considera crítico. Esto aumenta formulación, setup, secuencia y riesgo operativo. Conviene revisar si todas son necesarias o si algunas pueden racionalizarse."
    elif "SUSPICIOUS" in categories:
        found = f"Se detectaron tintas spot con nombres genéricos o sospechosos{f', incluyendo {sample}' if sample else ''}."
        brief = f"Hay tintas spot con nombres poco claros{f', incluyendo {sample}' if sample else ''}. Esto puede generar confusión en separación, formulación o asignación de tintas. Conviene renombrarlas correctamente antes de liberar."
    elif "DUPLICATE" in categories:
        found = f"Se detectaron posibles tintas spot duplicadas{f', incluyendo {sample}' if sample else ''}."
        brief = "Hay posibles tintas spot duplicadas o variantes del mismo color. Esto puede crear separaciones innecesarias o confusión en formulación. Conviene unificar nombres y confirmar cuál separación debe imprimirse."
    elif "WHITE" in categories:
        found = f"Se detectó una observación asociada a tinta blanca{f': {sample}' if sample else ''}."
        brief = "Hay una observación asociada a separaciones de blanco. Conviene validar cuál blanco debe imprimirse y si las demás separaciones son técnicas, duplicadas o intencionales."
    elif "TECHNICAL" in categories:
        found = f"Se detectaron separaciones técnicas{f', incluyendo {sample}' if sample else ''}."
        brief = "Hay separaciones spot que parecen técnicas. No necesariamente son un problema, pero deben estar bien clasificadas para que no se traten como tintas reales de impresión."
    elif spot_count is not None:
        found = f"Se detectaron {spot_count} tintas spot imprimibles."
        brief = f"Se detectaron {spot_count} tintas spot imprimibles. La cantidad no parece excesiva, pero conviene validar si corresponden a tintas reales, separaciones técnicas o nombres que podrían generar confusión."
    else:
        found = "Se detectó una observación en tintas spot."
        brief = "Hay una observación en tintas spot. Puede afectar separación, formulación o control en prensa. Conviene revisar nombres, duplicados y necesidad real de cada separación."

    return {
        "brief_comment": brief,
        "what_found": found,
        "why_it_matters": "Las tintas spot definen separaciones adicionales que deben formularse, asignarse y controlarse correctamente en preprensa y prensa.",
        "possible_impact": "Nombres incorrectos, duplicados o exceso de spots pueden generar errores de separación, tintas innecesarias, mayor setup o riesgo operativo.",
        "recommended_action": selected.get("action") or selected.get("recommendation") or "Validar nombres, duplicados y necesidad real de cada tinta spot.",
        "urgency": _severity_to_urgency(_get_severity(top_risk)),
        "evidence": {"printable_spot_count": spot_count, "spot_category": categories, "sample_spot_names": names[:5], "page": top_risk.get("page"), "rule_applied": "SPOT_COLOR_RISK", "confidence": "Media"}
    }


def _build_separation_insight(top_risk, related):
    selected = related[0] if related else {}
    count = selected.get("printable_separation_count") or top_risk.get("printable_separation_count")
    white = selected.get("white_detected")
    varnish = selected.get("varnish_detected")
    technical = selected.get("technical_separations_detected")

    if count is not None and count > 12:
        brief = f"El archivo tiene {count} separaciones imprimibles; para este perfil, más de 12 ya se considera crítico. En flexo esto puede superar la capacidad práctica de prensa o volver muy complejo el setup. Conviene revisar estaciones disponibles, secuencia y necesidad real de cada separación."
        found = f"Se detectaron {count} separaciones imprimibles."
    elif count is not None and count >= 11:
        brief = f"El archivo tiene {count} separaciones imprimibles, cerca del umbral crítico del perfil. Puede ser viable, pero requiere revisar capacidad de prensa, secuencia y necesidad de cada spot antes de liberar."
        found = f"Se detectaron {count} separaciones imprimibles."
    elif count is not None and count >= 9:
        brief = f"El archivo tiene {count} separaciones imprimibles. No parece crítico, pero ya implica una preparación más exigente en flexo. Conviene validar secuencia, blancos, barnices y spots especiales."
        found = f"Se detectaron {count} separaciones imprimibles."
    elif count is not None:
        brief = f"El archivo tiene {count} separaciones imprimibles, dentro del rango normal para packaging flexible. No requiere acción especial más allá de la validación normal del flujo."
        found = f"Se detectaron {count} separaciones imprimibles."
    else:
        brief = "El archivo presenta complejidad de separaciones. Conviene revisar estaciones disponibles, secuencia y necesidad real de cada separación."
        found = "Se detectó complejidad asociada a la cantidad de separaciones."

    return {
        "brief_comment": brief,
        "what_found": found,
        "why_it_matters": "Cada separación imprimible implica una tinta, estación o control adicional dentro del flujo de impresión.",
        "possible_impact": "Una cantidad alta de separaciones puede aumentar setup, complejidad, riesgo de error, tiempo de preparación y dificultad de control.",
        "recommended_action": selected.get("action") or selected.get("recommendation") or "Validar capacidad de prensa, secuencia y necesidad real de cada separación.",
        "urgency": _severity_to_urgency(_get_severity(top_risk)),
        "evidence": {"printable_separation_count": count, "white_detected": white, "varnish_detected": varnish, "technical_separations_detected": technical, "page": top_risk.get("page"), "rule_applied": "SEPARATION_COUNT_RISK", "confidence": "Alta"}
    }


def build_expert_insight(top_risk, report_data):
    check = top_risk.get("check")
    related = _find_related_findings(report_data, check)

    if check == "RGB_OBJECT":
        return _build_rgb_insight(top_risk, related)
    if check == "LOW_IMAGE_RESOLUTION":
        return _build_lowres_insight(top_risk, related)
    if check == "HIGH_TAC_RISK":
        return _build_tac_insight(top_risk, related)
    if check == "FONT_NOT_EMBEDDED":
        return _build_font_insight(top_risk, related)
    if check == "SPOT_COLOR_RISK":
        return _build_spot_insight(top_risk, related)
    if check == "SEPARATION_COUNT_RISK":
        return _build_separation_insight(top_risk, related)

    return {
        "brief_comment": top_risk.get("risk_reason") or top_risk.get("detail") or "Se detectó un hallazgo que requiere revisión.",
        "what_found": top_risk.get("detail") or "Se detectó un hallazgo relevante.",
        "why_it_matters": "Puede afectar el flujo de preprensa o producción.",
        "possible_impact": top_risk.get("risk_reason") or "Puede generar riesgo operativo.",
        "recommended_action": top_risk.get("action") or top_risk.get("recommendation") or "Revisar antes de liberar.",
        "urgency": _severity_to_urgency(_get_severity(top_risk)),
        "evidence": {"page": top_risk.get("page"), "rule_applied": top_risk.get("check"), "confidence": "Media"}
    }


def enrich_report_with_expert_insights(report_data):
    summary = report_data.get("readiness_summary", {})
    top_risks = summary.get("top_risks", [])

    if not isinstance(top_risks, list):
        return report_data

    for risk in top_risks:
        if isinstance(risk, dict):
            insight = build_expert_insight(risk, report_data)
            risk["expert_insight"] = insight
            risk["expert_comment"] = insight.get("brief_comment")

    return report_data
