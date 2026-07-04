import sys
import json
import csv
import re
from pathlib import Path
from datetime import datetime

import fitz

from context_engine import enrich_context
from business_rules import build_business_assessment
from readiness_engine import build_readiness_assessment
from readiness_summary import build_readiness_summary, build_fix_plan
from config.spot_utils import build_spot_inventory
from expert_comment_engine import enrich_report_with_expert_insights
from check_intelligence import enrich_findings_with_check_intelligence
from risk_evidence_engine import enrich_report_with_risk_evidence


SUPPORTED_EXTENSIONS = [".pdf", ".ai"]


def validate_input_file(input_path):
    path = Path(input_path)

    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo: {input_path}")

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Formato no soportado: {path.suffix}")

    return path


def decode_pdf_name(name):
    """
    Decodifica nombres PDF tipo Pantone#20485#20C.
    """
    name = str(name)

    def repl(match):
        try:
            return chr(int(match.group(1), 16))
        except Exception:
            return match.group(0)

    return re.sub(r"#([0-9A-Fa-f]{2})", repl, name)


def read_page_stream(doc, page):
    """
    Lee streams de contenido de una página.
    """
    text = ""

    try:
        xrefs = page.get_contents()
        if not xrefs:
            return ""

        for xref in xrefs:
            stream = doc.xref_stream(xref)
            if stream:
                text += stream.decode("latin-1", errors="ignore") + "\n"

    except Exception:
        return ""

    return text


def detect_separations(pdf_path):
    """
    Detecta separaciones spot globales:
    - /Separation /Name
    - /DeviceN [ /Name1 /Name2 ... ]
    """
    separations = set()
    doc = fitz.open(pdf_path)

    for xref in range(1, doc.xref_length()):
        try:
            obj = doc.xref_object(xref, compressed=False)
        except Exception:
            continue

        for match in re.finditer(r"/Separation\s*/([^\s<>\[\]\(\)]+)", obj):
            separations.add(decode_pdf_name(match.group(1)))

        for match in re.finditer(r"/DeviceN\s*\[(.*?)\]", obj, re.DOTALL):
            block = match.group(1)
            names = re.findall(r"/([^\s<>\[\]\(\)]+)", block)
            for name in names:
                separations.add(decode_pdf_name(name))

    doc.close()
    return sorted(separations)


def detect_page_boxes(pdf_path):
    doc = fitz.open(pdf_path)
    boxes = []

    for page_index, page in enumerate(doc, start=1):
        def box_data(rect):
            return {
                "x0_pt": round(rect.x0, 2),
                "y0_pt": round(rect.y0, 2),
                "x1_pt": round(rect.x1, 2),
                "y1_pt": round(rect.y1, 2),
                "width_pt": round(rect.width, 2),
                "height_pt": round(rect.height, 2),
                "width_mm": round(rect.width * 25.4 / 72, 2),
                "height_mm": round(rect.height * 25.4 / 72, 2)
            }

        boxes.append({
            "page": page_index,
            "rotation": page.rotation,
            "mediabox": box_data(page.mediabox),
            "cropbox": box_data(page.cropbox),
            "trimbox": box_data(page.trimbox),
            "bleedbox": box_data(page.bleedbox),
            "artbox": box_data(page.artbox)
        })

    doc.close()
    return boxes


def detect_live_fonts(pdf_path):
    """
    Detecta fuentes no embebidas.
    """
    doc = fitz.open(pdf_path)
    fonts = []

    for page_index, page in enumerate(doc, start=1):
        for font in page.get_fonts(full=True):
            xref = font[0]
            ext = font[1]
            font_type = font[2]
            basefont = font[3]
            name = font[4]

            embedded = ext not in ["n/a", ""]

            if not embedded:
                fonts.append({
                    "page": page_index,
                    "xref": xref,
                    "font_name": basefont,
                    "font_name_raw": name,
                    "font_type": font_type,
                    "font_ext": ext,
                    "embedded": embedded,
                    "resource_name": name
                })

    doc.close()
    return fonts


def check_font_embedding(live_fonts):
    findings = []

    for font in live_fonts:
        findings.append({
            "page": font.get("page", 1),
            "check": "FONT_NOT_EMBEDDED",
            "severity": "HIGH",
            "detail": "Fuente no embebida detectada",
            "value": f"{font.get('font_name')} | {font.get('font_type')}",
            "recommendation": "Incrustar o convertir fuentes antes de liberar a producción."
        })

    return findings



def check_small_text(page, page_number, warning_threshold_pt=5.0, critical_threshold_pt=4.0, max_findings=25):
    """
    Detecta texto vivo pequeño usando PyMuPDF page.get_text("dict").

    v1:
    - Solo texto vivo.
    - No detecta texto convertido a curvas.
    - No evalúa todavía si es positivo/negativo.
    - No cruza todavía contra fondo.
    """
    findings = []

    try:
        text_dict = page.get_text("dict")
    except Exception:
        return findings

    for block in text_dict.get("blocks", []):
        if block.get("type") != 0:
            continue

        for line in block.get("lines", []):
            for span in line.get("spans", []):
                raw_text = str(span.get("text", "")).strip()
                if not raw_text:
                    continue

                try:
                    size_pt = float(span.get("size") or 0)
                except Exception:
                    continue

                if size_pt <= 0 or size_pt >= warning_threshold_pt:
                    continue

                severity = "HIGH" if size_pt < critical_threshold_pt else "MEDIUM"
                text_height_mm = round(size_pt * 0.352778, 2)
                sample_text = raw_text[:80]
                bbox = span.get("bbox") or []

                findings.append({
                    "check": "SMALL_TEXT_RISK",
                    "severity": severity,
                    "page": page_number,
                    "value": f"{sample_text} | {size_pt:.2f} pt",
                    "detail": f"Texto vivo pequeño detectado: {size_pt:.2f} pt / {text_height_mm:.2f} mm aprox.",
                    "sample_text": sample_text,
                    "font_size_pt": round(size_pt, 2),
                    "text_height_mm": text_height_mm,
                    "font_name": span.get("font"),
                    "bbox": [round(float(x), 2) for x in bbox] if bbox else [],
                    "warning_threshold_pt": warning_threshold_pt,
                    "critical_threshold_pt": critical_threshold_pt,
                })

                if len(findings) >= max_findings:
                    return findings

    return findings

def check_rgb_objects(page_stream, page_number):
    """
    Detecta operadores RGB simples en content stream.
    MVP:
    - rg = RGB fill
    - RG = RGB stroke
    """

    findings = []

    rgb_patterns = [
        (r"(\d*\.?\d+)\s+(\d*\.?\d+)\s+(\d*\.?\d+)\s+rg", "fill"),
        (r"(\d*\.?\d+)\s+(\d*\.?\d+)\s+(\d*\.?\d+)\s+RG", "stroke")
    ]

    for pattern, mode in rgb_patterns:
        for match in re.finditer(pattern, page_stream):
            r, g, b = [float(x) for x in match.groups()]

            findings.append({
                "page": page_number,
                "check": "RGB_OBJECT",
                "severity": "MEDIUM",
                "detail": f"Objeto RGB detectado ({mode})",
                "value": f"RGB=({r}, {g}, {b})",
                "recommendation": "Convertir RGB a CMYK o spot validado según perfil de impresión."
            })

    return findings



def check_barcode_risk(page, page_number, minimum_image_dpi=300.0, critical_image_dpi=200.0, max_findings=20):
    """
    Barcode Intelligence v1.

    Detecta candidatos barcode/QR como imagen de bajo DPI.
    No decodifica el código.
    No valida GS1, quiet zone, magnificación ni lectura.
    """
    findings = []

    try:
        image_info = page.get_image_info(xrefs=True)
    except Exception:
        return findings

    try:
        page_text = page.get_text("text").lower()
    except Exception:
        page_text = ""

    barcode_keywords = [
        "barcode", "bar code", "ean", "upc", "gs1",
        "code128", "code 128", "datamatrix", "data matrix"
    ]
    qr_keywords = ["qr", "qrcode", "qr code"]

    has_barcode_keyword = any(k in page_text for k in barcode_keywords)
    has_qr_keyword = any(k in page_text for k in qr_keywords)

    page_area = abs(page.rect.width * page.rect.height) if getattr(page, "rect", None) else 0

    for idx, img in enumerate(image_info, start=1):
        bbox = img.get("bbox")
        width_px = img.get("width") or 0
        height_px = img.get("height") or 0

        if not bbox or not width_px or not height_px:
            continue

        rect = fitz.Rect(bbox)

        width_in = rect.width / 72 if rect.width else 0
        height_in = rect.height / 72 if rect.height else 0

        dpi_x = width_px / width_in if width_in else 0
        dpi_y = height_px / height_in if height_in else 0

        if not dpi_x or not dpi_y:
            continue

        effective_dpi = round(min(dpi_x, dpi_y), 1)

        if effective_dpi >= minimum_image_dpi:
            continue

        display_aspect = rect.width / rect.height if rect.height else 0
        normalized_aspect = max(display_aspect, 1 / display_aspect) if display_aspect else 0
        area_percent = round((abs(rect.width * rect.height) / page_area) * 100, 2) if page_area else 0

        is_barcode_shape = normalized_aspect >= 2.8
        is_qr_shape = 0.85 <= display_aspect <= 1.18 and area_percent <= 10

        if not (is_barcode_shape or is_qr_shape or has_barcode_keyword or has_qr_keyword):
            continue

        if is_barcode_shape:
            candidate_type = "barcode"
            detection_method = "wide_image_geometry"
            confidence = "Media"
        elif is_qr_shape:
            candidate_type = "qr"
            detection_method = "square_image_geometry"
            confidence = "Baja"
        elif has_qr_keyword:
            candidate_type = "qr"
            detection_method = "page_text_keyword"
            confidence = "Baja"
        else:
            candidate_type = "barcode"
            detection_method = "page_text_keyword"
            confidence = "Baja"

        severity = "HIGH" if effective_dpi < critical_image_dpi else "MEDIUM"

        findings.append({
            "check": "BARCODE_RISK",
            "severity": severity,
            "page": page_number,
            "value": f"{candidate_type} candidate image {idx}: {effective_dpi} dpi",
            "detail": (
                f"Posible {candidate_type.upper()} como imagen con {effective_dpi:.0f} dpi efectivos. "
                f"Barcode Intelligence v1 no confirma lectura; detecta riesgo técnico del candidato."
            ),
            "barcode_candidate_type": candidate_type,
            "barcode_confidence": confidence,
            "detection_method": detection_method,
            "effective_dpi": effective_dpi,
            "minimum_image_dpi": minimum_image_dpi,
            "critical_image_dpi": critical_image_dpi,
            "bbox": [round(float(x), 2) for x in bbox],
            "object_area_percent": area_percent,
            "display_aspect_ratio": round(display_aspect, 2) if display_aspect else 0,
            "image_width_px": width_px,
            "image_height_px": height_px,
        })

        if len(findings) >= max_findings:
            return findings

    return findings

def check_low_resolution_images(page, page_number):
    """
    Detecta imágenes con resolución efectiva menor a 250 dpi.
    """

    findings = []

    try:
        image_info = page.get_image_info(xrefs=True)
    except Exception:
        image_info = []

    for idx, img in enumerate(image_info, start=1):
        bbox = img.get("bbox")
        width = img.get("width") or 0
        height = img.get("height") or 0

        if not bbox:
            continue

        rect = fitz.Rect(bbox)

        width_in = rect.width / 72 if rect.width else 0
        height_in = rect.height / 72 if rect.height else 0

        dpi_x = width / width_in if width_in else 0
        dpi_y = height / height_in if height_in else 0

        if not dpi_x or not dpi_y:
            continue

        effective_dpi = round(min(dpi_x, dpi_y), 1)

        if effective_dpi < 250:
            findings.append({
                "page": page_number,
                "check": "LOW_IMAGE_RESOLUTION",
                "severity": "MEDIUM",
                "detail": "Imagen con baja resolución efectiva",
                "value": f"Imagen {idx}: {effective_dpi} dpi",
                "effective_dpi": effective_dpi,
                "bbox": [round(float(x), 2) for x in bbox],
                "image_index": idx,
                "recommendation": "Revisar resolución efectiva al tamaño final de uso."
            })

    return findings


def extract_cmyk_values_from_stream(page_stream):
    """
    Extrae operadores CMYK fill/stroke:
    - k = fill
    - K = stroke
    """
    results = []

    patterns = [
        (r"(\d*\.?\d+)\s+(\d*\.?\d+)\s+(\d*\.?\d+)\s+(\d*\.?\d+)\s+k", "fill"),
        (r"(\d*\.?\d+)\s+(\d*\.?\d+)\s+(\d*\.?\d+)\s+(\d*\.?\d+)\s+K", "stroke")
    ]

    for pattern, mode in patterns:
        for match in re.finditer(pattern, page_stream):
            c, m, y, k = [float(x) for x in match.groups()]

            # PDF puede usar 0-1. Convertimos a %
            values = [c, m, y, k]
            if max(values) <= 1:
                values = [v * 100 for v in values]

            results.append({
                "mode": mode,
                "cmyk": values,
                "tac": sum(values)
            })

    return results


def check_high_tac(page_stream, page_number, tac_limit=280):
    findings = []

    for item in extract_cmyk_values_from_stream(page_stream):
        tac = item["tac"]
        c, m, y, k = item["cmyk"]

        if tac > tac_limit:
            findings.append({
                "page": page_number,
                "check": "HIGH_TAC_RISK",
                "severity": "HIGH",
                "detail": f"Riesgo TAC alto en objeto CMYK ({item['mode']})",
                "value": f"TAC={tac:.1f}% | CMYK=({c:.1f}, {m:.1f}, {y:.1f}, {k:.1f})",
                "detected_tac": round(tac, 1),
                "recommendation": f"Reducir carga total de tinta. Límite configurado: {tac_limit}%."
            })

    return findings


def check_overprint_risk(doc):
    """
    Detecta overprint en streams/ExtGState.
    MVP robusto: busca /op true y /OP true en objetos PDF.
    """

    findings = []

    objects_text = ""
    for xref in range(1, doc.xref_length()):
        try:
            objects_text += doc.xref_object(xref, compressed=False) + "\n"
        except Exception:
            continue

    objects_text_lower = objects_text.lower()

    for page_number, page in enumerate(doc, start=1):
        try:
            content_text = read_page_stream(doc, page)
            search_text = (content_text + "\n" + objects_text).lower()

            has_overprint_fill = "/op true" in search_text or "/op 1" in search_text
            has_overprint_stroke = "/op true" in search_text or "/op 1" in search_text or "/opm" in objects_text_lower

            if not has_overprint_fill and not has_overprint_stroke:
                continue

            findings.append({
                "page": page_number,
                "check": "OVERPRINT_RISK",
                "severity": "MEDIUM",
                "detail": "Objeto con sobreimpresión detectada",
                "value": (
                    f"has_overprint_fill={has_overprint_fill} | "
                    f"has_overprint_stroke={has_overprint_stroke}"
                ),
                "recommendation": "Verificar intención de sobreimpresión antes de avanzar."
            })

        except Exception as e:
            findings.append({
                "page": page_number,
                "check": "OVERPRINT_RISK",
                "severity": "LOW",
                "detail": "No se pudo evaluar sobreimpresión en la página.",
                "value": str(e),
                "recommendation": "Revisar manualmente sobreimpresión."
            })

    return findings


def has_white_ink(separations):
    white_keywords = ["white", "blanco", "wht", "opaque white", "ink white"]

    for sep in separations:
        sep_lower = str(sep).lower()
        if any(keyword in sep_lower for keyword in white_keywords):
            return True

    return False


def enrich_overprint_with_white_context(findings, separations):
    white_detected = has_white_ink(separations)

    if not white_detected:
        return findings

    for finding in findings:
        if finding.get("check") == "OVERPRINT_RISK":
            finding["white_ink_detected"] = True
            finding["phase"] = "Fase 2 parcial"

    return findings


def check_white_ink_risk(separations):
    findings = []

    inventory = build_spot_inventory(separations)
    white_spots = inventory["white_spots"]

    if not white_spots:
        return findings

    white_names = [item["original_name"] for item in white_spots]

    if len(white_names) > 1:
        findings.append({
            "page": 1,
            "check": "WHITE_INK_RISK",
            "severity": "MEDIUM",
            "detail": "Múltiples separaciones asociadas a blanco detectadas",
            "value": ", ".join(white_names),
            "recommendation": "Unificar nomenclatura de blanco y validar separación correcta."
        })
    else:
        findings.append({
            "page": 1,
            "check": "WHITE_INK_RISK",
            "severity": "LOW",
            "detail": "Separación blanca detectada",
            "value": white_names[0],
            "recommendation": "Validar que el blanco corresponda a la intención del arte."
        })

    return findings


def check_spot_color_risk(separations):
    findings = []
    inventory = build_spot_inventory(separations)

    spot_count = inventory["spot_count"]
    printable_spot_count = inventory["printable_spot_count"]

    if spot_count == 0:
        findings.append({
            "page": 1,
            "check": "SPOT_COLOR_RISK",
            "severity": "LOW",
            "detail": "Documento sin tintas spot detectadas.",
            "value": "spot_count=0",
            "recommendation": "Validar si el trabajo requiere tintas especiales.",
            "spot_names": [],
            "spot_count": 0,
            "printable_spot_count": 0,
            "phase": "MVP"
        })
        return findings

    if inventory["white_spot_count"] == 1:
        names = [i["original_name"] for i in inventory["white_spots"]]
        findings.append({
            "page": 1,
            "check": "SPOT_COLOR_RISK",
            "severity": "LOW",
            "detail": "White Ink detectado como separación spot.",
            "value": ", ".join(names),
            "recommendation": "Validar que el blanco corresponda a la intención del arte.",
            "spot_names": names,
            "spot_count": spot_count,
            "printable_spot_count": printable_spot_count,
            "spot_category": ["WHITE"],
            "phase": "MVP"
        })

    elif inventory["white_spot_count"] > 1:
        names = [i["original_name"] for i in inventory["white_spots"]]
        findings.append({
            "page": 1,
            "check": "SPOT_COLOR_RISK",
            "severity": "MEDIUM",
            "detail": "Múltiples separaciones de blanco detectadas.",
            "value": ", ".join(names),
            "recommendation": "Verificar si corresponden a estrategia intencional de alta opacidad o a duplicidad no deseada.",
            "spot_names": names,
            "spot_count": spot_count,
            "printable_spot_count": printable_spot_count,
            "spot_category": ["WHITE"],
            "phase": "MVP"
        })

    if inventory["technical_spots"]:
        names = [i["original_name"] for i in inventory["technical_spots"]]
        findings.append({
            "page": 1,
            "check": "SPOT_COLOR_RISK",
            "severity": "LOW",
            "detail": "Separación técnica detectada.",
            "value": ", ".join(names),
            "recommendation": "Verificar que la separación técnica no sea tratada como tinta imprimible.",
            "spot_names": names,
            "spot_count": spot_count,
            "printable_spot_count": printable_spot_count,
            "spot_category": ["TECHNICAL"],
            "phase": "MVP"
        })

    if inventory["suspicious_spots"]:
        names = [i["original_name"] for i in inventory["suspicious_spots"]]
        findings.append({
            "page": 1,
            "check": "SPOT_COLOR_RISK",
            "severity": "MEDIUM",
            "detail": "Spot con nombre genérico o sospechoso detectado.",
            "value": ", ".join(names),
            "recommendation": "Renombrar la separación con un nombre técnico o de tinta real antes de liberar a producción.",
            "spot_names": names,
            "spot_count": spot_count,
            "printable_spot_count": printable_spot_count,
            "spot_category": ["SUSPICIOUS"],
            "phase": "MVP"
        })

    if inventory["duplicate_groups"]:
        names = []
        for group in inventory["duplicate_groups"].values():
            names.extend(group)

        findings.append({
            "page": 1,
            "check": "SPOT_COLOR_RISK",
            "severity": "MEDIUM",
            "detail": "Posible duplicidad de tinta spot por nombres inconsistentes.",
            "value": ", ".join(names),
            "recommendation": "Normalizar nombres de tintas spot para evitar separaciones duplicadas, errores de formulación o tintas adicionales innecesarias.",
            "spot_names": names,
            "spot_count": spot_count,
            "printable_spot_count": printable_spot_count,
            "spot_category": ["DUPLICATE"],
            "phase": "MVP"
        })

    if printable_spot_count > 12:
        names = [i["original_name"] for i in inventory["spots"] if i["category"] == "PRINTABLE"]
        findings.append({
            "page": 1,
            "check": "SPOT_COLOR_RISK",
            "severity": "HIGH",
            "detail": "Exceso crítico de tintas spot imprimibles.",
            "value": f"printable_spot_count={printable_spot_count}",
            "recommendation": "Revisar racionalización de separaciones spot para reducir complejidad, costo y riesgo operativo.",
            "spot_names": names,
            "spot_count": spot_count,
            "printable_spot_count": printable_spot_count,
            "spot_category": ["PRINTABLE_EXCESS"],
            "phase": "MVP"
        })

    elif printable_spot_count >= 9:
        names = [i["original_name"] for i in inventory["spots"] if i["category"] == "PRINTABLE"]
        findings.append({
            "page": 1,
            "check": "SPOT_COLOR_RISK",
            "severity": "MEDIUM",
            "detail": "Cantidad elevada de tintas spot imprimibles.",
            "value": f"printable_spot_count={printable_spot_count}",
            "recommendation": "Revisar racionalización de separaciones spot para reducir complejidad, costo y riesgo operativo.",
            "spot_names": names,
            "spot_count": spot_count,
            "printable_spot_count": printable_spot_count,
            "spot_category": ["PRINTABLE_HIGH"],
            "phase": "MVP"
        })

    return findings


def check_separation_count_risk(separations):
    findings = []
    inventory = build_spot_inventory(separations)

    printable_count = inventory["printable_separation_count"]

    context_data = {
        "printable_separation_count": printable_count,
        "process_count": inventory["process_count"],
        "process_count_source": inventory["process_count_source"],
        "white_detected": inventory["white_spot_count"] > 0,
        "varnish_detected": inventory["varnish_spot_count"] > 0,
        "technical_separations_detected": inventory["technical_spot_count"] > 0
    }

    if printable_count <= 8:
        severity = "LOW"
        detail = "Cantidad de separaciones dentro de rango normal para packaging flexible."
        recommendation = "Sin acción requerida. Mantener validación normal del flujo."
    elif printable_count in [9, 10]:
        severity = "LOW"
        detail = "Cantidad elevada de separaciones imprimibles."
        recommendation = "Verificar complejidad operativa y disponibilidad de estaciones de impresión."
    elif printable_count in [11, 12]:
        severity = "MEDIUM"
        detail = "Cantidad alta de separaciones imprimibles."
        recommendation = "Revisar racionalización de separaciones spot y evaluar conversión de colores secundarios a proceso."
    else:
        severity = "HIGH"
        detail = "Exceso crítico de separaciones imprimibles."
        recommendation = "Validar capacidad de prensa, secuencia de impresión y necesidad real de cada separación."

    findings.append({
        "page": 1,
        "check": "SEPARATION_COUNT_RISK",
        "severity": severity,
        "detail": detail,
        "value": f"printable_separation_count={printable_count}",
        "recommendation": recommendation,
        **context_data,
        "phase": "MVP"
    })

    return findings


def analyze_pdf_structure(pdf_path):
    path = Path(pdf_path)
    file_size_mb = round(path.stat().st_size / (1024 * 1024), 2)

    doc = fitz.open(pdf_path)

    page_count = len(doc)
    empty_pages = []
    vector_object_count = 0
    image_count = 0

    for page_index, page in enumerate(doc, start=1):
        drawings = page.get_drawings()
        images = page.get_images(full=True)
        text = page.get_text("text").strip()

        vector_object_count += len(drawings)
        image_count += len(images)

        if len(drawings) == 0 and len(images) == 0 and not text:
            empty_pages.append(page_index)

    total_object_count = vector_object_count + image_count

    doc.close()

    return {
        "page_count": page_count,
        "file_size_mb": file_size_mb,
        "empty_page_count": len(empty_pages),
        "empty_pages": empty_pages,
        "vector_object_count": vector_object_count,
        "image_count": image_count,
        "total_object_count": total_object_count
    }


def check_pdf_structure_risk(pdf_structure):
    findings = []

    page_count = pdf_structure.get("page_count", 0)
    file_size_mb = pdf_structure.get("file_size_mb", 0)
    empty_page_count = pdf_structure.get("empty_page_count", 0)
    vector_object_count = pdf_structure.get("vector_object_count", 0)
    image_count = pdf_structure.get("image_count", 0)
    total_object_count = pdf_structure.get("total_object_count", 0)

    if page_count == 0:
        severity = "HIGH"
        detail = "PDF sin páginas."
        recommendation = "Validar integridad del archivo."
    elif empty_page_count == page_count:
        severity = "HIGH"
        detail = "Todas las páginas están vacías."
        recommendation = "Verificar exportación o contenido del PDF."
    elif empty_page_count > 0:
        severity = "MEDIUM"
        detail = "Se detectaron páginas vacías."
        recommendation = "Validar si las páginas vacías son intencionales."
    elif file_size_mb > 500 or total_object_count > 15000 or vector_object_count > 15000 or image_count > 300:
        severity = "HIGH"
        detail = "Complejidad estructural crítica del PDF."
        recommendation = "Optimizar o reconstruir PDF antes de procesos pesados."
    elif file_size_mb > 200 or total_object_count > 5000 or vector_object_count > 5000 or image_count > 100:
        severity = "MEDIUM"
        detail = "Complejidad estructural elevada del PDF."
        recommendation = "Revisar optimización antes de RIP, trapping o imposición."
    else:
        severity = "LOW"
        detail = "Estructura PDF dentro de parámetros normales."
        recommendation = "Sin acción requerida."

    findings.append({
        "page": 1,
        "check": "PDF_STRUCTURE_RISK",
        "severity": severity,
        "detail": detail,
        "value": f"pages={page_count} | size_mb={file_size_mb} | objects={total_object_count}",
        "recommendation": recommendation,
        "page_count": page_count,
        "file_size_mb": file_size_mb,
        "empty_page_count": empty_page_count,
        "vector_object_count": vector_object_count,
        "image_count": image_count,
        "total_object_count": total_object_count,
        "phase": "MVP"
    })

    return findings



def _finding_bbox_key(finding):
    bbox = finding.get("bbox") or []
    if len(bbox) != 4:
        return None

    try:
        return tuple(round(float(x), 1) for x in bbox)
    except Exception:
        return None


def dedupe_lowres_against_barcode(findings):
    """
    Si el mismo bbox genera LOW_IMAGE_RESOLUTION y BARCODE_RISK,
    conserva BARCODE_RISK porque es el riesgo más específico para preprensa/calidad.
    """
    barcode_keys = {
        (f.get("page"), _finding_bbox_key(f))
        for f in findings
        if f.get("check") == "BARCODE_RISK" and _finding_bbox_key(f) is not None
    }

    if not barcode_keys:
        return findings

    deduped = []

    for finding in findings:
        if finding.get("check") == "LOW_IMAGE_RESOLUTION":
            key = (finding.get("page"), _finding_bbox_key(finding))
            if key in barcode_keys:
                continue

        deduped.append(finding)

    return deduped

def analyze_pdf(pdf_path):
    findings = []

    doc = fitz.open(pdf_path)

    for page_index in range(len(doc)):
        page = doc[page_index]
        page_number = page_index + 1

        page_stream = read_page_stream(doc, page)

        findings.extend(check_rgb_objects(page_stream, page_number))
        image_findings = []
        image_findings.extend(check_low_resolution_images(page, page_number))
        image_findings.extend(check_barcode_risk(page, page_number))
        findings.extend(dedupe_lowres_against_barcode(image_findings))
        findings.extend(check_small_text(page, page_number))
        findings.extend(check_high_tac(page_stream, page_number))

    findings.extend(check_overprint_risk(doc))

    doc.close()

    return findings


def calculate_gate_status(enriched_findings):
    if not enriched_findings:
        return "PASS"

    severities = [
        f.get("business_severity") or f.get("severity")
        for f in enriched_findings
    ]

    if "CRITICAL" in severities:
        return "FAIL"

    if "WARNING" in severities:
        return "WARNING"

    if "INFO" in severities:
        return "WARNING"

    return "PASS"


def write_json_report(report_data, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=4)


def write_csv_report(findings, output_path):
    fieldnames = [
        "page",
        "check",
        "severity",
        "business_severity",
        "risk_area",
        "detail",
        "value",
        "recommendation",
        "risk_reason",
        "action",
        "priority",
        "score_weight"
    ]

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for finding in findings:
            writer.writerow(finding)


def build_report(pdf_path):
    input_path = validate_input_file(pdf_path)

    separations = detect_separations(str(input_path))
    page_boxes = detect_page_boxes(str(input_path))
    live_fonts = detect_live_fonts(str(input_path))
    pdf_structure = analyze_pdf_structure(str(input_path))

    findings = analyze_pdf(str(input_path))
    findings = enrich_overprint_with_white_context(findings, separations)

    findings.extend(check_font_embedding(live_fonts))
    findings.extend(check_white_ink_risk(separations))
    findings.extend(check_spot_color_risk(separations))
    findings.extend(check_separation_count_risk(separations))
    findings.extend(check_pdf_structure_risk(pdf_structure))

    context_findings = enrich_context(findings, str(input_path))

    business_assessment = build_business_assessment(context_findings)
    priority_findings = business_assessment.get("priority_findings", [])
    priority_findings = enrich_findings_with_check_intelligence(priority_findings)
    business_assessment["priority_findings"] = priority_findings

    readiness_assessment = build_readiness_assessment(priority_findings)
    readiness_summary = build_readiness_summary(
        readiness_assessment,
        priority_findings
    )

    fix_plan = build_fix_plan(priority_findings)

    gate_status = calculate_gate_status(priority_findings)

    report_data = {
        "file": input_path.name,
        "pages": len(page_boxes),
        "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "gate_status": gate_status,
        "total_alerts": len(context_findings),
        "separations": separations,
        "page_boxes": page_boxes,
        "pdf_structure": pdf_structure,
        "live_fonts": live_fonts,
        "operational_profile": business_assessment.get("operational_profile", {}),
        "business_assessment": business_assessment,
        "readiness_assessment": readiness_assessment,
        "readiness_summary": readiness_summary,
        "fix_plan": fix_plan,
        "findings": context_findings
    }

    report_data = enrich_report_with_expert_insights(report_data)
    report_data = enrich_report_with_risk_evidence(report_data)

    return report_data


def save_report(report_data, output_dir="data/output"):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    json_path = output_path / "gate0_report.json"
    csv_path = output_path / "gate0_report.csv"

    write_json_report(report_data, json_path)
    write_csv_report(
        report_data.get("business_assessment", {}).get("priority_findings", []),
        csv_path
    )

    return json_path, csv_path


def main():
    if len(sys.argv) < 2:
        print("Uso: python gate0_check.py archivo.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]

    report = build_report(pdf_path)
    json_path, csv_path = save_report(report)

    print("\n===== GATE0 PACKAGING QA =====")
    print(f"Archivo: {report['file']}")
    print(f"Gate status: {report['gate_status']}")

    readiness = report.get("readiness_assessment", {})
    summary = report.get("readiness_summary", {})

    print(f"Readiness score: {readiness.get('readiness_score')}")
    print(f"Readiness status: {readiness.get('readiness_status')}")
    print(f"Decision: {readiness.get('readiness_decision')}")
    print(f"Headline: {summary.get('headline')}")
    print(f"Reporte JSON: {json_path}")
    print(f"Reporte CSV: {csv_path}")
    print("================================\n")


if __name__ == "__main__":
    main()
