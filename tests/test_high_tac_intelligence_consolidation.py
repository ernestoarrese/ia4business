from check_intelligence import get_check_intelligence


def test_high_tac_intelligence_preserves_prepress_guidance():
    data = get_check_intelligence("HIGH_TAC_RISK")

    assert "cobertura total" in data["criteria"].lower()
    assert "secado" in data["operational_context"].lower()
    assert "repinte" in data["possible_impact"].lower()
    assert "área" in data["area_guidance"].lower() or "area" in data["area_guidance"].lower()
    assert "negro enriquecido" in data["rich_black_guidance"].lower()
    assert "perfil operativo" in data["profile_guidance"].lower()
    assert "no corrige" in data["do_not_claim"].lower()


def test_high_tac_intelligence_is_assisted_not_autofix():
    data = get_check_intelligence("HIGH_TAC_RISK")

    assert data["fix_type"] == "assisted"
