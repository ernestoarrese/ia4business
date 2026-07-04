from check_intelligence import (
    get_check_intelligence,
    enrich_finding_with_check_intelligence,
    enrich_findings_with_check_intelligence,
)


def test_get_check_intelligence_for_barcode():
    data = get_check_intelligence("BARCODE_RISK")

    assert "barcode" in data["criteria"].lower()
    assert data["fix_type"] == "assisted"
    assert "gs1" in data["current_limitation"].lower()


def test_enrich_finding_adds_criteria_context_and_fix_type():
    finding = {
        "check": "SMALL_TEXT_RISK",
        "business_severity": "WARNING",
    }

    enriched = enrich_finding_with_check_intelligence(finding)

    assert enriched["criteria"]
    assert enriched["operational_context"]
    assert enriched["fix_type"] == "assisted"


def test_enrich_findings_preserves_existing_fields():
    findings = [
        {
            "check": "FONT_NOT_EMBEDDED",
            "criteria": "Custom criteria",
            "business_severity": "CRITICAL",
        }
    ]

    enriched = enrich_findings_with_check_intelligence(findings)

    assert enriched[0]["criteria"] == "Custom criteria"
    assert enriched[0]["fix_type"] == "manual"
