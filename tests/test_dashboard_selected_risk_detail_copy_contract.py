from pathlib import Path


SOURCE = Path("dashboard/index.html").read_text(encoding="utf-8")


def test_selected_risk_detail_uses_compact_labels():
    assert "<b>Riesgo</b>" in SOURCE
    assert "<b>Área útil</b>" in SOURCE
    assert "<b>Criterio</b>" in SOURCE
    assert "<b>Impacto</b>" in SOURCE
    assert "<b>Acción sugerida</b>" in SOURCE

    assert "<b>Tipo de riesgo</b>" not in SOURCE
    assert "<b>Área imprimible</b>" not in SOURCE
    assert "<b>Umbral / criterio</b>" not in SOURCE
    assert "<b>Por qué importa</b>" not in SOURCE
    assert "<b>Qué hacer</b>" not in SOURCE


def test_selected_risk_empty_state_is_compact_and_action_oriented():
    assert "Selecciona un riesgo para ver prioridad, evidencia y acción sugerida." in SOURCE
    assert "Selecciona un riesgo para ver comentario experto, evidencia e impacto." not in SOURCE
