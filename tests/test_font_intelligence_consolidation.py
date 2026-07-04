from check_intelligence import get_check_intelligence


def test_font_intelligence_preserves_prepress_guidance():
    data = get_check_intelligence("FONT_NOT_EMBEDDED")

    assert "fuentes no embebidas" in data["criteria"].lower()
    assert "sustituirse" in data["operational_context"].lower()
    assert "legal" in data["possible_impact"].lower()
    assert "curvas" in data["prepress_guidance"].lower()
    assert "textos legales" in data["legal_text_guidance"].lower()
    assert "no garantiza" in data["do_not_claim"].lower()


def test_font_intelligence_is_manual():
    data = get_check_intelligence("FONT_NOT_EMBEDDED")

    assert data["fix_type"] == "manual"
