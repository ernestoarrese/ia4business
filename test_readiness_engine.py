from readiness_engine import build_readiness_assessment


def test_class_a_critical_no_go():
    findings = [
        {
            "check": "FONT_NOT_EMBEDDED",
            "business_severity": "CRITICAL",
            "detail": "Fuente viva no embebida"
        }
    ]

    result = build_readiness_assessment(findings)

    assert result["readiness_status"] == "HIGH_RISK"
    assert result["readiness_decision"] == "NO_GO"
    assert result["readiness_score"] == 75


def test_low_image_warning_go_with_notes():
    findings = [
        {
            "check": "LOW_IMAGE_RESOLUTION",
            "business_severity": "WARNING",
            "detail": "Imagen baja resolución"
        }
    ]

    result = build_readiness_assessment(findings)

    assert result["readiness_status"] == "READY_WITH_NOTES"
    assert result["readiness_decision"] == "GO_WITH_NOTES"
    assert result["readiness_score"] == 93


def test_high_tac_critical_hold():
    findings = [
        {
            "check": "HIGH_TAC_RISK",
            "business_severity": "CRITICAL",
            "detail": "TAC alto"
        }
    ]

    result = build_readiness_assessment(findings)

    assert result["readiness_status"] == "REVIEW_REQUIRED"
    assert result["readiness_decision"] == "HOLD"
    assert result["readiness_score"] == 82

