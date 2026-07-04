from pathlib import Path

from business_rules import (
    build_business_assessment,
    load_profile,
    summarize_operational_profile,
)


def test_load_profile_reads_existing_profile():
    profile = load_profile("profiles/flexo_pet_bopp_default.json")

    assert profile["profile_name"] == "flexo_pet_bopp_default"
    assert profile["profile_file_found"] is True
    assert profile["tac"]["max_tac_percent"] == 280
    assert profile["small_text"]["warning_threshold_pt"] == 5.0


def test_load_profile_returns_explicit_fallback_when_missing(tmp_path):
    missing = tmp_path / "missing_profile.json"

    profile = load_profile(str(missing))

    assert profile["profile_file_found"] is False
    assert profile["profile_status"] == "FALLBACK_DEFAULT"
    assert profile["tac"]["max_tac_percent"] == 280
    assert profile["small_text"]["critical_threshold_pt"] == 4.0


def test_operational_profile_summary_contains_key_thresholds():
    profile = load_profile("profiles/flexo_pet_bopp_default.json")
    summary = summarize_operational_profile(profile)

    assert summary["profile_name"] == "flexo_pet_bopp_default"
    assert summary["process"] == "flexo"
    assert summary["substrate_family"] == "PET_BOPP"
    assert summary["tac_max_percent"] == 280
    assert summary["small_text_warning_threshold_pt"] == 5.0
    assert summary["small_text_critical_threshold_pt"] == 4.0


def test_business_assessment_exposes_operational_profile():
    assessment = build_business_assessment([
        {
            "check": "SMALL_TEXT_RISK",
            "page": 1,
            "font_size_pt": 4.5,
            "text_height_mm": 1.59,
            "sample_text": "small legal text",
        }
    ])

    assert "operational_profile" in assessment
    assert assessment["operational_profile"]["profile_name"] == "flexo_pet_bopp_default"
    assert assessment["operational_profile"]["small_text_warning_threshold_pt"] == 5.0
    assert assessment["priority_findings"][0]["profile_warning_threshold_pt"] == 5.0
