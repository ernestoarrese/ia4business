import sys
import json
import csv
import re
import os
from pathlib import Path
from datetime import datetime

import fitz

from context_engine import enrich_context
from business_rules import build_business_assessment
from readiness_engine import build_readiness_assessment
from readiness_summary import build_readiness_summary, build_fix_plan, build_production_readiness_v2
from config.spot_utils import build_spot_inventory
from expert_comment_engine import enrich_report_with_expert_insights
from check_intelligence import enrich_findings_with_check_intelligence
from risk_evidence_engine import enrich_report_with_risk_evidence
from collections import Counter


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



def _gate0_compact_token(value):
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def detect_separation_usage_capability(pdf_path, separations=None):
    """
    Experimental probe.

    Goal:
    - Detect whether the PDF contains enough low-level signals to attempt
      separation usage mapping in a future sprint.

    Important:
    - This does NOT compute bbox by separation.
    - This does NOT reclassify separations.
    - This is not safe for operational decisions yet.
    """
    separations = separations or []

    result = {
        "status": "EXPERIMENTAL",
        "detected_separation_count": len(separations),
        "separation_names": list(separations),
        "can_map_separation_resources": False,
        "can_detect_usage_tokens": False,
        "can_compute_bbox_by_separation": False,
        "safe_for_reclassification": False,
        "resource_separation_mentions": {},
        "pages_with_usage_tokens": [],
        "usage_token_count": 0,
        "colorspace_selector_count": 0,
        "limitations": [
            "Probe only detects low-level PDF signals.",
            "It does not associate each separation with object geometry.",
            "It does not inspect XObject/transparency/mask nesting reliably.",
            "It does not compute bbox by separation.",
            "It must not be used to reclassify separations yet."
        ],
    }

    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:
        result["error"] = f"Could not open PDF: {exc}"
        return result

    objects_text = ""

    try:
        for xref in range(1, doc.xref_length()):
            try:
                objects_text += doc.xref_object(xref, compressed=False) + "\n"
            except Exception:
                continue

        result["can_map_separation_resources"] = "/Separation" in objects_text

        for sep in separations:
            compact_sep = _gate0_compact_token(sep)
            if not compact_sep:
                continue

            count = 0
            for match in re.finditer(r"/Separation\s*/([^\s<>\[\]\(\)]+)", objects_text):
                found = decode_pdf_name(match.group(1))
                if _gate0_compact_token(found) == compact_sep:
                    count += 1

            # fallback: raw compact search in resource text
            if count == 0 and compact_sep in _gate0_compact_token(objects_text):
                count = 1

            result["resource_separation_mentions"][sep] = count

        for page_index in range(len(doc)):
            page = doc[page_index]
            xrefs = page.get_contents() or []

            page_usage_tokens = 0
            page_colorspace_selectors = 0

            for xref in xrefs:
                try:
                    raw = doc.xref_stream(xref)
                    text = raw.decode("latin-1", errors="ignore")
                except Exception:
                    continue

                # Operators that switch stroking/non-stroking color space:
                # /CS1 cs  or /CS1 CS
                selectors = re.findall(r"/[A-Za-z0-9_.#-]+\s+(?:cs|CS)\b", text)
                # Operators that set Separation/DeviceN tint values:
                # 0.5 scn / 0.5 SCN
                tint_ops = re.findall(r"\b(?:scn|SCN)\b", text)

                page_colorspace_selectors += len(selectors)
                page_usage_tokens += len(tint_ops)

            if page_usage_tokens or page_colorspace_selectors:
                result["pages_with_usage_tokens"].append({
                    "page": page_index + 1,
                    "colorspace_selector_count": page_colorspace_selectors,
                    "usage_token_count": page_usage_tokens,
                })

            result["usage_token_count"] += page_usage_tokens
            result["colorspace_selector_count"] += page_colorspace_selectors

        result["can_detect_usage_tokens"] = (
            result["usage_token_count"] > 0
            or result["colorspace_selector_count"] > 0
        )

        # This remains false until we can associate active separation colors
        # with concrete object geometry/bbox.
        result["can_compute_bbox_by_separation"] = False
        result["safe_for_reclassification"] = False

    finally:
        try:
            doc.close()
        except Exception:
            pass

    return result


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




def _box_tuple(box):
    if not isinstance(box, dict):
        return None
    try:
        return (
            float(box.get("x0_pt")),
            float(box.get("y0_pt")),
            float(box.get("x1_pt")),
            float(box.get("y1_pt")),
        )
    except Exception:
        return None


def _box_area(box):
    if not box:
        return 0.0
    x0, y0, x1, y1 = box
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def _boxes_equal(a, b, tolerance_pt=1.0):
    if not a or not b:
        return False
    return all(abs(float(x) - float(y)) <= tolerance_pt for x, y in zip(a, b))


def _intersection_area(a, b):
    if not a or not b:
        return 0.0
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b

    x0 = max(ax0, bx0)
    y0 = max(ay0, by0)
    x1 = min(ax1, bx1)
    y1 = min(ay1, by1)

    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def resolve_printable_area(page_box):
    """
    Resolve printable/relevant area from PDF page boxes.

    Priority:
    1. TrimBox when it is different from MediaBox.
    2. ArtBox fallback.
    3. CropBox fallback.
    4. Full page unconfirmed.
    """
    media = _box_tuple(page_box.get("mediabox"))
    trim = _box_tuple(page_box.get("trimbox"))
    art = _box_tuple(page_box.get("artbox"))
    crop = _box_tuple(page_box.get("cropbox"))

    if trim and media and not _boxes_equal(trim, media) and _box_area(trim) > 0:
        return {
            "source": "TRIMBOX_CONFIRMED",
            "confidence": "HIGH",
            "box": trim,
        }

    if art and media and not _boxes_equal(art, media) and _box_area(art) > 0:
        return {
            "source": "ARTBOX_FALLBACK",
            "confidence": "MEDIUM",
            "box": art,
        }

    if crop and media and not _boxes_equal(crop, media) and _box_area(crop) > 0:
        return {
            "source": "CROPBOX_FALLBACK",
            "confidence": "LOW",
            "box": crop,
        }

    return {
        "source": "UNCONFIRMED_FULL_PAGE",
        "confidence": "LOW",
        "box": media,
    }


def enrich_findings_with_printable_area(findings, page_boxes):
    """
    Adds printable area metadata to findings with bbox.

    If printable area is confirmed and the finding is clearly outside it,
    business rules may downgrade/exclude it from critical Top Risks.
    """
    page_box_map = {
        int(p.get("page")): p
        for p in page_boxes
        if isinstance(p, dict) and p.get("page") is not None
    }

    enriched = []

    for finding in findings:
        item = finding.copy()

        bbox = item.get("bbox") or []
        if not isinstance(bbox, list) or len(bbox) != 4:
            enriched.append(item)
            continue

        page_number = int(item.get("page") or 1)
        page_box = page_box_map.get(page_number)

        if not page_box:
            item["printable_area_source"] = "NO_PAGE_BOX"
            item["printable_area_confidence"] = "LOW"
            item["is_inside_printable_area"] = None
            enriched.append(item)
            continue

        area = resolve_printable_area(page_box)
        source = area.get("source")
        printable_box = area.get("box")

        try:
            finding_box = tuple(float(x) for x in bbox)
        except Exception:
            item["printable_area_source"] = source
            item["printable_area_confidence"] = area.get("confidence")
            item["is_inside_printable_area"] = None
            enriched.append(item)
            continue

        if source == "UNCONFIRMED_FULL_PAGE" or not printable_box:
            item["printable_area_source"] = source
            item["printable_area_confidence"] = area.get("confidence")
            item["is_inside_printable_area"] = None
            item["printable_area_overlap_percent"] = None
            enriched.append(item)
            continue

        finding_area = _box_area(finding_box)
        overlap = _intersection_area(finding_box, printable_box)
        overlap_percent = round((overlap / finding_area) * 100, 2) if finding_area else 0.0

        # Consider inside if most of the element is inside the printable area.
        inside = overlap_percent >= 80.0

        item["printable_area_source"] = source
        item["printable_area_confidence"] = area.get("confidence")
        item["is_inside_printable_area"] = inside
        item["printable_area_overlap_percent"] = overlap_percent
        item["printable_area_box"] = {
            "x0_pt": printable_box[0],
            "y0_pt": printable_box[1],
            "x1_pt": printable_box[2],
            "y1_pt": printable_box[3],
        }

        enriched.append(item)

    return enriched


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




def detect_process_colors_from_pdf(pdf_path, min_channel_percent=0.1):
    """
    Detecta colores de proceso usados en content streams mediante operadores CMYK:
    - k = fill
    - K = stroke

    Process Color Detection v1:
    - No asume CMYK completo.
    - Detecta C/M/Y/K solo si encuentra valores > min_channel_percent.
    - No certifica uso en imágenes raster ni todos los casos PDF complejos.
    """
    detected = set()

    patterns = [
        (r"(\d*\.?\d+)\s+(\d*\.?\d+)\s+(\d*\.?\d+)\s+(\d*\.?\d+)\s+k", "fill"),
        (r"(\d*\.?\d+)\s+(\d*\.?\d+)\s+(\d*\.?\d+)\s+(\d*\.?\d+)\s+K", "stroke"),
    ]

    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return []

    try:
        for page in doc:
            stream_text = ""

            try:
                contents = page.get_contents() or []
            except Exception:
                contents = []

            for xref in contents:
                try:
                    raw = doc.xref_stream(xref)
                    if raw:
                        stream_text += raw.decode("latin-1", errors="ignore") + "\n"
                except Exception:
                    continue

            for pattern, _mode in patterns:
                for match in re.finditer(pattern, stream_text):
                    values = [float(x) for x in match.groups()]

                    # PDF puede expresar CMYK en 0-1. Convertimos a porcentaje.
                    if max(values) <= 1:
                        values = [v * 100 for v in values]

                    for name, value in zip(["C", "M", "Y", "K"], values):
                        if value > min_channel_percent:
                            detected.add(name)
    finally:
        try:
            doc.close()
        except Exception:
            pass

    order = ["C", "M", "Y", "K"]
    return [c for c in order if c in detected]

def check_spot_color_risk(separations):
    """
    Spot Color Risk must use the same separation classification as
    Color Separation Summary.

    Important:
    - This check counts printable spot/white inks only.
    - It must not count process colors.
    - It must not count plano/technical separations.
    - Total operative separations are handled by SEPARATION_COUNT_RISK.
    """
    findings = []

    printable_spots = []
    technical_detected = False
    source = "SPOT_INVENTORY"

    try:
        from gate0.services.separation_intelligence_service import SeparationIntelligenceService
        summary = SeparationIntelligenceService().build_summary(separations)
        items = summary.get("items", []) if isinstance(summary, dict) else []

        if items:
            source = "SEPARATION_SUMMARY_CLASSIFICATION"
            printable_spots = [
                str(i.get("name", "")).strip()
                for i in items
                if i.get("type") in {"Spot", "Blanco", "Barniz"}
                and str(i.get("name", "")).strip()
            ]
            technical_detected = any(
                i.get("type") in {"Plano", "Technical"}
                for i in items
            )
    except Exception:
        printable_spots = []

    if not printable_spots:
        inventory = build_spot_inventory(separations)
        printable_spots = [
            str(x).strip()
            for x in inventory.get("printable_spots", [])
            if str(x).strip()
        ]
        technical_detected = inventory.get("technical_spot_count", 0) > 0

    printable_spot_count = len(printable_spots)

    def _normalize_spot_name_local(value):
        return re.sub(r"[^a-z0-9]", "", str(value or "").lower())

    normalized = [
        _normalize_spot_name_local(name)
        for name in printable_spots
        if name
    ]
    duplicates = sorted([
        name for name, count in Counter(normalized).items()
        if name and count > 1
    ])

    generic_spots = []
    for name in printable_spots:
        compact = _normalize_spot_name_local(name)
        is_generic = (
            compact in {"spot", "spot1", "spot2", "spot3", "tinta", "tinta1", "tinta2", "color", "color1"}
            or re.fullmatch(r"spot\d+", compact or "") is not None
            or re.fullmatch(r"tinta\d+", compact or "") is not None
            or re.fullmatch(r"color\d+", compact or "") is not None
        )
        if is_generic:
            generic_spots.append(name)

    white_spots = [
        name for name in printable_spots
        if "white" in name.lower()
        or "blanco" in name.lower()
    ]

    example = printable_spots[0] if printable_spots else "-"

    base_context = {
        "printable_spot_count": printable_spot_count,
        "spot_count": printable_spot_count,
        "spot_names_detected": printable_spots,
        "duplicate_spot_names": duplicates,
        "generic_spot_names": generic_spots,
        "white_spot_count": len(white_spots),
        "technical_separations_detected": technical_detected,
        "separation_count_source": source,
    }

    if printable_spot_count == 0:
        findings.append({
            "page": 1,
            "check": "SPOT_COLOR_RISK",
            "severity": "LOW",
            "detail": "Documento sin tintas spot detectadas.",
            "value": "0 tinta(s) spot/blanco imprimible(s)",
            "recommendation": "Sin acción requerida.",
            **base_context,
            "phase": "MVP"
        })
    elif printable_spot_count <= 8:
        findings.append({
            "page": 1,
            "check": "SPOT_COLOR_RISK",
            "severity": "LOW",
            "detail": (
                f"Se detectaron {printable_spot_count} tinta(s) spot/blanco imprimible(s). "
                "La cantidad está dentro del rango normal del perfil operativo."
            ),
            "value": f"{printable_spot_count} tinta(s) spot/blanco imprimible(s); ejemplo: {example}",
            "recommendation": "Sin acción requerida. Mantener validación normal de separaciones.",
            **base_context,
            "phase": "MVP"
        })
    elif printable_spot_count > 12:
        findings.append({
            "page": 1,
            "check": "SPOT_COLOR_RISK",
            "severity": "HIGH",
            "detail": (
                f"Se detectaron {printable_spot_count} tintas spot/blanco imprimibles. "
                "La cantidad supera el umbral crítico del perfil operativo."
            ),
            "value": f"{printable_spot_count} tinta(s) spot/blanco imprimible(s); ejemplo: {example}",
            "recommendation": "Racionalizar separaciones spot antes de liberar.",
            **base_context,
            "phase": "MVP"
        })
    elif printable_spot_count >= 9:
        findings.append({
            "page": 1,
            "check": "SPOT_COLOR_RISK",
            "severity": "MEDIUM",
            "detail": (
                f"Se detectaron {printable_spot_count} tintas spot/blanco imprimibles. "
                "La cantidad es elevada y puede aumentar complejidad operativa."
            ),
            "value": f"{printable_spot_count} tinta(s) spot/blanco imprimible(s); ejemplo: {example}",
            "recommendation": "Revisar si todas las tintas spot son necesarias o si alguna puede racionalizarse.",
            **base_context,
            "phase": "MVP"
        })

    if duplicates:
        findings.append({
            "page": 1,
            "check": "SPOT_COLOR_RISK",
            "severity": "MEDIUM",
            "detail": "Posible duplicidad de tinta spot por nombres inconsistentes.",
            "value": ", ".join(duplicates[:8]),
            "recommendation": "Normalizar nombres y validar si corresponden a la misma tinta.",
            **base_context,
            "phase": "MVP"
        })

    if generic_spots:
        findings.append({
            "page": 1,
            "check": "SPOT_COLOR_RISK",
            "severity": "MEDIUM",
            "detail": "Spot con nombre genérico o sospechoso detectado.",
            "value": ", ".join(generic_spots[:8]),
            "recommendation": "Renombrar separaciones spot con nomenclatura clara antes de liberar.",
            **base_context,
            "phase": "MVP"
        })

    if len(white_spots) > 1:
        findings.append({
            "page": 1,
            "check": "SPOT_COLOR_RISK",
            "severity": "MEDIUM",
            "detail": "Se detectaron múltiples separaciones asociadas a blanco.",
            "value": ", ".join(white_spots[:8]),
            "recommendation": "Unificar o confirmar la intención de cada blanco antes de liberar.",
            **base_context,
            "phase": "MVP"
        })

    return findings


def check_separation_count_risk(separations, process_colors=None):
    findings = []

    # Source of truth for spot/technical classification:
    # use the same classifier used by Color Separation Summary.
    try:
        from gate0.services.separation_intelligence_service import SeparationIntelligenceService
        summary = SeparationIntelligenceService().build_summary(separations)
        items = summary.get("items", []) if isinstance(summary, dict) else []
    except Exception:
        items = []

    inventory = build_spot_inventory(separations)

    process_colors = process_colors or []
    process_colors = [c for c in ["C", "M", "Y", "K"] if c in set(process_colors)]

    printable_spot_count = inventory["printable_spot_count"]
    process_count_source = "NO_PROCESS_COLORS_DETECTED"
    process_detection_confidence = "LOW"
    process_colors_detected = []

    if items:
        printable_spot_count = sum(
            1 for i in items
            if i.get("type") in {"Spot", "Blanco", "Barniz"}
        )

        explicit_process_items = [
            i for i in items
            if i.get("type") == "Process"
        ]

        # Some technical artwork templates include separations named C PERU / M PERU / Y PERU / K PERU.
        # Those must not inflate operative process color count.
        plan_process_letters = set()
        for i in items:
            name = str(i.get("name", "")).strip().lower().replace(" ", "")
            if i.get("type") in {"Plano", "Technical"}:
                if name == "cperu":
                    plan_process_letters.add("C")
                elif name == "mperu":
                    plan_process_letters.add("M")
                elif name == "yperu":
                    plan_process_letters.add("Y")
                elif name == "kperu":
                    plan_process_letters.add("K")

        if explicit_process_items:
            process_colors_detected = [
                str(i.get("name", "")).upper()
                for i in explicit_process_items
            ]
            process_count = len(explicit_process_items)
            process_count_source = "SEPARATION_SUMMARY_CLASSIFICATION"
            process_detection_confidence = "MEDIUM"
        else:
            process_colors_detected = [
                c for c in process_colors
                if c not in plan_process_letters
            ]
            process_count = len(process_colors_detected)

            if process_count > 0:
                process_count_source = "DETECTED_PROCESS_COLORS"
                process_detection_confidence = "MEDIUM"
            else:
                process_count_source = "NO_PROCESS_COLORS_DETECTED"
                process_detection_confidence = "LOW"

        technical_detected = any(i.get("type") in {"Plano", "Technical"} for i in items)
        white_detected = any(i.get("type") == "Blanco" for i in items)
        varnish_detected = any(i.get("type") == "Barniz" for i in items)
    else:
        process_colors_detected = process_colors
        process_count = len(process_colors_detected)

        if process_count > 0:
            process_count_source = "DETECTED_PROCESS_COLORS"
            process_detection_confidence = "MEDIUM"

        white_detected = inventory["white_spot_count"] > 0
        varnish_detected = inventory["varnish_spot_count"] > 0
        technical_detected = inventory["technical_spot_count"] > 0

    printable_count = process_count + printable_spot_count

    context_data = {
        "printable_separation_count": printable_count,
        "process_count": process_count,
        "process_color_count": process_count,
        "process_colors_detected": process_colors_detected,
        "process_count_source": process_count_source,
        "process_detection_confidence": process_detection_confidence,
        "printable_spot_count": printable_spot_count,
        "white_detected": white_detected,
        "varnish_detected": varnish_detected,
        "technical_separations_detected": technical_detected,
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
        "value": (
            f"printable_separation_count={printable_count} "
            f"(process={process_count}, spots={printable_spot_count})"
        ),
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
        if os.getenv("GATE0_ENABLE_BARCODE_RISK", "").strip().lower() in {"1", "true", "yes", "on"}:
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

# ---------------------------------------------------------------------
# Sprint 26A — Separation Usage v2 Foundation
# ---------------------------------------------------------------------

def _suv2_compact_name(name):
    import re
    return re.sub(r"[^a-z0-9]", "", str(name or "").strip().lower())


def _suv2_int(value, default=0):
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _suv2_lookup_resource_mentions(name, mentions):
    """
    Busca menciones de separación usando nombre exacto y forma compacta.
    """
    mentions = mentions or {}

    candidates = [
        str(name or ""),
        str(name or "").strip(),
        str(name or "").replace(" ", "_"),
        _suv2_compact_name(name),
    ]

    compact_mentions = {
        _suv2_compact_name(k): v
        for k, v in mentions.items()
    }

    for key in candidates:
        if key in mentions:
            return _suv2_int(mentions.get(key), 0)

    compact = _suv2_compact_name(name)
    return _suv2_int(compact_mentions.get(compact), 0)


def build_separation_usage_v2(separation_summary=None, separation_usage_capability=None):
    """
    Capa informativa sobre señales de uso de separaciones.

    Sprint 26A:
    - No reclasifica.
    - No cambia conteo operativo.
    - No afecta Production Readiness.
    - Solo transforma capability/probe en una lectura por separación.
    """
    separation_summary = separation_summary or {}
    separation_usage_capability = separation_usage_capability or {}

    summary_items = separation_summary.get("items") or []
    resource_mentions = separation_usage_capability.get("resource_separation_mentions") or {}

    can_map_resources = bool(separation_usage_capability.get("can_map_separation_resources"))
    can_compute_bbox = bool(separation_usage_capability.get("can_compute_bbox_by_separation"))
    safe_for_reclassification = bool(separation_usage_capability.get("safe_for_reclassification"))

    usage_token_count = _suv2_int(separation_usage_capability.get("usage_token_count"), 0)
    colorspace_selector_count = _suv2_int(separation_usage_capability.get("colorspace_selector_count"), 0)

    items = []

    for item in summary_items:
        name = item.get("name")
        mention_count = _suv2_lookup_resource_mentions(name, resource_mentions)

        if mention_count > 0:
            usage_signal_status = "RESOURCE_SIGNAL_FOUND"
            usage_signal_confidence = "LOW"
            explanation = (
                "La separación aparece en recursos PDF. Esto confirma presencia, "
                "pero todavía no confirma uso visual ni ubicación."
            )
        elif can_map_resources:
            usage_signal_status = "NO_DIRECT_RESOURCE_SIGNAL"
            usage_signal_confidence = "LOW"
            explanation = (
                "No se encontró una señal directa para esta separación en el probe actual. "
                "No significa que no se use; la lectura aún es limitada."
            )
        else:
            usage_signal_status = "USAGE_SIGNAL_NOT_AVAILABLE"
            usage_signal_confidence = "LOW"
            explanation = (
                "Gate0 aún no puede mapear de forma confiable recursos de separación para este archivo."
            )

        items.append({
            "name": name,
            "type": item.get("type"),
            "original_type": item.get("original_type"),
            "is_printable": item.get("is_printable"),
            "classification_source": item.get("classification_source"),
            "is_generic": item.get("is_generic"),
            "usage_signal_status": usage_signal_status,
            "usage_signal_confidence": usage_signal_confidence,
            "resource_mention_count": mention_count,
            "bbox_available": False,
            "can_compute_bbox_by_separation": can_compute_bbox,
            "safe_for_reclassification": safe_for_reclassification,
            "decision_impact": "INFORMATIONAL_ONLY",
            "operational_count_impact": "NO_IMPACT_IN_V2_FOUNDATION",
            "explanation": explanation,
        })

    with_signals = [
        i for i in items
        if i.get("usage_signal_status") == "RESOURCE_SIGNAL_FOUND"
    ]

    without_signals = [
        i for i in items
        if i.get("usage_signal_status") != "RESOURCE_SIGNAL_FOUND"
    ]

    printable_items = [i for i in items if i.get("is_printable")]
    non_printable_items = [i for i in items if i.get("is_printable") is False]

    return {
        "version": "v2_foundation",
        "safe_for_operational_decision": False,
        "safe_for_reclassification": False,
        "can_compute_bbox_by_separation": can_compute_bbox,
        "can_map_separation_resources": can_map_resources,
        "source": "separation_summary + separation_usage_capability",
        "summary": {
            "detected_separations": len(items),
            "printable_separations": len(printable_items),
            "non_printable_separations": len(non_printable_items),
            "separations_with_usage_signals": len(with_signals),
            "separations_without_usage_signals": len(without_signals),
            "usage_token_count": usage_token_count,
            "colorspace_selector_count": colorspace_selector_count,
        },
        "items": items,
        "product_note": (
            "Separation Usage v2 Foundation es informativo. "
            "No cambia conteos operativos, clasificación, riesgos ni Production Readiness."
        ),
        "current_limitation": (
            "Gate0 puede detectar presencia de separaciones y algunas señales de recursos, "
            "pero aún no calcula bbox ni uso visual por separación."
        ),
        "future_evolution": (
            "Separation Usage v2 deberá asociar separación, objeto, bbox y área imprimible "
            "antes de impactar decisiones operativas."
        ),
    }


def build_report(pdf_path):
    input_path = validate_input_file(pdf_path)

    separations = detect_separations(str(input_path))
    process_colors = detect_process_colors_from_pdf(str(input_path))
    page_boxes = detect_page_boxes(str(input_path))
    separation_usage_capability = detect_separation_usage_capability(str(input_path), separations=separations)

    # Sprint 26A.2 — Build separation_summary before using it in separation_usage_v2.
    try:
        from gate0.services.separation_intelligence_service import SeparationIntelligenceService
        separation_summary = SeparationIntelligenceService().build_summary(
            separations,
            process_count=len(process_colors or []),
            process_count_source=(
                "CONTENT_STREAM_PROCESS_COLORS"
                if process_colors
                else "NO_PROCESS_COLORS_DETECTED"
            ),
        )
    except Exception as exc:
        separation_summary = {
            "total": len(separations or []),
            "detected_total": len(separations or []),
            "operational_total": len(separations or []),
            "calculated_operational_total": len(separations or []),
            "process_count": len(process_colors or []),
            "process_count_source": "SEPARATION_SUMMARY_FALLBACK",
            "items": [],
            "printable_items": [],
            "printable_names": [],
            "warnings": [f"No se pudo construir separation_summary: {exc}"],
        }

    live_fonts = detect_live_fonts(str(input_path))
    pdf_structure = analyze_pdf_structure(str(input_path))

    findings = analyze_pdf(str(input_path))
    findings = enrich_overprint_with_white_context(findings, separations)

    findings.extend(check_font_embedding(live_fonts))
    findings.extend(check_white_ink_risk(separations))
    findings.extend(check_spot_color_risk(separations))
    findings.extend(check_separation_count_risk(separations, process_colors=process_colors))
    findings.extend(check_pdf_structure_risk(pdf_structure))

    findings = enrich_findings_with_printable_area(findings, page_boxes)

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

    production_readiness_v2 = build_production_readiness_v2(
        readiness_assessment,
        priority_findings,
        business_assessment.get("operational_profile", {})
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
        "separation_summary": separation_summary,
        "separation_usage_capability": separation_usage_capability,
        "separation_usage_v2": build_separation_usage_v2(
            separation_summary=separation_summary,
            separation_usage_capability=separation_usage_capability,
        ),
        "pdf_structure": pdf_structure,
        "live_fonts": live_fonts,
        "operational_profile": business_assessment.get("operational_profile", {}),
        "business_assessment": business_assessment,
        "readiness_assessment": readiness_assessment,
        "readiness_summary": readiness_summary,
        "production_readiness_v2": production_readiness_v2,
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
        print("Uso: python gate0_check.py archivo.pdf [output_dir]")
        sys.exit(1)

    pdf_path = sys.argv[1]

    # Sprint 27B — Runtime Isolation v1
    # Prefer explicit CLI output_dir, then env var, then legacy fallback.
    output_dir = (
        sys.argv[2]
        if len(sys.argv) >= 3
        else os.environ.get("GATE0_OUTPUT_DIR", "data/output")
    )

    report = build_report(pdf_path)
    json_path, csv_path = save_report(report, output_dir=output_dir)
# ---------------------------------------------------------------------
# Sprint 25C.1 — RGB_OBJECT Evidence Depth
# ---------------------------------------------------------------------

def check_rgb_objects(page_stream, page_number):
    """
    Detecta operadores RGB simples en content stream.

    Sprint 25C.1:
    - conserva compatibilidad con RGB_OBJECT v1.
    - agrega evidencia técnica del operador detectado.
    - declara explícitamente que no hay bbox/ubicación visual todavía.
    """
    import re

    findings = []

    if not page_stream:
        return findings

    rgb_patterns = [
        (r"([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+rg\b", "fill", "rg"),
        (r"([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+RG\b", "stroke", "RG"),
    ]

    for pattern, mode, operator in rgb_patterns:
        for match in re.finditer(pattern, page_stream):
            r, g, b = match.groups()

            findings.append({
                "check": "RGB_OBJECT",
                "page": page_number,
                "detail": f"Objeto RGB detectado ({mode})",
                "value": f"RGB=({r}, {g}, {b})",
                "rgb_values": [float(r), float(g), float(b)],
                "rgb_operator": operator,
                "rgb_mode": mode,
                "color_space": "DeviceRGB",
                "detection_method": "CONTENT_STREAM_RGB_OPERATOR",
                "bbox_available": False,
                "location_confidence": "NOT_AVAILABLE_IN_RGB_OBJECT_V1",
                "object_location_status": "NOT_LOCALIZED",
                "printable_area_status": "NOT_EVALUABLE_WITHOUT_BBOX",
                "requires_manual_location_review": True,
                "current_limitation": (
                    "RGB_OBJECT v1 detecta operadores RGB en el content stream, "
                    "pero todavía no identifica el objeto visual ni su bbox."
                ),
                "recommendation": (
                    "Validar si el RGB pertenece al arte productivo. "
                    "Si aplica, convertir RGB a CMYK o spot validado según perfil de impresión."
                ),
            })

    return findings




# ---------------------------------------------------------------------
# Sprint 25C.2 — HIGH_TAC_RISK Evidence Depth
# ---------------------------------------------------------------------

def check_high_tac(page_stream, page_number, tac_limit=280):
    """
    Detecta TAC alto desde operadores CMYK simples en content stream.

    Sprint 25C.2:
    - conserva HIGH_TAC_RISK v1.
    - agrega evidencia técnica de CMYK/TAC.
    - declara explícitamente que no hay bbox/ubicación visual todavía.
    """
    findings = []

    for item in extract_cmyk_values_from_stream(page_stream):
        tac = item["tac"]
        c, m, y, k = item["cmyk"]

        if tac > tac_limit:
            excess = tac - tac_limit

            findings.append({
                "check": "HIGH_TAC_RISK",
                "page": page_number,
                "detail": f"Riesgo TAC alto en objeto CMYK ({item['mode']})",
                "value": f"TAC={tac:.1f}% | CMYK=({c:.1f}, {m:.1f}, {y:.1f}, {k:.1f})",
                "detected_tac": round(tac, 1),
                "tac_limit": tac_limit,
                "tac_excess": round(excess, 1),
                "cmyk_values": [round(c, 1), round(m, 1), round(y, 1), round(k, 1)],
                "cmyk_operator": item.get("operator"),
                "cmyk_mode": item.get("mode"),
                "color_space": "DeviceCMYK",
                "detection_method": "CONTENT_STREAM_CMYK_OPERATOR",
                "bbox_available": False,
                "location_confidence": "NOT_AVAILABLE_IN_HIGH_TAC_RISK_V1",
                "object_location_status": "NOT_LOCALIZED",
                "printable_area_status": "NOT_EVALUABLE_WITHOUT_BBOX",
                "requires_manual_location_review": True,
                "current_limitation": (
                    "HIGH_TAC_RISK v1 calcula TAC desde operadores CMYK en el content stream, "
                    "pero todavía no identifica el objeto visual ni su bbox."
                ),
                "recommendation": (
                    f"Validar si el TAC alto pertenece al arte productivo. "
                    f"Si aplica, reducir carga total de tinta según estándar del proceso/sustrato. "
                    f"Límite configurado: {tac_limit}%."
                ),
            })

    return findings




# ---------------------------------------------------------------------
# Sprint 25C.3 — FONT_NOT_EMBEDDED Evidence Depth
# ---------------------------------------------------------------------

def check_font_embedding(live_fonts):
    """
    Crea hallazgos para fuentes no embebidas.

    Sprint 25C.3:
    - conserva FONT_NOT_EMBEDDED v1.
    - agrega evidencia técnica de fuente.
    - declara explícitamente que no asocia texto afectado todavía.
    """
    findings = []

    for font in live_fonts or []:
        font_name = font.get("font_name")
        font_type = font.get("font_type")
        font_ext = font.get("font_ext")
        font_name_raw = font.get("font_name_raw")
        page = font.get("page", 1)

        findings.append({
            "page": page,
            "check": "FONT_NOT_EMBEDDED",
            "detail": f"Fuente no embebida detectada: {font_name}",
            "value": f"{font_name} | {font_type}",
            "font_name": font_name,
            "font_name_raw": font_name_raw,
            "font_type": font_type,
            "font_ext": font_ext,
            "embedded": False,
            "font_embedding_status": "NOT_EMBEDDED",
            "detection_method": "PYMUPDF_PAGE_GET_FONTS",
            "text_association_status": "NOT_ASSOCIATED_IN_FONT_V1",
            "affected_text_available": False,
            "sample_text": None,
            "bbox_available": False,
            "object_location_status": "FONT_RESOURCE_LEVEL_ONLY",
            "requires_manual_text_review": True,
            "current_limitation": (
                "FONT_NOT_EMBEDDED v1 detecta la fuente no embebida a nivel de recurso PDF, "
                "pero todavía no asocia de forma confiable qué texto específico la usa."
            ),
            "recommendation": (
                "Incrustar la fuente en el PDF o convertir el texto a curvas antes de liberar. "
                "Validar especialmente textos legales, ingredientes, claims, códigos y advertencias."
            ),
        })

    return findings


# Sprint 27A.4.1 — main guard intentionally kept at EOF
if __name__ == "__main__":
    main()



