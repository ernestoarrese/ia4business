from pathlib import Path

from gate0_check import detect_separation_usage_capability


def write_minimal_pdf(path: Path):
    objects = []

    def add(obj: str):
        objects.append(obj)

    add("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    add("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    add(
        "3 0 obj\n"
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] "
        "/Resources << /ColorSpace << /CS1 5 0 R >> >> "
        "/Contents 4 0 R >>\n"
        "endobj\n"
    )

    stream = "q\n/CS1 cs\n0.5 scn\n10 10 100 100 re\nf\nQ\n"
    add(
        "4 0 obj\n"
        f"<< /Length {len(stream.encode('latin-1'))} >>\n"
        "stream\n"
        f"{stream}"
        "endstream\n"
        "endobj\n"
    )

    add(
        "5 0 obj\n"
        "[/Separation /PANTONE_485_C /DeviceCMYK 6 0 R]\n"
        "endobj\n"
    )

    add(
        "6 0 obj\n"
        "<< /FunctionType 2 /Domain [0 1] /C0 [0 0 0 0] /C1 [0 1 1 0] /N 1 >>\n"
        "endobj\n"
    )

    output = bytearray()
    output.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]

    for obj in objects:
        offsets.append(len(output))
        output.extend(obj.encode("latin-1"))

    xref_pos = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    output.extend(b"0000000000 65535 f \n")

    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))

    output.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_pos}\n"
            "%%EOF\n"
        ).encode("latin-1")
    )

    path.write_bytes(output)


def test_separation_usage_capability_detects_resources_and_usage_tokens(tmp_path):
    pdf_path = tmp_path / "separation_usage_probe.pdf"
    write_minimal_pdf(pdf_path)

    result = detect_separation_usage_capability(
        str(pdf_path),
        separations=["PANTONE 485 C"],
    )

    assert result["status"] == "EXPERIMENTAL"
    assert result["detected_separation_count"] == 1
    assert result["can_map_separation_resources"] is True
    assert result["can_detect_usage_tokens"] is True
    assert result["usage_token_count"] >= 1
    assert result["colorspace_selector_count"] >= 1
    assert result["can_compute_bbox_by_separation"] is False
    assert result["safe_for_reclassification"] is False
    assert result["resource_separation_mentions"]["PANTONE 485 C"] >= 1
