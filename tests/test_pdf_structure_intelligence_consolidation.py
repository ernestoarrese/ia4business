from check_intelligence import get_check_intelligence


def test_pdf_structure_intelligence_preserves_prepress_guidance():
    data = get_check_intelligence("PDF_STRUCTURE_RISK")

    assert "páginas vacías" in data["criteria"].lower() or "paginas vacías" in data["criteria"].lower()
    assert "rip" in data["operational_context"].lower()
    assert "fallo" in data["possible_impact"].lower()
    assert "páginas vacías" in data["empty_page_guidance"].lower() or "paginas vacías" in data["empty_page_guidance"].lower()
    assert "objetos" in data["complexity_guidance"].lower()
    assert "reconstruir" in data["workflow_guidance"].lower()
    assert "no corrige" in data["do_not_claim"].lower()


def test_pdf_structure_intelligence_is_manual():
    data = get_check_intelligence("PDF_STRUCTURE_RISK")

    assert data["fix_type"] == "manual"
