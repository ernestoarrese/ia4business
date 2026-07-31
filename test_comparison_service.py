from gate0.models.inspection_result import InspectionResult
from gate0.services.comparison_service import ComparisonService
from gate0.models.comparison_result import ComparisonResult


def test_candidate_pair_detection():
    service = ComparisonService()

    pairs = service.find_candidate_pairs([
        {"name": "design.ai", "extension": ".ai"},
        {"name": "design.pdf", "extension": ".pdf"},
    ])

    assert len(pairs) == 1
    assert pairs[0]["confidence"] == "Alta"


def test_compare_inspection_results_ok():
    service = ComparisonService()

    left = InspectionResult(
        file="design.ai",
        pages=1,
        page_boxes=[{"width_mm": 100, "height_mm": 200}],
        live_fonts=[{"font_name": "Frutiger"}],
        separations=["PANTONE 485 C"],
    )

    right = InspectionResult(
        file="design.pdf",
        pages=1,
        page_boxes=[{"width_mm": 100, "height_mm": 200}],
        live_fonts=[{"font_name": "Frutiger"}],
        separations=["PANTONE 485 C"],
    )

    result = service.compare_inspection_results(left, right)

    assert isinstance(result, ComparisonResult)
    assert result.overall_status == "OK"
    assert result.score == 100


def test_compare_inspection_results_high_risk_when_page_count_changes():
    service = ComparisonService()

    left = InspectionResult(file="design.ai", pages=1)
    right = InspectionResult(file="design.pdf", pages=2)

    result = service.compare_inspection_results(left, right)

    assert result.overall_status == "HIGH_RISK"
    assert result.decision == "No liberar sin revisión técnica"
    assert result.score < 100


def test_font_subset_prefix_is_ignored_in_comparison():
    service = ComparisonService()

    left = InspectionResult(
        file="design.ai",
        pages=1,
        live_fonts=[
            {"font_name": "MYVNQU+FrutigerLTStd-BoldCn"},
            {"font_name": "MYVNQU+HelveticaNeueLTStd-BdCn"},
        ],
    )

    right = InspectionResult(
        file="design.pdf",
        pages=1,
        live_fonts=[
            {"font_name": "WVRVAA+FrutigerLTStd-BoldCn"},
            {"font_name": "WVRVAA+HelveticaNeueLTStd-BdCn"},
        ],
    )

    result = service.compare_inspection_results(left, right)

    font_check = next(c for c in result.checks if c.get("category") == "Fonts")

    assert font_check["status"] == "OK"
    assert "FrutigerLTStd-BoldCn" in font_check["left"]
    assert "WVRVAA+" not in str(font_check["right"])


def test_comparison_result_v2_has_prepress_decision_for_ok_result():
    service = ComparisonService()

    left = InspectionResult(
        file="design.ai",
        pages=1,
        page_boxes=[{"width_mm": 100, "height_mm": 200}],
        live_fonts=[{"font_name": "Frutiger"}],
        separations=["PANTONE 485 C"],
    )

    right = InspectionResult(
        file="design.pdf",
        pages=1,
        page_boxes=[{"width_mm": 100, "height_mm": 200}],
        live_fonts=[{"font_name": "Frutiger"}],
        separations=["PANTONE 485 C"],
    )

    result = service.compare_inspection_results(left, right)

    assert result.overall_status == "OK"
    assert result.decision == "Consistencia estructural aceptable"
    assert result.recommendation
    assert result.metadata["mode"] == "structural_v2_guardrails"


def test_comparison_result_v2_groups_checks_by_category():
    service = ComparisonService()

    left = InspectionResult(
        file="design.ai",
        pages=1,
        page_boxes=[{"width_mm": 100, "height_mm": 200}],
        live_fonts=[{"font_name": "Frutiger"}],
        separations=["PANTONE 485 C"],
    )

    right = InspectionResult(
        file="design.pdf",
        pages=1,
        page_boxes=[{"width_mm": 100, "height_mm": 200}],
        live_fonts=[{"font_name": "Frutiger"}],
        separations=["PANTONE 485 C"],
    )

    result = service.compare_inspection_results(left, right)

    categories = {check["category"] for check in result.checks}

    assert "Pages" in categories
    assert "Fonts" in categories
    assert "Structure" in categories


def test_comparison_result_v2_high_risk_when_page_size_changes():
    service = ComparisonService()

    left = InspectionResult(
        file="design.ai",
        pages=1,
        page_boxes=[{"width_mm": 100, "height_mm": 200}],
    )

    right = InspectionResult(
        file="design.pdf",
        pages=1,
        page_boxes=[{"width_mm": 120, "height_mm": 200}],
    )

    result = service.compare_inspection_results(left, right)

    assert result.overall_status == "HIGH_RISK"
    assert result.decision == "No liberar sin revisión técnica"
    assert any(check["status"] == "CRITICAL" for check in result.checks)


def test_comparison_result_v2_review_required_when_separations_change():
    service = ComparisonService()

    left = InspectionResult(
        file="design.ai",
        pages=1,
        page_boxes=[{"width_mm": 100, "height_mm": 200}],
        separations=["PANTONE 485 C", "White"],
    )

    right = InspectionResult(
        file="design.pdf",
        pages=1,
        page_boxes=[{"width_mm": 100, "height_mm": 200}],
        separations=["PANTONE 485 C"],
    )

    result = service.compare_inspection_results(left, right)

    assert result.overall_status == "REVIEW_REQUIRED"
    assert result.decision == "Revisar diferencias antes de liberar"
    assert result.score < 100



def test_comparison_result_v2_not_ok_when_required_data_is_missing():
    service = ComparisonService()

    left = InspectionResult(file="design.ai", pages=1)
    right = InspectionResult(file="design.pdf", pages=1)

    result = service.compare_inspection_results(left, right)

    assert result.overall_status == "REVIEW_REQUIRED"
    assert result.score < 100
    assert result.metadata["not_evaluated_count"] > 0
    assert any(check["status"] == "NOT_EVALUATED" for check in result.checks)
    assert "no tuvo datos suficientes" in result.summary.lower()


def test_comparison_result_v2_high_risk_when_second_page_size_changes():
    service = ComparisonService()

    left = InspectionResult(
        file="design.ai",
        pages=2,
        page_boxes=[
            {"page": 1, "width_mm": 100, "height_mm": 200},
            {"page": 2, "width_mm": 100, "height_mm": 200},
        ],
        live_fonts=[{"font_name": "Frutiger"}],
        separations=["PANTONE 485 C"],
    )

    right = InspectionResult(
        file="design.pdf",
        pages=2,
        page_boxes=[
            {"page": 1, "width_mm": 100, "height_mm": 200},
            {"page": 2, "width_mm": 120, "height_mm": 200},
        ],
        live_fonts=[{"font_name": "Frutiger"}],
        separations=["PANTONE 485 C"],
    )

    result = service.compare_inspection_results(left, right)

    page_size_check = next(c for c in result.checks if c["name"] == "Page size")

    assert result.overall_status == "HIGH_RISK"
    assert page_size_check["status"] == "CRITICAL"
    assert page_size_check["metadata"]["mismatches"][0]["page"] == 2


def test_comparison_result_v2_warning_only_does_not_claim_critical_differences():
    service = ComparisonService()

    left = InspectionResult(
        file="design.ai",
        pages=1,
        page_boxes=[{"width_mm": 100, "height_mm": 200}],
        live_fonts=[{"font_name": "Frutiger"}],
        separations=["PANTONE 485 C", "White"],
    )

    right = InspectionResult(
        file="design.pdf",
        pages=1,
        page_boxes=[{"width_mm": 100, "height_mm": 200}],
        live_fonts=[{"font_name": "Helvetica"}],
        separations=["PANTONE 485 C"],
    )

    result = service.compare_inspection_results(left, right)

    assert result.metadata["critical_count"] == 0
    assert result.metadata["warning_count"] == 2
    assert result.overall_status == "REVIEW_REQUIRED"
    assert "críticas" not in result.summary.lower()
