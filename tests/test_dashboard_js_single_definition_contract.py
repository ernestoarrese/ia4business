import re
from pathlib import Path


HTML = Path("dashboard/index.html").read_text(encoding="utf-8")


def _dashboard_js():
    scripts = re.findall(
        r"<script[^>]*>(.*?)</script>",
        HTML,
        flags=re.S | re.I,
    )
    assert scripts, "dashboard/index.html debe contener al menos un script"
    return "\n\n".join(scripts)


JS = _dashboard_js()


TOP_LEVEL_FUNCTIONS = [
    "bindProductionReadinessDrilldown",
    "clampOccurrenceIndex",
    "renderOccurrenceNav",
    "renderSeparationUsageV2",
    "riskDataForActiveOccurrence",
    "selectProductionReadinessRisk",
]


def _top_level_function_count(name):
    return len(re.findall(rf"^function\s+{name}\s*\(", JS, flags=re.M))


def test_dashboard_has_single_active_definition_for_critical_js_functions():
    for name in TOP_LEVEL_FUNCTIONS:
        assert _top_level_function_count(name) == 1, name


def test_dashboard_keeps_pr2_drilldown_active_signature():
    assert "function selectProductionReadinessRisk(check,title)" in JS
    assert "pr2FindRiskIndex(check,title)" in JS
    assert "data-pr2-check" in HTML
    assert "data-pr2-title" in HTML


def test_dashboard_keeps_visual_navigation_active_contract():
    assert "function clampOccurrenceIndex(r,index)" in JS
    assert "visualNavigationItems(r)" in JS
    assert "function renderOccurrenceNav(r)" in JS
    assert "hasVisualZones(r)" in JS
    assert "function riskDataForActiveOccurrence(r)" in JS
    assert "visual_zones" in JS


def test_dashboard_keeps_compact_separation_usage_renderer():
    assert "function renderSeparationUsageV2(data)" in JS
    assert "Sprint 26A.3" in JS
    assert "separation_usage_v2" in JS
    assert "bboxLabel" in JS
