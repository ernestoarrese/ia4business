# Gate0 Parser Capability Matrix

## Estado actual validado

Gate0 puede detectar actualmente:

- RGB Detection
- Effective DPI
- Font Embedded
- TAC Detection
- Overprint Fill/Stroke parcial
- White Ink global
- Spot Detection global
- Number of Separations global
- PDF Structure Metrics

## Capacidades parciales

- Overprint por página/documento, no por objeto.
- White + Overprint se maneja como WARNING contextual.
- CMYK process count se asume como 4 en MVP.
- PyMuPDF puede convertir CMYK/Spot a RGB renderizado.

## Capacidades no disponibles actualmente

- Separación por objeto.
- Color activo por objeto.
- White por objeto.
- Spot por objeto.
- Rich Black real por objeto.
- Barcode Detection.
- QR Detection.
- Small Text Detection.
- Minimum Line Detection.

## Decisión técnica

No reconstruir object_color_separation_map.py en esta fase.

Motivo:

PyMuPDF no garantiza trazabilidad objeto → separación.

Por lo tanto, Gate0 no debe afirmar:

White objeto + Overprint = CRITICAL

Solo puede afirmar:

White global + Overprint en misma página = WARNING

## Próximo foco

- Dashboard base.
- Validación con archivos reales.
- Risk Intelligence Engine.
- Comment Engine v2.
