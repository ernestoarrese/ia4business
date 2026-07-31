from pathlib import Path

from app import _render_printable_report_html, _shareable_report_status_class


def _summary():
    return {
        "file": "sample.pdf",
        "client": "Cliente Demo",
        "pages": 2,
        "analyzed_at": "2026-07-31 18:00:00",
        "status": "REVIEW_REQUIRED",
        "status_label": "Requiere revisión",
        "decision": "HOLD",
        "decision_label": "Retener para revisión",
        "score": 82,
        "answer": "Requiere revisión antes de liberar.",
        "main_reason": "El archivo tiene riesgos que deben revisarse.",
        "recommended_action": "Revisar sobreimpresión y texto pequeño.",
        "operational_context": {
            "profile_context_label": "flexo / PET_BOPP",
            "profile_contract_valid": True,
            "context_statement": "Evaluado contra perfil productivo flexo / PET_BOPP.",
            "tac_max_percent": 280,
            "image_minimum_dpi": 250,
            "separation_normal_max_printable": 8,
        },
        "top_risks": [
            {
                "title": "Validar sobreimpresión",
                "severity": "WARNING",
                "reason": "Sobreimpresión detectada.",
                "action": "Abrir con Overprint Preview.",
            }
        ],
        "limitations": [
            "Gate0 no reemplaza el criterio final de preprensa.",
            "El detalle técnico permanece en el dashboard.",
        ],
    }


def test_app_defines_printable_report_route_and_uses_presenter():
    app_py = Path("app.py").read_text(encoding="utf-8")

    assert 'from gate0.services.shareable_report_presenter import build_shareable_report_summary' in app_py
    assert '@app.get("/report/print", response_class=HTMLResponse)' in app_py
    assert "build_shareable_report_summary(report_data)" in app_py
    assert "_load_report_data_for_print" in app_py


def test_printable_report_html_is_executive_and_printable():
    output = _render_printable_report_html(_summary())

    assert "Reporte ejecutivo" in output
    assert "Retener para revisión" in output
    assert "82" in output
    assert "flexo / PET_BOPP" in output
    assert "TAC máx." in output
    assert "DPI mín." in output
    assert "Separaciones normales" in output
    assert "Validar sobreimpresión" in output
    assert "Imprimir / guardar PDF" in output


def test_printable_report_html_does_not_duplicate_dashboard():
    output = _render_printable_report_html(_summary())

    assert "<iframe" not in output
    assert "feedback" not in output.lower()
    assert "risk-preview" not in output
    assert "api/pdf" not in output
    assert "gate0_report.json" not in output


def test_printable_report_status_classes_are_stable():
    assert _shareable_report_status_class("READY") == "ok"
    assert _shareable_report_status_class("READY_WITH_NOTES") == "ok"
    assert _shareable_report_status_class("REVIEW_REQUIRED") == "review"
    assert _shareable_report_status_class("HIGH_RISK") == "risk"
    assert _shareable_report_status_class("NO_GO") == "risk"
