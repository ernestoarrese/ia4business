import json
import re
from pathlib import Path


def load_profile(profile_path="profiles/flexo_pet_bopp_default.json"):
    path = Path(profile_path)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def upgrade_severity(severity):
    levels = ["PASS", "INFO", "WARNING", "CRITICAL"]
    if severity not in levels:
        return severity
    return levels[min(levels.index(severity) + 1, len(levels) - 1)]


def downgrade_severity(severity):
    levels = ["PASS", "INFO", "WARNING", "CRITICAL"]
    if severity not in levels:
        return severity
    return levels[max(levels.index(severity) - 1, 0)]


def extract_dpi_value(finding):
    if finding.get("effective_dpi") is not None:
        return float(finding["effective_dpi"])
    value = str(finding.get("value", ""))
    nums = re.findall(r"\d+(?:\.\d+)?", value)
    return float(min(float(n) for n in nums)) if nums else 0.0


def apply_business_fields(finding, severity, risk_area, risk_reason, priority, action, score_weight):
    finding["business_severity"] = severity
    finding["risk_area"] = risk_area
    finding["risk_reason"] = risk_reason
    finding["priority"] = priority
    finding["action"] = action
    finding["score_weight"] = score_weight
    return finding


def severity_meta(severity, weights):
    if severity == "CRITICAL":
        return 1, weights.get("CRITICAL", 35)
    if severity == "WARNING":
        return 2, weights.get("WARNING", 15)
    if severity == "INFO":
        return 3, weights.get("INFO", 1)
    return 4, 0


def evaluate_rgb_object(finding, profile):
    area = float(finding.get("object_area_percent") or 0)
    is_printable = finding.get("is_printable", True)
    object_type = finding.get("object_type", "unknown")

    rgb = profile.get("color", {}).get("rgb", {})
    info_max = rgb.get("info_max_area_percent", 3.0)
    critical_min = rgb.get("critical_min_area_percent", 15.0)
    critical_types = rgb.get("critical_object_types", ["background", "gradient", "skin", "brand", "logo"])

    if not is_printable:
        sev = "INFO"
        reason = "Objeto RGB detectado en elemento no imprimible."
    elif object_type in critical_types or area >= critical_min:
        sev = "CRITICAL"
        reason = f"Objeto RGB imprimible con riesgo de conversión no controlada. Área {area:.2f}%."
    elif area >= info_max:
        sev = "WARNING"
        reason = f"Objeto RGB imprimible de área media. Área {area:.2f}%."
    else:
        sev = "INFO"
        reason = f"Objeto RGB imprimible de área pequeña. Área {area:.2f}%."

    p, w = severity_meta(sev, {"CRITICAL": 35, "WARNING": 15, "INFO": 1})
    return apply_business_fields(finding, sev, "Color / Separaciones", reason, p, "Convertir RGB a CMYK o spot validado según perfil.", w)


def evaluate_low_image_resolution(finding, profile):
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


def evaluate_font_not_embedded(finding, profile):
    return apply_business_fields(
        finding,
        "CRITICAL",
        "Fuentes / Texto",
        "Fuente no embebida. Riesgo de sustitución tipográfica o cambio de contenido aprobado.",
        1,
        "Incrustar o convertir fuentes antes de avanzar.",
        35
    )


def evaluate_high_tac_risk(finding, profile):
    detected = float(finding.get("detected_tac") or 0)
    area = float(finding.get("object_area_percent") or 0)
    max_tac = profile.get("tac", {}).get("max_tac_percent", 280)
    excess = detected - max_tac

    if excess <= 0:
        sev = "PASS"
    elif excess <= 20:
        sev = "INFO" if area < 3 else "WARNING"
    elif excess <= 40:
        sev = "CRITICAL" if area >= 15 else "WARNING"
    else:
        sev = "CRITICAL"

    p, w = severity_meta(sev, {"CRITICAL": 40, "WARNING": 20, "INFO": 1})
    reason = f"TAC detectado {detected:.0f}% vs límite {max_tac:.0f}%. Exceso {max(excess, 0):.0f}%, área {area:.2f}%."
    return apply_business_fields(finding, sev, "Carga de tinta / Impresión", reason, p, "Reducir TAC según estándar del proceso/sustrato.", w)


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
    source = finding.get("process_count_source", "ASSUMED_CMYK")

    if count <= 8:
        sev = "PASS"
        reason = f"Cantidad de separaciones dentro de rango normal ({count}). Base proceso: {source}."
        action = "Sin acción requerida."
    elif count in [9, 10]:
        sev = "INFO"
        reason = f"Cantidad elevada de separaciones imprimibles ({count})."
        action = "Verificar complejidad operativa y disponibilidad de estaciones."
    elif count in [11, 12]:
        sev = "WARNING"
        reason = f"Cantidad alta de separaciones imprimibles ({count})."
        action = "Revisar racionalización de spots."
    else:
        sev = "CRITICAL"
        reason = f"Exceso crítico de separaciones imprimibles ({count})."
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
    enriched = [enrich_finding(f, profile) for f in findings]
    enriched = sorted(enriched, key=lambda x: x.get("priority", 99))
    risk_score = calculate_risk_score(enriched)

    return {
        "profile_name": profile.get("profile_name", "flexo_pet_bopp_default"),
        "process": profile.get("process", "flexo"),
        "gate_status": define_gate_status(enriched, risk_score),
        "risk_score": risk_score,
        "risk_level": define_risk_level(risk_score),
        "total_findings": len(enriched),
        "priority_findings": enriched
    }
