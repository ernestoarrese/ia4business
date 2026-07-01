from gate0.agents.inspection_agent import InspectionAgent
from gate0.engines.inspection_engine import InspectionEngine
from gate0.engines.reasoning_engine import ReasoningEngine
from gate0.engines.expert_engine import ExpertEngine
from gate0.engines.reporting_engine import ReportingEngine
from gate0.models.inspection_result import InspectionResult


def test_inspection_agent_returns_inspection_result():
    agent = InspectionAgent()
    result = agent.inspect("test.pdf")

    assert isinstance(result, InspectionResult)
    assert result.file == "test.pdf"


def test_engines_can_be_created():
    assert InspectionEngine() is not None
    assert ReasoningEngine() is not None
    assert ExpertEngine() is not None
    assert ReportingEngine() is not None
