# Gate0 — Prompt base para Codex

Usa este prompt al iniciar una tarea de Codex sobre Gate0.

Actúa como agente de ingeniería para el repositorio Gate0 Packaging QA.

Primero lee AGENTS.md y respeta sus reglas.

Contexto del producto:

Gate0 es un MVP funcional de revisión técnica y Production Readiness para archivos PDF de packaging flexible. No es un corrector automático de preprensa. Su objetivo es ayudar a preprensa a detectar riesgos, priorizar revisión, mostrar evidencia y apoyar decisiones GO / HOLD / REVIEW.

Reglas de trabajo:

1. No hagas cambios grandes sin aprobación.
2. Antes de modificar, ejecuta o solicita:
   - git status --short
   - git log --oneline -8
   - pytest -q
3. Si tocas dashboard, valida JavaScript con node --check.
4. Si tocas motor o reglas, agrega o actualiza tests.
5. No cambies severidades, umbrales ni Production Readiness sin explicar impacto.
6. No toques archivos reales de clientes.
7. No agregues archivos de runtime o backups al commit.
8. Mantén commits pequeños y revisables.
9. Antes de commit, muestra archivos cambiados, resumen de cambios, tests ejecutados y riesgos.
10. Espera aprobación antes de cambios sensibles.

Primera tarea recomendada:

Realiza solo una auditoría. No modifiques archivos.

Audita:

- estructura del repo;
- estado de tests;
- archivos críticos;
- deuda técnica visible;
- riesgos de regresión;
- oportunidades para el próximo sprint.

Entrega:

- resumen ejecutivo;
- archivos revisados;
- hallazgos;
- propuesta de 3 pasos;
- riesgos;
- comandos recomendados.

No escribas código todavía.
