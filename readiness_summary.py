"""
readiness_summary.py

Genera resumen ejecutivo del resultado Gate0.

Responsabilidad:
- Convertir readiness assessment + findings en mensaje entendible.
- Crear headline.
- Definir tono.
- Identificar top risks.
- Sugerir siguiente acción.
"""


def build_occurrence_summary(finding):
    """
    Compact occurrence payload for dashboard navigation.
    Keeps only fields useful to move preview/evidence between occurrences.
    """
    allowed = [
        "check",
        "page",
        "value",
        "detail",
        "sample_text",
        "severity",
        "business_severity",
        "risk_reason",
        "action",
        "recommendation",
        "bbox",
        "font_size_pt",
        "text_height_mm",
        "font_name",
        "effective_dpi",
        "minimum_image_dpi",
        "critical_image_dpi",
        "image_index",
        "object_area_percent",
        "image_role",
        "printable_area_source",
        "printable_area_confidence",
        "is_inside_printable_area",
        "printable_area_overlap_percent",
    ]

    return {
        key: finding.get(key)
        for key in allowed
        if finding.get(key) is not None
    }


def occurrence_key(item):
    return (
        item.get("page"),
        str(item.get("bbox")),
        str(item.get("value")),
    )


def order_occurrences(best_finding, occurrences, limit=50):
    """
    Put the selected best finding first, then the rest without duplicates.
    """
    best = build_occurrence_summary(best_finding)
    best_key = occurrence_key(best)

    ordered = []
    seen = set()

    for item in [best] + list(occurrences or []):
        key = occurrence_key(item)
        if key in seen:
            continue
        seen.add(key)
        ordered.append(item)

        if len(ordered) >= limit:
            break

    return ordered





def get_main_reason(top_risks):
    if not top_risks:
        return "No se detectaron riesgos relevantes."

    top = top_risks[0]

    return (
        top.get("risk_reason")
        or top.get("detail")
        or "Se detectó un riesgo relevante que requiere revisión."
    )


def get_simple_risk(top_risks):
    if not top_risks:
        return "El archivo no presenta alertas relevantes para el flujo inicial."

    top = top_risks[0]
    check = top.get("check", "UNKNOWN")

    simple_map = {
        "RGB_OBJECT": "Puede generar variación de color.",
        "LOW_IMAGE_RESOLUTION": "Puede generar pérdida visible de calidad.",
        "BARCODE_RISK": "Puede generar problemas de lectura o rechazo de calidad.",
        "FONT_NOT_EMBEDDED": "Puede modificar texto o apariencia aprobada.",
        "SMALL_TEXT_RISK": "Puede generar problemas de legibilidad.",
        "HIGH_TAC_RISK": "Puede generar problemas de impresión, secado o estabilidad.",
        "OVERPRINT_RISK": "Puede alterar el resultado visual por sobreimpresión.",
        "WHITE_INK_RISK": "Puede afectar la gestión de tinta blanca.",
        "SPOT_COLOR_RISK": "Puede generar confusión o complejidad en separaciones spot.",
        "SEPARATION_COUNT_RISK": "Puede aumentar la complejidad operativa de impresión.",
        "PDF_STRUCTURE_RISK": "Puede afectar procesamiento, RIP o preprensa."
    }

    return simple_map.get(
        check,
        "Puede generar riesgo operativo durante preprensa o producción."
    )


def get_next_action(decision, top_risks):
    if decision == "GO":
        return "Continuar con el flujo normal."

    if decision == "GO_WITH_NOTES":
        return "Continuar, dejando registradas las observaciones detectadas."

    if decision == "HOLD":
        if top_risks:
            return top_risks[0].get(
                "action",
                "Revisar el riesgo principal antes de continuar."
            )
        return "Revisar el archivo antes de continuar."

    if decision == "NO_GO":
        if top_risks:
            return top_risks[0].get(
                "action",
                "Corregir el archivo antes de avanzar."
            )
        return "Corregir el archivo antes de avanzar."

    return "Revisar resultado del análisis."


def get_tone(decision):
    if decision == "GO":
        return "positive"

    if decision == "GO_WITH_NOTES":
        return "caution"

    if decision == "HOLD":
        return "review"

    if decision == "NO_GO":
        return "critical"

    return "neutral"


def build_headline(status, decision, score):
    if decision == "GO":
        return f"Archivo listo para continuar. Score {score}/100."

    if decision == "GO_WITH_NOTES":
        return f"Archivo puede continuar con observaciones. Score {score}/100."

    if decision == "HOLD":
        return f"Archivo requiere revisión antes de avanzar. Score {score}/100."

    if decision == "NO_GO":
        return f"Archivo no debe avanzar sin corrección. Score {score}/100."

    return f"Resultado de análisis Gate0. Score {score}/100."


def build_user_message(decision, main_reason, next_action):
    return (
        f"{main_reason} "
        f"Siguiente acción recomendada: {next_action}"
    )


def build_readiness_summary(readiness_assessment, findings):
    """
    Construye resumen ejecutivo final.
    """

    score = readiness_assessment.get("readiness_score")
    status = readiness_assessment.get("readiness_status")
    decision = readiness_assessment.get("readiness_decision")

    top_risks = sort_top_risks(findings)

    main_reason = get_main_reason(top_risks)
    simple_risk = get_simple_risk(top_risks)
    next_action = get_next_action(decision, top_risks)
    tone = get_tone(decision)
    headline = build_headline(status, decision, score)
    user_message = build_user_message(decision, main_reason, next_action)

    return {
        "headline": headline,
        "decision": decision,
        "tone": tone,
        "score": score,
        "status": status,
        "main_reason": main_reason,
        "simple_risk": simple_risk,
        "next_action": next_action,
        "user_message": user_message,
        "top_risks": top_risks
    }


def classify_fix_type(check):
    autofix_candidates = {
        "RGB_OBJECT",
        "LOW_IMAGE_RESOLUTION",
        "SMALL_TEXT_RISK",
        "BARCODE_RISK",
        "SPOT_COLOR_RISK",
        "SEPARATION_COUNT_RISK",
    }

    manual_required = {
        "FONT_NOT_EMBEDDED",
        "PDF_STRUCTURE_RISK",
    }

    if check in manual_required:
        return "manual"

    if check in autofix_candidates:
        return "assisted"

    return "manual"


def build_fix_plan(findings, limit=6):
    """
    Fix Plan v1:
    Ordena acciones recomendadas desde los findings actuales.
    No ejecuta correcciones.
    No promete autofix.
    """
    if not findings:
        return []

    severity_rank = {
        "CRITICAL": 4,
        "HIGH": 4,
        "WARNING": 3,
        "MEDIUM": 3,
        "INFO": 2,
        "LOW": 1,
        "PASS": 0,
    }

    actionable = []

    for finding in findings:
        severity = str(
            finding.get("business_severity")
            or finding.get("severity")
            or "INFO"
        ).upper()

        if severity in {"PASS", "LOW", "INFO"}:
            continue

        check = finding.get("check", "UNKNOWN_CHECK")

        item = {
            "priority": finding.get("priority", 99),
            "check": check,
            "severity": severity,
            "page": finding.get("page"),
            "bbox": finding.get("bbox"),
            "printable_area_source": finding.get("printable_area_source"),
            "printable_area_confidence": finding.get("printable_area_confidence"),
            "is_inside_printable_area": finding.get("is_inside_printable_area"),
            "printable_area_overlap_percent": finding.get("printable_area_overlap_percent"),
            "problem": (
                finding.get("risk_reason")
                or finding.get("detail")
                or "Hallazgo requiere revisión."
            ),
            "recommended_action": (
                finding.get("action")
                or finding.get("recommendation")
                or "Revisar antes de liberar."
            ),
            "fix_type": classify_fix_type(check),
            "status": "pending",
            "source": "finding",
        }

        actionable.append(item)

    actionable = sorted(
        actionable,
        key=lambda x: (
            x.get("priority", 99),
            -severity_rank.get(x.get("severity", "INFO"), 1),
            x.get("check", ""),
        ),
    )

    for idx, item in enumerate(actionable[:limit], start=1):
        item["step"] = idx

    return actionable[:limit]



# ---------------------------------------------------------------------
# Production Readiness v2
# ---------------------------------------------------------------------

def _pr2_severity(finding):
    return str(
        finding.get("business_severity")
        or finding.get("severity")
        or "INFO"
    ).upper()






def _pr2_review_time(minutes_basis):
    if minutes_basis <= 0:
        return "0–2 minutos"
    if minutes_basis <= 2:
        return "3–5 minutos"
    if minutes_basis <= 4:
        return "5–10 minutos"
    return "10–15 minutos"


def _pr2_primary_reason(status, effective_risks, contextual_risks):
    if status == "READY":
        return "No se detectaron riesgos relevantes que impidan la producción."

    if status == "READY_WITH_NOTES":
        return "El archivo tiene observaciones contextuales, pero no se detectan riesgos que deban bloquear la liberación."

    if status == "REVIEW_REQUIRED":
        if len(effective_risks) == 1:
            return "Hay 1 riesgo que requiere revisión antes de liberar."
        return f"Hay {len(effective_risks)} riesgos que requieren revisión antes de liberar."

    if status == "HIGH_RISK":
        return "El archivo presenta riesgos altos que pueden afectar producción o liberación."

    if status == "NO_GO":
        return "El archivo presenta un riesgo crítico o bloqueante. No se recomienda liberar sin corrección."

    return "Gate0 requiere revisión del archivo antes de liberar."





# ---------------------------------------------------------------------
# Sprint 23B — Production Readiness v2 language refinement
# ---------------------------------------------------------------------

def _pr2_check(finding):
    return str((finding or {}).get("check") or "").upper()


def _pr2_has_white_overprint_context(finding):
    if not finding:
        return False

    check = _pr2_check(finding)
    if check != "OVERPRINT_RISK":
        return False

    context = str(finding.get("overprint_context") or "").upper()

    return bool(
        finding.get("white_ink_present")
        or finding.get("white_detected")
        or finding.get("has_white_ink")
        or finding.get("white_ink_detected")
        or "WHITE" in context
    )


def _pr2_title(finding):
    check = _pr2_check(finding)

    if _pr2_has_white_overprint_context(finding):
        return "Validar sobreimpresión con blanco"

    names = {
        "RGB_OBJECT": "Validar objetos RGB",
        "LOW_IMAGE_RESOLUTION": "Revisar imagen de baja resolución",
        "BARCODE_RISK": "Validar Barcode / QR",
        "SMALL_TEXT_RISK": "Revisar texto pequeño",
        "FONT_NOT_EMBEDDED": "Corregir fuente no embebida",
        "HIGH_TAC_RISK": "Revisar TAC alto",
        "OVERPRINT_RISK": "Validar sobreimpresión",
        "SPOT_COLOR_RISK": "Revisar tintas spot / separaciones",
        "SEPARATION_COUNT_RISK": "Revisar cantidad de separaciones",
        "PDF_STRUCTURE_RISK": "Revisar estructura del PDF",
        "WHITE_INK_RISK": "Validar blanco",
    }

    return (
        (finding or {}).get("title")
        or (finding or {}).get("display_name")
        or names.get(check)
        or check
        or "Revisar riesgo técnico"
    )




def _pr2_plain_action(finding):
    if not finding:
        return "Revisar el archivo antes de liberar."

    check = _pr2_check(finding)

    if _pr2_has_white_overprint_context(finding):
        return "Abrir con Overprint Preview y validar que el blanco reserve correctamente."

    if check == "OVERPRINT_RISK":
        return "No bloquear automáticamente. Validar solo si afecta elementos sensibles."

    if check == "SMALL_TEXT_RISK":
        return "Validar legibilidad en el arte final y ajustar tamaño si aplica."

    if check == "LOW_IMAGE_RESOLUTION":
        return "Revisar la imagen en la zona marcada y reemplazarla si afecta calidad visual."

    if check == "HIGH_TAC_RISK":
        return "Validar contra el límite operativo del perfil y ajustar separación si aplica."

    if check == "FONT_NOT_EMBEDDED":
        return "Incrustar fuente, convertir a curvas o corregir el recurso faltante."

    if check == "SPOT_COLOR_RISK":
        return "Validar si las separaciones son productivas, duplicadas o técnicas."

    if check == "SEPARATION_COUNT_RISK":
        return "Revisar si todas las separaciones son necesarias para producción."

    return finding.get("action") or finding.get("recommendation") or "Revisar antes de liberar."


def _pr2_answer(status):
    answers = {
        "READY": "Sí. El archivo está listo para producir.",
        "READY_WITH_NOTES": "Sí, con observaciones. El archivo puede liberarse si las notas son aceptables.",
        "REVIEW_REQUIRED": "Requiere revisión antes de liberar.",
        "HIGH_RISK": "No debería liberarse sin revisión técnica.",
        "NO_GO": "No liberar sin corrección o aprobación técnica.",
    }
    return answers.get(status, "Requiere revisión de preprensa.")


def _pr2_supervisor_summary(status, effective_risks, contextual_risks):
    if status == "READY":
        return "No se detectan condiciones relevantes que deban frenar la producción."

    if status == "READY_WITH_NOTES":
        return (
            "El archivo tiene observaciones contextuales, pero no se identifican riesgos "
            "que deban bloquear la liberación."
        )

    if status == "REVIEW_REQUIRED":
        if len(effective_risks) == 1:
            risk = _pr2_title(effective_risks[0])
            return f"El archivo no necesariamente está mal, pero debe revisarse: {risk}."
        return (
            "El archivo no necesariamente está mal, pero tiene condiciones que deben "
            "validarse antes de producción."
        )

    if status == "HIGH_RISK":
        return (
            "El archivo presenta riesgos altos. La liberación debería quedar retenida "
            "hasta completar revisión técnica."
        )

    if status == "NO_GO":
        return (
            "El archivo presenta una condición crítica o bloqueante. No se recomienda "
            "liberar sin corrección o aprobación técnica explícita."
        )

    return "Gate0 recomienda revisión técnica antes de liberar."







# ---------------------------------------------------------------------
# Sprint 23D — Production Readiness priority logic
# ---------------------------------------------------------------------

def _pr2_to_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default




def _pr2_sort_findings_by_priority(findings):
    findings = findings or []
    return [
        item
        for _, item in sorted(
            enumerate(findings),
            key=lambda pair: (-_pr2_priority_score(pair[1]), pair[0])
        )
    ]


def _pr2_next_step(status, review_items):
    if status == "READY":
        return "Liberar según flujo normal."

    if status == "READY_WITH_NOTES":
        return "Liberar si las observaciones son aceptables para el proceso."

    if review_items:
        titles = [item.get("title") for item in review_items if item.get("title")]
        if len(titles) == 1:
            return f"Revisar primero: {titles[0]}."
        if len(titles) >= 2:
            return f"Revisar primero: {titles[0]} y {titles[1]}."

    if status in {"HIGH_RISK", "NO_GO"}:
        return "Retener liberación y escalar a revisión técnica."

    return "Revisar hallazgos principales antes de liberar."





# ---------------------------------------------------------------------
# Sprint 23D.2 — Deduplicate Production Readiness review items
# ---------------------------------------------------------------------

def _pr2_review_item_key(finding):
    finding = finding or {}
    check = _pr2_check(finding)
    if check:
        return check
    return str(_pr2_title(finding)).upper()




def _pr2_collect_review_items(findings, limit=5):
    """
    Keep Production Readiness concise.

    Multiple occurrences of the same check should appear once, with
    occurrence_count incremented. Example:
    - Revisar texto pequeño (2 ocurrencias)
    instead of:
    - Revisar texto pequeño
    - Revisar texto pequeño
    """
    items = []
    seen = {}

    for finding in findings or []:
        key = _pr2_review_item_key(finding)

        if key in seen:
            item = seen[key]
            item["occurrence_count"] = int(item.get("occurrence_count") or 1) + 1
            item["priority_score"] = max(
                float(item.get("priority_score") or 0),
                round(_pr2_priority_score(finding), 2)
            )
            continue

        if len(items) >= limit:
            continue

        item = _pr2_make_review_item(finding)
        seen[key] = item
        items.append(item)

    return items





# ---------------------------------------------------------------------
# Sprint 25A — Risk Visual Evidence Clustering
# ---------------------------------------------------------------------

VISUAL_CLUSTER_CHECKS = {
    "SMALL_TEXT_RISK",
    "LOW_IMAGE_RESOLUTION",
}


def _vzc_to_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _vzc_parse_bbox(value):
    if value is None:
        return None

    if isinstance(value, (list, tuple)) and len(value) == 4:
        return [_vzc_to_float(x) for x in value]

    if isinstance(value, str):
        parts = [p.strip() for p in value.split(",")]
        if len(parts) == 4:
            return [_vzc_to_float(x) for x in parts]

    return None


def _vzc_bbox_area(bbox):
    if not bbox:
        return 0.0

    x0, y0, x1, y1 = bbox
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def _vzc_bbox_union(a, b):
    if not a:
        return b
    if not b:
        return a

    return [
        min(a[0], b[0]),
        min(a[1], b[1]),
        max(a[2], b[2]),
        max(a[3], b[3]),
    ]


def _vzc_bbox_intersects_or_near(a, b, margin=36):
    """
    Returns True when two bboxes overlap or are close enough to be
    reviewed as one visual zone.

    margin is in PDF points. 36 pt ~= 12.7 mm.
    """
    if not a or not b:
        return False

    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b

    return not (
        ax1 + margin < bx0
        or bx1 + margin < ax0
        or ay1 + margin < by0
        or by1 + margin < ay0
    )


def _vzc_occurrence_sort_key(item):
    bbox = _vzc_parse_bbox(item.get("bbox"))
    return (
        item.get("page") or 0,
        bbox[1] if bbox else 0,
        bbox[0] if bbox else 0,
    )


def build_visual_zones_for_occurrences(check, occurrences, limit=25):
    """
    Groups visual occurrences into approximate review zones.

    This is intentionally conservative:
    - only same page
    - only bbox-based
    - no semantic assumptions
    """
    check = str(check or "").upper()

    if check not in VISUAL_CLUSTER_CHECKS:
        return []

    valid = []
    for item in occurrences or []:
        bbox = _vzc_parse_bbox(item.get("bbox"))
        if bbox and _vzc_bbox_area(bbox) > 0:
            compact = dict(item)
            compact["bbox"] = bbox
            valid.append(compact)

    if not valid:
        return []

    valid = sorted(valid, key=_vzc_occurrence_sort_key)

    zones = []

    for item in valid:
        page = item.get("page") or 1
        bbox = item.get("bbox")
        matched = None

        for zone in zones:
            if zone.get("page") != page:
                continue

            if _vzc_bbox_intersects_or_near(zone.get("bbox"), bbox):
                matched = zone
                break

        if matched is None:
            matched = {
                "zone_index": len(zones),
                "page": page,
                "bbox": bbox,
                "occurrence_count": 0,
                "occurrences": [],
            }
            zones.append(matched)

        matched["bbox"] = _vzc_bbox_union(matched.get("bbox"), bbox)
        matched["occurrence_count"] += 1

        if len(matched["occurrences"]) < limit:
            matched["occurrences"].append(item)

    for idx, zone in enumerate(zones):
        zone["zone_index"] = idx
        zone["bbox"] = [round(x, 2) for x in zone.get("bbox", [])]

    return zones[:limit]


def sort_top_risks(findings, limit=3):
    """
    Ordena hallazgos por prioridad de negocio, evitando repetir el mismo check.

    Sprint 25A:
    - conserva occurrences.
    - agrega visual_zones para checks visuales.
    - mantiene fallback compatible con navegación por ocurrencias.
    """
    if not findings:
        return []

    grouped = {}

    severity_rank = {
        "PASS": 0,
        "INFO": 1,
        "LOW": 1,
        "WARNING": 2,
        "MEDIUM": 2,
        "CRITICAL": 3,
        "HIGH": 3,
    }

    for finding in findings:
        check = finding.get("check", "UNKNOWN")

        business_severity = (
            finding.get("business_severity")
            or finding.get("severity")
            or "INFO"
        )

        priority = finding.get("priority", 99)
        score_weight = finding.get("score_weight", 0)
        severity_score = severity_rank.get(str(business_severity).upper(), 1)

        candidate_sort_key = (
            priority,
            -score_weight,
            -severity_score
        )

        if check not in grouped:
            grouped[check] = {
                "best": finding,
                "occurrence_count": 1,
                "occurrences": [build_occurrence_summary(finding)],
                "max_score_weight": score_weight,
                "max_severity_score": severity_score,
            }
            continue

        grouped[check]["occurrence_count"] += 1

        if len(grouped[check].get("occurrences", [])) < 50:
            grouped[check].setdefault("occurrences", []).append(build_occurrence_summary(finding))

        grouped[check]["max_score_weight"] = max(
            grouped[check]["max_score_weight"],
            score_weight
        )
        grouped[check]["max_severity_score"] = max(
            grouped[check]["max_severity_score"],
            severity_score
        )

        current = grouped[check]["best"]
        current_business_severity = (
            current.get("business_severity")
            or current.get("severity")
            or "INFO"
        )

        current_sort_key = (
            current.get("priority", 99),
            -current.get("score_weight", 0),
            -severity_rank.get(str(current_business_severity).upper(), 1)
        )

        if candidate_sort_key < current_sort_key:
            grouped[check]["best"] = finding

    deduped = []

    for check, data in grouped.items():
        item = dict(data["best"])
        occurrences = order_occurrences(data["best"], data.get("occurrences", []))

        item["occurrence_count"] = data["occurrence_count"]
        item["occurrences"] = occurrences
        item["max_score_weight"] = data["max_score_weight"]
        item["max_severity_score"] = data["max_severity_score"]

        visual_zones = build_visual_zones_for_occurrences(check, occurrences)

        if visual_zones:
            item["visual_zone_count"] = len(visual_zones)
            item["visual_zones"] = visual_zones
            item["visual_occurrence_count"] = sum(
                int(zone.get("occurrence_count") or 0)
                for zone in visual_zones
            )

        deduped.append(item)

    deduped = sorted(
        deduped,
        key=lambda f: (
            -severity_rank.get(str(f.get("business_severity") or f.get("severity") or "INFO").upper(), 1),
            f.get("priority", 99),
            -f.get("score_weight", 0),
            -f.get("occurrence_count", 1)
        )
    )

    actionable = [
        f for f in deduped
        if severity_rank.get(str(f.get("business_severity") or f.get("severity") or "INFO").upper(), 1) >= 2
    ]

    return actionable[:limit]



# ---------------------------------------------------------------------
# Sprint 25B — Printable Area Priority Filter
# ---------------------------------------------------------------------

PRINTABLE_AREA_FILTER_CHECKS = {
    "RGB_OBJECT",
    "LOW_IMAGE_RESOLUTION",
    "SMALL_TEXT_RISK",
    "HIGH_TAC_RISK",
    "BARCODE_RISK",
}




def _pr2_printable_area_overlap(finding):
    return _pr2_to_float(
        finding.get("printable_area_overlap_percent")
        or finding.get("area_overlap_percent")
        or finding.get("visual_area_percent"),
        default=0.0,
    )


def _pr2_outside_confirmed_printable_area(finding):
    finding = finding or {}
    check = _pr2_check(finding)

    if check not in PRINTABLE_AREA_FILTER_CHECKS:
        return False

    if not _pr2_printable_area_confidence_confirmed(finding):
        return False

    if finding.get("is_inside_printable_area") is False:
        overlap = _pr2_printable_area_overlap(finding)
        return overlap <= 1.0

    return False


def _pr2_inside_confirmed_printable_area(finding):
    finding = finding or {}
    check = _pr2_check(finding)

    if check not in PRINTABLE_AREA_FILTER_CHECKS:
        return False

    if not _pr2_printable_area_confidence_confirmed(finding):
        return False

    return finding.get("is_inside_printable_area") is True


def _pr2_printable_area_status(finding):
    if _pr2_outside_confirmed_printable_area(finding):
        return "OUTSIDE_CONFIRMED_PRINTABLE_AREA"

    if _pr2_inside_confirmed_printable_area(finding):
        return "INSIDE_CONFIRMED_PRINTABLE_AREA"

    if _pr2_printable_area_confidence_confirmed(finding):
        return "PARTIAL_OR_UNCLEAR_PRINTABLE_AREA"

    return "PRINTABLE_AREA_NOT_CONFIRMED"


def _pr2_is_contextual_non_blocking(finding):
    severity = _pr2_severity(finding)
    score_weight = finding.get("score_weight", 0) or 0
    is_blocking = bool(finding.get("is_blocking"))

    if _pr2_outside_confirmed_printable_area(finding):
        return True

    if severity == "INFO":
        return True

    if score_weight == 0 and not is_blocking:
        return True

    return False


def _pr2_priority_score(finding):
    """
    Operational priority for Production Readiness v2.

    Sprint 25B:
    - confirmed outside printable area strongly lowers priority.
    - confirmed inside printable area increases confidence/priority.
    """
    finding = finding or {}
    check = _pr2_check(finding)
    severity = _pr2_severity(finding)

    score = 0.0

    if severity == "CRITICAL":
        score += 100
    elif severity == "WARNING":
        score += 60
    elif severity == "INFO":
        score += 10

    if finding.get("is_blocking"):
        score += 80

    score_weight = _pr2_to_float(finding.get("score_weight"), 0)
    score += min(max(score_weight, 0), 30)

    check_weights = {
        "FONT_NOT_EMBEDDED": 42,
        "HIGH_TAC_RISK": 36,
        "OVERPRINT_RISK": 34,
        "SMALL_TEXT_RISK": 28,
        "LOW_IMAGE_RESOLUTION": 24,
        "BARCODE_RISK": 24,
        "SEPARATION_COUNT_RISK": 22,
        "SPOT_COLOR_RISK": 20,
        "RGB_OBJECT": 18,
        "PDF_STRUCTURE_RISK": 16,
        "WHITE_INK_RISK": 14,
    }

    score += check_weights.get(check, 10)

    detail_text = " ".join([
        str(finding.get("detail") or ""),
        str(finding.get("risk_reason") or ""),
        str(finding.get("expert_comment") or ""),
    ]).lower()

    if check == "OVERPRINT_RISK" and severity == "WARNING":
        score += 24

        if (
            "área visual significativa" in detail_text
            or "area visual significativa" in detail_text
            or "visual significativa" in detail_text
            or "visual significant" in detail_text
            or "100.00%" in detail_text
            or "100%" in detail_text
        ):
            score += 26

    if _pr2_has_white_overprint_context(finding):
        score += 24

    if check == "OVERPRINT_RISK" and severity == "INFO":
        score -= 18

    if _pr2_outside_confirmed_printable_area(finding):
        score -= 80

    elif _pr2_inside_confirmed_printable_area(finding):
        score += 14

    else:
        if finding.get("is_inside_printable_area") is True:
            score += 8
        elif finding.get("is_inside_printable_area") is False:
            score -= 8

    overlap = _pr2_printable_area_overlap(finding)

    if overlap >= 80:
        score += 8
    elif overlap == 0 and finding.get("is_inside_printable_area") is False:
        score -= 6

    if finding.get("requires_visual_validation"):
        score += 4

    return score


def _pr2_plain_reason(finding):
    if not finding:
        return ""

    check = _pr2_check(finding)

    if _pr2_outside_confirmed_printable_area(finding):
        return (
            "El hallazgo está fuera del área imprimible confirmada. "
            "Se mantiene como observación, pero no debería bloquear la liberación."
        )

    if _pr2_has_white_overprint_context(finding):
        return (
            "Hay señales de sobreimpresión y el archivo contiene blanco. "
            "No es un defecto confirmado, pero debe validarse antes de liberar."
        )

    if check == "OVERPRINT_RISK":
        return (
            "Hay señales de sobreimpresión en el PDF. Puede ser normal, "
            "pero conviene validar si afecta elementos críticos."
        )

    if check == "SMALL_TEXT_RISK":
        return (
            "Hay texto pequeño que puede comprometer legibilidad si está dentro "
            "de una zona relevante del diseño."
        )

    if check == "LOW_IMAGE_RESOLUTION":
        return (
            "Hay una imagen con resolución efectiva baja que podría perder definición en impresión."
        )

    if check == "HIGH_TAC_RISK":
        return (
            "Hay zonas con cobertura total de tinta alta que pueden generar riesgo operativo."
        )

    if check == "FONT_NOT_EMBEDDED":
        return (
            "Hay fuentes no embebidas. El arte puede cambiar al abrirse o procesarse."
        )

    if check == "SPOT_COLOR_RISK":
        return (
            "Hay una condición en tintas spot o separaciones especiales que requiere revisión."
        )

    if check == "SEPARATION_COUNT_RISK":
        return (
            "La cantidad de separaciones imprimibles requiere validación antes de liberar."
        )

    return (
        finding.get("risk_reason")
        or finding.get("detail")
        or finding.get("expert_comment")
        or "Condición técnica a revisar."
    )


def _pr2_make_review_item(finding):
    return {
        "check": finding.get("check"),
        "title": _pr2_title(finding),
        "severity": _pr2_severity(finding),
        "priority_score": round(_pr2_priority_score(finding), 2),
        "reason": _pr2_plain_reason(finding),
        "action": _pr2_plain_action(finding),
        "occurrence_count": 1,
        "printable_area_status": _pr2_printable_area_status(finding),
    }


def build_production_readiness_v2(readiness_assessment, priority_findings, operational_profile=None):
    """
    Production Readiness v2 with printable area priority filter.

    If a visual finding is confirmed outside printable area, it is treated
    as contextual instead of an effective production risk.
    """
    readiness_assessment = readiness_assessment or {}
    priority_findings = priority_findings or []
    operational_profile = operational_profile or {}

    decision = readiness_assessment.get("readiness_decision") or "-"
    legacy_status = readiness_assessment.get("readiness_status") or "-"
    score = readiness_assessment.get("readiness_score")

    critical_risks = []
    warning_risks = []
    contextual_risks = []

    for finding in priority_findings:
        severity = _pr2_severity(finding)

        if _pr2_is_contextual_non_blocking(finding):
            contextual_risks.append(finding)
            continue

        if severity == "CRITICAL" or finding.get("is_blocking"):
            critical_risks.append(finding)
        elif severity == "WARNING":
            warning_risks.append(finding)

    critical_risks = _pr2_sort_findings_by_priority(critical_risks)
    warning_risks = _pr2_sort_findings_by_priority(warning_risks)
    contextual_risks = _pr2_sort_findings_by_priority(contextual_risks)

    effective_risks = critical_risks + warning_risks

    if any(f.get("is_blocking") for f in critical_risks) or decision == "NO_GO":
        status = "NO_GO"
        production_decision = "No liberar sin corrección o aprobación técnica."
    elif critical_risks:
        status = "HIGH_RISK"
        production_decision = "Retener liberación hasta revisión técnica."
    elif warning_risks:
        status = "REVIEW_REQUIRED"
        production_decision = "Revisar antes de liberar."
    elif contextual_risks:
        status = "READY_WITH_NOTES"
        production_decision = "Liberable con observaciones."
    else:
        status = "READY"
        production_decision = "Liberable."

    primary = effective_risks[0] if effective_risks else (contextual_risks[0] if contextual_risks else None)

    review_items = _pr2_collect_review_items(effective_risks, limit=5)

    if not review_items and contextual_risks:
        review_items = _pr2_collect_review_items(contextual_risks, limit=3)

    review_time_basis = len(review_items)

    if any(int(item.get("occurrence_count") or 1) > 1 for item in review_items):
        review_time_basis += 1

    if critical_risks:
        review_time_basis += 2

    confidence = "Media"
    if status in {"READY", "NO_GO"}:
        confidence = "Alta"

    answer = _pr2_answer(status)
    supervisor_summary = _pr2_supervisor_summary(status, effective_risks, contextual_risks)
    next_step = _pr2_next_step(status, review_items)

    return {
        "version": "v2_printable_area_priority",
        "question": "¿Está este archivo listo para producir?",
        "answer": answer,
        "status": status,
        "legacy_status": legacy_status,
        "legacy_decision": decision,
        "decision": production_decision,
        "score": score,
        "confidence": confidence,
        "main_reason": supervisor_summary,
        "supervisor_summary": supervisor_summary,
        "next_step": next_step,
        "primary_risk": _pr2_title(primary) if primary else None,
        "primary_risk_reason": _pr2_plain_reason(primary) if primary else None,
        "primary_risk_priority_score": round(_pr2_priority_score(primary), 2) if primary else None,
        "primary_printable_area_status": _pr2_printable_area_status(primary) if primary else None,
        "review_time_estimate": _pr2_review_time(review_time_basis),
        "effective_risk_count": len(effective_risks),
        "critical_risk_count": len(critical_risks),
        "warning_risk_count": len(warning_risks),
        "contextual_note_count": len(contextual_risks),
        "what_to_review_first": review_items,
        "operational_context": {
            "profile_name": operational_profile.get("profile_name"),
            "process": operational_profile.get("process"),
            "substrate_family": operational_profile.get("substrate_family"),
        },
        "product_note": (
            "Production Readiness v2 es una capa ejecutiva de decisión. "
            "No reemplaza aún el criterio final de preprensa."
        ),
    }



# ---------------------------------------------------------------------
# Sprint 25B.1 — Do not confuse UNCONFIRMED with CONFIRMED
# ---------------------------------------------------------------------

def _pr2_printable_area_confidence_confirmed(finding):
    """
    Returns True only for explicitly confirmed printable-area sources.

    Important:
    - `UNCONFIRMED_FULL_PAGE` must NOT be treated as confirmed.
    - Avoid substring checks like `"CONFIRMED" in source` because
      UNCONFIRMED contains CONFIRMED.
    """
    finding = finding or {}

    source = str(finding.get("printable_area_source") or "").upper().strip()
    confidence = str(finding.get("printable_area_confidence") or "").upper().strip()

    unconfirmed_markers = {
        "UNCONFIRMED",
        "UNCONFIRMED_FULL_PAGE",
        "LOW",
        "UNKNOWN",
        "NONE",
        "",
    }

    if source in unconfirmed_markers:
        return False

    if source.startswith("UNCONFIRMED"):
        return False

    if confidence in unconfirmed_markers:
        return False

    if confidence.startswith("UNCONFIRMED"):
        return False

    confirmed_sources = {
        "TRIMBOX_CONFIRMED",
        "ARTBOX_CONFIRMED",
        "CROPBOX_CONFIRMED",
        "BLEEDBOX_CONFIRMED",
    }

    confirmed_confidence = {
        "CONFIRMED",
        "HIGH",
    }

    if source in confirmed_sources:
        return True

    if confidence in confirmed_confidence:
        return True

    return False

