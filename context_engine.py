"""
context_engine.py

Responsabilidad:
Agregar contexto operacional a hallazgos técnicos.

NO decide severidad.
NO calcula riesgo.
NO toma decisiones GO/HOLD/NO_GO.
"""

import fitz


def calculate_rgb_area_percent(pdf_path):
    """
    Calcula área RGB aproximada sobre página.
    MVP:
    - Usa get_drawings().
    - Suma áreas de objetos con fill/stroke RGB.
    """

    rgb_area_by_page = {}

    doc = fitz.open(pdf_path)

    for page_index, page in enumerate(doc, start=1):
        page_area = abs(page.rect.width * page.rect.height)
        rgb_area = 0

        for drawing in page.get_drawings():
            fill = drawing.get("fill")
            stroke = drawing.get("color")
            rect = drawing.get("rect")

            if rect is None:
                continue

            has_rgb_fill = fill is not None and len(fill) == 3
            has_rgb_stroke = stroke is not None and len(stroke) == 3

            if has_rgb_fill or has_rgb_stroke:
                rgb_area += abs(rect.width * rect.height)

        rgb_area_by_page[page_index] = (
            round((rgb_area / page_area) * 100, 2)
            if page_area else 0
        )

    doc.close()
    return rgb_area_by_page


def calculate_tac_area_percent(pdf_path):
    """
    Calcula área aproximada para objetos vectoriales con fill.
    MVP:
    - PyMuPDF puede convertir CMYK a RGB.
    - TAC real viene del parser técnico.
    - Esta función estima área afectada.
    """

    tac_area_by_page = {}

    doc = fitz.open(pdf_path)

    for page_index, page in enumerate(doc, start=1):
        page_area = abs(page.rect.width * page.rect.height)
        tac_area = 0

        for drawing in page.get_drawings():
            fill = drawing.get("fill")
            rect = drawing.get("rect")

            if fill is None or rect is None:
                continue

            tac_area += abs(rect.width * rect.height)

        tac_area_by_page[page_index] = (
            round((tac_area / page_area) * 100, 2)
            if page_area else 0
        )

    doc.close()
    return tac_area_by_page


def calculate_image_context(pdf_path):
    """
    Calcula contexto básico por imagen:
    - effective_dpi
    - área aproximada
    MVP:
    usa get_image_info cuando está disponible.
    """

    image_context_by_page = {}

    doc = fitz.open(pdf_path)

    for page_index, page in enumerate(doc, start=1):
        page_area = abs(page.rect.width * page.rect.height)
        items = []

        try:
            image_info = page.get_image_info(xrefs=True)
        except Exception:
            image_info = []

        for idx, img in enumerate(image_info, start=1):
            bbox = img.get("bbox")
            width = img.get("width") or 0
            height = img.get("height") or 0

            area_percent = 0
            effective_dpi = None

            if bbox and page_area:
                rect = fitz.Rect(bbox)
                area_percent = round((abs(rect.width * rect.height) / page_area) * 100, 2)

                width_in = rect.width / 72 if rect.width else 0
                height_in = rect.height / 72 if rect.height else 0

                dpi_x = width / width_in if width_in else 0
                dpi_y = height / height_in if height_in else 0

                effective_dpi = round(min(dpi_x, dpi_y), 1) if dpi_x and dpi_y else None

            items.append({
                "image_index": idx,
                "effective_dpi": effective_dpi,
                "object_area_percent": area_percent,
                "image_role": "unknown"
            })

        image_context_by_page[page_index] = items

    doc.close()
    return image_context_by_page


def parse_overprint_flags(value):
    value = str(value)

    return {
        "has_overprint_fill": "has_overprint_fill=True" in value,
        "has_overprint_stroke": "has_overprint_stroke=True" in value
    }


def mark_area_flags(item, small_threshold=3, large_threshold=15):
    area = item.get("object_area_percent")

    if area is None:
        item["is_large_area"] = False
        item["is_small_object"] = False
        return item

    area = float(area)

    item["is_large_area"] = area >= large_threshold
    item["is_small_object"] = area < small_threshold

    return item


def enrich_context(findings, pdf_path=None):
    """
    Enriquece findings técnicos con contexto base validado.
    """

    enriched = []

    rgb_area_by_page = {}
    tac_area_by_page = {}
    image_context_by_page = {}

    if pdf_path:
        rgb_area_by_page = calculate_rgb_area_percent(pdf_path)
        tac_area_by_page = calculate_tac_area_percent(pdf_path)
        image_context_by_page = calculate_image_context(pdf_path)

    image_counter_by_page = {}

    for finding in findings:
        item = finding.copy()

        check = item.get("check", "")
        value = item.get("value", "")
        page = item.get("page", 1)

        item.setdefault("object_area_percent", None)
        item.setdefault("page_area_percent", None)
        item.setdefault("is_large_area", False)
        item.setdefault("is_small_object", False)
        item.setdefault("is_printable", True)
        item.setdefault("object_type", "unknown")
        item.setdefault("layer_hint", "ARTWORK")

        if check == "RGB_OBJECT":
            item["object_type"] = "vector"
            area = rgb_area_by_page.get(page, 0)
            item["object_area_percent"] = area
            mark_area_flags(item)

        elif check == "LOW_IMAGE_RESOLUTION":
            item["object_type"] = "image"

            current_idx = image_counter_by_page.get(page, 0)
            page_images = image_context_by_page.get(page, [])

            if current_idx < len(page_images):
                img_ctx = page_images[current_idx]
                item["effective_dpi"] = img_ctx.get("effective_dpi")
                item["object_area_percent"] = img_ctx.get("object_area_percent")
                item["image_role"] = img_ctx.get("image_role", "unknown")

            image_counter_by_page[page] = current_idx + 1
            mark_area_flags(item, small_threshold=1, large_threshold=10)

        elif check == "HIGH_TAC_RISK":
            item["object_type"] = "vector"
            item["object_area_percent"] = tac_area_by_page.get(page, 0)
            item["tac_role"] = item.get("tac_role", "unknown")
            mark_area_flags(item)

        elif check == "FONT_NOT_EMBEDDED":
            item["object_type"] = "text"
            item["object_area_percent"] = 1
            item["is_small_object"] = True
            item["is_large_area"] = False

        elif check == "OVERPRINT_RISK":
            item["object_type"] = "vector"
            item["object_role"] = item.get("object_role", "unknown")
            flags = parse_overprint_flags(value)
            item["has_overprint_fill"] = item.get("has_overprint_fill", flags["has_overprint_fill"])
            item["has_overprint_stroke"] = item.get("has_overprint_stroke", flags["has_overprint_stroke"])
            item["object_area_percent"] = item.get("object_area_percent") or 100
            mark_area_flags(item)

        elif check == "WHITE_INK_RISK":
            item["object_type"] = "separation"
            item["object_role"] = "white_ink"
            item["is_printable"] = True
            item["white_names_detected"] = value

        elif check == "SPOT_COLOR_RISK":
            item["object_type"] = "separation"
            item["is_printable"] = True

        elif check == "SEPARATION_COUNT_RISK":
            item["object_type"] = "separation_summary"
            item["is_printable"] = True

        elif check == "PDF_STRUCTURE_RISK":
            item["object_type"] = "pdf_structure"
            item["is_printable"] = True

        enriched.append(item)

    return enriched
