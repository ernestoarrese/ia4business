from pathlib import Path


AGENTS = Path("AGENTS.md").read_text(encoding="utf-8")
PROMPT = Path("docs/codex/gate0_codex_prompt.md").read_text(encoding="utf-8")


def test_agents_protocol_exists_and_identifies_gate0():
    assert "Gate0 Packaging QA" in AGENTS
    assert "Production Readiness" in AGENTS
    assert "flexible packaging" in AGENTS


def test_agents_protocol_requires_safe_workflow():
    required = [
        "git status --short",
        "pytest -q",
        "python -m py_compile",
        "git diff --stat",
    ]

    for text in required:
        assert text in AGENTS


def test_agents_protocol_protects_dashboard_javascript():
    assert "dashboard/index.html" in AGENTS
    assert "node --check" in AGENTS
    assert "Production Readiness block" in AGENTS
    assert "visual zone / occurrence navigation" in AGENTS


def test_agents_protocol_protects_runtime_and_business_rules():
    assert "business_rules.py" in AGENTS
    assert "readiness_summary.py" in AGENTS
    assert "session-specific files under data/runtime" in AGENTS
    assert "Legacy data/output may remain only as CLI/fallback behavior." in AGENTS


def test_codex_prompt_is_audit_first_and_no_write_first():
    assert "No modifiques archivos" in PROMPT
    assert "Realiza solo una auditoría" in PROMPT
    assert "No escribas código todavía" in PROMPT
    assert "AGENTS.md" in PROMPT
