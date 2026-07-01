# Gate0 Experience Layer v1

## Propósito

El Experience Layer convierte el uso real de Gate0 en aprendizaje acumulado.

No reemplaza al Knowledge Layer.  
No define reglas oficiales por sí solo.  
No toma decisiones operativas directamente.

Su función es detectar patrones a partir del histórico, feedback y casos reales.

---

## Diferencia entre Knowledge y Experience

### Knowledge Layer

Conocimiento validado y estable.

Ejemplos:

- TAC máximo por proceso.
- Umbrales de separaciones.
- Severidad por check.
- Limitaciones del parser.
- Reglas por cliente o perfil.

### Experience Layer

Aprendizaje observado a partir del uso real.

Ejemplos:

- Checks más frecuentes.
- Riesgos con peor feedback.
- Clientes con más HOLD / NO_GO.
- Tipos de ZIP más comunes.
- Comentarios que el usuario pide mejorar.
- Patrones recurrentes entre riesgo, decisión y feedback.

---

## Flujo

```text
Análisis reales
↓
History
↓
Feedback
↓
Experience Layer
↓
Patrones
↓
Mejoras propuestas
↓
Knowledge Layer validado

