from gate0_check import check_high_tac
from business_rules import evaluate_high_tac_risk


def test_high_tac_detector_adds_evidence_depth_without_bbox():
    findings = check_high_tac("0.9 0.8 0.7 0.6 k", 1, tac_limit=280)

    assert len(findings) == 1

    first = findings[0]
    assert first["check"] == "HIGH_TAC_RISK"
    assert first["page"] == 1
    assert first["color_space"] == "DeviceCMYK"
    assert first["detection_method"] == "CONTENT_STREAM_CMYK_OPERATOR"
    assert first["detected_tac"] == 300.0
    assert first["tac_limit"] == 280
    assert first["tac_excess"] == 20.0
    assert first["bbox_available"] is False
    assert first["object_location_status"] == "NOT_LOCALIZED"
    assert first["printable_area_status"] == "NOT_EVALUABLE_WITHOUT_BBOX"
    assert first["requires_manual_location_review"] is True


def test_high_tac_business_rule_does_not_invent_zero_area_without_bbox():
    result = evaluate_high_tac_risk(
        {
            "check": "HIGH_TAC_RISK",
            "detected_tac": 321,
            "bbox_available": False,
            "object_location_status": "NOT_LOCALIZED",
        },
        {"tac": {"max_tac_percent": 280}},
    )

    severity = result.get("business_severity") or result.get("severity")

    assert severity == "INFO"
    assert result.get("score_weight", 0) == 0
    assert "ubicación visual" in result.get("risk_reason", "").lower()


def test_high_tac_business_rule_still_escalates_when_area_is_known():
    result = evaluate_high_tac_risk(
        {
            "check": "HIGH_TAC_RISK",
            "detected_tac": 321,
            "object_area_percent": 0.5,
        },
        {"tac": {"max_tac_percent": 280}},
    )

    severity = result.get("business_severity") or result.get("severity")

    assert severity == "CRITICAL"
    assert result.get("score_weight", 0) >= 25
