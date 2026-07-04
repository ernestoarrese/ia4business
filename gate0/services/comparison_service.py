from pathlib import Path
import re

from gate0.models.comparison_result import ComparisonResult


class ComparisonService:
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

    def compare_inspection_results(self, left, right) -> ComparisonResult:
        checks = []
        warnings = []
        score = 100

        def add_check(name, status, left_value, right_value, penalty=0):
            nonlocal score
            if status != "OK":
                score -= penalty
            checks.append({
                "name": name,
                "status": status,
                "left": left_value,
                "right": right_value,
            })

        add_check(
            "Pages",
            "OK" if left.pages == right.pages else "WARNING",
            left.pages,
            right.pages,
            penalty=15,
        )

        left_box = left.page_boxes[0] if left.page_boxes else {}
        right_box = right.page_boxes[0] if right.page_boxes else {}

        left_size = (left_box.get("width_mm"), left_box.get("height_mm"))
        right_size = (right_box.get("width_mm"), right_box.get("height_mm"))

        size_ok = left_size == right_size
        add_check(
            "Page size",
            "OK" if size_ok else "WARNING",
            left_size,
            right_size,
            penalty=20,
        )

        left_fonts = sorted({f.get("font_name") for f in left.live_fonts if f.get("font_name")})
        right_fonts = sorted({f.get("font_name") for f in right.live_fonts if f.get("font_name")})

        add_check(
            "Fonts",
            "OK" if left_fonts == right_fonts else "WARNING",
            left_fonts,
            right_fonts,
            penalty=15,
        )

        left_seps = sorted(left.separations or [])
        right_seps = sorted(right.separations or [])

        add_check(
            "Separations",
            "OK" if left_seps == right_seps else "WARNING",
            left_seps,
            right_seps,
            penalty=25,
        )

        score = max(0, score)
        overall_status = "OK" if score >= 90 else "REVIEW"

        if overall_status != "OK":
            warnings.append("Se detectaron diferencias estructurales entre los archivos comparados.")

        return ComparisonResult(
            left_file=left.file,
            right_file=right.file,
            overall_status=overall_status,
            score=score,
            checks=checks,
            warnings=warnings,
            metadata={
                "comparison_type": "InspectionResult vs InspectionResult",
                "mode": "structural_v1",
            },
        )
