from pathlib import Path


def _last_index(text, needle):
    pos = text.rfind(needle)
    assert pos >= 0, f"No se encontró: {needle}"
    return pos


def test_gate0_check_main_guard_is_after_evidence_depth_redefinitions():
    source = Path("gate0_check.py").read_text(encoding="utf-8")

    main_guard = _last_index(source, 'if __name__ == "__main__":')

    assert main_guard > _last_index(source, "# Sprint 25C.1 — RGB_OBJECT Evidence Depth")
    assert main_guard > _last_index(source, "def check_rgb_objects")
    assert main_guard > _last_index(source, "# Sprint 25C.2 — HIGH_TAC_RISK Evidence Depth")
    assert main_guard > _last_index(source, "def check_high_tac")
    assert main_guard > _last_index(source, "# Sprint 25C.3")
    assert main_guard > _last_index(source, "def check_font_embedding")


def test_gate0_check_has_single_main_guard():
    source = Path("gate0_check.py").read_text(encoding="utf-8")
    assert source.count('if __name__ == "__main__":') == 1
