from gate0.services.shareable_report_presenter import build_shareable_report_summary


def _base_report():
    return {
        "file": "sample.pdf",
        "client": "Cliente Demo",
        "pages": 2,
        "analyzed_at": "2026-07-31 18:00:00",
        "production_readiness_v2": {
            "status": "REVIEW_REQUIRED",
            "legacy_decision": "HOLD",
            "score": 82,
            "answer": "Requiere revisión antes de liberar.",
            "main_reason": "El archivo tiene riesgos que deben revisarse.",
            "next_step": "Revisar sobreimpresión y texto pequeño.",
            "product_note": "Production Readiness v2 es una capa ejecutiva de decisión. No reemplaza aún el criterio final de preprensa.",
            "operational_context": {
                "profile_name": "flexo_pet_bopp_default",
                "profile_context_label": "flexo / PET_BOPP",
                "profile_contract_valid": True,
                "context_statement": "Evaluado contra perfil productivo flexo / PET_BOPP.",
                "key_thresholds": {
                    "tac_max_percent": 280,
                    "image_minimum_dpi": 250,
                    "separation_normal_max_printable": 8,
                },
            },
            "what_to_review_first": [
                {
                    "title": "Validar sobreimpresión",
                    "severity": "WARNING",
                    "reason": "Sobreimpresión detectada en área visual significativa.",
                    "action": "Abrir con Overprint Preview.",
                },
                {
                    "title": "Revisar texto pequeño",
                    "severity": "WARNING",
                    "reason": "Texto pequeño dentro del área imprimible.",
                    "action": "Validar legibilidad antes de liberar.",
                },
            ],
        },
    }


def test_shareable_report_summary_uses_production_readiness_decision_fields():
    summary = build_shareable_report_summary(_base_report())

    assert summary["version"] == "shareable_report_v1"
    assert summary["file"] == "sample.pdf"
    assert summary["client"] == "Cliente Demo"
    assert summary["status"] == "REVIEW_REQUIRED"
    assert summary["status_label"] == "Requiere revisión"
    assert summary["decision"] == "HOLD"
    assert summary["decision_label"] == "Retener para revisión"
    assert summary["score"] == 82
    assert summary["recommended_action"] == "Revisar sobreimpresión y texto pequeño."


def test_shareable_report_summary_exposes_compact_production_context():
    summary = build_shareable_report_summary(_base_report())
    context = summary["operational_context"]

    assert context["profile_name"] == "flexo_pet_bopp_default"
    assert context["profile_context_label"] == "flexo / PET_BOPP"
    assert context["profile_contract_valid"] is True
    assert context["context_statement"] == "Evaluado contra perfil productivo flexo / PET_BOPP."
    assert context["tac_max_percent"] == 280
    assert context["image_minimum_dpi"] == 250
    assert context["separation_normal_max_printable"] == 8


def test_shareable_report_summary_limits_top_risks_to_three():
    report = _base_report()
    report["production_readiness_v2"]["what_to_review_first"] = [
        {"title": "R1", "severity": "CRITICAL", "reason": "A", "action": "A1"},
        {"title": "R2", "severity": "WARNING", "reason": "B", "action": "B1"},
        {"title": "R3", "severity": "WARNING", "reason": "C", "action": "C1"},
        {"title": "R4", "severity": "INFO", "reason": "D", "action": "D1"},
    ]

    summary = build_shareable_report_summary(report)

    assert summary["risk_count"] == 3
    assert [risk["title"] for risk in summary["top_risks"]] == ["R1", "R2", "R3"]


def test_shareable_report_summary_falls_back_to_priority_findings():
    summary = build_shareable_report_summary({
        "file": "fallback.pdf",
        "readiness_assessment": {
            "readiness_status": "HIGH_RISK",
            "readiness_decision": "NO_GO",
            "readiness_score": 55,
        },
        "business_assessment": {
            "operational_profile": {
                "profile_name": "flexo_pet_bopp_default",
                "process": "flexo",
                "substrate_family": "PET_BOPP",
                "tac_max_percent": 280,
                "image_minimum_dpi": 250,
                "separation_normal_max_printable": 8,
            },
            "priority_findings": [
                {
                    "check": "FONT_NOT_EMBEDDED",
                    "business_severity": "CRITICAL",
                    "risk_reason": "Fuente crítica no embebida.",
                    "recommended_action": "Incrustar fuentes o convertir a curvas.",
                }
            ],
        },
    })

    assert summary["status"] == "HIGH_RISK"
    assert summary["decision"] == "NO_GO"
    assert summary["score"] == 55
    assert summary["operational_context"]["profile_context_label"] == "flexo / PET_BOPP"
    assert summary["top_risks"][0]["title"] == "FONT_NOT_EMBEDDED"
    assert summary["top_risks"][0]["severity"] == "CRITICAL"


def test_shareable_report_summary_keeps_limitations_concise():
    summary = build_shareable_report_summary(_base_report())

    assert len(summary["limitations"]) == 3
    assert any("criterio final de preprensa" in item for item in summary["limitations"])
    assert any("detalle técnico permanece en el dashboard" in item for item in summary["limitations"])
    assert any("no corrige automáticamente" in item.lower() for item in summary["limitations"])
