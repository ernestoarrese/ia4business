import re
import shutil
import subprocess
from pathlib import Path


HTML = Path("dashboard/index.html").read_text(encoding="utf-8")


def _dashboard_js():
    scripts = re.findall(
        r"<script[^>]*>(.*?)</script>",
        HTML,
        flags=re.S | re.I,
    )
    assert scripts, "dashboard/index.html debe contener al menos un script"
    return "\n\n".join(scripts)


JS = _dashboard_js()


def test_dashboard_javascript_syntax_is_valid_when_node_is_available(tmp_path):
    node = shutil.which("node")
    if not node:
        return

    js_path = tmp_path / "dashboard_script_check.js"
    js_path.write_text(JS, encoding="utf-8")

    result = subprocess.run(
        [node, "--check", str(js_path)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_dashboard_current_compact_copy_is_protected():
    expected = [
        "Riesgos principales",
        "Detalle del riesgo",
        "Archivo PDF analizado",
        "Riesgo",
        "Área útil",
        "Criterio",
        "Impacto",
        "Acción sugerida",
        "Selecciona un riesgo para ver prioridad, evidencia y acción sugerida.",
    ]

    for text in expected:
        assert text in HTML


def test_dashboard_old_redundant_copy_does_not_return():
    forbidden = [
        ">Top Risks<",
        ">Riesgo seleccionado<",
        'title="PDF analizado"',
        "Vista del archivo",
        "Preview de producción",
        "Selecciona un riesgo para ver comentario experto, evidencia e impacto.",
        "<b>Tipo de riesgo</b>",
        "<b>Área imprimible</b>",
        "<b>Umbral / criterio</b>",
        "<b>Por qué importa</b>",
        "<b>Qué hacer</b>",
    ]

    for text in forbidden:
        assert text not in HTML


def test_dashboard_pr2_drilldown_hooks_are_present():
    assert "data-pr2-check" in HTML
    assert "data-pr2-title" in HTML
    assert "selectProductionReadinessRisk(" in HTML
    assert "pr2FindRiskIndex" in JS


def test_dashboard_visual_navigation_support_is_present():
    assert "visualNavigationItems" in JS
    assert "visual_zones" in JS
    assert "renderOccurrenceNav" in JS
    assert "riskDataForActiveOccurrence" in JS
    assert "changeRiskOccurrence" in JS


def test_dashboard_separation_usage_inline_support_is_present():
    assert "renderSeparationUsageV2" in JS
    assert "separationUsageSignalMap" in JS
    assert "renderSeparationUsageSignal" in JS
    assert "sep-signal" in HTML
