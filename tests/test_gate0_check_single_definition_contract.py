import re
from pathlib import Path

from gate0_check import check_font_embedding, check_high_tac, check_rgb_objects


SOURCE = Path("gate0_check.py").read_text(encoding="utf-8")


def _top_level_definition_count(name):
    return len(re.findall(rf"^def {name}\(", SOURCE, flags=re.M))


def test_gate0_check_has_single_active_definition_for_evidence_depth_functions():
    assert _top_level_definition_count("check_rgb_objects") == 1
    assert _top_level_definition_count("check_high_tac") == 1
    assert _top_level_definition_count("check_font_embedding") == 1


def test_gate0_check_evidence_depth_functions_remain_before_main_guard():
    main_guard = SOURCE.rfind('if __name__ == "__main__":')

    assert main_guard > SOURCE.rfind("def check_rgb_objects")
    assert main_guard > SOURCE.rfind("def check_high_tac")
    assert main_guard > SOURCE.rfind("def check_font_embedding")


def test_rgb_object_single_definition_keeps_evidence_depth_fields():
    findings = check_rgb_objects("0.1 0.2 0.3 rg", 1)

    assert findings
    first = findings[0]

    assert first["check"] == "RGB_OBJECT"
    assert first["bbox_available"] is False
    assert first["location_confidence"] == "NOT_AVAILABLE_IN_RGB_OBJECT_V1"
    assert first["object_location_status"] == "NOT_LOCALIZED"
    assert first["requires_manual_location_review"] is True


def test_high_tac_single_definition_keeps_evidence_depth_fields():
    findings = check_high_tac("0.9 0.8 0.7 0.6 k", 1, tac_limit=280)

    assert findings
    first = findings[0]

    assert first["check"] == "HIGH_TAC_RISK"
    assert first["detected_tac"] == 300.0
    assert first["tac_limit"] == 280
    assert first["bbox_available"] is False
    assert first["location_confidence"] == "NOT_AVAILABLE_IN_HIGH_TAC_RISK_V1"
    assert first["requires_manual_location_review"] is True


def test_font_embedding_single_definition_keeps_resource_level_limitation():
    findings = check_font_embedding([
        {
            "page": 1,
            "xref": 10,
            "font_name": "Helvetica",
            "font_name_raw": "Helvetica",
            "font_type": "Type1",
            "font_ext": "",
            "embedded": False,
        }
    ])

    assert findings
    first = findings[0]

    assert first["check"] == "FONT_NOT_EMBEDDED"
    assert first["font_name"] == "Helvetica"
    assert first["embedded"] is False
    assert first["text_association_status"] == "NOT_ASSOCIATED_IN_FONT_V1"
    assert first["affected_text_available"] is False
    assert first["bbox_available"] is False
    assert first["requires_manual_text_review"] is True
