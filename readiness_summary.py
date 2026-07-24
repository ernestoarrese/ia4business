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


def build_occurrence_summary(finding):
    """
    Compact occurrence payload for dashboard navigation.
    Keeps only fields useful to move preview/evidence between occurrences.
    """
    allowed = [
        "check",
        "page",
        "value",
        "detail",
        "sample_text",
        "severity",
        "business_severity",
        "risk_reason",
        "action",
        "recommendation",
        "bbox",
        "font_size_pt",
        "text_height_mm",
        "font_name",
        "effective_dpi",
        "minimum_image_dpi",
        "critical_image_dpi",
        "image_index",
        "object_area_percent",
        "image_role",
        "printable_area_source",
        "printable_area_confidence",
        "is_inside_printable_area",
        "printable_area_overlap_percent",
    ]

    return {
        key: finding.get(key)
        for key in allowed
        if finding.get(key) is not None
    }


def occurrence_key(item):
    return (
        item.get("page"),
        str(item.get("bbox")),
        str(item.get("value")),
    )


def order_occurrences(best_finding, occurrences, limit=50):
    """
    Put the selected best finding first, then the rest without duplicates.
    """
    best = build_occurrence_summary(best_finding)
    best_key = occurrence_key(best)

    ordered = []
    seen = set()

    for item in [best] + list(occurrences or []):
        key = occurrence_key(item)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(item)

        if len(ordered) >= limit:
            break

    return ordered


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
                "occurrences": [build_occurrence_summary(finding)],
                "max_score_weight": score_weight,
                "max_severity_score": severity_score,
            }
            continue

        grouped[check]["occurrence_count"] += 1
        if len(grouped[check].get("occurrences", [])) < 50:
            grouped[check].setdefault("occurrences", []).append(build_occurrence_summary(finding))

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
        item["occurrences"] = order_occurrences(data["best"], data.get("occurrences", []))
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


def classify_fix_type(check):
    autofix_candidates = {
        "RGB_OBJECT",
        "LOW_IMAGE_RESOLUTION",
        "SMALL_TEXT_RISK",
        "BARCODE_RISK",
        "SPOT_COLOR_RISK",
        "SEPARATION_COUNT_RISK",
    }

    manual_required = {
        "FONT_NOT_EMBEDDED",
        "PDF_STRUCTURE_RISK",
    }

    if check in manual_required:
        return "manual"

    if check in autofix_candidates:
        return "assisted"

    return "manual"


def build_fix_plan(findings, limit=6):
    """
    Fix Plan v1:
    Ordena acciones recomendadas desde los findings actuales.
    No ejecuta correcciones.
    No promete autofix.
    """
    if not findings:
        return []

    severity_rank = {
        "CRITICAL": 4,
        "HIGH": 4,
        "WARNING": 3,
        "MEDIUM": 3,
        "INFO": 2,
        "LOW": 1,
        "PASS": 0,
    }

    actionable = []

    for finding in findings:
        severity = str(
            finding.get("business_severity")
            or finding.get("severity")
            or "INFO"
        ).upper()

        if severity in {"PASS", "LOW", "INFO"}:
            continue

        check = finding.get("check", "UNKNOWN_CHECK")

        item = {
            "priority": finding.get("priority", 99),
            "check": check,
            "severity": severity,
            "page": finding.get("page"),
            "bbox": finding.get("bbox"),
            "printable_area_source": finding.get("printable_area_source"),
            "printable_area_confidence": finding.get("printable_area_confidence"),
            "is_inside_printable_area": finding.get("is_inside_printable_area"),
            "printable_area_overlap_percent": finding.get("printable_area_overlap_percent"),
            "problem": (
                finding.get("risk_reason")
                or finding.get("detail")
                or "Hallazgo requiere revisión."
            ),
            "recommended_action": (
                finding.get("action")
                or finding.get("recommendation")
                or "Revisar antes de liberar."
            ),
            "fix_type": classify_fix_type(check),
            "status": "pending",
            "source": "finding",
        }

        actionable.append(item)

    actionable = sorted(
        actionable,
        key=lambda x: (
            x.get("priority", 99),
            -severity_rank.get(x.get("severity", "INFO"), 1),
            x.get("check", ""),
        ),
    )

    for idx, item in enumerate(actionable[:limit], start=1):
        item["step"] = idx

    return actionable[:limit]



# ---------------------------------------------------------------------
# Production Readiness v2
# ---------------------------------------------------------------------

def _pr2_severity(finding):
    return str(
        finding.get("business_severity")
        or finding.get("severity")
        or "INFO"
    ).upper()


def _pr2_title(finding):
    check = str(finding.get("check") or "").upper()

    names = {
        "RGB_OBJECT": "Objetos RGB",
        "LOW_IMAGE_RESOLUTION": "Imagen con baja resolución",
        "BARCODE_RISK": "Barcode / QR",
        "SMALL_TEXT_RISK": "Texto pequeño / legibilidad",
        "FONT_NOT_EMBEDDED": "Fuente no embebida",
        "HIGH_TAC_RISK": "TAC alto",
        "OVERPRINT_RISK": "Sobreimpresión",
        "SPOT_COLOR_RISK": "Tintas spot / separaciones",
        "SEPARATION_COUNT_RISK": "Cantidad de separaciones",
        "PDF_STRUCTURE_RISK": "Estructura del PDF",
        "WHITE_INK_RISK": "Blanco",
    }

    return (
        finding.get("title")
        or finding.get("display_name")
        or names.get(check)
        or check
        or "Riesgo técnico"
    )


def _pr2_is_contextual_non_blocking(finding):
    severity = _pr2_severity(finding)
    score_weight = finding.get("score_weight", 0) or 0
    is_blocking = bool(finding.get("is_blocking"))

    if severity == "INFO":
        return True

    if score_weight == 0 and not is_blocking:
        return True

    return False


def _pr2_review_time(minutes_basis):
    if minutes_basis <= 0:
        return "0–2 minutos"
    if minutes_basis <= 2:
        return "3–5 minutos"
    if minutes_basis <= 4:
        return "5–10 minutos"
    return "10–15 minutos"


def _pr2_primary_reason(status, effective_risks, contextual_risks):
    if status == "READY":
        return "No se detectaron riesgos relevantes que impidan la producción."

    if status == "READY_WITH_NOTES":
        return "El archivo tiene observaciones contextuales, pero no se detectan riesgos que deban bloquear la liberación."

    if status == "REVIEW_REQUIRED":
        if len(effective_risks) == 1:
            return "Hay 1 riesgo que requiere revisión antes de liberar."
        return f"Hay {len(effective_risks)} riesgos que requieren revisión antes de liberar."

    if status == "HIGH_RISK":
        return "El archivo presenta riesgos altos que pueden afectar producción o liberación."

    if status == "NO_GO":
        return "El archivo presenta un riesgo crítico o bloqueante. No se recomienda liberar sin corrección."

    return "Gate0 requiere revisión del archivo antes de liberar."


def build_production_readiness_v2(readiness_assessment, priority_findings, operational_profile=None):
    """
    Production Readiness v2.

    Turns technical findings into an executive production decision.

    Goal:
    - Answer whether the file is ready to produce.
    - Explain the main reason.
    - Estimate review effort.
    - List what to review first.

    This does not replace the existing readiness engine yet.
    It adds a product-facing decision layer.
    """
    readiness_assessment = readiness_assessment or {}
    priority_findings = priority_findings or []
    operational_profile = operational_profile or {}

    decision = readiness_assessment.get("readiness_decision") or "-"
    legacy_status = readiness_assessment.get("readiness_status") or "-"
    score = readiness_assessment.get("readiness_score")

    critical_risks = []
    warning_risks = []
    contextual_risks = []

    for finding in priority_findings:
        severity = _pr2_severity(finding)

        if _pr2_is_contextual_non_blocking(finding):
            contextual_risks.append(finding)
            continue

        if severity == "CRITICAL" or finding.get("is_blocking"):
            critical_risks.append(finding)
        elif severity == "WARNING":
            warning_risks.append(finding)

    effective_risks = critical_risks + warning_risks

    if any(f.get("is_blocking") for f in critical_risks) or decision == "NO_GO":
        status = "NO_GO"
        production_decision = "No liberar sin corrección o revisión técnica."
    elif critical_risks:
        status = "HIGH_RISK"
        production_decision = "No liberar sin revisión técnica."
    elif warning_risks:
        status = "REVIEW_REQUIRED"
        production_decision = "Revisar antes de liberar."
    elif contextual_risks:
        status = "READY_WITH_NOTES"
        production_decision = "Liberable con observaciones."
    else:
        status = "READY"
        production_decision = "Liberable."

    primary = effective_risks[0] if effective_risks else (contextual_risks[0] if contextual_risks else None)

    review_items = []
    for finding in effective_risks[:5]:
        review_items.append({
            "check": finding.get("check"),
            "title": _pr2_title(finding),
            "severity": _pr2_severity(finding),
            "reason": finding.get("risk_reason") or finding.get("detail") or finding.get("expert_comment") or "",
            "action": finding.get("action") or finding.get("recommendation") or "Revisar antes de liberar.",
        })

    if not review_items and contextual_risks:
        for finding in contextual_risks[:3]:
            review_items.append({
                "check": finding.get("check"),
                "title": _pr2_title(finding),
                "severity": _pr2_severity(finding),
                "reason": finding.get("risk_reason") or finding.get("detail") or finding.get("expert_comment") or "",
                "action": finding.get("action") or finding.get("recommendation") or "Validar si aplica.",
            })

    review_time_basis = len(effective_risks)
    if critical_risks:
        review_time_basis += 2

    confidence = "Media"
    if status in {"READY", "NO_GO"}:
        confidence = "Alta"
    elif contextual_risks and not effective_risks:
        confidence = "Media"

    return {
        "version": "v2_foundation",
        "status": status,
        "legacy_status": legacy_status,
        "legacy_decision": decision,
        "decision": production_decision,
        "score": score,
        "confidence": confidence,
        "main_reason": _pr2_primary_reason(status, effective_risks, contextual_risks),
        "primary_risk": _pr2_title(primary) if primary else None,
        "review_time_estimate": _pr2_review_time(review_time_basis),
        "effective_risk_count": len(effective_risks),
        "critical_risk_count": len(critical_risks),
        "warning_risk_count": len(warning_risks),
        "contextual_note_count": len(contextual_risks),
        "what_to_review_first": review_items,
        "operational_context": {
            "profile_name": operational_profile.get("profile_name"),
            "process": operational_profile.get("process"),
            "substrate_family": operational_profile.get("substrate_family"),
        },
        "product_note": (
            "Production Readiness v2 es una capa ejecutiva de decisión. "
            "No reemplaza aún el criterio final de preprensa."
        ),
    }

