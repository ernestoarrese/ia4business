from check_intelligence import get_check_intelligence


def test_barcode_intelligence_preserves_prepress_guidance():
    data = get_check_intelligence("BARCODE_RISK")

    assert "leerse" in data["operational_context"].lower()
    assert "pixelado" in data["possible_impact"].lower()
    assert "registro" in data["possible_impact"].lower()
    assert "una sola tinta" in data["single_ink_guidance"].lower()
    assert "gs1" in data["current_limitation"].lower()
    assert "no certifica" in data["do_not_claim"].lower()


def test_barcode_intelligence_is_assisted_not_autofix():
    data = get_check_intelligence("BARCODE_RISK")

    assert data["fix_type"] == "assisted"
