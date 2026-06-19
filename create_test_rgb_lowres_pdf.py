from pathlib import Path
import fitz

out = Path("data/input/gate0_test_rgb_lowres_dedupe.pdf")

doc = fitz.open()
page = doc.new_page(width=595, height=842)

# Varios objetos RGB vectoriales para disparar RGB_OBJECT repetido
page.draw_rect(
    fitz.Rect(60, 80, 535, 220),
    color=(0.9, 0.1, 0.1),
    fill=(1, 0.85, 0.2),
    width=2,
)

page.draw_rect(
    fitz.Rect(60, 250, 535, 390),
    color=(0.1, 0.4, 0.9),
    fill=(0.2, 0.9, 0.4),
    width=2,
)

page.draw_circle(
    fitz.Point(300, 500),
    90,
    color=(0.8, 0.2, 0.9),
    fill=(0.95, 0.6, 0.1),
    width=2,
)

# Imagen raster muy pequeña escalada grande para baja resolución
w, h = 80, 80
samples = bytearray()

for y in range(h):
    for x in range(w):
        r, g, b = 245, 158, 11
        if abs(x - y) < 3 or abs((w - x) - y) < 3:
            r, g, b = 255, 255, 255
        samples.extend([r, g, b])

pix = fitz.Pixmap(fitz.csRGB, w, h, bytes(samples), False)

# Escalada grande => dpi efectivo bajo
page.insert_image(
    fitz.Rect(120, 580, 475, 780),
    pixmap=pix
)

doc.save(out)
doc.close()

print(f"PDF creado: {out}")
