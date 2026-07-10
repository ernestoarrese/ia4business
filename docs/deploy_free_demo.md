# Gate0 — Deploy demo gratuito

## Objetivo

Probar Gate0 fuera de Codespaces usando Docker y una plataforma gratuita experimental.

## Flujo recomendado

1. Desarrollar en Codespaces.
2. Probar localmente con uvicorn.
3. Ejecutar tests.
4. Construir imagen Docker.
5. Probar contenedor local.
6. Subir a GitHub.
7. Conectar Render o alternativa gratuita.

## Comandos locales

```bash
docker build -t gate0-demo .
docker run --rm -p 8000:8000 gate0-demo
```

## URL local

```text
http://localhost:8000
```

En Codespaces:

```bash
echo "https://${CODESPACE_NAME}-8000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
```

## Validaciones

- Abre pantalla inicial.
- /health responde status ok.
- PDF pequeño funciona.
- ZIP pequeño funciona.
- Probar límite real con ZIP 20 MB y 50 MB.

## Limitaciones esperadas

- Plataformas gratuitas pueden dormir por inactividad.
- Pueden tener límites de upload, CPU, RAM o disco temporal.
- No usar todavía como producción con archivos confidenciales permanentes.

## Siguiente decisión

Si la demo gratuita es lenta o limita ZIPs reales, pasar a VPS / AWS Lightsail / servidor propio.

## Render demo validation
- Auto Deploy On Commit validado manualmente.
- Fecha: Fri Jul 10 23:54:04 UTC 2026
