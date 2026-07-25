from gate0_check import check_font_embedding
from business_rules import evaluate_font_not_embedded


def test_font_not_embedded_finding_adds_evidence_depth():
    findings = check_font_embedding([
        {
            "page": 1,
            "font_name": "Helvetica",
            "font_name_raw": "F1",
            "font_type": "Type1",
            "font_ext": "n/a",
            "embedded": False,
        }
    ])

    assert len(findings) == 1

    item = findings[0]
    assert item["check"] == "FONT_NOT_EMBEDDED"
    assert item["page"] == 1
    assert item["font_name"] == "Helvetica"
    assert item["font_name_raw"] == "F1"
    assert item["font_type"] == "Type1"
    assert item["font_ext"] == "n/a"
    assert item["embedded"] is False
    assert item["font_embedding_status"] == "NOT_EMBEDDED"
    assert item["detection_method"] == "PYMUPDF_PAGE_GET_FONTS"
    assert item["text_association_status"] == "NOT_ASSOCIATED_IN_FONT_V1"
    assert item["affected_text_available"] is False
    assert item["bbox_available"] is False
    assert item["requires_manual_text_review"] is True


def test_font_not_embedded_business_reason_includes_font_name_and_limitation():
    result = evaluate_font_not_embedded(
        {
            "check": "FONT_NOT_EMBEDDED",
            "font_name": "Helvetica",
            "font_type": "Type1",
            "text_association_status": "NOT_ASSOCIATED_IN_FONT_V1",
        },
        {},
    )

    severity = result.get("business_severity") or result.get("severity")

    assert severity == "CRITICAL"
    assert result.get("score_weight", 0) >= 25
    assert "Helvetica" in result.get("risk_reason", "")
    assert "qué texto específico" in result.get("risk_reason", "")
