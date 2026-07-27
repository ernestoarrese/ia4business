import json
import re
from pathlib import Path


def default_operational_profile(profile_path="profiles/flexo_pet_bopp_default.json"):
    """
    Fallback explícito cuando no existe archivo de perfil.

    Esto evita que Gate0 opere con supuestos invisibles.
    El objetivo comercial es que todo análisis indique siempre contra qué estándar fue evaluado.
    """
    return {
        "profile_name": "flexo_pet_bopp_default",
        "profile_version": "fallback",
        "profile_status": "FALLBACK_DEFAULT",
        "profile_source": str(profile_path),
        "profile_file_found": False,
        "process": "flexo",
        "substrate_family": "PET_BOPP",
        "description": "Fallback interno. Crear o revisar profiles/flexo_pet_bopp_default.json para usar conocimiento operativo versionado.",
        "tac": {
            "max_tac_percent": 280
        },
        "image_resolution": {
            "minimum_dpi": 250,
            "recommended_dpi": 300
        },
        "separations": {
            "normal_max_printable": 8,
            "info_max_printable": 10,
            "warning_max_printable": 12,
            "critical_above_printable": 12
        },
        "small_text": {
            "enabled": True,
            "warning_threshold_pt": 5.0,
            "critical_threshold_pt": 4.0
        }
    }


def load_profile(profile_path="profiles/flexo_pet_bopp_default.json"):
    path = Path(profile_path)

    if not path.exists():
        return default_operational_profile(profile_path)

    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        profile = default_operational_profile(profile_path)
        profile["profile_status"] = "FALLBACK_INVALID_JSON"
        profile["profile_file_found"] = True
        return profile

    profile.setdefault("profile_name", path.stem)
    profile.setdefault("profile_version", "unknown")
    profile.setdefault("profile_status", "FILE_LOADED")
    profile.setdefault("process", "unknown")
    profile.setdefault("substrate_family", "unknown")
    profile["profile_source"] = str(path)
    profile["profile_file_found"] = True

    return profile


def summarize_operational_profile(profile):
    small_text = profile.get("small_text", {}) if isinstance(profile, dict) else {}
    tac = profile.get("tac", {}) if isinstance(profile, dict) else {}
    image_resolution = profile.get("image_resolution", {}) if isinstance(profile, dict) else {}
    separations = profile.get("separations", {}) if isinstance(profile, dict) else {}
    barcode = profile.get("barcode", {}) if isinstance(profile, dict) else {}

    return {
        "profile_name": profile.get("profile_name"),
        "profile_version": profile.get("profile_version"),
        "profile_status": profile.get("profile_status"),
        "profile_source": profile.get("profile_source"),
        "profile_file_found": profile.get("profile_file_found"),
        "process": profile.get("process"),
        "substrate_family": profile.get("substrate_family"),
        "tac_max_percent": tac.get("max_tac_percent"),
        "small_text_warning_threshold_pt": small_text.get("warning_threshold_pt"),
        "small_text_critical_threshold_pt": small_text.get("critical_threshold_pt"),
        "image_minimum_dpi": image_resolution.get("minimum_dpi"),
        "image_recommended_dpi": image_resolution.get("recommended_dpi"),
        "separation_normal_max_printable": separations.get("normal_max_printable"),
        "separation_warning_max_printable": separations.get("warning_max_printable"),
        "separation_critical_above_printable": separations.get("critical_above_printable"),
        "barcode_image_minimum_dpi": barcode.get("minimum_image_dpi", 300),
        "barcode_image_critical_dpi": barcode.get("critical_image_dpi", 200)
    }





def severity_meta(severity, score_weight_map=None):
    """
    Devuelve prioridad y peso de score según severidad de negocio.
    """
    severity = str(severity or "INFO").upper()
    score_weight_map = score_weight_map or {}

    priority_map = {
        "CRITICAL": 1,
        "WARNING": 2,
        "INFO": 3,
        "PASS": 99,
    }

    return (
        priority_map.get(severity, 3),
        score_weight_map.get(severity, 0)
    )


def upgrade_severity(severity):
    """
    Eleva severidad un nivel para objetos críticos como logos, producto o información relevante.
    """
    severity = str(severity or "INFO").upper()

    if severity == "INFO":
        return "WARNING"
    if severity == "WARNING":
        return "CRITICAL"

    return severity


def apply_business_fields(finding, severity, risk_area, risk_reason, priority, action, score_weight):
    """
    Agrega campos de negocio estándar a un hallazgo técnico.
    """
    finding["business_severity"] = severity
    finding["risk_area"] = risk_area
    finding["risk_reason"] = risk_reason
    finding["priority"] = priority
    finding["action"] = action
    finding["score_weight"] = score_weight

    return finding


def extract_dpi_value(value):
    """
    Extrae un valor de DPI desde dict, número o texto.
    """
    import re

    if isinstance(value, dict):
        for key in ["effective_dpi", "dpi", "value", "detail"]:
            if key in value:
                extracted = extract_dpi_value(value.get(key))
                if extracted is not None:
                    return extracted
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if value is None:
        return None

    text_value = str(value)

    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*dpi", text_value, flags=re.IGNORECASE)
    if match:
        return float(match.group(1))

    match = re.search(r"([0-9]+(?:\.[0-9]+)?)", text_value)
    if match:
        return float(match.group(1))

    return None



def is_outside_confirmed_printable_area(finding):
    return (
        finding.get("is_inside_printable_area") is False
        and finding.get("printable_area_source") in {
            "TRIMBOX_CONFIRMED",
            "ARTBOX_FALLBACK",
            "CROPBOX_FALLBACK",
        }
    )


def outside_printable_area_business_result(finding, risk_area):
    source = finding.get("printable_area_source", "UNKNOWN")
    overlap = finding.get("printable_area_overlap_percent")
    reason = (
        f"El hallazgo está fuera del área imprimible/relevante confirmada ({source}). "
        f"Solape con área útil: {overlap}%."
    )
    action = "No bloquear por este hallazgo; validar si corresponde a plano, referencia o información técnica fuera del arte."
    p, w = severity_meta("INFO", {"INFO": 1})
    return apply_business_fields(finding, "INFO", risk_area, reason, p, action, w)


def evaluate_barcode_risk(finding, profile):
    effective_dpi = float(finding.get("effective_dpi") or 0)
    minimum_dpi = float(finding.get("minimum_image_dpi") or 300)
    critical_dpi = float(finding.get("critical_image_dpi") or 200)
    candidate_type = finding.get("barcode_candidate_type", "barcode")
    confidence = str(finding.get("barcode_confidence", "Baja")).lower()
    method = str(finding.get("detection_method", "")).lower()

    # MVP safety:
    # If Barcode Intelligence cannot strongly confirm the candidate,
    # do not allow it to become a CRITICAL Top Risk.
    strong_method = (
        "barcode_pattern" in method
        or "wide_image_geometry_barcode_pattern" in method
    )
    strong_confidence = confidence in {"media", "alta", "high"}

    if not strong_method and not strong_confidence:
        sev = "INFO"
        reason = (
            f"Posible {candidate_type} con {effective_dpi:.0f} dpi, pero la confianza de detección es baja. "
            "Validar visualmente; no se confirma como código funcional."
        )
        action = "Revisar manualmente si el elemento realmente es un código de barras o QR."
        p, w = severity_meta(sev, {"INFO": 1})
        return apply_business_fields(finding, sev, "Código de barras / QR", reason, p, action, w)

    if effective_dpi < critical_dpi:
        sev = "CRITICAL"
        reason = (
            f"Se detectó un posible {candidate_type} como imagen de {effective_dpi:.0f} dpi efectivos. "
            "Puede haber riesgo de lectura si el código está rasterizado, escalado o con baja resolución."
        )
        action = "Validar escaneo antes de liberar."
    elif effective_dpi < minimum_dpi:
        sev = "WARNING"
        reason = (
            f"Se detectó un posible {candidate_type} por debajo del mínimo recomendado "
            f"({effective_dpi:.0f} dpi < {minimum_dpi:.0f} dpi)."
        )
        action = "Validar legibilidad y escaneo."
    else:
        sev = "PASS"
        reason = "Candidato barcode/QR dentro de resolución mínima."
        action = "Sin acción requerida."

    p, w = severity_meta(sev, {"CRITICAL": 30, "WARNING": 18, "INFO": 1})
    return apply_business_fields(finding, sev, "Código de barras / QR", reason, p, action, w)

def evaluate_low_image_resolution(finding, profile):
    if is_outside_confirmed_printable_area(finding):
        return outside_printable_area_business_result(finding, "Resolución de imagen")

    dpi = extract_dpi_value(finding)
    area = float(finding.get("object_area_percent") or 0)
    image_role = finding.get("image_role", "unknown")
    is_printable = finding.get("is_printable", True)

    if not is_printable:
        sev = "INFO"
    elif dpi >= 250:
        sev = "PASS"
    elif dpi >= 200:
        if area < 1:
            sev = "INFO"
        elif area <= 10:
            sev = "WARNING"
        else:
            sev = "CRITICAL"
    elif dpi >= 150:
        sev = "INFO" if area < 3 else "WARNING"
    else:
        sev = "WARNING" if area < 3 else "CRITICAL"

    if image_role in ["barcode", "qr"]:
        sev = "CRITICAL"
    elif image_role in ["product", "face", "logo", "brand"]:
        sev = upgrade_severity(sev)

    p, w = severity_meta(sev, {"CRITICAL": 30, "WARNING": 15, "INFO": 1})
    reason = f"Imagen con resolución efectiva {dpi:.0f} dpi, área {area:.2f}% e image_role '{image_role}'."
    return apply_business_fields(finding, sev, "Resolución / Imagen", reason, p, "Revisar resolución efectiva y solicitar imagen en mayor resolución si aplica.", w)



def evaluate_small_text_risk(finding, profile):
    if is_outside_confirmed_printable_area(finding):
        return outside_printable_area_business_result(finding, "Texto pequeño / legibilidad")

    small_text_profile = profile.get("small_text", {}) if isinstance(profile, dict) else {}

    enabled = small_text_profile.get("enabled", True)
    warning_threshold = float(small_text_profile.get("warning_threshold_pt", 5.0))
    critical_threshold = float(small_text_profile.get("critical_threshold_pt", 4.0))

    size_pt = float(finding.get("font_size_pt") or 0)
    height_mm = float(finding.get("text_height_mm") or 0)
    sample = finding.get("sample_text") or finding.get("value") or ""

    if not enabled:
        sev = "PASS"
    elif size_pt <= 0:
        sev = "INFO"
    elif size_pt < critical_threshold:
        sev = "CRITICAL"
    elif size_pt < warning_threshold:
        sev = "WARNING"
    else:
        sev = "PASS"

    reason = (
        f"Texto vivo pequeño detectado: {size_pt:.2f} pt / {height_mm:.2f} mm aprox. "
        f"Límites del perfil: WARNING < {warning_threshold:.2f} pt, "
        f"CRITICAL < {critical_threshold:.2f} pt. "
        f"Muestra: '{sample[:40]}'."
    )

    action = (
        "Revisar legibilidad según proceso, sustrato y condición de impresión. "
        "Validar especialmente legales, ingredientes, advertencias y textos negativos."
    )

    p, w = severity_meta(sev, {"CRITICAL": 35, "WARNING": 18, "INFO": 1})
    result = apply_business_fields(finding, sev, "Texto / Legibilidad", reason, p, action, w)

    result["profile_warning_threshold_pt"] = warning_threshold
    result["profile_critical_threshold_pt"] = critical_threshold
    result["profile_small_text_enabled"] = enabled

    return result




def evaluate_overprint_risk(finding, profile):
    area = float(finding.get("object_area_percent") or 0)
    has_op = finding.get("has_overprint_fill") or finding.get("has_overprint_stroke")

    if not has_op:
        sev, reason, action = "PASS", "Objeto sin sobreimpresión activa.", "Sin acción requerida."
    elif finding.get("white_ink_detected") is True:
        sev = "WARNING"
        reason = "White Ink y Overprint detectados en la misma página. No se confirma aún que el objeto con overprint sea el blanco."
        action = "Verificar si el blanco tiene sobreimpresión activa y si genera reserva correctamente."
    elif area > 10:
        sev = "WARNING"
        reason = f"Sobreimpresión detectada en área visual significativa ({area:.2f}%)."
        action = "Verificar intención de diseño y efecto visual."
    else:
        sev = "INFO"
        reason = "Sobreimpresión detectada. Verificar intención de diseño."
        action = "Confirmar si corresponde a trapping manual, refuerzo cromático o estrategia normal."

    p, w = severity_meta(sev, {"WARNING": 20, "INFO": 1})
    return apply_business_fields(finding, sev, "Sobreimpresión", reason, p, action, w)


def evaluate_white_ink_risk(finding, profile):
    detail = finding.get("detail", "")
    value = finding.get("value", "")

    if "Múltiples" in detail or "," in value:
        sev = "WARNING"
        reason = "Múltiples separaciones asociadas a blanco. Puede generar duplicidad o confusión de planchas."
        action = "Unificar nomenclatura de blanco y validar separación correcta."
    elif "no estándar" in detail:
        sev = "WARNING"
        reason = "Separación blanca con nombre no estándar."
        action = "Normalizar nombre de blanco."
    else:
        sev = "INFO"
        reason = "Separación blanca detectada."
        action = "Confirmar uso de blanco según especificación."

    p, w = severity_meta(sev, {"WARNING": 15, "INFO": 1})
    return apply_business_fields(finding, sev, "Tinta blanca / Separaciones", reason, p, action, w)


def evaluate_spot_color_risk(finding, profile):
    detail = finding.get("detail", "")
    count = int(finding.get("printable_spot_count") or 0)

    if "Exceso crítico" in detail or count > 12:
        sev = "CRITICAL"
        reason = "Exceso crítico de tintas spot imprimibles."
        action = "Racionalizar separaciones spot antes de liberar."
    elif any(x in detail for x in ["Múltiples", "genérico", "duplicidad"]) or count >= 9:
        sev = "WARNING"
        reason = "Riesgo asociado a gestión de separaciones spot."
        action = finding.get("recommendation", "Revisar y normalizar separaciones spot.")
    else:
        sev = "INFO"
        reason = "Información operativa sobre separaciones spot."
        action = finding.get("recommendation", "Validar separaciones spot.")

    p, w = severity_meta(sev, {"CRITICAL": 35, "WARNING": 15, "INFO": 1})
    return apply_business_fields(finding, sev, "Separaciones spot", reason, p, action, w)


def evaluate_separation_count_risk(finding, profile):
    count = int(finding.get("printable_separation_count") or 0)
    source = finding.get("process_count_source", "NO_PROCESS_COLORS_DETECTED")
    process_count = int(finding.get("process_count") or finding.get("process_color_count") or 0)
    spot_count = int(finding.get("printable_spot_count") or 0)

    detail_suffix = f" Conteo operativo: {count} imprimibles (proceso={process_count}, spots={spot_count}). Base proceso: {source}."

    if count <= 8:
        sev = "PASS"
        reason = f"Cantidad de separaciones dentro de rango normal ({count}).{detail_suffix}"
        action = "Sin acción requerida."
    elif count in [9, 10]:
        sev = "INFO"
        reason = f"Cantidad elevada de separaciones imprimibles ({count}).{detail_suffix}"
        action = "Verificar complejidad operativa y disponibilidad de estaciones."
    elif count in [11, 12]:
        sev = "WARNING"
        reason = f"Cantidad alta de separaciones imprimibles ({count}).{detail_suffix}"
        action = "Revisar racionalización de spots."
    else:
        sev = "CRITICAL"
        reason = f"Exceso crítico de separaciones imprimibles ({count}).{detail_suffix}"
        action = "Validar capacidad de prensa y racionalización de separaciones."

    p, w = severity_meta(sev, {"CRITICAL": 35, "WARNING": 20, "INFO": 1})
    return apply_business_fields(finding, sev, "Complejidad de separaciones", reason, p, action, w)


def evaluate_pdf_structure_risk(finding, profile):
    tech = finding.get("severity", "LOW")

    if tech == "HIGH":
        sev = "CRITICAL"
        reason = "Condición estructural crítica del PDF."
        action = "Optimizar, reconstruir o validar archivo."
    elif tech == "MEDIUM":
        sev = "WARNING"
        reason = "Complejidad estructural elevada."
        action = "Revisar optimización antes de RIP/trapping/imposición."
    else:
        sev = "PASS"
        reason = "Estructura PDF dentro de parámetros normales."
        action = "Sin acción requerida."

    p, w = severity_meta(sev, {"CRITICAL": 35, "WARNING": 20})
    return apply_business_fields(finding, sev, "Estructura PDF", reason, p, action, w)


def enrich_finding(finding, profile):
    check = str(finding.get("check", "")).strip()

    if check == "RGB_OBJECT":
        return evaluate_rgb_object(finding.copy(), profile)
    if check == "BARCODE_RISK":
        return evaluate_barcode_risk(finding.copy(), profile)
    if check == "LOW_IMAGE_RESOLUTION":
        return evaluate_low_image_resolution(finding.copy(), profile)
    if check == "SMALL_TEXT_RISK":
        return evaluate_small_text_risk(finding.copy(), profile)
    if check == "FONT_NOT_EMBEDDED":
        return evaluate_font_not_embedded(finding.copy(), profile)
    if check == "HIGH_TAC_RISK":
        return evaluate_high_tac_risk(finding.copy(), profile)
    if check == "OVERPRINT_RISK":
        return evaluate_overprint_risk(finding.copy(), profile)
    if check == "WHITE_INK_RISK":
        return evaluate_white_ink_risk(finding.copy(), profile)
    if check == "SPOT_COLOR_RISK":
        return evaluate_spot_color_risk(finding.copy(), profile)
    if check == "SEPARATION_COUNT_RISK":
        return evaluate_separation_count_risk(finding.copy(), profile)
    if check == "PDF_STRUCTURE_RISK":
        return evaluate_pdf_structure_risk(finding.copy(), profile)

    return apply_business_fields(
        finding.copy(),
        finding.get("severity", "INFO"),
        "General",
        "Hallazgo pendiente de clasificación específica.",
        3,
        "Revisar manualmente.",
        10
    )


def calculate_risk_score(enriched_findings):
    if not enriched_findings:
        return 0
    score = 0
    severity_weight = {"CRITICAL": 40, "WARNING": 25, "INFO": 10, "PASS": 0}
    for f in enriched_findings:
        sev = f.get("business_severity", "INFO")
        score += f.get("score_weight", 10) + severity_weight.get(sev, 10)
    return min(score, 100)


def define_risk_level(score):
    if score >= 80:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    if score > 0:
        return "LOW"
    return "NONE"


def define_gate_status(enriched_findings, risk_score):
    severities = [f.get("business_severity") for f in enriched_findings]
    if "CRITICAL" in severities:
        return "FAIL"
    if risk_score > 0:
        return "WARNING"
    return "PASS"


def build_business_assessment(findings, profile_path="profiles/flexo_pet_bopp_default.json"):
    profile = load_profile(profile_path)
    operational_profile = summarize_operational_profile(profile)

    enriched = [enrich_finding(f, profile) for f in findings]
    enriched = sorted(enriched, key=lambda x: x.get("priority", 99))
    risk_score = calculate_risk_score(enriched)

    return {
        "profile_name": profile.get("profile_name", "flexo_pet_bopp_default"),
        "profile_version": profile.get("profile_version", "unknown"),
        "profile_status": profile.get("profile_status", "unknown"),
        "profile_source": profile.get("profile_source", profile_path),
        "profile_file_found": profile.get("profile_file_found", False),
        "process": profile.get("process", "flexo"),
        "substrate_family": profile.get("substrate_family", "unknown"),
        "operational_profile": operational_profile,
        "gate_status": define_gate_status(enriched, risk_score),
        "risk_score": risk_score,
        "risk_level": define_risk_level(risk_score),
        "total_findings": len(enriched),
        "priority_findings": enriched
    }




# ---------------------------------------------------------------------
# Sprint 25C.1 — RGB_OBJECT Evidence Depth
# ---------------------------------------------------------------------

def _rgb_has_location_or_area(finding):
    if not finding:
        return False

    if finding.get("bbox"):
        return True

    if finding.get("object_area_percent") is not None:
        return True

    return False


def evaluate_rgb_object(finding, profile):
    """
    Evalúa RGB_OBJECT sin sobrededucir.

    Sprint 25C.1:
    - Si no hay bbox ni área, no inventa área 0.00%.
    - Mantiene el hallazgo como observación contextual.
    - Deja claro que falta ubicar visualmente el objeto.
    """
    finding = finding or {}
    profile = profile or {}

    rgb = profile.get("color", {}).get("rgb", {})
    info_max = rgb.get("info_max_area_percent", 3.0)
    critical_min = rgb.get("critical_min_area_percent", 15.0)
    critical_types = rgb.get("critical_object_types", ["background", "gradient", "skin", "brand", "logo"])

    if finding.get("is_printable") is False:
        reason = "Objeto RGB detectado en elemento no imprimible."
        return apply_business_fields(
            finding,
            "INFO",
            "Color / Separaciones",
            reason,
            5,
            "Validar si el elemento debe mantenerse como técnico/no imprimible.",
            0,
        )

    if not _rgb_has_location_or_area(finding):
        reason = (
            "RGB detectado por operador de color, sin ubicación visual confirmada. "
            "Gate0 aún no puede confirmar si pertenece al arte productivo o a un elemento técnico."
        )
        return apply_business_fields(
            finding,
            "INFO",
            "Color / Separaciones",
            reason,
            6,
            "Validar visualmente si el RGB pertenece al arte productivo antes de convertir.",
            0,
        )

    area = float(finding.get("object_area_percent") or 0)
    obj_type = str(finding.get("object_type", "")).lower()

    if area >= critical_min or obj_type in critical_types:
        sev, p, w = "CRITICAL", 1, 25
        reason = f"Objeto RGB imprimible con riesgo de conversión no controlada. Área {area:.2f}%."
    elif area >= info_max:
        sev, p, w = "WARNING", 2, 12
        reason = f"Objeto RGB imprimible de área media. Área {area:.2f}%."
    else:
        sev, p, w = "INFO", 6, 0
        reason = f"Objeto RGB imprimible de área pequeña. Área {area:.2f}%."

    return apply_business_fields(
        finding,
        sev,
        "Color / Separaciones",
        reason,
        p,
        "Convertir RGB a CMYK o spot validado según perfil.",
        w,
    )




# ---------------------------------------------------------------------
# Sprint 25C.2 — HIGH_TAC_RISK Evidence Depth
# ---------------------------------------------------------------------

def _tac_has_location_or_area(finding):
    if not finding:
        return False

    if finding.get("bbox"):
        return True

    if finding.get("object_area_percent") is not None:
        return True

    return False


def evaluate_high_tac_risk(finding, profile):
    """
    Evalúa HIGH_TAC_RISK sin sobrededucir área/ubicación.

    Sprint 25C.2:
    - Si no hay bbox ni área, no inventa área 0.00%.
    - Mantiene la alerta como observación contextual.
    - Si en el futuro llega bbox/área, conserva la lógica de severidad por exceso/área.
    """
    finding = finding or {}
    profile = profile or {}

    detected = float(finding.get("detected_tac") or 0)
    max_tac = float(profile.get("tac", {}).get("max_tac_percent") or finding.get("tac_limit") or 280)
    excess = detected - max_tac

    finding["profile_tac_limit"] = max_tac
    finding["tac_excess"] = round(max(excess, 0), 1)

    if not _tac_has_location_or_area(finding):
        reason = (
            f"TAC detectado {detected:.0f}% vs límite {max_tac:.0f}%. "
            f"Exceso {max(excess, 0):.0f}%. "
            "Gate0 aún no puede confirmar la ubicación visual ni el área afectada."
        )
        return apply_business_fields(
            finding,
            "INFO",
            "Carga de tinta / Impresión",
            reason,
            6,
            "Validar visualmente si el TAC alto pertenece al arte productivo antes de ajustar separaciones.",
            0,
        )

    area = float(finding.get("object_area_percent") or 0)

    if excess >= 40:
        sev, p, w = "CRITICAL", 1, 25
    elif excess >= 20 or area >= 15:
        sev, p, w = "WARNING", 2, 14
    else:
        sev, p, w = "INFO", 6, 0

    reason = (
        f"TAC detectado {detected:.0f}% vs límite {max_tac:.0f}%. "
        f"Exceso {max(excess, 0):.0f}%, área {area:.2f}%."
    )

    return apply_business_fields(
        finding,
        sev,
        "Carga de tinta / Impresión",
        reason,
        p,
        "Reducir TAC según estándar del proceso/sustrato.",
        w,
    )




# ---------------------------------------------------------------------
# Sprint 25C.3 — FONT_NOT_EMBEDDED Evidence Depth
# ---------------------------------------------------------------------

def evaluate_font_not_embedded(finding, profile):
    """
    Evalúa fuente no embebida.

    Sprint 25C.3:
    - mantiene severidad crítica.
    - agrega razón con nombre de fuente si existe.
    - no afirma texto afectado si no está asociado.
    """
    finding = finding or {}

    font_name = finding.get("font_name") or finding.get("value") or "fuente no identificada"
    font_type = finding.get("font_type")
    text_status = finding.get("text_association_status")

    if text_status == "NOT_ASSOCIATED_IN_FONT_V1":
        reason = (
            f"Fuente no embebida detectada: {font_name}"
            f"{f' ({font_type})' if font_type else ''}. "
            "Riesgo de sustitución tipográfica o cambio de contenido aprobado. "
            "Gate0 aún no asocia de forma confiable qué texto específico usa esta fuente."
        )
    else:
        reason = (
            f"Fuente no embebida detectada: {font_name}. "
            "Riesgo de sustitución tipográfica o cambio de contenido aprobado."
        )

    return apply_business_fields(
        finding,
        "CRITICAL",
        "Fuentes / Texto",
        reason,
        1,
        "Incrustar la fuente, convertir texto a curvas o corregir el recurso antes de avanzar.",
        25,
    )

