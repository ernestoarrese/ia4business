from gate0_check import check_rgb_objects
from business_rules import evaluate_rgb_object


def test_rgb_object_detector_adds_evidence_depth_without_bbox():
    findings = check_rgb_objects("0.1 0.2 0.3 rg 0.4 0.5 0.6 RG", 1)

    assert len(findings) == 2

    first = findings[0]
    assert first["check"] == "RGB_OBJECT"
    assert first["page"] == 1
    assert first["color_space"] == "DeviceRGB"
    assert first["detection_method"] == "CONTENT_STREAM_RGB_OPERATOR"
    assert first["bbox_available"] is False
    assert first["object_location_status"] == "NOT_LOCALIZED"
    assert first["printable_area_status"] == "NOT_EVALUABLE_WITHOUT_BBOX"
    assert first["requires_manual_location_review"] is True


def test_rgb_object_business_rule_does_not_invent_zero_area_without_bbox():
    result = evaluate_rgb_object(
        {
            "check": "RGB_OBJECT",
            "value": "RGB=(0.1, 0.2, 0.3)",
            "bbox_available": False,
            "object_location_status": "NOT_LOCALIZED",
        },
        {"color": {"rgb": {}}},
    )

    severity = result.get("business_severity") or result.get("severity")

    assert severity == "INFO"
    assert result.get("score_weight", 0) == 0
    assert "sin ubicación visual confirmada" in result.get("risk_reason", "").lower()


def test_rgb_object_business_rule_still_escalates_when_area_is_large():
    result = evaluate_rgb_object(
        {
            "check": "RGB_OBJECT",
            "object_area_percent": 18,
            "is_printable": True,
        },
        {"color": {"rgb": {"critical_min_area_percent": 15}}},
    )

    severity = result.get("business_severity") or result.get("severity")

    assert severity == "CRITICAL"
    assert result.get("score_weight", 0) >= 25
