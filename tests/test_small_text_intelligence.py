import fitz

from gate0_check import check_small_text
from business_rules import enrich_finding
from expert_comment_engine import build_expert_insight


def test_small_text_detector_finds_text_under_5pt():
    doc = fitz.open()
    page = doc.new_page(width=500, height=500)

    page.insert_text((50, 50), "tiny 3pt", fontsize=3)
    page.insert_text((50, 80), "small 4.5pt", fontsize=4.5)
    page.insert_text((50, 110), "normal 6pt", fontsize=6)

    findings = check_small_text(page, page_number=1)

    sizes = [f["font_size_pt"] for f in findings]

    assert any(size < 4 for size in sizes)
    assert any(4 <= size < 5 for size in sizes)
    assert all(size < 5 for size in sizes)
    assert all(f["check"] == "SMALL_TEXT_RISK" for f in findings)
    assert all(f["page"] == 1 for f in findings)
    assert all("bbox" in f for f in findings)


def test_small_text_business_rule_critical_under_4pt():
    finding = {
        "check": "SMALL_TEXT_RISK",
        "page": 1,
        "font_size_pt": 3.5,
        "text_height_mm": 1.23,
        "sample_text": "legal tiny text",
    }

    result = enrich_finding(finding, profile={})

    assert result["business_severity"] == "CRITICAL"
    assert result["risk_area"] == "Texto / Legibilidad"
    assert "legibilidad" in result["action"].lower()


def test_small_text_business_rule_warning_under_5pt():
    finding = {
        "check": "SMALL_TEXT_RISK",
        "page": 1,
        "font_size_pt": 4.5,
        "text_height_mm": 1.59,
        "sample_text": "small legal text",
    }

    result = enrich_finding(finding, profile={})

    assert result["business_severity"] == "WARNING"


def test_small_text_expert_comment():
    risk = {
        "check": "SMALL_TEXT_RISK",
        "business_severity": "WARNING",
        "page": 1,
        "font_size_pt": 4.5,
        "text_height_mm": 1.59,
        "sample_text": "small legal text",
    }

    report = {
        "business_assessment": {
            "priority_findings": [risk]
        }
    }

    insight = build_expert_insight(risk, report)

    assert insight["evidence"]["rule_applied"] == "SMALL_TEXT_RISK"
    assert "legibilidad" in insight["brief_comment"].lower()
