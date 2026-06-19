from pathlib import Path

from gate0_check import build_report


def write_pdf(objects, path):
    output = bytearray()
    output.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []

    for obj_num, content in objects:
        offsets.append(len(output))
        output.extend(f"{obj_num} 0 obj\n{content}\nendobj\n".encode("latin-1"))

    xref_pos = len(output)
    max_obj = max(num for num, _ in objects)

    output.extend(f"xref\n0 {max_obj + 1}\n".encode("latin-1"))
    output.extend(b"0000000000 65535 f \n")

    offset_map = {num: offset for (num, _), offset in zip(objects, offsets)}
    for i in range(1, max_obj + 1):
        offset = offset_map.get(i, 0)
        if offset:
            output.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
        else:
            output.extend(b"0000000000 00000 f \n")

    output.extend(
        f"trailer\n<< /Size {max_obj + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF\n".encode("latin-1")
    )

    Path(path).write_bytes(output)


def test_gate0_build_report_end_to_end(tmp_path):
    pdf_path = tmp_path / "gate0_e2e_test.pdf"

    content = (
        "q\n"
        "1 0 0 rg\n"
        "80 80 160 160 re\n"
        "f\n"
        "Q\n"
        "q\n"
        "1 1 1 0.8 k\n"
        "280 80 220 220 re\n"
        "f\n"
        "Q\n"
        "q\n"
        "/CSWhite cs\n"
        "1 scn\n"
        "100 300 120 120 re\n"
        "f\n"
        "Q\n"
    )

    objects = [
        (1, "<< /Type /Catalog /Pages 2 0 R >>"),
        (2, "<< /Type /Pages /Kids [3 0 R] /Count 1 >>"),
        (
            3,
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 600] "
            "/Resources << "
            "/ColorSpace << /CSWhite 5 0 R >> "
            "/Font << /F1 6 0 R >> "
            ">> "
            "/Contents 4 0 R >>"
        ),
        (4, f"<< /Length {len(content.encode('latin-1'))} >>\nstream\n{content}endstream"),
        (
            5,
            "[/Separation /White /DeviceCMYK "
            "<< /FunctionType 2 /Domain [0 1] /C0 [0 0 0 0] /C1 [0 0 0 0] /N 1 >>]"
        ),
        (6, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    ]

    write_pdf(objects, pdf_path)

    report = build_report(str(pdf_path))

    assert report["file"] == "gate0_e2e_test.pdf"
    assert report["pages"] == 1
    assert "business_assessment" in report
    assert "readiness_assessment" in report
    assert "readiness_summary" in report

    checks = [
        item["check"]
        for item in report["business_assessment"]["priority_findings"]
    ]

    assert "RGB_OBJECT" in checks
    assert "HIGH_TAC_RISK" in checks
    assert "WHITE_INK_RISK" in checks
    assert "SPOT_COLOR_RISK" in checks
    assert "SEPARATION_COUNT_RISK" in checks
    assert "PDF_STRUCTURE_RISK" in checks

    assert report["readiness_assessment"]["readiness_decision"] in [
        "GO",
        "GO_WITH_NOTES",
        "HOLD",
        "NO_GO"
    ]
