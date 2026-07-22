from gate0.services.separation_intelligence_service import SeparationIntelligenceService


def test_separation_classification_contract_by_name():
    svc = SeparationIntelligenceService()

    cases = {
        "C": "Process",
        "M": "Process",
        "Y": "Process",
        "K": "Process",
        "Cyan": "Process",
        "Process Black": "Process",
        "C PERU": "Plano",
        "M PERU": "Plano",
        "Y PERU": "Plano",
        "K PERU": "Plano",
        "Dieline": "Plano",
        "Troquel": "Plano",
        "Sustrato": "Technical",
        "Substrate": "Technical",
        "Material": "Technical",
        "Materials": "Technical",
        "Materiales": "Technical",
        "Dimensions": "Technical",
        "Mechanical Artwork": "Technical",
        "Technical Drawing": "Technical",
        "White": "Blanco",
        "Blanco Calzado": "Blanco",
        "Opaque White": "Blanco",
        "Barniz Mate": "Barniz",
        "Varnish": "Barniz",
        "PANTONE 485 C": "Spot",
        "Spot 1": "Spot",
    }

    for name, expected in cases.items():
        assert svc.classify(name) == expected, name


def test_separation_summary_counts_printable_and_non_printable():
    svc = SeparationIntelligenceService()

    summary = svc.build_summary([
        "C",
        "M",
        "Y",
        "K",
        "PANTONE 485 C",
        "White",
        "Barniz Mate",
        "Material",
        "C PERU",
        "Technical Drawing",
    ])

    assert summary["detected_total"] == 10
    assert summary["calculated_operational_total"] == 7
    assert summary["operational_total"] == 7
    assert summary["process_count"] == 4
    assert summary["spot_count"] == 1
    assert summary["white_count"] == 1
    assert summary["varnish_count"] == 1
    assert summary["plano_count"] == 1
    assert summary["technical_count"] == 2
    assert summary["printable_spot_like_count"] == 3
    assert summary["non_printable_count"] == 3


def test_location_usage_outside_trimbox_can_downgrade_printable_to_technical():
    svc = SeparationIntelligenceService()

    summary = svc.build_summary(
        ["PANTONE 485 C"],
        usage_by_name={
            "PANTONE 485 C": {
                "has_confirmed_trimbox": True,
                "has_confirmed_bleedbox": False,
                "inside_trimbox_percent": 0,
                "outside_trimbox_percent": 100,
                "usage_source": "TEST_TRIMBOX",
            }
        },
    )

    item = summary["items"][0]

    assert item["original_type"] == "Spot"
    assert item["type"] == "Technical"
    assert item["is_printable"] is False
    assert item["classification_source"] == "LOCATION_CONFIRMED"
    assert item["usage_status"] == "NON_PRINTABLE_BY_LOCATION_CONFIRMED"
    assert summary["operational_total"] == 0


def test_location_usage_inside_bleedbox_stays_printable_even_if_outside_trimbox():
    svc = SeparationIntelligenceService()

    summary = svc.build_summary(
        ["PANTONE 485 C"],
        usage_by_name={
            "PANTONE 485 C": {
                "has_confirmed_trimbox": True,
                "has_confirmed_bleedbox": True,
                "inside_trimbox_percent": 0,
                "outside_trimbox_percent": 100,
                "inside_bleedbox_percent": 100,
                "outside_bleedbox_percent": 0,
                "usage_source": "TEST_BLEEDBOX",
            }
        },
    )

    item = summary["items"][0]

    assert item["original_type"] == "Spot"
    assert item["type"] == "Spot"
    assert item["is_printable"] is True
    assert item["classification_source"] == "NAME"
    assert item["usage_status"] == "PRINTABLE_IN_BLEED_OR_TRIM"
    assert summary["operational_total"] == 1
