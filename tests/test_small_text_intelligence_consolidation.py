from check_intelligence import get_check_intelligence


def test_small_text_intelligence_preserves_prepress_guidance():
    data = get_check_intelligence("SMALL_TEXT_RISK")

    assert "perfil operativo" in data["criteria"].lower()
    assert "legibilidad" in data["operational_context"].lower()
    assert "legal" in data["possible_impact"].lower()
    assert "negativo" in data["negative_text_guidance"].lower()
    assert "varias tintas" in data["multicolor_guidance"].lower()
    assert "no certifica" in data["do_not_claim"].lower()


def test_small_text_intelligence_is_assisted_not_autofix():
    data = get_check_intelligence("SMALL_TEXT_RISK")

    assert data["fix_type"] == "assisted"
