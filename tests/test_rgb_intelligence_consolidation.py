from check_intelligence import get_check_intelligence


def test_rgb_intelligence_preserves_prepress_guidance():
    data = get_check_intelligence("RGB_OBJECT")

    assert "rgb" in data["criteria"].lower()
    assert "impresión" in data["operational_context"].lower() or "impresion" in data["operational_context"].lower()
    assert "color" in data["possible_impact"].lower()
    assert "perfil" in data["conversion_guidance"].lower()
    assert "conversiones automáticas" in data["color_management_guidance"].lower() or "conversiones automaticas" in data["color_management_guidance"].lower()
    assert "no garantiza" in data["do_not_claim"].lower()


def test_rgb_intelligence_is_assisted_not_autofix():
    data = get_check_intelligence("RGB_OBJECT")

    assert data["fix_type"] == "assisted"
