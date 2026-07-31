from pathlib import Path
import sys

import pytest
from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app as gate0_app


VALID_SID = "a" * 32


def _prepare_compare_session(tmp_path, monkeypatch):
    temp_root = tmp_path / "temp"
    session_dir = temp_root / VALID_SID
    session_dir.mkdir(parents=True)

    ai_path = session_dir / "design.ai"
    pdf_path = session_dir / "design.pdf"

    ai_path.write_bytes(b"%PDF-compatible AI placeholder")
    pdf_path.write_bytes(b"%PDF placeholder")

    monkeypatch.setattr(gate0_app, "TEMP_DIR", temp_root)

    return ai_path, pdf_path


def test_compare_candidate_path_resolves_valid_file_inside_session(tmp_path, monkeypatch):
    ai_path, _ = _prepare_compare_session(tmp_path, monkeypatch)

    resolved = gate0_app._resolve_compare_candidate_path(
        sid=VALID_SID,
        relative_file="design.ai",
        allowed_suffixes={".ai"},
        label="AI",
    )

    assert resolved == ai_path.resolve()


def test_compare_candidate_path_rejects_path_traversal(tmp_path, monkeypatch):
    _prepare_compare_session(tmp_path, monkeypatch)

    with pytest.raises(HTTPException) as exc:
        gate0_app._resolve_compare_candidate_path(
            sid=VALID_SID,
            relative_file="../design.ai",
            allowed_suffixes={".ai"},
            label="AI",
        )

    assert exc.value.status_code == 400


def test_compare_candidate_path_rejects_absolute_path(tmp_path, monkeypatch):
    _prepare_compare_session(tmp_path, monkeypatch)

    with pytest.raises(HTTPException) as exc:
        gate0_app._resolve_compare_candidate_path(
            sid=VALID_SID,
            relative_file="/tmp/design.ai",
            allowed_suffixes={".ai"},
            label="AI",
        )

    assert exc.value.status_code == 400


def test_compare_candidate_path_rejects_wrong_extension(tmp_path, monkeypatch):
    _prepare_compare_session(tmp_path, monkeypatch)

    with pytest.raises(HTTPException) as exc:
        gate0_app._resolve_compare_candidate_path(
            sid=VALID_SID,
            relative_file="design.pdf",
            allowed_suffixes={".ai"},
            label="AI",
        )

    assert exc.value.status_code == 400


def test_compare_candidate_path_rejects_invalid_sid(tmp_path, monkeypatch):
    _prepare_compare_session(tmp_path, monkeypatch)

    with pytest.raises(HTTPException) as exc:
        gate0_app._resolve_compare_candidate_path(
            sid="../../bad",
            relative_file="design.ai",
            allowed_suffixes={".ai"},
            label="AI",
        )

    assert exc.value.status_code == 400


def test_compare_candidate_path_missing_file_is_404(tmp_path, monkeypatch):
    _prepare_compare_session(tmp_path, monkeypatch)

    with pytest.raises(HTTPException) as exc:
        gate0_app._resolve_compare_candidate_path(
            sid=VALID_SID,
            relative_file="missing.ai",
            allowed_suffixes={".ai"},
            label="AI",
        )

    assert exc.value.status_code == 404
