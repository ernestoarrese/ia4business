import re
from pathlib import Path

import business_rules


SOURCE = Path("business_rules.py").read_text(encoding="utf-8")


def _definition_count(name):
    return len(re.findall(rf"^def {name}\(", SOURCE, flags=re.M))


def test_business_rules_has_single_definition_for_remaining_duplicate_functions():
    assert _definition_count("severity_meta") == 1
    assert _definition_count("evaluate_font_not_embedded") == 1


def test_business_rules_keeps_active_severity_meta_tuple_contract():
    rank, score_weight = business_rules.severity_meta("WARNING", {"WARNING": 12})

    assert rank == 2
    assert score_weight == 12


def test_business_rules_keeps_font_not_embedded_as_critical_without_changing_shape():
    result = business_rules.evaluate_font_not_embedded(
        {
            "check": "FONT_NOT_EMBEDDED",
            "font_name": "Helvetica",
            "font_type": "Type1",
            "embedded": False,
            "text_association_status": "NOT_ASSOCIATED_IN_FONT_V1",
        },
        {},
    )

    assert result["check"] == "FONT_NOT_EMBEDDED"
    assert result["business_severity"] == "CRITICAL"
    assert result["font_name"] == "Helvetica"
    assert result["font_type"] == "Type1"
    assert result["embedded"] is False
