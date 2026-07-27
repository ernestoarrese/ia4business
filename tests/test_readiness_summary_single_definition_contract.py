import re
from pathlib import Path

from readiness_summary import (
    _pr2_printable_area_confidence_confirmed,
    build_production_readiness_v2,
)


SOURCE = Path("readiness_summary.py").read_text(encoding="utf-8")


CONSOLIDATED_FUNCTIONS = [
    "sort_top_risks",
    "_pr2_title",
    "_pr2_is_contextual_non_blocking",
    "_pr2_next_step",
    "_pr2_priority_score",
    "_pr2_make_review_item",
    "_pr2_plain_reason",
    "_pr2_printable_area_confidence_confirmed",
    "build_production_readiness_v2",
]


def _definition_count(name):
    return len(re.findall(rf"^def {name}\(", SOURCE, flags=re.M))


def test_readiness_summary_has_single_definition_for_consolidated_functions():
    for name in CONSOLIDATED_FUNCTIONS:
        assert _definition_count(name) == 1, name


def test_readiness_summary_keeps_active_pr2_printable_area_version():
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


def test_readiness_summary_keeps_strict_printable_area_confirmation():
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
