from pathlib import Path


SOURCE = Path("dashboard/index.html").read_text(encoding="utf-8")


def test_dashboard_uses_spanish_compact_risk_labels():
    assert "Riesgos principales" in SOURCE
    assert "Detalle del riesgo" in SOURCE
    assert ">Top Risks<" not in SOURCE
    assert ">Riesgo seleccionado<" not in SOURCE


def test_dashboard_pdf_viewer_title_is_clear():
    assert 'title="Archivo PDF analizado"' in SOURCE
    assert 'title="PDF analizado"' not in SOURCE


def test_dashboard_does_not_show_known_redundant_viewer_copy():
    assert "Vista del archivo" not in SOURCE
    assert "Preview de producción" not in SOURCE
