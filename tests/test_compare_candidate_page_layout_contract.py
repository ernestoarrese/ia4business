from pathlib import Path


def test_compare_candidate_page_has_file_layout_safeguards():
    app = Path("app.py").read_text(encoding="utf-8")

    assert "def _compare_display_filename" in app
    assert "Path(str(value or \"\")).name" in app
    assert "Sprint 27A.1 — Compare file cards responsive fix" in app
    assert "overflow-wrap:anywhere" in app
    assert "table-layout:fixed" in app


def test_compare_candidate_page_renders_executive_presenter_sections():
    app = Path("app.py").read_text(encoding="utf-8")
    presenter = Path("gate0/services/compare_executive_presenter.py").read_text(encoding="utf-8")

    assert "build_compare_executive_summary" in app
    assert "Confianza" in app
    assert "Top diferencias" in app
    assert "Checks no evaluados" in app
    assert "Limitación explícita" in app
    assert "executive.get(\"limitation\", \"\")" in app
    assert "No valida equivalencia visual píxel a píxel" in presenter
