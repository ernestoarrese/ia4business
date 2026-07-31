from pathlib import Path
import sys

import fitz

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gate0.engines.inspection_engine import InspectionEngine
from gate0.services.separation_extraction_service import extract_pdf_separations


def _make_basic_pdf(path):
    doc = fitz.open()
    doc.new_page(width=100, height=100)
    doc.save(path)
    doc.close()


def test_separation_extraction_service_delegates_to_gate0_parser(monkeypatch, tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    _make_basic_pdf(pdf_path)

    captured = {}

    def fake_detect_separations(path):
        captured["path"] = path
        return ["PANTONE 485 C", "White"]

    import gate0_check

    monkeypatch.setattr(gate0_check, "detect_separations", fake_detect_separations)

    result = extract_pdf_separations(pdf_path)

    assert result == ["PANTONE 485 C", "White"]
    assert captured["path"] == str(pdf_path)


def test_inspection_engine_populates_separations_for_compare_engine(monkeypatch, tmp_path):
    pdf_path = tmp_path / "candidate.pdf"
    _make_basic_pdf(pdf_path)

    def fake_extract_pdf_separations(path):
        assert Path(path) == pdf_path
        return ["PANTONE 485 C", "White"]

    monkeypatch.setattr(
        "gate0.engines.inspection_engine.extract_pdf_separations",
        fake_extract_pdf_separations,
    )

    result = InspectionEngine().inspect(pdf_path)

    assert result.separations == ["PANTONE 485 C", "White"]
    assert result.pdf_structure["separation_count"] == 2
    assert result.metadata["separation_extraction_status"] == "EVALUATED"
    assert result.metadata["separation_extraction_source"] == "gate0_check.detect_separations"


def test_inspection_engine_marks_separation_extraction_failure_without_crashing(monkeypatch, tmp_path):
    pdf_path = tmp_path / "candidate.pdf"
    _make_basic_pdf(pdf_path)

    def failing_extract_pdf_separations(path):
        raise RuntimeError("synthetic extraction failure")

    monkeypatch.setattr(
        "gate0.engines.inspection_engine.extract_pdf_separations",
        failing_extract_pdf_separations,
    )

    result = InspectionEngine().inspect(pdf_path)

    assert result.separations == []
    assert result.pdf_structure["separation_count"] == 0
    assert result.metadata["separation_extraction_status"] == "FAILED"
    assert "synthetic extraction failure" in result.metadata["separation_extraction_error"]
