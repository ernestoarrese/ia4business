from pathlib import Path

from parser_capability_audit import audit_parser_capabilities


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


def test_parser_audit_detects_spot_and_white(tmp_path):
    pdf_path = tmp_path / "white_test.pdf"

    content = (
        "q\n"
        "/CSWhite cs\n"
        "1 scn\n"
        "100 100 200 200 re\n"
        "f\n"
        "Q\n"
    )

    objects = [
        (1, "<< /Type /Catalog /Pages 2 0 R >>"),
        (2, "<< /Type /Pages /Kids [3 0 R] /Count 1 >>"),
        (
            3,
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 600] "
            "/Resources << /ColorSpace << /CSWhite 5 0 R >> >> "
            "/Contents 4 0 R >>"
        ),
        (4, f"<< /Length {len(content.encode('latin-1'))} >>\nstream\n{content}endstream"),
        (
            5,
            "[/Separation /White /DeviceCMYK "
            "<< /FunctionType 2 /Domain [0 1] /C0 [0 0 0 0] /C1 [0 0 0 0] /N 1 >>]"
        )
    ]

    write_pdf(objects, pdf_path)

    report = audit_parser_capabilities(str(pdf_path))

    assert report["capabilities"]["spot_detection"] is True
    assert report["capabilities"]["number_of_separations"] is True
    assert "WHITE_INK_RISK" in report["raw_inventory"]["checks_detected"]
