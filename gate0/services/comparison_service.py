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

    def _page_size_from_box(self, box):
        box = box or {}
        return (box.get("width_mm"), box.get("height_mm"))

    def _compare_all_page_sizes(self, left_page_boxes, right_page_boxes):
        if not left_page_boxes or not right_page_boxes:
            return {
                "status": "NOT_EVALUATED",
                "left": left_page_boxes or [],
                "right": right_page_boxes or [],
                "message": "No hay información suficiente de tamaño de página para comparar.",
            }

        if len(left_page_boxes) != len(right_page_boxes):
            return {
                "status": "CRITICAL",
                "left": [self._page_size_from_box(b) for b in left_page_boxes],
                "right": [self._page_size_from_box(b) for b in right_page_boxes],
                "message": "La cantidad de cajas de página no coincide. Validar exportación, páginas o arte final.",
            }

        mismatches = []

        for index, (left_box, right_box) in enumerate(zip(left_page_boxes, right_page_boxes), start=1):
            left_size = self._page_size_from_box(left_box)
            right_size = self._page_size_from_box(right_box)

            if not self._page_size_matches(left_size, right_size):
                mismatches.append({
                    "page": index,
                    "left": left_size,
                    "right": right_size,
                })

        if mismatches:
            return {
                "status": "CRITICAL",
                "left": [self._page_size_from_box(b) for b in left_page_boxes],
                "right": [self._page_size_from_box(b) for b in right_page_boxes],
                "message": "El tamaño de una o más páginas cambió. Validar plano, sangrado, caja de corte o exportación.",
                "mismatches": mismatches,
            }

        return {
            "status": "OK",
            "left": [self._page_size_from_box(b) for b in left_page_boxes],
            "right": [self._page_size_from_box(b) for b in right_page_boxes],
            "message": "",
        }

    def compare_inspection_results(self, left, right) -> ComparisonResult:
        checks = []
        warnings = []
        score = 100

        def add_check(category, name, status, left_value, right_value, penalty=0, message="", metadata=None):
            nonlocal score

            if status != "OK":
                score -= penalty

            check = {
                "category": category,
                "name": name,
                "status": status,
                "left": left_value,
                "right": right_value,
                "message": message,
            }

            if metadata:
                check["metadata"] = metadata

            checks.append(check)

        left_pages = getattr(left, "pages", 0)
        right_pages = getattr(right, "pages", 0)

        if not left_pages or not right_pages:
            add_check(
                "Pages",
                "Page count",
                "NOT_EVALUATED",
                left_pages,
                right_pages,
                penalty=10,
                message="No hay información suficiente de cantidad de páginas para comparar.",
            )
        else:
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
        page_size_result = self._compare_all_page_sizes(left_page_boxes, right_page_boxes)

        add_check(
            "Pages",
            "Page size",
            page_size_result["status"],
            page_size_result["left"],
            page_size_result["right"],
            penalty=30 if page_size_result["status"] == "CRITICAL" else 10,
            message=page_size_result["message"],
            metadata={"mismatches": page_size_result.get("mismatches", [])},
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

        if not left_fonts and not right_fonts:
            add_check(
                "Fonts",
                "Live fonts",
                "NOT_EVALUATED",
                left_fonts,
                right_fonts,
                penalty=5,
                message="No hay fuentes vivas evaluables en ambos archivos. Puede ser correcto si todo fue convertido a curvas, pero no debe contarse como coincidencia confirmada.",
            )
        else:
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

        if not left_seps and not right_seps:
            add_check(
                "Structure",
                "Separations",
                "NOT_EVALUATED",
                left_seps,
                right_seps,
                penalty=10,
                message="No hay separaciones evaluables en ambos archivos. El Compare Engine aún no debe interpretar listas vacías como coincidencia confirmada.",
            )
        else:
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
        not_evaluated_count = sum(1 for check in checks if check["status"] == "NOT_EVALUATED")

        if critical_count > 0:
            overall_status = "HIGH_RISK"
            decision = "No liberar sin revisión técnica"
            summary = "Se detectaron diferencias críticas entre el AI y el PDF."
            recommendation = "Comparar contra el arte aprobado antes de liberar a producción. Priorizar páginas, tamaño final y separaciones."
        elif warning_count > 0:
            overall_status = "REVIEW_REQUIRED"
            decision = "Revisar diferencias antes de liberar"
            summary = "La comparación estructural encontró diferencias que podrían ser válidas, pero requieren confirmación."
            recommendation = "Validar fuentes, separaciones y cambios esperados antes de continuar."
        elif not_evaluated_count > 0:
            overall_status = "REVIEW_REQUIRED"
            decision = "Revisión requerida por cobertura incompleta"
            summary = "La comparación estructural no tuvo datos suficientes para confirmar consistencia completa."
            recommendation = "No interpretar este resultado como OK. Completar revisión manual o mejorar extracción antes de liberar."
        elif score < 95:
            overall_status = "REVIEW_REQUIRED"
            decision = "Revisar diferencias antes de liberar"
            summary = "La comparación estructural encontró señales que requieren confirmación."
            recommendation = "Validar los puntos observados antes de continuar."
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
                "mode": "structural_v2_guardrails",
                "critical_count": critical_count,
                "warning_count": warning_count,
                "not_evaluated_count": not_evaluated_count,
                "categories": sorted({check["category"] for check in checks}),
            },
        )
