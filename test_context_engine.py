from context_engine import enrich_context


def test_font_not_embedded_context():
    findings = [
        {
            "page": 1,
            "check": "FONT_NOT_EMBEDDED",
            "value": "Helvetica"
        }
    ]

    result = enrich_context(findings)

    assert result[0]["object_type"] == "text"
    assert result[0]["object_area_percent"] == 1
    assert result[0]["is_small_object"] is True


def test_overprint_context_flags_from_value():
    findings = [
        {
            "page": 1,
            "check": "OVERPRINT_RISK",
            "value": "has_overprint_fill=True | has_overprint_stroke=False"
        }
    ]

    result = enrich_context(findings)

    assert result[0]["object_type"] == "vector"
    assert result[0]["has_overprint_fill"] is True
    assert result[0]["has_overprint_stroke"] is False
    assert result[0]["object_area_percent"] == 100


def test_white_ink_context():
    findings = [
        {
            "page": 1,
            "check": "WHITE_INK_RISK",
            "value": "White"
        }
    ]

    result = enrich_context(findings)

    assert result[0]["object_type"] == "separation"
    assert result[0]["object_role"] == "white_ink"
    assert result[0]["white_names_detected"] == "White"
