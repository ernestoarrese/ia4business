from business_rules import (
    evaluate_rgb_object,
    evaluate_high_tac_risk,
    evaluate_low_image_resolution,
    evaluate_small_text_risk,
    evaluate_separation_count_risk,
)
from readiness_engine import build_readiness_assessment
from gate0_check import check_high_tac


PROFILE = {
    "color": {
        "rgb": {
            "info_max_area_percent": 3.0,
            "critical_min_area_percent": 15.0,
        }
    },
    "image_resolution": {
        "minimum_dpi": 250,
        "critical_dpi": 150,
        "warning_dpi": 200,
        "large_area_percent": 15,
    },
    "text": {
        "min_text_size_pt": 5,
        "critical_text_size_pt": 4,
    },
    "tac": {
        "max_tac_percent": 280,
        "warning_excess_percent": 20,
        "critical_excess_percent": 40,
        "large_area_percent": 15,
    },
    "separations": {
        "max_operational_separations": 8,
        "warning_separations": 11,
        "critical_separations": 13,
    },
}


def test_rgb_without_bbox_is_contextual_info_and_weight_zero():
    result = evaluate_rgb_object(
        {
            "check": "RGB_OBJECT",
            "page": 1,
            "bbox_available": False,
            "object_area_percent": None,
            "is_printable": True,
        },
        PROFILE,
    )

    assert result["business_severity"] == "INFO"
    assert result.get("readiness_weight", 0) == 0
    assert result.get("bbox_available") is False


def test_rgb_area_thresholds_are_stable():
    small = evaluate_rgb_object(
        {"check": "RGB_OBJECT", "object_area_percent": 2.99, "is_printable": True},
        PROFILE,
    )
    medium = evaluate_rgb_object(
        {"check": "RGB_OBJECT", "object_area_percent": 3.0, "is_printable": True},
        PROFILE,
    )
    large = evaluate_rgb_object(
        {"check": "RGB_OBJECT", "object_area_percent": 15.0, "is_printable": True},
        PROFILE,
    )

    assert small["business_severity"] == "INFO"
    assert medium["business_severity"] == "WARNING"
    assert large["business_severity"] == "CRITICAL"


def test_tac_equal_or_below_limit_does_not_create_high_tac_finding():
    findings = check_high_tac("0.7 0.7 0.7 0.7 k", 1, tac_limit=280)
    assert findings == []


def test_tac_without_bbox_is_contextual_info_and_weight_zero():
    result = evaluate_high_tac_risk(
        {
            "check": "HIGH_TAC_RISK",
            "page": 1,
            "detected_tac": 300,
            "tac_limit": 280,
            "bbox_available": False,
            "object_area_percent": None,
        },
        PROFILE,
    )

    assert result["business_severity"] == "INFO"
    assert result.get("readiness_weight", 0) == 0
    assert result.get("bbox_available") is False


def test_tac_excess_thresholds_are_stable():
    warning = evaluate_high_tac_risk(
        {
            "check": "HIGH_TAC_RISK",
            "detected_tac": 300,
            "tac_limit": 280,
            "object_area_percent": 0.5,
        },
        PROFILE,
    )
    critical = evaluate_high_tac_risk(
        {
            "check": "HIGH_TAC_RISK",
            "detected_tac": 321,
            "tac_limit": 280,
            "object_area_percent": 0.5,
        },
        PROFILE,
    )

    assert warning["business_severity"] == "WARNING"
    assert critical["business_severity"] == "CRITICAL"


def test_low_image_resolution_uses_profile_minimum_dpi():
    below_profile_min = evaluate_low_image_resolution(
        {
            "check": "LOW_IMAGE_RESOLUTION",
            "effective_dpi": 249,
            "minimum_image_dpi": 250,
            "object_area_percent": 2,
        },
        PROFILE,
    )

    assert below_profile_min["business_severity"] in {"INFO", "WARNING", "CRITICAL"}
    assert "250" in below_profile_min["risk_reason"] or below_profile_min.get("minimum_image_dpi") == 250


def test_small_text_thresholds_are_stable():
    critical = evaluate_small_text_risk(
        {"check": "SMALL_TEXT_RISK", "font_size_pt": 3.99},
        PROFILE,
    )
    warning = evaluate_small_text_risk(
        {"check": "SMALL_TEXT_RISK", "font_size_pt": 4.0},
        PROFILE,
    )
    pass_like = evaluate_small_text_risk(
        {"check": "SMALL_TEXT_RISK", "font_size_pt": 5.0},
        PROFILE,
    )

    assert critical["business_severity"] == "CRITICAL"
    assert warning["business_severity"] == "WARNING"
    assert pass_like["business_severity"] in {"PASS", "INFO"}


def test_separation_count_thresholds_are_stable():
    pass_result = evaluate_separation_count_risk(
        {"check": "SEPARATION_COUNT_RISK", "printable_separation_count": 8},
        PROFILE,
    )
    info_result = evaluate_separation_count_risk(
        {"check": "SEPARATION_COUNT_RISK", "printable_separation_count": 9},
        PROFILE,
    )
    warning_result = evaluate_separation_count_risk(
        {"check": "SEPARATION_COUNT_RISK", "printable_separation_count": 11},
        PROFILE,
    )
    critical_result = evaluate_separation_count_risk(
        {"check": "SEPARATION_COUNT_RISK", "printable_separation_count": 13},
        PROFILE,
    )

    assert pass_result["business_severity"] == "PASS"
    assert info_result["business_severity"] == "INFO"
    assert warning_result["business_severity"] == "WARNING"
    assert critical_result["business_severity"] == "CRITICAL"


def test_readiness_thresholds_are_stable():
    ready = build_readiness_assessment([])
    notes = build_readiness_assessment([
        {"business_severity": "INFO", "readiness_weight": 5, "check": "RGB_OBJECT"}
    ])
    review = build_readiness_assessment([
        {"business_severity": "WARNING", "readiness_weight": 18, "check": "HIGH_TAC_RISK"}
    ])

    assert ready["readiness_status"] == "READY"
    assert ready["readiness_decision"] == "GO"

    # INFO findings may remain READY or READY_WITH_NOTES depending on current scoring.
    assert notes["readiness_status"] in {"READY", "READY_WITH_NOTES"}
    assert notes["readiness_decision"] in {"GO", "GO_WITH_NOTES"}

    # WARNING findings should not become NO_GO by themselves.
    assert review["readiness_status"] in {"READY_WITH_NOTES", "REVIEW_REQUIRED"}
    assert review["readiness_decision"] in {"GO_WITH_NOTES", "HOLD"}
