"""
Compare Executive Presenter

Transforms low-level ComparisonResult checks into an executive prepress summary.

This presenter does not change scoring or technical comparison logic.
It only prepares a clearer interpretation for /compare-candidate.
"""


def _status_label(status):
    return {
        "OK": "Sin diferencias relevantes",
        "REVIEW_REQUIRED": "Requiere revisión",
        "HIGH_RISK": "Alto riesgo",
    }.get(str(status or ""), str(status or "Revisión requerida"))


def _check_rank(check):
    status = str((check or {}).get("status", ""))
    return {
        "CRITICAL": 0,
        "WARNING": 1,
        "NOT_EVALUATED": 2,
        "OK": 3,
    }.get(status, 4)


def _check_title(check):
    category = str((check or {}).get("category") or "Check")
    name = str((check or {}).get("name") or "Validación")
    return f"{category} — {name}"


def _check_action(check):
    status = str((check or {}).get("status") or "")

    if status == "CRITICAL":
        return "Detener liberación y revisar contra el arte aprobado antes de continuar."

    if status == "WARNING":
        return "Confirmar si la diferencia es esperada o si requiere corrección de preprensa."

    if status == "NOT_EVALUATED":
        return "Completar revisión manual o mejorar extracción antes de interpretar como consistente."

    return "Sin acción adicional para este check."


def _default_message(check):
    status = str((check or {}).get("status") or "")

    if status == "CRITICAL":
        return "Se detectó una diferencia crítica."

    if status == "WARNING":
        return "Se detectó una diferencia que requiere confirmación."

    if status == "NOT_EVALUATED":
        return "Este check no tuvo datos suficientes para confirmar consistencia."

    return "Sin diferencia relevante."


def _top_differences(checks, limit=3):
    issues = [
        check for check in (checks or [])
        if str(check.get("status")) in {"CRITICAL", "WARNING", "NOT_EVALUATED"}
    ]

    issues = sorted(issues, key=_check_rank)

    result = []

    for check in issues[:limit]:
        result.append({
            "title": _check_title(check),
            "status": str(check.get("status") or ""),
            "detail": check.get("message") or _default_message(check),
            "left": check.get("left"),
            "right": check.get("right"),
            "action": _check_action(check),
        })

    return result


def _not_evaluated_items(checks):
    items = []

    for check in checks or []:
        if str(check.get("status")) == "NOT_EVALUATED":
            items.append({
                "title": _check_title(check),
                "detail": check.get("message") or _default_message(check),
            })

    return items


def _confidence_from_coverage(coverage_percent, total_checks):
    if total_checks <= 0:
        return "Baja"

    if coverage_percent >= 90:
        return "Alta"

    if coverage_percent >= 60:
        return "Media"

    return "Baja"


def _next_action(result, not_evaluated_count):
    status = str(getattr(result, "overall_status", "") or "")

    if status == "HIGH_RISK":
        return "No liberar. Revisar las diferencias críticas contra el arte aprobado."

    if status == "REVIEW_REQUIRED" and not_evaluated_count > 0:
        return "No interpretar como OK. Completar revisión manual de los checks no evaluados."

    if status == "REVIEW_REQUIRED":
        return "Validar si las diferencias detectadas son esperadas antes de liberar."

    if status == "OK":
        return "Puede continuar el flujo normal, manteniendo revisión visual habitual."

    return "Revisar el resultado antes de liberar."


def build_compare_executive_summary(result):
    checks = list(getattr(result, "checks", []) or [])
    metadata = getattr(result, "metadata", {}) or {}

    total_checks = len(checks)
    not_evaluated_count = int(metadata.get("not_evaluated_count") or 0)

    if not metadata.get("not_evaluated_count"):
        not_evaluated_count = sum(1 for check in checks if str(check.get("status")) == "NOT_EVALUATED")

    evaluated_checks = total_checks - not_evaluated_count
    coverage_percent = round((evaluated_checks / total_checks) * 100) if total_checks else 0
    confidence = _confidence_from_coverage(coverage_percent, total_checks)

    limitation = (
        "Comparación estructural. No valida equivalencia visual píxel a píxel, "
        "posición exacta de todos los objetos ni cambios de diseño no representados "
        "en los checks disponibles."
    )

    return {
        "status": getattr(result, "overall_status", ""),
        "status_label": _status_label(getattr(result, "overall_status", "")),
        "score": getattr(result, "score", 0),
        "decision": getattr(result, "decision", ""),
        "summary": getattr(result, "summary", ""),
        "recommendation": getattr(result, "recommendation", ""),
        "coverage_percent": coverage_percent,
        "confidence": confidence,
        "evaluated_checks": evaluated_checks,
        "total_checks": total_checks,
        "critical_count": int(metadata.get("critical_count") or 0),
        "warning_count": int(metadata.get("warning_count") or 0),
        "not_evaluated_count": not_evaluated_count,
        "top_differences": _top_differences(checks),
        "not_evaluated_items": _not_evaluated_items(checks),
        "next_action": _next_action(result, not_evaluated_count),
        "limitation": limitation,
    }
