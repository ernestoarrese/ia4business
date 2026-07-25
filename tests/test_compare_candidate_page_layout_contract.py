from pathlib import Path


def test_compare_candidate_page_has_file_layout_safeguards():
    app = Path("app.py").read_text(encoding="utf-8")

    assert "def _compare_display_filename" in app
    assert "Path(str(value or \"\")).name" in app
    assert "Sprint 27A.1 — Compare file cards responsive fix" in app
    assert "overflow-wrap:anywhere" in app
    assert "table-layout:fixed" in app
