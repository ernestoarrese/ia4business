from readiness_summary import build_production_readiness_v2


def test_production_readiness_ready_without_findings():
    result = build_production_readiness_v2(
        {"readiness_status": "READY", "readiness_decision": "GO", "readiness_score": 100},
        [],
        {"profile_name": "flexo_pet_bopp_default", "process": "flexo"},
    )

    assert result["status"] == "READY"
    assert result["decision"] == "Liberable."
    assert result["review_time_estimate"] == "0–2 minutos"
    assert result["effective_risk_count"] == 0


def test_production_readiness_contextual_info_is_ready_with_notes():
    result = build_production_readiness_v2(
        {"readiness_status": "READY_WITH_NOTES", "readiness_decision": "GO_WITH_NOTES", "readiness_score": 95},
        [{
            "check": "OVERPRINT_RISK",
            "severity": "INFO",
            "business_severity": "INFO",
            "score_weight": 0,
            "is_blocking": False,
            "risk_reason": "Overprint genérico contextual.",
        }],
        {},
    )

    assert result["status"] == "READY_WITH_NOTES"
    assert result["effective_risk_count"] == 0
    assert result["contextual_note_count"] == 1
    assert result["what_to_review_first"][0]["title"] == "Validar sobreimpresión"


def test_production_readiness_warning_requires_review():
    result = build_production_readiness_v2(
        {"readiness_status": "REVIEW_REQUIRED", "readiness_decision": "HOLD", "readiness_score": 82},
        [{
            "check": "SMALL_TEXT_RISK",
            "severity": "WARNING",
            "business_severity": "WARNING",
            "score_weight": 8,
            "is_blocking": False,
            "risk_reason": "Texto pequeño dentro del área imprimible.",
        }],
        {},
    )

    assert result["status"] == "REVIEW_REQUIRED"
    assert result["decision"] == "Revisar antes de liberar."
    assert result["effective_risk_count"] == 1
    assert result["what_to_review_first"][0]["title"] == "Revisar texto pequeño"


def test_production_readiness_blocking_critical_is_no_go():
    result = build_production_readiness_v2(
        {"readiness_status": "HIGH_RISK", "readiness_decision": "NO_GO", "readiness_score": 45},
        [{
            "check": "FONT_NOT_EMBEDDED",
            "severity": "CRITICAL",
            "business_severity": "CRITICAL",
            "score_weight": 25,
            "is_blocking": True,
            "risk_reason": "Fuente crítica no embebida.",
        }],
        {},
    )

    assert result["status"] == "NO_GO"
    assert result["decision"] == "No liberar sin corrección o aprobación técnica."
    assert result["critical_risk_count"] == 1


def test_production_readiness_v2_uses_supervisor_language_for_white_overprint():
    result = build_production_readiness_v2(
        {"readiness_status": "REVIEW_REQUIRED", "readiness_decision": "HOLD", "readiness_score": 86},
        [{
            "check": "OVERPRINT_RISK",
            "severity": "WARNING",
            "business_severity": "WARNING",
            "score_weight": 8,
            "is_blocking": False,
            "white_ink_present": True,
            "overprint_context": "WHITE_PRESENT_CONTEXTUAL_RISK",
        }],
        {},
    )

    assert result["version"] in {"v2_language_refined", "v2_priority_refined", "v2_priority_deduped"}
    assert result["answer"] == "Requiere revisión antes de liberar."
    assert result["primary_risk"] == "Validar sobreimpresión con blanco"
    assert "no se confirma" not in result["supervisor_summary"].lower()
    assert "Overprint Preview" in result["what_to_review_first"][0]["action"]


def test_production_readiness_v2_ready_answer_is_plain_language():
    result = build_production_readiness_v2(
        {"readiness_status": "READY", "readiness_decision": "GO", "readiness_score": 100},
        [],
        {},
    )

    assert result["question"] == "¿Está este archivo listo para producir?"
    assert result["answer"] == "Sí. El archivo está listo para producir."
    assert result["next_step"] == "Liberar según flujo normal."



def test_production_readiness_v2_prioritizes_overprint_before_small_text_when_both_are_warning():
    result = build_production_readiness_v2(
        {"readiness_status": "REVIEW_REQUIRED", "readiness_decision": "HOLD", "readiness_score": 82},
        [
            {
                "check": "SMALL_TEXT_RISK",
                "severity": "WARNING",
                "business_severity": "WARNING",
                "score_weight": 8,
                "is_blocking": False,
                "risk_reason": "Texto pequeño dentro del área imprimible.",
            },
            {
                "check": "OVERPRINT_RISK",
                "severity": "WARNING",
                "business_severity": "WARNING",
                "score_weight": 8,
                "is_blocking": False,
                "risk_reason": "Sobreimpresión detectada en área visual significativa.",
                "printable_area_overlap_percent": 100,
                "requires_visual_validation": True,
            },
        ],
        {},
    )

    assert result["version"] in {"v2_priority_refined", "v2_priority_deduped"}
    assert result["status"] == "REVIEW_REQUIRED"
    assert result["primary_risk"] == "Validar sobreimpresión"
    assert result["what_to_review_first"][0]["title"] == "Validar sobreimpresión"
    assert result["what_to_review_first"][1]["title"] == "Revisar texto pequeño"


def test_production_readiness_v2_prioritizes_white_overprint_before_small_text():
    result = build_production_readiness_v2(
        {"readiness_status": "REVIEW_REQUIRED", "readiness_decision": "HOLD", "readiness_score": 82},
        [
            {
                "check": "SMALL_TEXT_RISK",
                "severity": "WARNING",
                "business_severity": "WARNING",
                "score_weight": 12,
                "is_blocking": False,
            },
            {
                "check": "OVERPRINT_RISK",
                "severity": "WARNING",
                "business_severity": "WARNING",
                "score_weight": 8,
                "is_blocking": False,
                "white_ink_present": True,
                "overprint_context": "WHITE_PRESENT_CONTEXTUAL_RISK",
            },
        ],
        {},
    )

    assert result["primary_risk"] == "Validar sobreimpresión con blanco"
    assert result["what_to_review_first"][0]["title"] == "Validar sobreimpresión con blanco"
    assert "Overprint Preview" in result["what_to_review_first"][0]["action"]


def test_production_readiness_v2_blocking_critical_still_beats_warning_overprint():
    result = build_production_readiness_v2(
        {"readiness_status": "HIGH_RISK", "readiness_decision": "NO_GO", "readiness_score": 45},
        [
            {
                "check": "OVERPRINT_RISK",
                "severity": "WARNING",
                "business_severity": "WARNING",
                "score_weight": 8,
                "is_blocking": False,
                "white_ink_present": True,
            },
            {
                "check": "FONT_NOT_EMBEDDED",
                "severity": "CRITICAL",
                "business_severity": "CRITICAL",
                "score_weight": 25,
                "is_blocking": True,
            },
        ],
        {},
    )

    assert result["status"] == "NO_GO"
    assert result["primary_risk"] == "Corregir fuente no embebida"
    assert result["what_to_review_first"][0]["severity"] == "CRITICAL"



def test_production_readiness_v2_prioritizes_visual_significant_overprint_before_small_text():
    result = build_production_readiness_v2(
        {"readiness_status": "REVIEW_REQUIRED", "readiness_decision": "HOLD", "readiness_score": 82},
        [
            {
                "check": "SMALL_TEXT_RISK",
                "severity": "WARNING",
                "business_severity": "WARNING",
                "score_weight": 12,
                "is_blocking": False,
                "risk_reason": "Texto pequeño dentro del área imprimible.",
            },
            {
                "check": "OVERPRINT_RISK",
                "severity": "WARNING",
                "business_severity": "WARNING",
                "score_weight": 8,
                "is_blocking": False,
                "risk_reason": "Sobreimpresión detectada en área visual significativa (100.00%).",
                "requires_visual_validation": True,
            },
        ],
        {},
    )

    assert result["primary_risk"] == "Validar sobreimpresión"
    assert result["what_to_review_first"][0]["title"] == "Validar sobreimpresión"
    assert result["what_to_review_first"][1]["title"] == "Revisar texto pequeño"



def test_production_readiness_v2_deduplicates_repeated_small_text_occurrences():
    result = build_production_readiness_v2(
        {"readiness_status": "REVIEW_REQUIRED", "readiness_decision": "HOLD", "readiness_score": 82},
        [
            {
                "check": "OVERPRINT_RISK",
                "severity": "WARNING",
                "business_severity": "WARNING",
                "score_weight": 8,
                "is_blocking": False,
                "risk_reason": "Sobreimpresión detectada en área visual significativa (100.00%).",
                "requires_visual_validation": True,
            },
            {
                "check": "SMALL_TEXT_RISK",
                "severity": "WARNING",
                "business_severity": "WARNING",
                "score_weight": 12,
                "is_blocking": False,
                "risk_reason": "Texto pequeño dentro del área imprimible.",
            },
            {
                "check": "SMALL_TEXT_RISK",
                "severity": "WARNING",
                "business_severity": "WARNING",
                "score_weight": 12,
                "is_blocking": False,
                "risk_reason": "Texto pequeño dentro del área imprimible.",
            },
        ],
        {},
    )

    assert result["version"] == "v2_priority_deduped"
    assert result["primary_risk"] == "Validar sobreimpresión"
    assert len(result["what_to_review_first"]) == 2
    assert result["what_to_review_first"][0]["title"] == "Validar sobreimpresión"
    assert result["what_to_review_first"][1]["title"] == "Revisar texto pequeño"
    assert result["what_to_review_first"][1]["occurrence_count"] == 2
