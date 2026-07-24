from readiness_summary import build_production_readiness_v2


def test_production_readiness_ready_without_findings():
    result = build_production_readiness_v2(
        {"readiness_status": "READY", "readiness_decision": "GO", "readiness_score": 100},
        [],
        {"profile_name": "flexo_pet_bopp_default", "process": "flexo"},
    )

    assert result["status"] == "READY"
    assert result["decision"] == "Liberable."
    assert result["review_time_estimate"] == "0–2 minutos"
    assert result["effective_risk_count"] == 0


def test_production_readiness_contextual_info_is_ready_with_notes():
    result = build_production_readiness_v2(
        {"readiness_status": "READY_WITH_NOTES", "readiness_decision": "GO_WITH_NOTES", "readiness_score": 95},
        [{
            "check": "OVERPRINT_RISK",
            "severity": "INFO",
            "business_severity": "INFO",
            "score_weight": 0,
            "is_blocking": False,
            "risk_reason": "Overprint genérico contextual.",
        }],
        {},
    )

    assert result["status"] == "READY_WITH_NOTES"
    assert result["effective_risk_count"] == 0
    assert result["contextual_note_count"] == 1
    assert result["what_to_review_first"][0]["title"] == "Sobreimpresión"


def test_production_readiness_warning_requires_review():
    result = build_production_readiness_v2(
        {"readiness_status": "REVIEW_REQUIRED", "readiness_decision": "HOLD", "readiness_score": 82},
        [{
            "check": "SMALL_TEXT_RISK",
            "severity": "WARNING",
            "business_severity": "WARNING",
            "score_weight": 8,
            "is_blocking": False,
            "risk_reason": "Texto pequeño dentro del área imprimible.",
        }],
        {},
    )

    assert result["status"] == "REVIEW_REQUIRED"
    assert result["decision"] == "Revisar antes de liberar."
    assert result["effective_risk_count"] == 1
    assert result["what_to_review_first"][0]["title"] == "Texto pequeño / legibilidad"


def test_production_readiness_blocking_critical_is_no_go():
    result = build_production_readiness_v2(
        {"readiness_status": "HIGH_RISK", "readiness_decision": "NO_GO", "readiness_score": 45},
        [{
            "check": "FONT_NOT_EMBEDDED",
            "severity": "CRITICAL",
            "business_severity": "CRITICAL",
            "score_weight": 25,
            "is_blocking": True,
            "risk_reason": "Fuente crítica no embebida.",
        }],
        {},
    )

    assert result["status"] == "NO_GO"
    assert result["decision"] == "No liberar sin corrección o revisión técnica."
    assert result["critical_risk_count"] == 1
