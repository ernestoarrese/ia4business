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
import zipfile
import html
import csv
from datetime import datetime

app = FastAPI(title="Gate0 Packaging QA")

ROOT = Path(__file__).parent
RUNTIME_DIR = ROOT / "data" / "runtime"
UPLOADS_DIR = RUNTIME_DIR / "uploads"
REPORTS_DIR = RUNTIME_DIR / "reports"
TEMP_DIR = RUNTIME_DIR / "temp"
DASHBOARD_DIR = ROOT / "dashboard"

TTL_SECONDS = 30 * 60
HISTORY_DIR = ROOT / "data" / "history"
HISTORY_CSV = HISTORY_DIR / "analysis_history.csv"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/dashboard", StaticFiles(directory=str(DASHBOARD_DIR), html=True), name="dashboard")


def cleanup_old_runtime_files():
    now = time.time()
    for folder in [UPLOADS_DIR, REPORTS_DIR, TEMP_DIR]:
        for path in folder.glob("*"):
            try:
                if path.is_file() and now - path.stat().st_mtime > TTL_SECONDS:
                    path.unlink()
            except Exception:
                pass




def append_analysis_history(data):
    summary = data.get("readiness_summary", {})
    assessment = data.get("readiness_assessment", {})
    metrics = assessment.get("readiness_metrics", {})
    top_risks = summary.get("top_risks", [])
    top = top_risks[0] if top_risks else {}

    top_risk = top.get("check", "")
    top_risk_title = top.get("title") or top.get("check", "")
    top_risk_severity = top.get("business_severity") or top.get("severity") or ""

    file_exists = HISTORY_CSV.exists()

    fieldnames = [
        "timestamp",
        "session_id",
        "client",
        "file",
        "score",
        "status",
        "decision",
        "critical_count",
        "warning_count",
        "info_count",
        "top_risk",
        "top_risk_title",
        "top_risk_severity",
        "analysis_duration_seconds",
        "feedback_score",
        "feedback_comment",
    ]

    with HISTORY_CSV.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "session_id": data.get("session_id"),
            "client": data.get("client"),
            "file": data.get("file"),
            "score": summary.get("score"),
            "status": summary.get("status"),
            "decision": summary.get("decision"),
            "critical_count": metrics.get("critical_count", 0),
            "warning_count": metrics.get("warning_count", 0),
            "info_count": metrics.get("info_count", 0),
            "top_risk": top_risk,
            "top_risk_title": top_risk_title,
            "top_risk_severity": top_risk_severity,
            "analysis_duration_seconds": data.get("analysis_duration_seconds", ""),
            "feedback_score": "",
            "feedback_comment": "",
        })


def update_feedback_history(session_id, feedback_score, feedback_comment):
    if not HISTORY_CSV.exists():
        return False

    rows = []
    updated = False

    with HISTORY_CSV.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if row.get("session_id") == session_id:
                row["feedback_score"] = feedback_score
                row["feedback_comment"] = feedback_comment
                updated = True
            rows.append(row)

    if not updated:
        return False

    with HISTORY_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return True


def session_paths(session_id):
    return {
        "pdf": UPLOADS_DIR / f"{session_id}.pdf",
        "json": REPORTS_DIR / f"{session_id}.json",
        "csv": REPORTS_DIR / f"{session_id}.csv",
    }



ANALYZABLE_EXTENSIONS = {".pdf", ".ai"}
IMAGE_EXTENSIONS = {".psd", ".tif", ".tiff", ".jpg", ".jpeg", ".png"}
FONT_EXTENSIONS = {".otf", ".ttf"}


def safe_extract_zip(zip_path, extract_dir):
    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as z:
        for member in z.infolist():
            member_path = Path(member.filename)

            if member.is_dir():
                continue

            # Evitar path traversal
            if member_path.is_absolute() or ".." in member_path.parts:
                continue

            target = extract_dir / member.filename
            target.parent.mkdir(parents=True, exist_ok=True)

            with z.open(member) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)


def scan_intake_folder(folder):
    analyzable = []
    images = []
    fonts = []
    others = []

    for path in folder.rglob("*"):
        if not path.is_file():
            continue

        suffix = path.suffix.lower()
        rel = str(path.relative_to(folder))

        item = {
            "name": path.name,
            "relative_path": rel,
            "size_mb": round(path.stat().st_size / (1024 * 1024), 2),
            "extension": suffix,
        }

        if suffix in ANALYZABLE_EXTENSIONS:
            analyzable.append(item)
        elif suffix in IMAGE_EXTENSIONS:
            images.append(item)
        elif suffix in FONT_EXTENSIONS:
            fonts.append(item)
        else:
            others.append(item)

    return {
        "analyzable": sorted(analyzable, key=lambda x: x["relative_path"].lower()),
        "images": images,
        "fonts": fonts,
        "others": others,
    }


def possible_duplicate_note(analyzable):
    stems = {}
    for item in analyzable:
        stem = Path(item["name"]).stem.lower()
        stems.setdefault(stem, []).append(item["name"])

    duplicates = [names for names in stems.values() if len(names) > 1]

    if not duplicates:
        return ""

    return "Hay archivos con nombres similares. Pueden corresponder al mismo diseño; selecciona solo la versión que deseas analizar."


def render_zip_selection(session_id, client, inventory):
    analyzable = inventory["analyzable"]
    duplicate_note = possible_duplicate_note(analyzable)

    options = ""

    for idx, item in enumerate(analyzable):
        checked = "checked" if idx == 0 else ""
        label = html.escape(item["relative_path"])
        size = item["size_mb"]
        ext = item["extension"].upper().replace(".", "")

        options += f"""
        <label class="file-option">
          <input type="radio" name="selected_file" value="{html.escape(item['relative_path'])}" {checked}/>
          <div>
            <b>{label}</b>
            <span>{ext} · {size} MB</span>
          </div>
        </label>
        """

    if not options:
        options = '<div class="empty">No se encontraron PDF o AI analizables dentro del ZIP.</div>'

    return f"""
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Gate0 ZIP Intake</title>
<style>
body{{margin:0;min-height:100vh;font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;background:#f6f7fb;color:#0f172a;display:grid;place-items:center}}
.card{{width:min(860px,94vw);background:white;border:1px solid #e5e7eb;border-radius:28px;padding:32px;box-shadow:0 24px 70px rgba(15,23,42,.10)}}
h1{{font-size:34px;letter-spacing:-.05em;margin:0 0 8px}}
p{{color:#667085;line-height:1.45}}
.summary{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:20px 0}}
.summary div{{background:#f8fafc;border:1px solid #edf2f7;border-radius:18px;padding:14px}}
.summary b{{display:block;font-size:22px}}
.summary span{{color:#667085;font-size:13px}}
.file-option{{display:flex;gap:12px;align-items:flex-start;border:1px solid #e5e7eb;border-radius:18px;padding:14px;margin:10px 0;cursor:pointer}}
.file-option:hover{{border-color:#93c5fd;background:#f8fafc}}
.file-option input{{margin-top:4px}}
.file-option b{{display:block}}
.file-option span{{display:block;color:#667085;font-size:13px;margin-top:4px}}
.note{{background:#fffbeb;border:1px solid #fde68a;border-radius:16px;padding:12px;color:#92400e;margin:14px 0}}
button{{width:100%;border:0;border-radius:999px;background:#111827;color:#fff;padding:15px 18px;font-weight:950;font-size:16px;cursor:pointer;margin-top:16px}}
.empty{{padding:18px;background:#f8fafc;border-radius:16px;color:#667085}}
</style>
</head>
<body>
<main class="card">
  <h1>Selecciona archivo para análisis</h1>
  <p>Gate0 encontró archivos dentro del ZIP. En esta versión se analiza un archivo a la vez.</p>

  <div class="summary">
    <div><b>{len(inventory["analyzable"])}</b><span>PDF / AI analizables</span></div>
    <div><b>{len(inventory["images"])}</b><span>Imágenes soporte</span></div>
    <div><b>{len(inventory["fonts"])}</b><span>Fuentes soporte</span></div>
  </div>

  {f'<div class="note">{html.escape(duplicate_note)}</div>' if duplicate_note else ''}

  <form action="/analyze-selected" method="post">
    <input type="hidden" name="sid" value="{html.escape(session_id)}"/>
    <input type="hidden" name="client" value="{html.escape(client)}"/>
    {options}
    <button type="submit" {"disabled" if not analyzable else ""}>Analizar seleccionado</button>
  </form>
</main>
</body>
</html>
"""


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
  <p>Sube un PDF o ZIP. Si es ZIP, Gate0 mostrará los archivos analizables para que selecciones uno.</p>
  <form class="drop" action="/analyze" method="post" enctype="multipart/form-data">
    <label>Cliente / Proyecto opcional</label>
    <input type="text" name="client" placeholder="Ejemplo: Control Test"/>
    <label>Archivo PDF o ZIP</label>
    <input type="file" name="file" accept="application/pdf,.pdf,.zip,application/zip" required/>
    <button type="submit">Analizar archivo</button>
    <div class="note">Runtime seguro v1: archivos temporales con limpieza automática.</div>
  </form>
</main>
</body>
</html>
"""



def run_gate0_analysis(input_file_path, original_filename, client, session_id, input_type="PDF", files_detected=1):
    paths = session_paths(session_id)

    # Copia el archivo seleccionado al runtime principal solo si viene de otra ruta
    input_file_path = Path(input_file_path)
    if input_file_path.resolve() != paths["pdf"].resolve():
        shutil.copy(input_file_path, paths["pdf"])

    cmd = [sys.executable, "gate0_check.py", str(paths["pdf"])]
    analysis_start = time.time()
    result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    analysis_duration_seconds = round(time.time() - analysis_start, 2)

    if result.returncode != 0:
        return HTMLResponse(f"<h1>Error ejecutando Gate0</h1><pre>{result.stderr}</pre><pre>{result.stdout}</pre>", status_code=500)

    default_json = ROOT / "data" / "output" / "gate0_report.json"
    default_csv = ROOT / "data" / "output" / "gate0_report.csv"

    if not default_json.exists():
        raise HTTPException(status_code=500, detail="No se encontró gate0_report.json")

    with default_json.open("r", encoding="utf-8") as f:
        data = json.load(f)

    data["file"] = original_filename or Path(input_file_path).name
    data["client"] = client.strip() if client and client.strip() else "Sin cliente"
    data["process"] = data.get("business_assessment", {}).get("process", "flexo")
    data["session_id"] = session_id
    data["runtime_ttl_minutes"] = 30
    data["analysis_duration_seconds"] = analysis_duration_seconds
    data["input_type"] = input_type
    data["files_detected"] = files_detected

    with paths["json"].open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    append_analysis_history(data)

    if default_csv.exists():
        shutil.copy(default_csv, paths["csv"])

    return RedirectResponse(url=f"/dashboard/index.html?sid={session_id}", status_code=303)


@app.post("/analyze")
async def analyze_pdf(file: UploadFile = File(...), client: str = Form(default="")):
    cleanup_old_runtime_files()

    filename = file.filename or ""
    suffix = Path(filename).suffix.lower()

    if suffix not in [".pdf", ".ai", ".zip"]:
        raise HTTPException(status_code=400, detail="Solo se permiten PDF, AI o ZIP.")

    session_id = uuid.uuid4().hex

    if suffix in [".pdf", ".ai"]:
        upload_path = UPLOADS_DIR / f"{session_id}{suffix}"

        with upload_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return run_gate0_analysis(
            input_file_path=upload_path,
            original_filename=filename,
            client=client,
            session_id=session_id,
            input_type=suffix.replace(".", "").upper(),
            files_detected=1,
        )

    # ZIP Intake v1
    zip_path = UPLOADS_DIR / f"{session_id}.zip"
    extract_dir = TEMP_DIR / session_id

    with zip_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        safe_extract_zip(zip_path, extract_dir)
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="ZIP inválido o corrupto.")

    inventory = scan_intake_folder(extract_dir)

    # Guardar inventario runtime
    paths = session_paths(session_id)
    inventory_data = {
        "session_id": session_id,
        "client": client.strip() if client and client.strip() else "Sin cliente",
        "source_zip": filename,
        "inventory": inventory,
    }

    with paths["json"].open("w", encoding="utf-8") as f:
        json.dump(inventory_data, f, indent=4, ensure_ascii=False)

    return HTMLResponse(render_zip_selection(session_id, client, inventory))


@app.post("/analyze-selected")
async def analyze_selected(
    sid: str = Form(...),
    selected_file: str = Form(...),
    client: str = Form(default="")
):
    cleanup_old_runtime_files()

    extract_dir = TEMP_DIR / sid
    selected_path = extract_dir / selected_file

    if not selected_path.exists() or not selected_path.is_file():
        raise HTTPException(status_code=404, detail="Archivo seleccionado no existe o expiró.")

    suffix = selected_path.suffix.lower()

    if suffix not in [".pdf", ".ai"]:
        raise HTTPException(status_code=400, detail="Archivo no analizable.")

    inventory = scan_intake_folder(extract_dir)

    return run_gate0_analysis(
        input_file_path=selected_path,
        original_filename=selected_path.name,
        client=client,
        session_id=sid,
        input_type="ZIP",
        files_detected=len(inventory.get("analyzable", [])),
    )



@app.get("/api/report")
def get_report(sid: str):
    cleanup_old_runtime_files()
    paths = session_paths(sid)
    if not paths["json"].exists():
        raise HTTPException(status_code=404, detail="Reporte expirado o inexistente")
    with paths["json"].open("r", encoding="utf-8") as f:
        return JSONResponse(json.load(f))



@app.post("/api/feedback")
async def save_feedback(payload: dict):
    sid = payload.get("sid")
    score = str(payload.get("score", "")).strip()
    comment = str(payload.get("comment", "")).strip()

    if not sid:
        raise HTTPException(status_code=400, detail="Falta sid")

    ok = update_feedback_history(sid, score, comment)

    if not ok:
        raise HTTPException(status_code=404, detail="No se encontró sesión en histórico")

    return {"ok": True}


@app.get("/api/pdf")
def get_pdf(sid: str):
    cleanup_old_runtime_files()
    paths = session_paths(sid)
    if not paths["pdf"].exists():
        raise HTTPException(status_code=404, detail="PDF expirado o inexistente")
    return FileResponse(str(paths["pdf"]), media_type="application/pdf", headers={"Content-Disposition": "inline; filename=gate0_upload.pdf"})
