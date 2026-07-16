import json
import re
from pathlib import Path


DEFAULT_CONFIG_PATH = "config/spot_keywords.json"


def load_spot_keywords(config_path=DEFAULT_CONFIG_PATH):
    path = Path(config_path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_spot_name(name):
    normalized = str(name).lower().strip()
    normalized = normalized.replace("-", " ").replace("_", " ")
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = normalized.replace("pms", "pantone")
    normalized = re.sub(r"(pantone\s*\d+)c\b", r"\1 c", normalized)
    normalized = re.sub(r"(pantone\s*\d+)\s*c\b", r"\1 c", normalized)
    return normalized.strip()


def contains_keyword(normalized_name, keyword_list):
    return any(normalize_spot_name(k) in normalized_name for k in keyword_list)


def classify_spot_name(name, keywords):
    normalized = normalize_spot_name(name)

    if contains_keyword(normalized, keywords.get("white_names", [])):
        return "WHITE"

    if contains_keyword(normalized, keywords.get("technical_names", [])):
        return "TECHNICAL"

    if contains_keyword(normalized, keywords.get("varnish_names", [])):
        return "VARNISH"

    return "PRINTABLE"


def is_generic_suspicious_name(name, keywords):
    return contains_keyword(
        normalize_spot_name(name),
        keywords.get("generic_suspicious_names", [])
    )


def is_pantone_suspicious(name):
    normalized = normalize_spot_name(name)

    patterns = [
        r"\bpanton\b",
        r"\bpanton\d+",
        r"\bpms\s+[a-zA-Z]+\b",
        r"^pantone$",
        r"^pms$"
    ]

    return any(re.search(p, normalized) for p in patterns)


def group_equivalent_spots(spot_names):
    groups = {}

    for name in spot_names:
        normalized = normalize_spot_name(name)
        groups.setdefault(normalized, [])
        groups[normalized].append(name)

    return {
        key: values
        for key, values in groups.items()
        if len(values) > 1
    }


def _gate0_is_non_printable_spot(name):
    normalized = _gate0_normalize_spot_name(name)
    compact = normalized.replace(" ", "")

    # Plan/process-control separations used by some artwork templates.
    if compact in {"cperu", "mperu", "yperu", "kperu"}:
        return True

    non_printable_compact = {
        "all",
        "pie",
        "sustrato",
        "substrato",
        "substrate",
        "texto",
        "text",
        "plano",
        "plano1",
        "plano2",
        "technical",
        "technicaldrawing",
        "technicalinformation",
        "dimensions",
        "dimension",
        "mechanical",
        "mechanicalartwork",
        "dieline",
        "troquel",
        "cut",
        "cutter",
        "knife",
    }

    if compact in non_printable_compact:
        return True

    non_printable_contains = [
        "technical",
        "drawing",
        "dimension",
        "mechanical",
        "plano",
        "troquel",
        "dieline",
        "sustrato",
        "substrato",
        "substrate",
    ]

    return any(token in normalized for token in non_printable_contains)


def build_spot_inventory(separations, config_path=DEFAULT_CONFIG_PATH):
    keywords = load_spot_keywords(config_path)

    inventory = []

    for sep in separations:
        category = classify_spot_name(sep, keywords)

        inventory.append({
            "original_name": sep,
            "normalized_name": normalize_spot_name(sep),
            "category": category,
            "is_generic_suspicious": is_generic_suspicious_name(sep, keywords),
            "is_pantone_suspicious": is_pantone_suspicious(sep)
        })

    printable_spots = [i for i in inventory if i["category"] == "PRINTABLE"]
    white_spots = [i for i in inventory if i["category"] == "WHITE"]
    technical_spots = [i for i in inventory if i["category"] == "TECHNICAL"]
    varnish_spots = [i for i in inventory if i["category"] == "VARNISH"]
    suspicious_spots = [
        i for i in inventory
        if i["is_generic_suspicious"] or i["is_pantone_suspicious"]
    ]

    process_count = 4
    process_count_source = "ASSUMED_CMYK"

    printable_separation_count = (
        process_count
        + len(printable_spots)
        + len(white_spots)
        + len(varnish_spots)
    )

    return {
        "spot_count": len(separations),
        "process_count": process_count,
        "process_count_source": process_count_source,
        "printable_separation_count": printable_separation_count,
        "printable_spot_count": len(printable_spots),
        "white_spot_count": len(white_spots),
        "technical_spot_count": len(technical_spots),
        "varnish_spot_count": len(varnish_spots),
        "spots": inventory,
        "white_spots": white_spots,
        "technical_spots": technical_spots,
        "varnish_spots": varnish_spots,
        "suspicious_spots": suspicious_spots,
        "duplicate_groups": group_equivalent_spots(separations)
    }


# Gate0 non-printable separation classification wrapper v1
# Mantiene el parser completo, pero excluye separaciones de plano/técnicas del conteo operativo.
import re as _gate0_re
import unicodedata as _gate0_unicodedata

def _gate0_normalize_nonprintable_name(name):
    value = str(name or "").strip().lower()
    value = "".join(
        c for c in _gate0_unicodedata.normalize("NFD", value)
        if _gate0_unicodedata.category(c) != "Mn"
    )
    value = _gate0_re.sub(r"[^a-z0-9]+", "", value)
    return value

def _gate0_is_non_printable_separation(name):
    normalized = _gate0_normalize_nonprintable_name(name)

    exact = {
        "all",
        "pie",
        "texto",
        "text",
        "sustrato",
        "substrate",
    }

    if normalized in exact:
        return True

    keywords = [
        "plano",
        "dieline",
        "troquel",
        "corte",
        "cut",
        "cutter",
        "knife",
        "guia",
        "guide",
        "dimension",
        "dimensions",
        "mechanical",
        "mechanicalartwork",
        "technicaldrawing",
        "technical",
    ]

    return any(keyword in normalized for keyword in keywords)

_GATE0_ORIGINAL_BUILD_SPOT_INVENTORY = build_spot_inventory

def build_spot_inventory(separations, config_path=DEFAULT_CONFIG_PATH):
    inventory = _GATE0_ORIGINAL_BUILD_SPOT_INVENTORY(separations, config_path=config_path)
    spots = list(inventory.get("spots", []))

    for item in spots:
        name = item.get("original_name") or item.get("name") or ""
        if _gate0_is_non_printable_separation(name):
            item["category"] = "TECHNICAL"
            item["is_printable"] = False
        elif item.get("category") in {"PRINTABLE", "WHITE", "VARNISH"}:
            item["is_printable"] = True

    printable_categories = {"PRINTABLE", "WHITE", "VARNISH"}
    technical_spots = [i for i in spots if i.get("category") == "TECHNICAL"]
    white_spots = [i for i in spots if i.get("category") == "WHITE"]
    varnish_spots = [i for i in spots if i.get("category") == "VARNISH"]
    printable_spots = [
        i for i in spots
        if i.get("category") in printable_categories
        and not _gate0_is_non_printable_separation(i.get("original_name") or i.get("name") or "")
    ]

    inventory["spots"] = spots
    inventory["technical_spots"] = technical_spots
    inventory["white_spots"] = white_spots
    inventory["varnish_spots"] = varnish_spots
    inventory["printable_spots"] = printable_spots
    inventory["technical_spot_count"] = len(technical_spots)
    inventory["white_spot_count"] = len(white_spots)
    inventory["varnish_spot_count"] = len(varnish_spots)
    inventory["printable_spot_count"] = len(printable_spots)
    inventory["printable_separation_count"] = len(printable_spots)

    if "suspicious_spots" in inventory:
        inventory["suspicious_spots"] = [
            i for i in inventory["suspicious_spots"]
            if not _gate0_is_non_printable_separation(i.get("original_name") or i.get("name") or "")
        ]

    return inventory

