from pathlib import Path
import re

from gate0.models.comparison_result import ComparisonResult


class ComparisonService:
    def normalize_font_name(self, font_name: str) -> str:
        """
        Normaliza nombres de fuentes PDF ignorando prefijos de subset.

        Ejemplo:
        MYVNQU+FrutigerLTStd-BoldCn -> FrutigerLTStd-BoldCn
        """
        font_name = str(font_name or "").strip()

        if "+" in font_name:
            prefix, base = font_name.split("+", 1)
            if len(prefix) == 6 and prefix.isalpha():
                return base

        return font_name

    def normalize_stem(self, filename: str) -> str:
        stem = Path(filename).stem.lower()
        stem = re.sub(r"(curvas|curve|final|arte|art|print|impresion|produccion|prod)", "", stem)
        stem = re.sub(r"[^a-z0-9]", "", stem)
        return stem

    def find_candidate_pairs(self, analyzable: list[dict]) -> list[dict]:
        groups = {}

        for item in analyzable:
            key = self.normalize_stem(item.get("name", ""))
            if not key:
                continue
            groups.setdefault(key, []).append(item)

        pairs = []

        for key, items in groups.items():
            extensions = {i.get("extension", "").lower() for i in items}

            if ".ai" in extensions and ".pdf" in extensions:
                pairs.append({
                    "match_key": key,
                    "confidence": "Alta",
                    "reason": "AI y PDF con nombre similar. Podrían corresponder al mismo diseño.",
                    "files": items,
                })
            elif len(items) > 1:
                pairs.append({
                    "match_key": key,
                    "confidence": "Media",
                    "reason": "Archivos con nombre similar. Revisar si son versiones del mismo diseño.",
                    "files": items,
                })

        return pairs

    def _page_size_matches(self, left_size, right_size, tolerance_mm: float = 0.5) -> bool:
        """
        Compara tamaño de página con tolerancia operativa.

        En packaging es normal encontrar pequeñas diferencias por redondeo de exportación.
        Una diferencia mayor a 0.5 mm ya merece revisión de preprensa.
        """
        if left_size == right_size:
            return True

        if not left_size or not right_size:
            return False

        try:
            lw, lh = left_size
            rw, rh = right_size
            if lw is None or lh is None or rw is None or rh is None:
                return False
            return abs(float(lw) - float(rw)) <= tolerance_mm and abs(float(lh) - float(rh)) <= tolerance_mm
        except (TypeError, ValueError):
            return False

    def compare_inspection_results(self, left, right) -> ComparisonResult:
        checks = []
        warnings = []
        score = 100

        def add_check(category, name, status, left_value, right_value, penalty=0, message=""):
            nonlocal score

            if status != "OK":
                score -= penalty

            checks.append({
                "category": category,
                "name": name,
                "status": status,
                "left": left_value,
                "right": right_value,
                "message": message,
            })

        left_pages = getattr(left, "pages", 0)
        right_pages = getattr(right, "pages", 0)

        add_check(
            "Pages",
            "Page count",
            "OK" if left_pages == right_pages else "CRITICAL",
            left_pages,
            right_pages,
            penalty=30,
            message="La cantidad de páginas cambió entre el AI y el PDF." if left_pages != right_pages else "",
        )

        left_page_boxes = getattr(left, "page_boxes", []) or []
        right_page_boxes = getattr(right, "page_boxes", []) or []

        left_box = left_page_boxes[0] if left_page_boxes else {}
        right_box = right_page_boxes[0] if right_page_boxes else {}

        left_size = (left_box.get("width_mm"), left_box.get("height_mm"))
        right_size = (right_box.get("width_mm"), right_box.get("height_mm"))

        size_ok = self._page_size_matches(left_size, right_size)
        add_check(
            "Pages",
            "Page size",
            "OK" if size_ok else "CRITICAL",
            left_size,
            right_size,
            penalty=30,
            message="El tamaño de página cambió. Validar plano, sangrado, caja de corte o exportación." if not size_ok else "",
        )

        left_fonts = sorted({
            self.normalize_font_name(f.get("font_name"))
            for f in (getattr(left, "live_fonts", []) or [])
            if f.get("font_name")
        })

        right_fonts = sorted({
            self.normalize_font_name(f.get("font_name"))
            for f in (getattr(right, "live_fonts", []) or [])
            if f.get("font_name")
        })

        add_check(
            "Fonts",
            "Live fonts",
            "OK" if left_fonts == right_fonts else "WARNING",
            left_fonts,
            right_fonts,
            penalty=15,
            message="Las fuentes vivas no coinciden. Validar si hubo conversión a curvas, sustitución o pérdida de texto editable." if left_fonts != right_fonts else "",
        )

        left_seps = sorted(getattr(left, "separations", []) or [])
        right_seps = sorted(getattr(right, "separations", []) or [])

        add_check(
            "Structure",
            "Separations",
            "OK" if left_seps == right_seps else "WARNING",
            left_seps,
            right_seps,
            penalty=25,
            message="Las separaciones no coinciden. Revisar tintas spot, blanco, barniz, plano técnico o conversión no esperada." if left_seps != right_seps else "",
        )

        score = max(0, score)

        critical_count = sum(1 for check in checks if check["status"] == "CRITICAL")
        warning_count = sum(1 for check in checks if check["status"] == "WARNING")

        if critical_count > 0 or score < 70:
            overall_status = "HIGH_RISK"
            decision = "No liberar sin revisión técnica"
            summary = "Se detectaron diferencias críticas entre el AI y el PDF."
            recommendation = "Comparar contra el arte aprobado antes de liberar a producción. Priorizar páginas, tamaño final y separaciones."
        elif warning_count > 0 or score < 95:
            overall_status = "REVIEW_REQUIRED"
            decision = "Revisar diferencias antes de liberar"
            summary = "La comparación estructural encontró diferencias que podrían ser válidas, pero requieren confirmación."
            recommendation = "Validar fuentes, separaciones y cambios esperados antes de continuar."
        else:
            overall_status = "OK"
            decision = "Consistencia estructural aceptable"
            summary = "No se detectaron diferencias estructurales relevantes entre el AI y el PDF."
            recommendation = "Puede continuar el flujo normal de revisión."

        for check in checks:
            if check["message"]:
                warnings.append(check["message"])

        if not warnings:
            warnings.append("Sin advertencias estructurales relevantes.")

        return ComparisonResult(
            left_file=getattr(left, "file", ""),
            right_file=getattr(right, "file", ""),
            overall_status=overall_status,
            score=score,
            decision=decision,
            summary=summary,
            recommendation=recommendation,
            checks=checks,
            warnings=warnings,
            metadata={
                "comparison_type": "InspectionResult vs InspectionResult",
                "mode": "structural_v2",
                "critical_count": critical_count,
                "warning_count": warning_count,
                "categories": sorted({check["category"] for check in checks}),
            },
        )
