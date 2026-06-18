from gate0_check import detect_separations, check_spot_color_risk, check_separation_count_risk


def test_spot_color_no_spots():
    findings = check_spot_color_risk([])
    assert findings[0]["check"] == "SPOT_COLOR_RISK"
    assert findings[0]["detail"] == "Documento sin tintas spot detectadas."


def test_separation_count_assumed_cmyk_pass():
    findings = check_separation_count_risk([])
    assert findings[0]["check"] == "SEPARATION_COUNT_RISK"
    assert findings[0]["printable_separation_count"] == 4
    assert findings[0]["process_count_source"] == "ASSUMED_CMYK"


def test_spot_duplicate_and_suspicious():
    separations = ["Pantone 485 C", "PANTONE 485C", "Spot 1"]
    findings = check_spot_color_risk(separations)
    details = [f["detail"] for f in findings]

    assert "Posible duplicidad de tinta spot por nombres inconsistentes." in details
    assert "Spot con nombre genérico o sospechoso detectado." in details
