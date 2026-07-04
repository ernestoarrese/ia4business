from check_intelligence import get_check_intelligence


def test_low_image_intelligence_preserves_prepress_guidance():
    data = get_check_intelligence("LOW_IMAGE_RESOLUTION")

    assert "resolución efectiva" in data["criteria"].lower() or "resolucion efectiva" in data["criteria"].lower()
    assert "pixelada" in data["operational_context"].lower()
    assert "calidad" in data["possible_impact"].lower()
    assert "rol de la imagen" in data["current_limitation"].lower()
    assert "dpi efectivo" in data["effective_dpi_guidance"].lower()
    assert "área" in data["area_guidance"].lower() or "area" in data["area_guidance"].lower()
    assert "barcode" in data["barcode_dedupe_guidance"].lower()
    assert "no certifica" in data["do_not_claim"].lower()


def test_low_image_intelligence_is_assisted_not_autofix():
    data = get_check_intelligence("LOW_IMAGE_RESOLUTION")

    assert data["fix_type"] == "assisted"
