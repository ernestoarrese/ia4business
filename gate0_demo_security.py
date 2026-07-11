import base64
import os
import secrets
from starlette.responses import PlainTextResponse


def install_demo_security(app):
    demo_user = os.getenv("GATE0_DEMO_USER", "gate0").strip() or "gate0"
    demo_password = os.getenv("GATE0_DEMO_PASSWORD", "").strip()
    max_upload_mb = int(os.getenv("GATE0_MAX_UPLOAD_MB", "100"))
    max_upload_bytes = max_upload_mb * 1024 * 1024

    def auth_challenge():
        return PlainTextResponse(
            "Gate0 demo privada. Autenticación requerida.",
            status_code=401,
            headers={"WWW-Authenticate": "Basic realm=\"Gate0 Demo\""},
        )

    def basic_auth_ok(authorization_header):
        if not demo_password:
            return True

        if not authorization_header or not authorization_header.lower().startswith("basic "):
            return False

        try:
            token = authorization_header.split(" ", 1)[1].strip()
            decoded = base64.b64decode(token).decode("utf-8")
            username, password = decoded.split(":", 1)
        except Exception:
            return False

        return secrets.compare_digest(username, demo_user) and secrets.compare_digest(password, demo_password)

    @app.middleware("http")
    async def gate0_demo_auth_middleware(request, call_next):
        if request.url.path == "/health":
            return await call_next(request)

        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > max_upload_bytes:
                    return PlainTextResponse(
                        f"Archivo demasiado grande para esta demo. Límite configurado: {max_upload_mb} MB.",
                        status_code=413,
                    )
            except ValueError:
                pass

        if not basic_auth_ok(request.headers.get("authorization")):
            return auth_challenge()

        return await call_next(request)
