from pathlib import Path

from business_rules import (
    build_business_assessment,
    build_production_profile_contract,
    load_profile,
    summarize_operational_profile,
    validate_operational_profile,
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


def test_validate_operational_profile_accepts_default_profile_contract():
    profile = load_profile("profiles/flexo_pet_bopp_default.json")

    validation = validate_operational_profile(profile)

    assert validation["contract_version"] == "production_profile_contract_v1"
    assert validation["is_valid"] is True
    assert validation["missing_fields"] == []
    assert "tac.max_tac_percent" in validation["required_fields"]


def test_validate_operational_profile_reports_missing_required_fields():
    validation = validate_operational_profile({
        "profile_name": "incomplete_profile",
        "profile_version": "test",
    })

    assert validation["is_valid"] is False
    assert "process" in validation["missing_fields"]
    assert "substrate_family" in validation["missing_fields"]
    assert "tac.max_tac_percent" in validation["missing_fields"]
    assert "small_text.critical_threshold_pt" in validation["missing_fields"]


def test_build_production_profile_contract_exposes_context_and_thresholds():
    profile = load_profile("profiles/flexo_pet_bopp_default.json")

    contract = build_production_profile_contract(profile)

    assert contract["contract_version"] == "production_profile_contract_v1"
    assert contract["is_valid"] is True
    assert contract["profile_name"] == "flexo_pet_bopp_default"
    assert contract["context_label"] == "flexo / PET_BOPP"
    assert contract["thresholds"]["tac_max_percent"] == 280
    assert contract["thresholds"]["image_minimum_dpi"] == 250
    assert contract["thresholds"]["separation_normal_max_printable"] == 8
    assert contract["thresholds"]["small_text_warning_threshold_pt"] == 5.0


def test_operational_profile_summary_exposes_profile_contract_metadata():
    profile = load_profile("profiles/flexo_pet_bopp_default.json")
    summary = summarize_operational_profile(profile)

    assert summary["production_profile_contract"] == "production_profile_contract_v1"
    assert summary["profile_contract_valid"] is True
    assert summary["profile_contract_missing_fields"] == []
    assert summary["profile_context_label"] == "flexo / PET_BOPP"
    assert summary["profile_thresholds"]["separation_critical_above_printable"] == 12
