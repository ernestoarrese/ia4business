from pathlib import Path


def test_dashboard_defines_inline_separation_usage_helpers():
    html = Path("dashboard/index.html").read_text(encoding="utf-8")

    assert "function separationUsageSignalMap" in html
    assert "function separationUsageSignalForItem" in html
    assert "function renderSeparationUsageSignal" in html
    assert "const usageMap=separationUsageSignalMap(data);" in html
    assert "renderSeparationUsageSignal(i,usageMap)" in html
