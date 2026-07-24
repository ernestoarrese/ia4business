from readiness_summary import build_readiness_summary




def test_visual_zone_clustering_groups_close_small_text_occurrences():
    readiness = {
        "readiness_score": 82,
        "readiness_status": "REVIEW_REQUIRED",
        "readiness_decision": "HOLD",
    }

    findings = [
        {
            "check": "SMALL_TEXT_RISK",
            "severity": "WARNING",
            "business_severity": "WARNING",
            "priority": 2,
            "score_weight": 8,
            "page": 1,
            "bbox": [100, 100, 150, 112],
            "font_size_pt": 4.4,
            "risk_reason": "Texto pequeño.",
        },
        {
            "check": "SMALL_TEXT_RISK",
            "severity": "WARNING",
            "business_severity": "WARNING",
            "priority": 2,
            "score_weight": 8,
            "page": 1,
            "bbox": [154, 101, 205, 113],
            "font_size_pt": 4.5,
            "risk_reason": "Texto pequeño.",
        },
        {
            "check": "SMALL_TEXT_RISK",
            "severity": "WARNING",
            "business_severity": "WARNING",
            "priority": 2,
            "score_weight": 8,
            "page": 1,
            "bbox": [500, 500, 550, 512],
            "font_size_pt": 4.7,
            "risk_reason": "Texto pequeño.",
        },
    ]

    result = build_readiness_summary(readiness, findings)
    small_text = result["top_risks"][0]

    assert small_text["check"] == "SMALL_TEXT_RISK"
    assert small_text["occurrence_count"] == 3
    assert small_text["visual_zone_count"] == 2
    assert len(small_text["visual_zones"]) == 2
    assert small_text["visual_zones"][0]["occurrence_count"] == 2
    assert small_text["visual_zones"][1]["occurrence_count"] == 1


def test_visual_zone_clustering_does_not_apply_to_overprint():
    readiness = {
        "readiness_score": 82,
        "readiness_status": "REVIEW_REQUIRED",
        "readiness_decision": "HOLD",
    }

    findings = [
        {
            "check": "OVERPRINT_RISK",
            "severity": "WARNING",
            "business_severity": "WARNING",
            "priority": 2,
            "score_weight": 8,
            "page": 1,
            "bbox": [100, 100, 150, 112],
            "risk_reason": "Overprint.",
        },
        {
            "check": "OVERPRINT_RISK",
            "severity": "WARNING",
            "business_severity": "WARNING",
            "priority": 2,
            "score_weight": 8,
            "page": 1,
            "bbox": [154, 101, 205, 113],
            "risk_reason": "Overprint.",
        },
    ]

    result = build_readiness_summary(readiness, findings)
    overprint = result["top_risks"][0]

    assert overprint["check"] == "OVERPRINT_RISK"
    assert overprint["occurrence_count"] == 2
    assert "visual_zones" not in overprint
