from pathlib import Path


HTML = Path("dashboard/index.html").read_text(encoding="utf-8")


def _render_pr2_area():
    start = HTML.index("function renderProductionReadinessV2")
    end = HTML.index("function renderSeparations")
    return HTML[start:end]


def test_dashboard_exposes_shareable_report_button():
    assert 'id="shareableReportLink"' in HTML
    assert "Reporte ejecutivo" in HTML
    assert 'target="_blank"' in HTML
    assert 'rel="noopener"' in HTML


def test_dashboard_report_button_uses_printable_report_route_with_sid():
    assert "function configureShareableReportLink()" in HTML
    assert "/report/print?sid=" in HTML
    assert "encodeURIComponent(SID)" in HTML
    assert "configureShareableReportLink();" in HTML


def test_production_readiness_review_list_hides_redundant_occurrence_suffix():
    area = _render_pr2_area()

    assert "occurrence_count" not in area
    assert "ocurrencias" not in area
    assert "occurrence-count" not in area
    assert "pr2-review-link" in area
    assert "item.reason" in area
