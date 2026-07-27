import re
from pathlib import Path

from config.spot_utils import build_spot_inventory


SOURCE = Path("config/spot_utils.py").read_text(encoding="utf-8")


def _definition_count(name):
    return len(re.findall(rf"^def {name}\(", SOURCE, flags=re.M))


def test_spot_utils_has_single_build_spot_inventory_definition():
    assert _definition_count("build_spot_inventory") == 1
    assert "_GATE0_ORIGINAL_BUILD_SPOT_INVENTORY" not in SOURCE


def test_build_spot_inventory_keeps_non_printable_separations_out_of_operational_count():
    inventory = build_spot_inventory([
        "PANTONE 485 C",
        "Blanco",
        "Barniz",
        "Plano",
        "Material",
        "Technical Drawing",
    ])

    technical_names = {
        item["original_name"]
        for item in inventory["technical_spots"]
    }

    printable_names = {
        item["original_name"]
        for item in inventory["printable_spots"]
    }

    assert {"Plano", "Material", "Technical Drawing"}.issubset(technical_names)
    assert "PANTONE 485 C" in printable_names
    assert "Blanco" in printable_names
    assert "Barniz" in printable_names

    assert inventory["technical_spot_count"] == 3
    assert inventory["printable_spot_count"] == 3
    assert inventory["printable_separation_count"] == 3


def test_build_spot_inventory_keeps_expected_summary_keys():
    inventory = build_spot_inventory(["PANTONE 485 C", "White", "Plano"])

    expected_keys = {
        "spot_count",
        "process_count",
        "process_count_source",
        "printable_separation_count",
        "printable_spot_count",
        "white_spot_count",
        "technical_spot_count",
        "varnish_spot_count",
        "spots",
        "white_spots",
        "technical_spots",
        "varnish_spots",
        "printable_spots",
        "suspicious_spots",
        "duplicate_groups",
    }

    assert expected_keys.issubset(set(inventory.keys()))
    assert inventory["process_count"] == 4
    assert inventory["process_count_source"] == "ASSUMED_CMYK"
