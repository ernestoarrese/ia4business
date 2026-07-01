from pathlib import Path
import fitz

from gate0.agents.inspection_agent import InspectionAgent
from gate0.engines.inspection_engine import InspectionEngine
from gate0.engines.reasoning_engine import ReasoningEngine
from gate0.engines.expert_engine import ExpertEngine
from gate0.engines.reporting_engine import ReportingEngine
from gate0.models.inspection_result import InspectionResult


def create_test_pdf(path):
    doc = fitz.open()
    doc.new_page(width=595, height=842)
    doc.save(path)
    doc.close()


def test_inspection_agent_returns_inspection_result(tmp_path):
    pdf = tmp_path / "test.pdf"
    create_test_pdf(pdf)

    agent = InspectionAgent()
    result = agent.inspect(pdf)

    assert isinstance(result, InspectionResult)
    assert result.file.endswith("test.pdf")
    assert result.pages == 1
    assert result.pdf_structure["page_count"] == 1
    assert result.page_boxes[0]["width_mm"] > 0


def test_engines_can_be_created():
    assert InspectionEngine() is not None
    assert ReasoningEngine() is not None
    assert ExpertEngine() is not None
    assert ReportingEngine() is not None
