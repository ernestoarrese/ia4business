import json
import subprocess
import sys
from pathlib import Path

import fitz

from gate0_orchestrator import Gate0Orchestrator


def _make_pdf(path: Path, text: str = "Gate0 runtime isolation test"):
    doc = fitz.open()
    page = doc.new_page(width=300, height=200)
    page.insert_text((40, 80), text, fontsize=12)
    doc.save(path)
    doc.close()


def test_gate0_check_cli_writes_report_to_custom_output_dir(tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    output_dir = tmp_path / "session_output"
    _make_pdf(pdf_path)

    result = subprocess.run(
        [sys.executable, "gate0_check.py", str(pdf_path), str(output_dir)],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (output_dir / "gate0_report.json").exists()
    assert (output_dir / "gate0_report.csv").exists()

    data = json.loads((output_dir / "gate0_report.json").read_text(encoding="utf-8"))
    assert data["file"] == "sample.pdf"


def test_orchestrator_uses_session_specific_output_dir(tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    output_dir = tmp_path / "runtime" / "session_abc"
    _make_pdf(pdf_path)

    orchestrator = Gate0Orchestrator(Path.cwd())
    data = orchestrator.run(pdf_path, output_dir=output_dir)

    assert data["file"] == "sample.pdf"
    assert (output_dir / "gate0_report.json").exists()
    assert (output_dir / "gate0_report.csv").exists()


def test_two_orchestrator_runs_write_to_distinct_session_dirs(tmp_path):
    pdf_a = tmp_path / "a.pdf"
    pdf_b = tmp_path / "b.pdf"
    out_a = tmp_path / "runtime" / "sid_a"
    out_b = tmp_path / "runtime" / "sid_b"

    _make_pdf(pdf_a, "PDF A")
    _make_pdf(pdf_b, "PDF B")

    orchestrator = Gate0Orchestrator(Path.cwd())
    data_a = orchestrator.run(pdf_a, output_dir=out_a)
    data_b = orchestrator.run(pdf_b, output_dir=out_b)

    assert data_a["file"] == "a.pdf"
    assert data_b["file"] == "b.pdf"

    report_a = json.loads((out_a / "gate0_report.json").read_text(encoding="utf-8"))
    report_b = json.loads((out_b / "gate0_report.json").read_text(encoding="utf-8"))

    assert report_a["file"] == "a.pdf"
    assert report_b["file"] == "b.pdf"


def test_app_uses_session_output_dir_instead_of_default_csv():
    source = Path("app.py").read_text(encoding="utf-8")

    assert "session_output_dir = REPORTS_DIR / session_id" in source
    assert 'orchestrator.run(paths["pdf"], output_dir=session_output_dir)' in source
    assert 'session_csv = session_output_dir / "gate0_report.csv"' in source
    assert 'default_csv = ROOT / "data" / "output" / "gate0_report.csv"' not in source
