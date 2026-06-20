from pathlib import Path
import fitz

INPUT = Path("data/input")
INPUT.mkdir(parents=True, exist_ok=True)


# ============================================================
# 1) FONT_NOT_EMBEDDED
# Usa fuente base Helvetica. Normalmente queda como no embebida.
# ============================================================

font_pdf = INPUT / "gate0_test_font_not_embedded.pdf"

doc = fitz.open()
page = doc.new_page(width=595, height=842)
page.insert_text(
    (72, 140),
    "Gate0 font test - Helvetica live text",
    fontsize=28,
    fontname="helv",
    color=(0, 0, 0),
)
doc.save(font_pdf)
doc.close()

print(f"Creado: {font_pdf}")


# ============================================================
# 2) HIGH_TAC_RISK
# PDF mínimo con operador CMYK: 1 1 1 1 k = TAC 400%
# ============================================================

def write_pdf_with_stream(path, stream, resources=""):
    objects = []

    objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    objects.append("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    objects.append(
        f"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        f"/Resources << {resources} >> /Contents 4 0 R >>\nendobj\n"
    )

    stream_bytes = stream.encode("latin-1")
    objects.append(
        f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n"
        f"{stream}\nendstream\nendobj\n"
    )

    pdf = "%PDF-1.4\n"
    offsets = [0]

    for obj in objects:
        offsets.append(len(pdf.encode("latin-1")))
        pdf += obj

    xref_pos = len(pdf.encode("latin-1"))
    pdf += f"xref\n0 {len(objects)+1}\n"
    pdf += "0000000000 65535 f \n"

    for off in offsets[1:]:
        pdf += f"{off:010d} 00000 n \n"

    pdf += (
        "trailer\n"
        f"<< /Size {len(objects)+1} /Root 1 0 R >>\n"
        "startxref\n"
        f"{xref_pos}\n"
        "%%EOF\n"
    )

    Path(path).write_bytes(pdf.encode("latin-1"))


tac_stream = """
q
1 1 1 1 k
80 520 430 180 re
f
Q
"""

tac_pdf = INPUT / "gate0_test_high_tac_400.pdf"
write_pdf_with_stream(tac_pdf, tac_stream)
print(f"Creado: {tac_pdf}")


# ============================================================
# 3) SPOT + SEPARATION COUNT
# PDF mínimo con DeviceN y 13 separaciones Pantone.
# Debe disparar:
# - SPOT_COLOR_RISK
# - SEPARATION_COUNT_RISK
# ============================================================

spot_names = [f"/Pantone#{100+i}#20C" for i in range(13)]
device_n_names = " ".join(spot_names)

spot_resources = f"""
/ColorSpace <<
/CS1 [ /DeviceN [ {device_n_names} ] /DeviceCMYK 5 0 R ]
>>
"""

spot_stream = """
q
/CS1 cs
0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 scn
80 520 430 180 re
f
Q
"""

# Necesitamos función tint transform como objeto 5
def write_spot_pdf(path):
    objects = []

    objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    objects.append("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    objects.append(
        f"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        f"/Resources << {spot_resources} >> /Contents 4 0 R >>\nendobj\n"
    )

    stream_bytes = spot_stream.encode("latin-1")
    objects.append(
        f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n"
        f"{spot_stream}\nendstream\nendobj\n"
    )

    # Tint transform function: dummy conversion to CMYK
    objects.append(
        "5 0 obj\n"
        "<< /FunctionType 2 /Domain [0 1] /C0 [0 0 0 0] /C1 [1 1 1 1] /N 1 >>\n"
        "endobj\n"
    )

    pdf = "%PDF-1.4\n"
    offsets = [0]

    for obj in objects:
        offsets.append(len(pdf.encode("latin-1")))
        pdf += obj

    xref_pos = len(pdf.encode("latin-1"))
    pdf += f"xref\n0 {len(objects)+1}\n"
    pdf += "0000000000 65535 f \n"

    for off in offsets[1:]:
        pdf += f"{off:010d} 00000 n \n"

    pdf += (
        "trailer\n"
        f"<< /Size {len(objects)+1} /Root 1 0 R >>\n"
        "startxref\n"
        f"{xref_pos}\n"
        "%%EOF\n"
    )

    Path(path).write_bytes(pdf.encode("latin-1"))


spot_pdf = INPUT / "gate0_test_13_spots_separations.pdf"
write_spot_pdf(spot_pdf)
print(f"Creado: {spot_pdf}")
