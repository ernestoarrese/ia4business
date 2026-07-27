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
        "material",
        "materials",
        "materiales",
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
    """
    Gate0 non-printable separation classifier.

    These names represent plans, technical artwork, substrate/material references,
    dimensions or support layers. They must not count as printable/operative inks.
    """
    normalized = _gate0_normalize_nonprintable_name(name)
    compact = (
        normalized
        .replace(" ", "")
        .replace("_", "")
        .replace("-", "")
        .replace("/", "")
    )

    non_printable_compact = {
        "plano",
        "plano1",
        "plano2",
        "dieline",
        "diecut",
        "troquel",
        "cut",
        "cutter",
        "knife",
        "guide",
        "guia",
        "sustrato",
        "substrato",
        "substrate",
        "material",
        "materials",
        "materiales",
        "technical",
        "technicaldrawing",
        "technicalinformation",
        "mechanical",
        "mechanicalartwork",
        "dimensions",
        "dimension",
        "texto",
        "text",
        "reference",
        "referencia",
        "legend",
        "notes",
        "nota",
    }

    if compact in non_printable_compact:
        return True

    non_printable_contains = [
        "technical",
        "technical drawing",
        "technical information",
        "drawing",
        "mechanical",
        "mechanical artwork",
        "dimensions",
        "dimension",
        "plano",
        "dieline",
        "troquel",
        "sustrato",
        "substrato",
        "substrate",
        "material",
        "materials",
        "materiales",
        "texto",
        "text",
        "reference",
        "referencia",
        "legend",
        "notes",
        "nota",
    ]

    return any(token in normalized for token in non_printable_contains)


def build_spot_inventory(separations, config_path=DEFAULT_CONFIG_PATH):
    """
    Build spot/separation inventory.

    Consolidated version:
    - Keeps the original keyword-based classification.
    - Applies Gate0 non-printable separation filter.
    - Excludes technical/plan/material separations from printable operational count.
    """
    keywords = load_spot_keywords(config_path)

    spots = []

    for sep in separations:
        category = classify_spot_name(sep, keywords)

        if _gate0_is_non_printable_separation(sep):
            category = "TECHNICAL"

        item = {
            "original_name": sep,
            "normalized_name": normalize_spot_name(sep),
            "category": category,
            "is_generic_suspicious": is_generic_suspicious_name(sep, keywords),
            "is_pantone_suspicious": is_pantone_suspicious(sep),
        }

        if category in {"PRINTABLE", "WHITE", "VARNISH"}:
            item["is_printable"] = True
        else:
            item["is_printable"] = False

        if _gate0_is_non_printable_separation(sep):
            item["category"] = "TECHNICAL"
            item["is_printable"] = False

        spots.append(item)

    printable_categories = {"PRINTABLE", "WHITE", "VARNISH"}

    technical_spots = [
        i for i in spots
        if i.get("category") == "TECHNICAL"
    ]

    white_spots = [
        i for i in spots
        if i.get("category") == "WHITE"
    ]

    varnish_spots = [
        i for i in spots
        if i.get("category") == "VARNISH"
    ]

    printable_spots = [
        i for i in spots
        if i.get("category") in printable_categories
        and not _gate0_is_non_printable_separation(
            i.get("original_name") or i.get("name") or ""
        )
    ]

    suspicious_spots = [
        i for i in spots
        if (
            i.get("is_generic_suspicious")
            or i.get("is_pantone_suspicious")
        )
        and not _gate0_is_non_printable_separation(
            i.get("original_name") or i.get("name") or ""
        )
    ]

    process_count = 4
    process_count_source = "ASSUMED_CMYK"

    return {
        "spot_count": len(separations),
        "process_count": process_count,
        "process_count_source": process_count_source,
        "printable_separation_count": len(printable_spots),
        "printable_spot_count": len(printable_spots),
        "white_spot_count": len(white_spots),
        "technical_spot_count": len(technical_spots),
        "varnish_spot_count": len(varnish_spots),
        "spots": spots,
        "white_spots": white_spots,
        "technical_spots": technical_spots,
        "varnish_spots": varnish_spots,
        "printable_spots": printable_spots,
        "suspicious_spots": suspicious_spots,
        "duplicate_groups": group_equivalent_spots(separations),
    }



