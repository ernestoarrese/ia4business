from gate0.models.inspection_result import InspectionResult
from gate0.models.decision_result import DecisionResult
from gate0.models.expert_report import ExpertReport
from gate0.models.analysis_record import AnalysisRecord


def test_inspection_result_defaults():
    result = InspectionResult(file="test.pdf")
    assert result.file == "test.pdf"
    assert result.technical_findings == []
    assert result.metadata == {}


def test_decision_result_creation():
    result = DecisionResult(
        gate_status="FAIL",
        readiness_score=76,
        readiness_status="REVIEW_REQUIRED",
        readiness_decision="HOLD",
    )
    assert result.readiness_decision == "HOLD"


def test_expert_report_defaults():
    report = ExpertReport()
    assert report.expert_comments == []
    assert report.recommendations == []


def test_analysis_record_creation():
    record = AnalysisRecord(
        session_id="abc123",
        file="test.pdf",
        score=93,
        decision="GO_WITH_NOTES",
    )
    assert record.session_id == "abc123"
    assert record.decision == "GO_WITH_NOTES"
