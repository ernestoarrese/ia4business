from gate0.models.comparison_result import ComparisonResult
from gate0.services.compare_executive_presenter import build_compare_executive_summary


def test_compare_executive_summary_reports_high_confidence_for_full_ok():
    result = ComparisonResult(
        left_file="design.ai",
        right_file="design.pdf",
        overall_status="OK",
        score=100,
        decision="Consistencia estructural aceptable",
        summary="No se detectaron diferencias estructurales relevantes.",
        recommendation="Puede continuar.",
        checks=[
            {"category": "Pages", "name": "Page count", "status": "OK", "left": 1, "right": 1, "message": ""},
            {"category": "Pages", "name": "Page size", "status": "OK", "left": [(100, 200)], "right": [(100, 200)], "message": ""},
            {"category": "Fonts", "name": "Live fonts", "status": "OK", "left": ["Frutiger"], "right": ["Frutiger"], "message": ""},
            {"category": "Structure", "name": "Separations", "status": "OK", "left": ["White"], "right": ["White"], "message": ""},
        ],
        metadata={"critical_count": 0, "warning_count": 0, "not_evaluated_count": 0},
    )

    executive = build_compare_executive_summary(result)

    assert executive["confidence"] == "Alta"
    assert executive["coverage_percent"] == 100
    assert executive["top_differences"] == []
    assert executive["next_action"] == "Puede continuar el flujo normal, manteniendo revisión visual habitual."


def test_compare_executive_summary_prioritizes_critical_warning_and_not_evaluated():
    result = ComparisonResult(
        left_file="design.ai",
        right_file="design.pdf",
        overall_status="HIGH_RISK",
        score=45,
        checks=[
            {
                "category": "Structure",
                "name": "Separations",
                "status": "WARNING",
                "left": ["White"],
                "right": [],
                "message": "Las separaciones no coinciden.",
            },
            {
                "category": "Fonts",
                "name": "Live fonts",
                "status": "NOT_EVALUATED",
                "left": [],
                "right": [],
                "message": "No hay fuentes vivas evaluables.",
            },
            {
                "category": "Pages",
                "name": "Page size",
                "status": "CRITICAL",
                "left": [(100, 200)],
                "right": [(120, 200)],
                "message": "El tamaño de una o más páginas cambió.",
            },
        ],
        metadata={"critical_count": 1, "warning_count": 1, "not_evaluated_count": 1},
    )

    executive = build_compare_executive_summary(result)

    assert executive["top_differences"][0]["status"] == "CRITICAL"
    assert executive["top_differences"][1]["status"] == "WARNING"
    assert executive["top_differences"][2]["status"] == "NOT_EVALUATED"
    assert executive["critical_count"] == 1
    assert executive["warning_count"] == 1
    assert executive["not_evaluated_count"] == 1
    assert executive["next_action"] == "No liberar. Revisar las diferencias críticas contra el arte aprobado."


def test_compare_executive_summary_marks_low_confidence_when_checks_are_not_evaluated():
    result = ComparisonResult(
        left_file="design.ai",
        right_file="design.pdf",
        overall_status="REVIEW_REQUIRED",
        score=75,
        checks=[
            {"category": "Pages", "name": "Page count", "status": "OK", "left": 1, "right": 1, "message": ""},
            {"category": "Pages", "name": "Page size", "status": "NOT_EVALUATED", "left": [], "right": [], "message": "No hay datos."},
            {"category": "Fonts", "name": "Live fonts", "status": "NOT_EVALUATED", "left": [], "right": [], "message": "No hay datos."},
            {"category": "Structure", "name": "Separations", "status": "NOT_EVALUATED", "left": [], "right": [], "message": "No hay datos."},
        ],
        metadata={"critical_count": 0, "warning_count": 0, "not_evaluated_count": 3},
    )

    executive = build_compare_executive_summary(result)

    assert executive["coverage_percent"] == 25
    assert executive["confidence"] == "Baja"
    assert len(executive["not_evaluated_items"]) == 3
    assert "No interpretar como OK" in executive["next_action"]


def test_compare_executive_summary_includes_explicit_visual_limitation():
    result = ComparisonResult(
        left_file="design.ai",
        right_file="design.pdf",
        overall_status="OK",
        score=100,
        checks=[],
        metadata={},
    )

    executive = build_compare_executive_summary(result)

    assert "Comparación estructural" in executive["limitation"]
    assert "No valida equivalencia visual píxel a píxel" in executive["limitation"]
