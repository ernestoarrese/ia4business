from business_rules import build_business_assessment


def find_check(result, check):
    for item in result["priority_findings"]:
        if item["check"] == check:
            return item
    return None


def test_rgb_large_is_critical():
    result = build_business_assessment([
        {"check": "RGB_OBJECT", "object_area_percent": 18, "is_printable": True}
    ])
    item = find_check(result, "RGB_OBJECT")
    assert item["business_severity"] == "CRITICAL"


def test_low_image_220_large_is_critical():
    result = build_business_assessment([
        {"check": "LOW_IMAGE_RESOLUTION", "effective_dpi": 220, "object_area_percent": 15}
    ])
    item = find_check(result, "LOW_IMAGE_RESOLUTION")
    assert item["business_severity"] == "CRITICAL"


def test_tac_excess_over_40_is_critical_even_small():
    result = build_business_assessment([
        {"check": "HIGH_TAC_RISK", "detected_tac": 321, "object_area_percent": 0.5}
    ])
    item = find_check(result, "HIGH_TAC_RISK")
    assert item["business_severity"] == "CRITICAL"


def test_overprint_white_same_page_warning():
    result = build_business_assessment([
        {
            "check": "OVERPRINT_RISK",
            "has_overprint_fill": True,
            "white_ink_detected": True,
            "object_area_percent": 100
        }
    ])
    item = find_check(result, "OVERPRINT_RISK")
    assert item["business_severity"] == "WARNING"


def test_separation_count_17_critical():
    result = build_business_assessment([
        {"check": "SEPARATION_COUNT_RISK", "printable_separation_count": 17}
    ])
    item = find_check(result, "SEPARATION_COUNT_RISK")
    assert item["business_severity"] == "CRITICAL"


def test_pdf_structure_empty_critical():
    result = build_business_assessment([
        {"check": "PDF_STRUCTURE_RISK", "severity": "HIGH"}
    ])
    item = find_check(result, "PDF_STRUCTURE_RISK")
    assert item["business_severity"] == "CRITICAL"
