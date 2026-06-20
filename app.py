from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import shutil
import subprocess
import sys
import json

app = FastAPI(title="Gate0 Packaging QA")

ROOT = Path(__file__).parent
INPUT_DIR = ROOT / "data" / "input"
OUTPUT_DIR = ROOT / "data" / "output"
DASHBOARD_DIR = ROOT / "dashboard"

CURRENT_PDF = INPUT_DIR / "current_upload.pdf"
REPORT_JSON = OUTPUT_DIR / "gate0_report.json"

INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/dashboard", StaticFiles(directory=str(DASHBOARD_DIR), html=True), name="dashboard")
app.mount("/data", StaticFiles(directory=str(ROOT / "data")), name="data")


@app.get("/", response_class=HTMLResponse)
def upload_page():
    return """
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Gate0 Upload</title>
<style>
*{box-sizing:border-box}body{margin:0;min-height:100vh;font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;background:#f6f7fb;color:#0f172a;display:grid;place-items:center}
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
  <p>Sube un PDF. Gate0 analizará el archivo y abrirá el dashboard con la decisión, riesgos principales y evidencia.</p>
  <form class="drop" action="/analyze" method="post" enctype="multipart/form-data">
    <label>Cliente / Proyecto opcional</label>
    <input type="text" name="client" placeholder="Ejemplo: Alicorp, Gloria, Control Test"/>
    <label>Archivo PDF</label>
    <input type="file" name="file" accept="application/pdf,.pdf" required/>
    <button type="submit">Analizar archivo</button>
    <div class="note">El dashboard mostrará “Sin cliente” si no completas el campo.</div>
  </form>
</main>
</body>
</html>
"""


@app.post("/analyze")
async def analyze_pdf(file: UploadFile = File(...), client: str = Form(default="")):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se permiten PDF.")

    with CURRENT_PDF.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    cmd = [sys.executable, "gate0_check.py", str(CURRENT_PDF)]
    result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)

    if result.returncode != 0:
        return HTMLResponse(f"""
        <h1>Error ejecutando Gate0</h1>
        <h2>Comando</h2><pre>{' '.join(cmd)}</pre>
        <h2>STDOUT</h2><pre>{result.stdout}</pre>
        <h2>STDERR</h2><pre>{result.stderr}</pre>
        """, status_code=500)

    if not REPORT_JSON.exists():
        raise HTTPException(status_code=500, detail="No se encontró gate0_report.json")

    with REPORT_JSON.open("r", encoding="utf-8") as f:
        data = json.load(f)

    data["file"] = file.filename or "current_upload.pdf"
    data["client"] = client.strip() if client and client.strip() else "Sin cliente"
    data["process"] = data.get("business_assessment", {}).get("process", "flexo")

    with REPORT_JSON.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return RedirectResponse(url="/dashboard/index.html", status_code=303)


@app.get("/api/report")
def get_report():
    if not REPORT_JSON.exists():
        raise HTTPException(status_code=404, detail="No existe reporte")
    with REPORT_JSON.open("r", encoding="utf-8") as f:
        return JSONResponse(json.load(f))


@app.get("/api/pdf")
def get_pdf():
    if not CURRENT_PDF.exists():
        raise HTTPException(status_code=404, detail="No existe PDF")
    return FileResponse(
        str(CURRENT_PDF),
        media_type="application/pdf",
        headers={"Content-Disposition": "inline; filename=current_upload.pdf"}
    )
