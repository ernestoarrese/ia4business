import re
from pathlib import Path

from business_rules import evaluate_high_tac_risk, evaluate_rgb_object


SOURCE = Path("business_rules.py").read_text(encoding="utf-8")


PROFILE = {
    "color": {
        "rgb": {
            "info_max_area_percent": 3.0,
            "critical_min_area_percent": 15.0,
        }
    },
    "tac": {
        "max_tac_percent": 280,
        "warning_excess_percent": 20,
        "critical_excess_percent": 40,
        "large_area_percent": 15,
    },
}


def _top_level_definition_count(name):
    return len(re.findall(rf"^def {name}\(", SOURCE, flags=re.M))


def test_business_rules_has_single_active_definition_for_25c_functions():
    assert _top_level_definition_count("evaluate_rgb_object") == 1
    assert _top_level_definition_count("evaluate_high_tac_risk") == 1


def test_rgb_business_rule_keeps_no_bbox_contextual_behavior():
    result = evaluate_rgb_object(
        {
            "check": "RGB_OBJECT",
            "bbox_available": False,
            "object_area_percent": None,
            "is_printable": True,
        },
        PROFILE,
    )

    assert result["business_severity"] == "INFO"
    assert result.get("readiness_weight", 0) == 0
    assert "ubicación" in result["risk_reason"].lower() or "área" in result["risk_reason"].lower()


def test_rgb_business_rule_keeps_area_thresholds():
    info = evaluate_rgb_object(
        {"check": "RGB_OBJECT", "object_area_percent": 2.99, "is_printable": True},
        PROFILE,
    )
    warning = evaluate_rgb_object(
        {"check": "RGB_OBJECT", "object_area_percent": 3.0, "is_printable": True},
        PROFILE,
    )
    critical = evaluate_rgb_object(
        {"check": "RGB_OBJECT", "object_area_percent": 15.0, "is_printable": True},
        PROFILE,
    )

    assert info["business_severity"] == "INFO"
    assert warning["business_severity"] == "WARNING"
    assert critical["business_severity"] == "CRITICAL"


def test_tac_business_rule_keeps_no_bbox_contextual_behavior():
    result = evaluate_high_tac_risk(
        {
            "check": "HIGH_TAC_RISK",
            "detected_tac": 300,
            "tac_limit": 280,
            "bbox_available": False,
            "object_area_percent": None,
        },
        PROFILE,
    )

    assert result["business_severity"] == "INFO"
    assert result.get("readiness_weight", 0) == 0
    assert "ubicación" in result["risk_reason"].lower() or "área" in result["risk_reason"].lower()


def test_tac_business_rule_keeps_excess_thresholds():
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
