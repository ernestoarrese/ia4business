# Sprint 29B.1 — Production Context Audit

## Objetivo

Auditar qué existe hoy en Gate0 para Production Context y definir el siguiente paso para convertirlo en una capa explícita del producto.

## Estado confirmado

Gate0 ya tiene una base parcial de contexto productivo:

- `context_engine.py` enriquece hallazgos técnicos con contexto disponible.
- `profiles/flexo_pet_bopp_default.json` define un perfil operativo inicial.
- `business_rules.py` carga perfiles operativos.
- `business_rules.py` expone `operational_profile`.
- `readiness_summary.py` recibe `operational_profile`.
- `gate0_check.py` incluye `operational_profile` en el reporte.
- Existen pruebas para carga de perfil y uso de thresholds.

## Perfil actual

Perfil existente:

- `profile_name`: `flexo_pet_bopp_default`
- `process`: `flexo`
- `substrate_family`: `PET_BOPP`
- `max_tac_percent`: `280`
- `minimum_dpi`: `250`
- `recommended_dpi`: `300`
- separaciones normales hasta `8`
- revisión entre `9–12`
- crítico sobre `12`

## Lo que ya está conectado

### Business Rules

`business_rules.py` ya puede:

- cargar profile desde `profiles/flexo_pet_bopp_default.json`;
- usar fallback si el profile falta o es inválido;
- exponer resumen operativo;
- usar thresholds de Small Text;
- usar límite TAC desde profile;
- exponer `operational_profile` dentro de `business_assessment`.

### Production Readiness

`readiness_summary.py` ya recibe `operational_profile` y lo incluye en `production_readiness_v2.operational_context`.

### Reporte principal

`gate0_check.py` ya incluye:

- `business_assessment`;
- `operational_profile`;
- `production_readiness_v2`.

## Lo que falta

Gate0 todavía no tiene un contrato explícito de Production Context como producto.

Falta:

- normalizar el contrato mínimo de profile;
- validar que el profile tenga campos obligatorios;
- exponer claramente qué profile se usó;
- proteger thresholds críticos con tests;
- preparar selección futura de perfiles sin romper el default;
- conectar el contexto al lenguaje ejecutivo de manera más visible.

## Riesgos

- El contexto existe, pero puede pasar desapercibido en UI/reportes.
- Si el profile cambia sin contrato, se pueden romper reglas de negocio.
- Gate0 todavía opera con un solo profile default.
- No hay selector de proceso/material todavía.
- La capa de contexto aún no diferencia varios escenarios productivos.

## Recomendación

Avanzar con:

### Sprint 29B.2 — Production Profile Contract

Objetivo:

- crear contrato mínimo validado para perfiles productivos;
- agregar pruebas de campos obligatorios;
- proteger thresholds actuales;
- preparar metadata clara para UI/reporte;
- mantener `flexo_pet_bopp_default` como default.

No cambiar todavía:

- UI;
- dashboard;
- scoring;
- reglas de severidad;
- selección de múltiples perfiles.

