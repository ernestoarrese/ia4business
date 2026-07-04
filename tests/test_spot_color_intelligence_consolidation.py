from check_intelligence import get_check_intelligence


def test_spot_color_intelligence_preserves_prepress_guidance():
    data = get_check_intelligence("SPOT_COLOR_RISK")

    assert "spot" in data["criteria"].lower()
    assert "blanco" in data["white_ink_guidance"].lower()
    assert "genéricos" in data["generic_name_guidance"].lower() or "genericos" in data["generic_name_guidance"].lower()
    assert "485c" in data["duplicate_guidance"].lower()
    assert "técnicas" in data["technical_separation_guidance"].lower() or "tecnicas" in data["technical_separation_guidance"].lower()
    assert "racionalizarse" in data["rationalization_guidance"].lower()
    assert "no decide automáticamente" in data["do_not_claim"].lower()


def test_spot_color_intelligence_is_assisted_not_autofix():
    data = get_check_intelligence("SPOT_COLOR_RISK")

    assert data["fix_type"] == "assisted"
