from gate0_check import build_separation_usage_v2


def test_separation_usage_v2_is_informational_and_does_not_reclassify():
    separation_summary = {
        "operational_total": 2,
        "items": [
            {
                "name": "PANTONE 485 C",
                "type": "Spot",
                "original_type": "Spot",
                "is_printable": True,
                "classification_source": "NAME",
                "is_generic": False,
            },
            {
                "name": "Plano",
                "type": "Plano",
                "original_type": "Plano",
                "is_printable": False,
                "classification_source": "NAME",
                "is_generic": False,
            },
        ],
    }

    capability = {
        "can_map_separation_resources": True,
        "can_compute_bbox_by_separation": False,
        "safe_for_reclassification": False,
        "usage_token_count": 1,
        "colorspace_selector_count": 1,
        "resource_separation_mentions": {
            "PANTONE 485 C": 1,
        },
    }

    result = build_separation_usage_v2(separation_summary, capability)

    assert result["version"] == "v2_foundation"
    assert result["safe_for_operational_decision"] is False
    assert result["safe_for_reclassification"] is False
    assert result["can_compute_bbox_by_separation"] is False
    assert result["summary"]["detected_separations"] == 2
    assert result["summary"]["separations_with_usage_signals"] == 1
    assert result["summary"]["separations_without_usage_signals"] == 1

    pantone = result["items"][0]
    assert pantone["name"] == "PANTONE 485 C"
    assert pantone["type"] == "Spot"
    assert pantone["is_printable"] is True
    assert pantone["usage_signal_status"] == "RESOURCE_SIGNAL_FOUND"
    assert pantone["decision_impact"] == "INFORMATIONAL_ONLY"
    assert pantone["operational_count_impact"] == "NO_IMPACT_IN_V2_FOUNDATION"

    plano = result["items"][1]
    assert plano["name"] == "Plano"
    assert plano["type"] == "Plano"
    assert plano["is_printable"] is False
    assert plano["usage_signal_status"] == "NO_DIRECT_RESOURCE_SIGNAL"


def test_separation_usage_v2_compact_lookup_matches_underscore_names():
    result = build_separation_usage_v2(
        {
            "items": [
                {
                    "name": "PANTONE 485 C",
                    "type": "Spot",
                    "is_printable": True,
                    "classification_source": "NAME",
                }
            ]
        },
        {
            "can_map_separation_resources": True,
            "resource_separation_mentions": {
                "PANTONE_485_C": 2,
            },
        },
    )

    item = result["items"][0]
    assert item["usage_signal_status"] == "RESOURCE_SIGNAL_FOUND"
    assert item["resource_mention_count"] == 2


def test_separation_usage_v2_handles_missing_capability_safely():
    result = build_separation_usage_v2(
        {
            "items": [
                {
                    "name": "White",
                    "type": "Blanco",
                    "is_printable": True,
                    "classification_source": "NAME",
                }
            ]
        },
        {},
    )

    assert result["safe_for_operational_decision"] is False
    assert result["items"][0]["usage_signal_status"] == "USAGE_SIGNAL_NOT_AVAILABLE"
    assert result["items"][0]["bbox_available"] is False
