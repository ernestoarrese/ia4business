from check_intelligence import get_check_intelligence


def test_separation_count_intelligence_preserves_prepress_guidance():
    data = get_check_intelligence("SEPARATION_COUNT_RISK")

    assert "separaciones imprimibles" in data["criteria"].lower()
    assert "complejidad" in data["operational_context"].lower()
    assert "prensa" in data["press_capacity_guidance"].lower()
    assert "consolidarse" in data["rationalization_guidance"].lower()
    assert "técnicas" in data["technical_separation_guidance"].lower() or "tecnicas" in data["technical_separation_guidance"].lower()
    assert "no decide automáticamente" in data["do_not_claim"].lower()


def test_separation_count_intelligence_is_assisted_not_autofix():
    data = get_check_intelligence("SEPARATION_COUNT_RISK")

    assert data["fix_type"] == "assisted"
