from pathlib import Path


def test_dashboard_uses_compact_production_context_copy():
    html = Path("dashboard/index.html").read_text(encoding="utf-8")

    assert "Perfil productivo" in html
    assert "Perfil usado" not in html
    assert "TAC máx." in html
    assert "DPI mín." in html
    assert "Separaciones normales" in html
    assert "Texto pequeño" not in html[html.index("function renderOperationalProfile"):html.index("function processSourceLabel")]


def test_dashboard_profile_chip_prefers_readiness_operational_context():
    html = Path("dashboard/index.html").read_text(encoding="utf-8")

    profile_area = html[html.index("function renderOperationalProfile"):html.index("function processSourceLabel")]

    assert "data.production_readiness_v2?.operational_context" in profile_area
    assert "profile_context_label" in profile_area
    assert "context_statement" in profile_area
    assert "profile_contract_valid" in profile_area
    assert "profile_contract_missing_fields" in profile_area


def test_dashboard_profile_panel_limits_decision_fields():
    html = Path("dashboard/index.html").read_text(encoding="utf-8")
    profile_area = html[html.index("function renderOperationalProfile"):html.index("function processSourceLabel")]

    assert "Contrato" in profile_area
    assert "TAC máx." in profile_area
    assert "DPI mín." in profile_area
    assert "Separaciones normales" in profile_area
    assert "Campos por revisar" in profile_area
