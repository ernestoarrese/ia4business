# Gate0 Knowledge Layer v1

Gate0 no debe depender únicamente de lógica embebida en código. La plataforma debe separar claramente motor, agentes, conocimiento experto, histórico de aprendizaje y presentación.

El Knowledge Layer es una capa transversal consultada por los agentes. No inspecciona archivos, no calcula readiness, no genera dashboard y no reemplaza a los agentes.

## Rol del Knowledge Layer

Responde preguntas como:

- ¿Cuál es el TAC máximo permitido para este perfil?
- ¿Cuántas separaciones son aceptables para este proceso?
- ¿Qué significa un RGB imprimible?
- ¿Qué riesgo operativo genera una fuente no embebida?
- ¿Qué clientes tienen reglas particulares?
- ¿Qué problemas aparecen con mayor frecuencia en el histórico?

## Dominios de conocimiento

### 1. Business Knowledge

Reglas de negocio y criterios operativos:

- Severidad por check.
- Penalizaciones readiness.
- Umbrales de TAC.
- Umbrales de separaciones.
- Reglas GO / GO_WITH_NOTES / HOLD / NO_GO.

Archivos actuales relacionados:

- business_rules.py
- readiness_engine.py
- profiles/

### 2. Packaging Knowledge

Conocimiento experto de preprensa y packaging:

- Por qué RGB afecta impresión.
- Por qué TAC alto genera problemas de secado.
- Por qué fuentes no embebidas son críticas.
- Por qué demasiadas separaciones aumentan riesgo operativo.
- Qué hacer frente a spots duplicados, blancos, barnices o separaciones técnicas.

Archivos actuales relacionados:

- expert_comment_engine.py
- risk_evidence_engine.py
- readiness_summary.py

### 3. Process Knowledge

Conocimiento específico del proceso productivo:

- Flexografía.
- Huecograbado.
- Offset.
- Digital.

Cada proceso puede tener límites distintos de TAC, resolución, separaciones, textos negativos y sobreimpresión.

### 4. Customer Knowledge

Conocimiento específico por cliente o familia de productos:

- Cliente con estándar propio de color.
- Cliente que exige PDF en curvas.
- Cliente que acepta cierto número máximo de spots.
- Cliente que requiere blanco técnico específico.
- Cliente con reglas particulares de naming.

Este conocimiento no debe estar embebido en código duro.

### 5. Parser Capability Knowledge

Conocimiento sobre qué puede y qué no puede detectar Gate0:

- PyMuPDF detecta separaciones globales.
- PyMuPDF no asocia confiablemente objeto → separación.
- White global + Overprint página puede ser WARNING.
- White objeto + Overprint objeto no debe asumirse como CRITICAL si no hay evidencia.

Archivos actuales relacionados:

- parser_capability_audit.py
- parser_capability_matrix.md

### 6. Learning Knowledge

Conocimiento derivado del histórico de uso.

Fuente principal:

- data/history/analysis_history.csv

Ejemplos futuros:

- Checks más frecuentes.
- Clientes con más HOLD / NO_GO.
- Riesgos con peor feedback.
- Comentarios expertos menos útiles.
- ZIPs con más archivos soporte.
- Casos donde el usuario pide mejoras recurrentes.

## Relación History → Learning Knowledge

El histórico no debe verse solo como estadística. Debe verse como materia prima del aprendizaje.

Flujo:

Análisis reales
↓
Histórico
↓
Patrones
↓
Learning Knowledge
↓
Mejores reglas
↓
Mejores comentarios
↓
Mejores decisiones

## Qué NO debe vivir en código duro

Evitar hardcodear directamente en agentes:

- Umbrales por cliente.
- Umbrales por proceso.
- Textos expertos largos.
- Reglas específicas de naming.
- Reglas particulares de cliente.
- Límites técnicos que pueden cambiar.
- Recomendaciones que dependan del contexto productivo.

El código debe ejecutar. El conocimiento debe configurar e informar.

## Principio arquitectónico

Las reglas de negocio pueden cambiar sin modificar el motor.  
El conocimiento puede crecer sin modificar los agentes.  
Los agentes pueden evolucionar sin modificar el dashboard.  
El dashboard puede cambiar sin modificar la lógica técnica.

## Estado actual

| Dominio | Estado actual |
|---|---|
| Business Knowledge | Parcial en business_rules.py, readiness_engine.py, profiles/ |
| Packaging Knowledge | Parcial en expert_comment_engine.py, risk_evidence_engine.py |
| Process Knowledge | Parcial en perfiles |
| Customer Knowledge | No implementado |
| Parser Capability Knowledge | Documentado parcialmente |
| Learning Knowledge | Iniciado con histórico + feedback |

## Próxima evolución recomendada

1. Documentar reglas existentes.
2. Mantener histórico limpio y enriquecido.
3. Revisar histórico cada cierto número de análisis reales.
4. Convertir patrones repetidos en mejoras del Knowledge Layer.
5. Mover gradualmente textos expertos y umbrales desde código hacia configuración.

## Regla de evolución

Antes de agregar nuevos checks, preguntar:

1. ¿El histórico demuestra que este problema aparece con frecuencia?
2. ¿El usuario lo entiende?
3. ¿El comentario actual ayuda?
4. ¿La decisión Gate0 fue razonable?
5. ¿Esto pertenece a detección, decisión, conocimiento experto o reporting?

Gate0 debe aprender de su uso real antes de expandirse agresivamente.
