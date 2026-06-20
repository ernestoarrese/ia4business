from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import shutil
import subprocess
import sys
import json
import time
import uuid

app = FastAPI(title="Gate0 Packaging QA")

ROOT = Path(__file__).parent
RUNTIME_DIR = ROOT / "data" / "runtime"
UPLOADS_DIR = RUNTIME_DIR / "uploads"
REPORTS_DIR = RUNTIME_DIR / "reports"
DASHBOARD_DIR = ROOT / "dashboard"

TTL_SECONDS = 30 * 60

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/dashboard", StaticFiles(directory=str(DASHBOARD_DIR), html=True), name="dashboard")


def cleanup_old_runtime_files():
    now = time.time()
    for folder in [UPLOADS_DIR, REPORTS_DIR]:
        for path in folder.glob("*"):
            try:
                if path.is_file() and now - path.stat().st_mtime > TTL_SECONDS:
                    path.unlink()
            except Exception:
                pass


def session_paths(session_id):
    return {
        "pdf": UPLOADS_DIR / f"{session_id}.pdf",
        "json": REPORTS_DIR / f"{session_id}.json",
        "csv": REPORTS_DIR / f"{session_id}.csv",
    }


@app.get("/", response_class=HTMLResponse)
def upload_page():
    cleanup_old_runtime_files()
    return """
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Gate0 Upload</title>
<style>
body{margin:0;min-height:100vh;font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;background:#f6f7fb;color:#0f172a;display:grid;place-items:center}
.card{width:min(720px,92vw);background:white;border:1px solid #e5e7eb;border-radius:28px;padding:36px;box-shadow:0 24px 70px rgba(15,23,42,.10)}
.logo{width:48px;height:48px;border-radius:16px;background:#111827;color:#fff;display:grid;place-items:center;font-weight:950;margin-bottom:18px}
h1{font-size:38px;letter-spacing:-.05em;margin:0 0 8px}p{color:#667085;line-height:1.45}
.drop{margin-top:24px;border:2px dashed #cbd5e1;background:#f8fafc;border-radius:24px;padding:28px}
label{display:block;font-weight:850;margin:0 0 8px}input{width:100%;padding:14px;border:1px solid #e5e7eb;border-radius:14px;background:white;margin-bottom:16px;font-size:15px}
button{width:100%;border:0;border-radius:999px;background:#111827;color:#fff;padding:15px 18px;font-weight:950;font-size:16px;cursor:pointer}
.note{font-size:13px;color:#667085;margin-top:14px}
</style>
</head>
<body>
<main class="card">
  <div class="logo">G0</div>
  <h1>Gate0 Packaging QA</h1>
  <p>Sube un PDF. Gate0 analizará el archivo y abrirá el dashboard. Los archivos temporales se eliminan automáticamente.</p>
  <form class="drop" action="/analyze" method="post" enctype="multipart/form-data">
    <label>Cliente / Proyecto opcional</label>
    <input type="text" name="client" placeholder="Ejemplo: Control Test"/>
    <label>Archivo PDF</label>
    <input type="file" name="file" accept="application/pdf,.pdf" required/>
    <button type="submit">Analizar archivo</button>
    <div class="note">Runtime seguro v1: archivos temporales con limpieza automática.</div>
  </form>
</main>
</body>
</html>
"""


@app.post("/analyze")
async def analyze_pdf(file: UploadFile = File(...), client: str = Form(default="")):
    cleanup_old_runtime_files()

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten PDF.")

    session_id = uuid.uuid4().hex
    paths = session_paths(session_id)

    with paths["pdf"].open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    cmd = [sys.executable, "gate0_check.py", str(paths["pdf"])]
    result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)

    if result.returncode != 0:
        return HTMLResponse(f"<h1>Error ejecutando Gate0</h1><pre>{result.stderr}</pre><pre>{result.stdout}</pre>", status_code=500)

    default_json = ROOT / "data" / "output" / "gate0_report.json"
    default_csv = ROOT / "data" / "output" / "gate0_report.csv"

    if not default_json.exists():
        raise HTTPException(status_code=500, detail="No se encontró gate0_report.json")

    with default_json.open("r", encoding="utf-8") as f:
        data = json.load(f)

    data["file"] = file.filename or "current_upload.pdf"
    data["client"] = client.strip() if client and client.strip() else "Sin cliente"
    data["process"] = data.get("business_assessment", {}).get("process", "flexo")
    data["session_id"] = session_id
    data["runtime_ttl_minutes"] = 30

    with paths["json"].open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    if default_csv.exists():
        shutil.copy(default_csv, paths["csv"])

    return RedirectResponse(url=f"/dashboard/index.html?sid={session_id}", status_code=303)


@app.get("/api/report")
def get_report(sid: str):
    cleanup_old_runtime_files()
    paths = session_paths(sid)
    if not paths["json"].exists():
        raise HTTPException(status_code=404, detail="Reporte expirado o inexistente")
    with paths["json"].open("r", encoding="utf-8") as f:
        return JSONResponse(json.load(f))


@app.get("/api/pdf")
def get_pdf(sid: str):
    cleanup_old_runtime_files()
    paths = session_paths(sid)
    if not paths["pdf"].exists():
        raise HTTPException(status_code=404, detail="PDF expirado o inexistente")
    return FileResponse(str(paths["pdf"]), media_type="application/pdf", headers={"Content-Disposition": "inline; filename=gate0_upload.pdf"})
