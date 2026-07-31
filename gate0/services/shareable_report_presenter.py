"""
Shareable Report Presenter v1.

Transforms full Gate0 report_data into a compact executive summary.

This module does not render HTML.
This module does not generate PDF.
This module does not change scoring or readiness logic.
"""


def _as_dict(value):
    return value if isinstance(value, dict) else {}


def _as_list(value):
    return value if isinstance(value, list) else []


def _first_value(*values, default=None):
    for value in values:
        if value is not None and value != "":
            return value
    return default


def _status_label(status):
    status = str(status or "").upper()

    return {
        "READY": "Liberable",
        "READY_WITH_NOTES": "Liberable con observaciones",
        "REVIEW_REQUIRED": "Requiere revisión",
        "HIGH_RISK": "Alto riesgo",
        "NO_GO": "No liberar",
    }.get(status, status or "No informado")


def _decision_label(decision):
    decision = str(decision or "").upper()

    return {
        "GO": "Liberar",
        "GO_WITH_NOTES": "Liberar con observaciones",
        "HOLD": "Retener para revisión",
        "NO_GO": "No liberar",
    }.get(decision, decision or "No informado")


def _operational_context(report_data):
    report_data = _as_dict(report_data)

    production_readiness = _as_dict(report_data.get("production_readiness_v2"))
    business_assessment = _as_dict(report_data.get("business_assessment"))

    return (
        _as_dict(production_readiness.get("operational_context"))
        or _as_dict(report_data.get("operational_profile"))
        or _as_dict(business_assessment.get("operational_profile"))
    )


def _context_label(context):
    context = _as_dict(context)

    label = context.get("profile_context_label")
    if label:
        return label

    process = context.get("process")
    substrate = context.get("substrate_family")

    if process or substrate:
        return " / ".join(str(v) for v in [process, substrate] if v)

    return context.get("profile_name") or "No informado"


def _context_thresholds(context):
    context = _as_dict(context)
    thresholds = _as_dict(context.get("key_thresholds")) or _as_dict(context.get("profile_thresholds"))

    return {
        "tac_max_percent": _first_value(thresholds.get("tac_max_percent"), context.get("tac_max_percent")),
        "image_minimum_dpi": _first_value(thresholds.get("image_minimum_dpi"), context.get("image_minimum_dpi")),
        "separation_normal_max_printable": _first_value(
            thresholds.get("separation_normal_max_printable"),
            context.get("separation_normal_max_printable"),
        ),
    }


def _risk_from_review_item(item):
    item = _as_dict(item)

    return {
        "title": _first_value(item.get("title"), item.get("check"), default="Riesgo sin título"),
        "severity": str(_first_value(item.get("severity"), item.get("business_severity"), default="INFO")).upper(),
        "reason": _first_value(item.get("reason"), item.get("risk_reason"), item.get("message"), default="Sin detalle."),
        "action": _first_value(item.get("action"), item.get("recommended_action"), default="Revisar técnicamente antes de liberar."),
    }


def _risk_from_finding(item):
    item = _as_dict(item)

    return {
        "title": _first_value(item.get("risk_title"), item.get("title"), item.get("check"), default="Riesgo sin título"),
        "severity": str(_first_value(item.get("business_severity"), item.get("severity"), default="INFO")).upper(),
        "reason": _first_value(item.get("risk_reason"), item.get("reason"), item.get("message"), default="Sin detalle."),
        "action": _first_value(
            item.get("recommended_action"),
            item.get("action"),
            item.get("fix_recommendation"),
            default="Revisar técnicamente antes de liberar.",
        ),
    }


def _top_risks(report_data, limit=3):
    report_data = _as_dict(report_data)
    production_readiness = _as_dict(report_data.get("production_readiness_v2"))
    business_assessment = _as_dict(report_data.get("business_assessment"))

    review_items = _as_list(production_readiness.get("what_to_review_first"))
    if review_items:
        return [_risk_from_review_item(item) for item in review_items[:limit]]

    priority_findings = _as_list(business_assessment.get("priority_findings"))
    if not priority_findings:
        priority_findings = _as_list(report_data.get("findings"))

    return [_risk_from_finding(item) for item in priority_findings[:limit]]


def _recommended_action(production_readiness, top_risks):
    production_readiness = _as_dict(production_readiness)

    return _first_value(
        production_readiness.get("next_step"),
        top_risks[0].get("action") if top_risks else None,
        default="Liberar según flujo normal si no hay observaciones adicionales.",
    )


def _limitations(production_readiness):
    production_readiness = _as_dict(production_readiness)

    product_note = production_readiness.get("product_note")

    items = [
        product_note or "Gate0 no reemplaza el criterio final de preprensa.",
        "El reporte resume riesgos prioritarios; el detalle técnico permanece en el dashboard.",
        "Gate0 no corrige automáticamente el archivo.",
    ]

    result = []
    for item in items:
        if item and item not in result:
            result.append(item)

    return result


def build_shareable_report_summary(report_data):
    """
    Build compact executive summary for a shareable/printable report.
    """
    report_data = _as_dict(report_data)

    production_readiness = _as_dict(report_data.get("production_readiness_v2"))
    readiness_assessment = _as_dict(report_data.get("readiness_assessment"))
    readiness_summary = _as_dict(report_data.get("readiness_summary"))
    context = _operational_context(report_data)

    status = _first_value(
        production_readiness.get("status"),
        readiness_assessment.get("readiness_status"),
        readiness_summary.get("status"),
        default="UNKNOWN",
    )

    decision = _first_value(
        production_readiness.get("legacy_decision"),
        readiness_assessment.get("readiness_decision"),
        readiness_summary.get("decision"),
        production_readiness.get("decision"),
        default="UNKNOWN",
    )

    score = _first_value(
        production_readiness.get("score"),
        readiness_assessment.get("readiness_score"),
        readiness_summary.get("score"),
        default="-",
    )

    top_risks = _top_risks(report_data, limit=3)

    context_thresholds = _context_thresholds(context)

    return {
        "version": "shareable_report_v1",
        "file": report_data.get("file") or "-",
        "client": report_data.get("client") or "Sin cliente",
        "pages": report_data.get("pages") or report_data.get("pdf_structure", {}).get("page_count") or "-",
        "analyzed_at": report_data.get("analyzed_at") or "-",
        "status": status,
        "status_label": _status_label(status),
        "decision": decision,
        "decision_label": _decision_label(decision),
        "score": score,
        "answer": production_readiness.get("answer") or readiness_summary.get("headline") or "-",
        "main_reason": production_readiness.get("main_reason") or production_readiness.get("supervisor_summary") or "-",
        "recommended_action": _recommended_action(production_readiness, top_risks),
        "operational_context": {
            "profile_name": context.get("profile_name"),
            "profile_context_label": _context_label(context),
            "profile_contract_valid": context.get("profile_contract_valid"),
            "context_statement": context.get("context_statement") or f"Evaluado contra perfil productivo {_context_label(context)}.",
            "tac_max_percent": context_thresholds.get("tac_max_percent"),
            "image_minimum_dpi": context_thresholds.get("image_minimum_dpi"),
            "separation_normal_max_printable": context_thresholds.get("separation_normal_max_printable"),
        },
        "top_risks": top_risks,
        "risk_count": len(top_risks),
        "limitations": _limitations(production_readiness),
    }
