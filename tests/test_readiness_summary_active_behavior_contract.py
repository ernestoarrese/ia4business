from readiness_summary import (
    _pr2_printable_area_confidence_confirmed,
    build_production_readiness_v2,
)


def test_pr2_active_version_is_printable_area_priority():
    result = build_production_readiness_v2(
        {
            "readiness_status": "READY",
            "readiness_decision": "GO",
            "readiness_score": 100,
        },
        [],
        {},
    )

    assert result["version"] == "v2_printable_area_priority"
    assert result["question"] == "¿Está este archivo listo para producir?"
    assert result["answer"] == "Sí. El archivo está listo para producir."


def test_pr2_confirmed_outside_printable_area_becomes_contextual_note():
    result = build_production_readiness_v2(
        {
            "readiness_status": "REVIEW_REQUIRED",
            "readiness_decision": "HOLD",
            "readiness_score": 90,
        },
        [
            {
                "check": "SMALL_TEXT_RISK",
                "severity": "WARNING",
                "business_severity": "WARNING",
                "score_weight": 8,
                "is_blocking": False,
                "risk_reason": "Texto pequeño.",
                "printable_area_source": "TRIMBOX_CONFIRMED",
                "printable_area_confidence": "CONFIRMED",
                "is_inside_printable_area": False,
                "printable_area_overlap_percent": 0,
            }
        ],
        {},
    )

    assert result["status"] == "READY_WITH_NOTES"
    assert result["effective_risk_count"] == 0
    assert result["contextual_note_count"] == 1
    assert result["primary_printable_area_status"] == "OUTSIDE_CONFIRMED_PRINTABLE_AREA"


def test_pr2_unconfirmed_outside_printable_area_does_not_downgrade_risk():
    result = build_production_readiness_v2(
        {
            "readiness_status": "REVIEW_REQUIRED",
            "readiness_decision": "HOLD",
            "readiness_score": 82,
        },
        [
            {
                "check": "SMALL_TEXT_RISK",
                "severity": "WARNING",
                "business_severity": "WARNING",
                "score_weight": 8,
                "is_blocking": False,
                "risk_reason": "Texto pequeño.",
                "printable_area_source": "UNCONFIRMED_FULL_PAGE",
                "printable_area_confidence": "UNCONFIRMED",
                "is_inside_printable_area": False,
                "printable_area_overlap_percent": 0,
            }
        ],
        {},
    )

    assert result["status"] == "REVIEW_REQUIRED"
    assert result["effective_risk_count"] == 1
    assert result["contextual_note_count"] == 0
    assert result["primary_printable_area_status"] != "OUTSIDE_CONFIRMED_PRINTABLE_AREA"


def test_pr2_printable_area_confidence_confirmed_helper_is_strict():
    assert _pr2_printable_area_confidence_confirmed(
        {
            "printable_area_source": "TRIMBOX_CONFIRMED",
            "printable_area_confidence": "CONFIRMED",
        }
    ) is True

    assert _pr2_printable_area_confidence_confirmed(
        {
            "printable_area_source": "UNCONFIRMED_FULL_PAGE",
            "printable_area_confidence": "UNCONFIRMED",
        }
    ) is False

    assert _pr2_printable_area_confidence_confirmed(
        {
            "printable_area_source": "",
            "printable_area_confidence": "",
        }
    ) is False


def test_pr2_white_overprint_keeps_supervisor_priority_language():
    result = build_production_readiness_v2(
        {
            "readiness_status": "REVIEW_REQUIRED",
            "readiness_decision": "HOLD",
            "readiness_score": 82,
        },
        [
            {
                "check": "SMALL_TEXT_RISK",
                "severity": "WARNING",
                "business_severity": "WARNING",
                "score_weight": 12,
                "is_blocking": False,
                "risk_reason": "Texto pequeño dentro del área imprimible.",
            },
            {
                "check": "OVERPRINT_RISK",
                "severity": "WARNING",
                "business_severity": "WARNING",
                "score_weight": 8,
                "is_blocking": False,
                "white_ink_present": True,
                "overprint_context": "WHITE_PRESENT_CONTEXTUAL_RISK",
                "risk_reason": "Sobreimpresión detectada con blanco presente.",
            },
        ],
        {},
    )

    assert result["status"] == "REVIEW_REQUIRED"
    assert result["primary_risk"] == "Validar sobreimpresión con blanco"
    assert result["what_to_review_first"][0]["title"] == "Validar sobreimpresión con blanco"


def test_pr2_repeated_small_text_remains_deduplicated():
    result = build_production_readiness_v2(
        {
            "readiness_status": "REVIEW_REQUIRED",
            "readiness_decision": "HOLD",
            "readiness_score": 82,
        },
        [
            {
                "check": "SMALL_TEXT_RISK",
                "severity": "WARNING",
                "business_severity": "WARNING",
                "score_weight": 12,
                "is_blocking": False,
                "risk_reason": "Texto pequeño dentro del área imprimible.",
            },
            {
                "check": "SMALL_TEXT_RISK",
                "severity": "WARNING",
                "business_severity": "WARNING",
                "score_weight": 12,
                "is_blocking": False,
                "risk_reason": "Texto pequeño dentro del área imprimible.",
            },
        ],
        {},
    )

    assert len(result["what_to_review_first"]) == 1
    assert result["what_to_review_first"][0]["title"] == "Revisar texto pequeño"
    assert result["what_to_review_first"][0]["occurrence_count"] == 2
