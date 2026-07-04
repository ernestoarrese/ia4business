from check_intelligence import get_check_intelligence


def test_overprint_intelligence_preserves_prepress_guidance():
    data = get_check_intelligence("OVERPRINT_RISK")

    assert "sobreimpresión" in data["criteria"].lower()
    assert "intención válida" in data["operational_context"].lower()
    assert "blanco" in data["possible_impact"].lower()
    assert "parcial" in data["current_limitation"].lower()
    assert "blanco" in data["white_overprint_guidance"].lower()
    assert "separaciones" in data["visual_validation_guidance"].lower()
    assert "intención" in data["intent_guidance"].lower()
    assert "no certifica" in data["do_not_claim"].lower()


def test_overprint_intelligence_is_assisted_not_autofix():
    data = get_check_intelligence("OVERPRINT_RISK")

    assert data["fix_type"] == "assisted"
