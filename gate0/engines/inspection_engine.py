"""
Inspection Engine

Responsabilidad:
- Extraer información técnica base del archivo.
- Construir InspectionResult.
- No decide GO/HOLD/NO_GO.
- No genera comentarios expertos.

Core Migration Phase 1:
- Extrae metadata estructural básica del PDF/AI compatible.
"""

from pathlib import Path
import fitz

from gate0.models.inspection_result import InspectionResult
from gate0.services.separation_extraction_service import extract_pdf_separations


class InspectionEngine:
    def inspect(self, input_file):
        input_file = Path(input_file)

        with fitz.open(input_file) as doc:
            pages = doc.page_count

            metadata = {
                "engine": "InspectionEngine",
                "mode": "core_metadata_v1",
                "file_name": input_file.name,
                "file_suffix": input_file.suffix.lower(),
                "file_size_mb": round(input_file.stat().st_size / (1024 * 1024), 2),
                "is_pdf_compatible": True,
            }

            page_boxes = []

            for page_index, page in enumerate(doc):
                rect = page.rect

                page_boxes.append({
                    "page": page_index + 1,
                    "width_pt": round(rect.width, 2),
                    "height_pt": round(rect.height, 2),
                    "width_mm": round(rect.width * 25.4 / 72, 2),
                    "height_mm": round(rect.height * 25.4 / 72, 2),
                    "rotation": page.rotation,
                })

            live_fonts = []

            for page_index, page in enumerate(doc):
                try:
                    fonts = page.get_fonts(full=True)
                except Exception:
                    fonts = []

                for font in fonts:
                    font_name = font[3] if len(font) > 3 else "unknown"
                    font_type = font[2] if len(font) > 2 else "unknown"
                    embedded = bool(font[6]) if len(font) > 6 else False

                    live_fonts.append({
                        "page": page_index + 1,
                        "font_name": font_name,
                        "font_type": font_type,
                        "embedded": embedded,
                        "is_embedded": embedded,
                    })

            pdf_structure = {
                "page_count": pages,
                "file_size_mb": metadata["file_size_mb"],
                "font_count": len(live_fonts),
            }

        separations = []

        try:
            separations = extract_pdf_separations(input_file)
            metadata["separation_extraction_status"] = "EVALUATED"
            metadata["separation_extraction_source"] = "gate0_check.detect_separations"
        except Exception as exc:
            separations = []
            metadata["separation_extraction_status"] = "FAILED"
            metadata["separation_extraction_error"] = str(exc)

        pdf_structure["separation_count"] = len(separations)

        return InspectionResult(
            file=str(input_file),
            pages=pages,
            separations=separations,
            page_boxes=page_boxes,
            pdf_structure=pdf_structure,
            live_fonts=live_fonts,
            metadata=metadata,
        )
