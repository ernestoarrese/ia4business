"""
readiness_engine.py

Motor de decisión Gate0.

Responsabilidad:
- Convertir hallazgos enriquecidos en un score de preparación.
- Definir status operativo.
- Definir decisión final GO / HOLD / NO_GO.
- No detecta problemas.
- No interpreta reglas técnicas.
"""

CLASS_PENALTIES = {
    "A": {
        "CRITICAL": 25,
        "WARNING": 12,
        "INFO": 3
    },
    "B": {
        "CRITICAL": 18,
        "WARNING": 7,
        "INFO": 2
    },
    "C": {
        "CRITICAL": 12,
        "WARNING": 5,
        "INFO": 1
    }
}


CHECK_CLASS = {
    "FONT_NOT_EMBEDDED": "A",
    "PDF_STRUCTURE_RISK": "A",

    "LOW_IMAGE_RESOLUTION": "B",
    "BARCODE_RISK": "B",
    "SMALL_TEXT_RISK": "B",
    "HIGH_TAC_RISK": "B",
    "OVERPRINT_RISK": "B",

    "RGB_OBJECT": "C",
    "WHITE_INK_RISK": "C",
    "SPOT_COLOR_RISK": "C",
    "SEPARATION_COUNT_RISK": "C"
}


def normalize_severity(value):
    if not value:
        return "INFO"

    value = str(value).upper().strip()

    if value in ["CRITICAL", "WARNING", "INFO", "PASS"]:
        return value

    if value == "HIGH":
        return "CRITICAL"

    if value == "MEDIUM":
        return "WARNING"

    if value == "LOW":
        return "INFO"

    return "INFO"


def get_check_class(check_name):
    return CHECK_CLASS.get(check_name, "C")


def calculate_readiness_score(findings):
    """
    Calcula score de 0 a 100.
    Parte de 100 y descuenta según clase + severidad.
    Penaliza una sola vez por tipo de check con mayor severidad.
    """

    if not findings:
        return {
            "score": 100,
            "penalty": 0,
            "applied_rules": [],
            "class_a_critical_count": 0,
            "critical_count": 0,
            "warning_count": 0,
            "info_count": 0
        }

    worst_by_check = {}

    severity_rank = {
        "PASS": 0,
        "INFO": 1,
        "WARNING": 2,
        "CRITICAL": 3
    }

    for finding in findings:
        check = finding.get("check", "UNKNOWN")
        severity = normalize_severity(
            finding.get("business_severity") or finding.get("severity")
        )

        if severity == "PASS":
            continue

        current = worst_by_check.get(check)

        if current is None:
            worst_by_check[check] = finding
        else:
            current_severity = normalize_severity(
                current.get("business_severity") or current.get("severity")
            )
            if severity_rank[severity] > severity_rank[current_severity]:
                worst_by_check[check] = finding

    total_penalty = 0
    applied_rules = []

    class_a_critical_count = 0
    critical_count = 0
    warning_count = 0
    info_count = 0

    for check, finding in worst_by_check.items():
        severity = normalize_severity(
            finding.get("business_severity") or finding.get("severity")
        )
        check_class = get_check_class(check)

        penalty = CLASS_PENALTIES.get(check_class, {}).get(severity, 0)

        total_penalty += penalty

        if severity == "CRITICAL":
            critical_count += 1
            if check_class == "A":
                class_a_critical_count += 1

        elif severity == "WARNING":
            warning_count += 1

        elif severity == "INFO":
            info_count += 1

        applied_rules.append({
            "check": check,
            "class": check_class,
            "severity": severity,
            "penalty": penalty,
            "page": finding.get("page"),
            "detail": finding.get("detail"),
            "risk_area": finding.get("risk_area"),
            "risk_reason": finding.get("risk_reason"),
            "action": finding.get("action")
        })

    score = max(0, 100 - total_penalty)

    return {
        "score": score,
        "penalty": total_penalty,
        "applied_rules": applied_rules,
        "class_a_critical_count": class_a_critical_count,
        "critical_count": critical_count,
        "warning_count": warning_count,
        "info_count": info_count
    }


def define_readiness_status(score, metrics):
    """
    Define estado operativo.
    """

    if metrics.get("class_a_critical_count", 0) > 0:
        return "HIGH_RISK"

    if score >= 95:
        return "READY"

    if score >= 85:
        return "READY_WITH_NOTES"

    if score >= 70:
        return "REVIEW_REQUIRED"

    return "HIGH_RISK"


def define_readiness_decision(status, metrics):
    """
    Define decisión final.
    """

    if status == "READY":
        return "GO"

    if status == "READY_WITH_NOTES":
        return "GO_WITH_NOTES"

    if status == "REVIEW_REQUIRED":
        return "HOLD"

    return "NO_GO"


def build_readiness_assessment(findings):
    """
    Punto de entrada principal.
    """

    metrics = calculate_readiness_score(findings)
    score = metrics["score"]
    status = define_readiness_status(score, metrics)
    decision = define_readiness_decision(status, metrics)

    return {
        "readiness_score": score,
        "readiness_status": status,
        "readiness_decision": decision,
        "readiness_metrics": metrics
    }

