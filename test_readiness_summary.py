from readiness_summary import build_readiness_summary


def test_summary_no_go_with_top_risk():
    readiness = {
        "readiness_score": 75,
        "readiness_status": "HIGH_RISK",
        "readiness_decision": "NO_GO"
    }

    findings = [
        {
            "check": "FONT_NOT_EMBEDDED",
            "business_severity": "CRITICAL",
            "priority": 1,
            "score_weight": 20,
            "risk_reason": "Fuente no embebida con riesgo de sustitución tipográfica.",
            "action": "Incrustar o convertir fuentes antes de avanzar."
        }
    ]

    result = build_readiness_summary(readiness, findings)

    assert result["decision"] == "NO_GO"
    assert result["tone"] == "critical"
    assert result["top_risks"][0]["check"] == "FONT_NOT_EMBEDDED"
    assert "Fuente no embebida" in result["main_reason"]


def test_summary_go_without_findings():
    readiness = {
        "readiness_score": 100,
        "readiness_status": "READY",
        "readiness_decision": "GO"
    }

    result = build_readiness_summary(readiness, [])

    assert result["decision"] == "GO"
    assert result["tone"] == "positive"
    assert result["top_risks"] == []
    assert result["next_action"] == "Continuar con el flujo normal."
    