import sys
import json
from pathlib import Path
from datetime import datetime

from gate0_check import (
    validate_input_file,
    detect_separations,
    detect_page_boxes,
    detect_live_fonts,
    analyze_pdf,
    check_white_ink_risk
)
from context_engine import enrich_context


AUDIT_VARIABLES = {
    "rgb_detection": False,
    "effective_dpi": False,
    "font_embedded": False,
    "tac_detection": False,
    "overprint_fill": False,
    "overprint_stroke": False,
    "object_area_percent": False,
    "is_printable": False,
    "object_type": False,
    "object_role": False,
    "color_values": False,
    "separation_names": False,
    "spot_detection": False,
    "active_object_color": False,
    "number_of_separations": False,
    "text_size_pt": False,
    "line_width_mm": False,
    "barcode_detection": False,
    "qr_detection": False,
    "rich_black_detection": False,
    "reverse_text_detection": False,
    "background_color_context": False,
}


def audit_parser_capabilities(pdf_path):
    capabilities = AUDIT_VARIABLES.copy()

    separations = detect_separations(pdf_path)
    page_boxes = detect_page_boxes(pdf_path)
    live_fonts = detect_live_fonts(pdf_path)

    findings = analyze_pdf(pdf_path)
    findings.extend(check_white_ink_risk(separations))

    enriched = enrich_context(findings, pdf_path)

    for finding in enriched:
        check = finding.get("check")

        if check == "RGB_OBJECT":
            capabilities["rgb_detection"] = True

        if check == "LOW_IMAGE_RESOLUTION":
            capabilities["effective_dpi"] = finding.get("effective_dpi") is not None

        if check == "HIGH_TAC_RISK":
            capabilities["tac_detection"] = finding.get("detected_tac") is not None

        if check == "OVERPRINT_RISK":
            capabilities["overprint_fill"] = bool(finding.get("has_overprint_fill"))
            capabilities["overprint_stroke"] = bool(finding.get("has_overprint_stroke"))

        if finding.get("object_area_percent") is not None:
            capabilities["object_area_percent"] = True

        if finding.get("is_printable") is not None:
            capabilities["is_printable"] = True

        if finding.get("object_type") not in [None, "", "unknown"]:
            capabilities["object_type"] = True

        if finding.get("object_role") not in [None, "", "unknown"]:
            capabilities["object_role"] = True

    if live_fonts:
        capabilities["font_embedded"] = True

    if separations:
        capabilities["spot_detection"] = True
        capabilities["number_of_separations"] = True

    return {
        "file": Path(pdf_path).name,
        "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "capabilities": capabilities,
        "raw_inventory": {
            "total_findings": len(findings),
            "total_enriched_findings": len(enriched),
            "separations_detected": separations,
            "number_of_separations": len(separations),
            "fonts_detected": live_fonts,
            "page_boxes_detected": bool(page_boxes),
            "checks_detected": sorted(list(set(f.get("check") for f in enriched)))
        }
    }


def print_audit_report(report):
    print("\n===== PARSER CAPABILITY AUDIT =====")
    print(f"Archivo: {report['file']}")

    for key, value in report["capabilities"].items():
        label = key.replace("_", " ").title()
        print(f"[{'OK' if value else 'MISSING'}] {label}")

    print("\nChecks detectados:")
    for check in report["raw_inventory"]["checks_detected"]:
        print(f"- {check}")

    print("\n===============================\n")


def main():
    if len(sys.argv) < 2:
        print("Uso: python parser_capability_audit.py archivo.pdf")
        sys.exit(1)

    input_path = validate_input_file(sys.argv[1])
    report = audit_parser_capabilities(str(input_path))

    output_dir = Path("data/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_json = output_dir / "parser_capability_audit.json"

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=4)

    print_audit_report(report)
    print(f"Reporte JSON generado: {output_json}")


if __name__ == "__main__":
    main()
