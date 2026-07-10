from gate0_check import detect_separations, check_spot_color_risk, check_separation_count_risk, detect_process_colors_from_pdf


def test_spot_color_no_spots():
    findings = check_spot_color_risk([])
    assert findings[0]["check"] == "SPOT_COLOR_RISK"
    assert findings[0]["detail"] == "Documento sin tintas spot detectadas."


def test_separation_count_does_not_assume_cmyk():
    findings = check_separation_count_risk([])
    assert findings[0]["check"] == "SEPARATION_COUNT_RISK"
    assert findings[0]["printable_separation_count"] == 0
    assert findings[0]["process_count"] == 0
    assert findings[0]["process_colors_detected"] == []
    assert findings[0]["process_count_source"] == "NO_PROCESS_COLORS_DETECTED"


def test_separation_count_uses_detected_process_colors():
    findings = check_separation_count_risk(["Pantone 485 C", "White"], process_colors=["K"])
    assert findings[0]["check"] == "SEPARATION_COUNT_RISK"
    assert findings[0]["process_colors_detected"] == ["K"]
    assert findings[0]["process_count"] == 1
    assert findings[0]["printable_spot_count"] == 2
    assert findings[0]["printable_separation_count"] == 3
    assert findings[0]["process_count_source"] == "DETECTED_PROCESS_COLORS"


def test_separation_count_cmyk_plus_spots():
    findings = check_separation_count_risk(["Pantone 485 C", "Spot 1"], process_colors=["C", "M", "Y", "K"])
    assert findings[0]["process_count"] == 4
    assert findings[0]["printable_spot_count"] == 2
    assert findings[0]["printable_separation_count"] == 6


def test_spot_duplicate_and_suspicious():
    separations = ["Pantone 485 C", "PANTONE 485C", "Spot 1"]
    findings = check_spot_color_risk(separations)
    details = [f["detail"] for f in findings]

    assert "Posible duplicidad de tinta spot por nombres inconsistentes." in details
    assert "Spot con nombre genérico o sospechoso detectado." in details


def test_separation_count_excludes_plan_and_technical_separations():
    separations = [
        "All",
        "Blanco calzado",
        "PANTONE 2995 C",
        "PANTONE Reflex Blue C",
        "Pie",
        "Sustrato",
        "Texto",
    ]

    findings = check_separation_count_risk(separations, process_colors=[])
    item = findings[0]

    assert item["printable_spot_count"] == 3
    assert item["printable_separation_count"] == 3
    assert item["process_count"] == 0
    assert item["process_count_source"] == "NO_PROCESS_COLORS_DETECTED"
    assert item["technical_separations_detected"] is True


def test_separation_count_k_plus_printable_spots_excludes_plan():
    separations = [
        "All",
        "Blanco calzado",
        "PANTONE 2995 C",
        "PANTONE Reflex Blue C",
        "Pie",
        "Sustrato",
        "Texto",
    ]

    findings = check_separation_count_risk(separations, process_colors=["K"])
    item = findings[0]

    assert item["process_colors_detected"] == ["K"]
    assert item["process_count"] == 1
    assert item["printable_spot_count"] == 3
    assert item["printable_separation_count"] == 4

