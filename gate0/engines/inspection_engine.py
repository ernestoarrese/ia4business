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

            pdf_structure = {
                "page_count": pages,
                "file_size_mb": metadata["file_size_mb"],
            }

        return InspectionResult(
            file=str(input_file),
            pages=pages,
            page_boxes=page_boxes,
            pdf_structure=pdf_structure,
            metadata=metadata,
        )
