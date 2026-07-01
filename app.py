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
from gate0.services.history_service import HistoryService

app = FastAPI(title="Gate0 Packaging QA")

ROOT = Path(__file__).parent
RUNTIME_DIR = ROOT / "data" / "runtime"
UPLOADS_DIR = RUNTIME_DIR / "uploads"
REPORTS_DIR = RUNTIME_DIR / "reports"
TEMP_DIR = RUNTIME_DIR / "temp"
MANUAL_UPLOADS_DIR = RUNTIME_DIR / "manual_uploads"
DASHBOARD_DIR = ROOT / "dashboard"

TTL_SECONDS = 30 * 60
HISTORY_DIR = ROOT / "data" / "history"
HISTORY_CSV = HISTORY_DIR / "analysis_history.csv"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)
MANUAL_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_DIR.mkdir(parents=True, exist_ok=True)
history_service = HistoryService(HISTORY_CSV)

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
    history_service.save_analysis(data)

def update_feedback_history(session_id, feedback_score, feedback_comment):
    return history_service.update_feedback(session_id, feedback_score, feedback_comment)

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

        # Ignorar basura común de ZIP generado en Mac y archivos vacíos
        if "__MACOSX" in path.parts:
            continue

        if path.name.startswith("._") or path.name == ".DS_Store":
            continue

        if path.stat().st_size == 0:
            continue

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
    analyzable = inventory.get("analyzable", [])
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

    support_images = "".join(
        f"<li>{html.escape(item['name'])} <span>{item['size_mb']} MB</span></li>"
        for item in inventory.get("images", [])[:20]
    ) or "<li>No se detectaron imágenes soporte.</li>"

    support_fonts = "".join(
        f"<li>{html.escape(item['name'])} <span>{item['size_mb']} MB</span></li>"
        for item in inventory.get("fonts", [])[:30]
    ) or "<li>No se detectaron fuentes soporte.</li>"

    return f"""
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Gate0 ZIP Intake</title>
<style>
body{{margin:0;min-height:100vh;font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;background:#f6f7fb;color:#0f172a;display:grid;place-items:center}}
.card{{width:min(960px,94vw);background:white;border:1px solid #e5e7eb;border-radius:28px;padding:32px;box-shadow:0 24px 70px rgba(15,23,42,.10)}}
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
.support-box{{margin-top:20px;background:#f8fafc;border:1px solid #edf2f7;border-radius:18px;padding:16px}}
.support-box h3{{margin:0 0 8px;font-size:16px}}
.support-grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.support-box ul{{margin:8px 0 0;padding-left:18px;color:#334155;font-size:13px;line-height:1.45;max-height:220px;overflow:auto}}
.support-box li span{{color:#667085;font-size:12px}}
@media(max-width:800px){{.summary,.support-grid{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<main class="card">
  <h1>Selecciona archivo para análisis</h1>
  <p>Gate0 encontró archivos dentro del ZIP. En esta versión se analiza un archivo a la vez.</p>

  <div class="summary">
    <div><b>{len(inventory.get("analyzable", []))}</b><span>PDF / AI analizables</span></div>
    <div><b>{len(inventory.get("images", []))}</b><span>Imágenes soporte</span></div>
    <div><b>{len(inventory.get("fonts", []))}</b><span>Fuentes soporte</span></div>
  </div>

  {f'<div class="note">{html.escape(duplicate_note)}</div>' if duplicate_note else ''}

  <form action="/analyze-selected" method="post">
    <input type="hidden" name="sid" value="{html.escape(session_id)}"/>
    <input type="hidden" name="client" value="{html.escape(client)}"/>
    {options}
    <button type="submit" {"disabled" if not analyzable else ""}>Analizar seleccionado</button>
  </form>

  <div class="support-box">
    <h3>Soportes encontrados</h3>
    <div class="support-grid">
      <div>
        <b>Imágenes ({len(inventory.get("images", []))})</b>
        <ul>{support_images}</ul>
      </div>
      <div>
        <b>Fuentes ({len(inventory.get("fonts", []))})</b>
        <ul>{support_fonts}</ul>
      </div>
    </div>
  </div>
</main>
</body>
</html>
"""



def list_manual_zips():
    items = []
    for path in sorted(MANUAL_UPLOADS_DIR.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True):
        items.append({
            "name": path.name,
            "size_mb": round(path.stat().st_size / (1024 * 1024), 2),
        })
    return items



@app.get("/", response_class=HTMLResponse)
def upload_page():
    cleanup_old_runtime_files()
    manual_zips = list_manual_zips()

    zip_cards = ""
    for z in manual_zips:
        zip_cards += f"""
        <label class="zip-card">
          <input type="radio" name="zip_name" value="{html.escape(z['name'])}">
          <div>
            <b>{html.escape(z['name'])}</b>
            <span>{z['size_mb']} MB · ZIP local</span>
          </div>
        </label>
        """

    if not zip_cards:
        zip_cards = '<div class="empty">No hay ZIPs locales en data/runtime/manual_uploads/</div>'

    return f"""
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Gate0 Upload</title>
<style>
body{{margin:0;min-height:100vh;font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;background:#f6f7fb;color:#0f172a;display:grid;place-items:center}}
.card{{width:min(820px,92vw);background:white;border:1px solid #e5e7eb;border-radius:28px;padding:36px;box-shadow:0 24px 70px rgba(15,23,42,.10)}}
.logo{{width:48px;height:48px;border-radius:16px;background:#111827;color:#fff;display:grid;place-items:center;font-weight:950;margin-bottom:18px}}
h1{{font-size:38px;letter-spacing:-.05em;margin:0 0 8px}}
h2{{font-size:18px;margin:26px 0 10px}}
p{{color:#667085;line-height:1.45}}
.drop{{margin-top:18px;border:2px dashed #cbd5e1;background:#f8fafc;border-radius:24px;padding:24px}}
label{{display:block;font-weight:850;margin:0 0 8px}}
input[type=text], input[type=file]{{width:100%;padding:14px;border:1px solid #e5e7eb;border-radius:14px;background:white;margin-bottom:16px;font-size:15px}}
button{{width:100%;border:0;border-radius:999px;background:#111827;color:#fff;padding:15px 18px;font-weight:950;font-size:16px;cursor:pointer}}
.note{{font-size:13px;color:#667085;margin-top:14px}}
.zip-card{{display:flex;gap:12px;align-items:flex-start;border:1px solid #e5e7eb;border-radius:18px;padding:14px;margin:10px 0;cursor:pointer;background:#fff}}
.zip-card:hover{{border-color:#93c5fd;background:#f8fafc}}
.zip-card input{{margin-top:4px}}
.zip-card b{{display:block}}
.zip-card span{{display:block;color:#667085;font-size:13px;margin-top:4px}}
.empty{{padding:16px;background:#f8fafc;border:1px solid #edf2f7;border-radius:16px;color:#667085}}
.divider{{height:1px;background:#e5e7eb;margin:26px 0}}
</style>
</head>
<body>
<main class="card">
  <div class="logo">G0</div>
  <h1>Gate0 Packaging QA</h1>
  <p>Sube un PDF/ZIP pequeño o selecciona un ZIP local grande desde runtime.</p>

  <form class="drop" action="/analyze" method="post" enctype="multipart/form-data">
    <label>Cliente / Proyecto opcional</label>
    <input type="text" name="client" placeholder="Ejemplo: Control Test"/>
    <label>Archivo PDF o ZIP pequeño</label>
    <input type="file" name="file" accept="application/pdf,.pdf,.zip,application/zip"/>
    <button type="submit">Analizar archivo subido</button>
    <div class="note">Para ZIPs grandes usa la sección inferior.</div>
  </form>

  <div class="divider"></div>

  <form action="/analyze-local-zip" method="post">
    <label>Cliente / Proyecto opcional</label>
    <input type="text" name="client" placeholder="Ejemplo: Cliente ZIP"/>
    <h2>ZIPs locales grandes</h2>
    <p>Coloca tus ZIPs en <b>data/runtime/manual_uploads/</b> y aparecerán aquí.</p>
    {zip_cards}
    <button type="submit">Abrir ZIP seleccionado</button>
  </form>
</main>
</body>
</html>
"""




def run_gate0_analysis(input_file_path, original_filename, client, session_id, input_type="PDF", files_detected=1):
    paths = session_paths(session_id)

    input_file_path = Path(input_file_path)

    if input_file_path.resolve() != paths["pdf"].resolve():
        shutil.copy(input_file_path, paths["pdf"])

    cmd = [sys.executable, "gate0_check.py", str(paths["pdf"])]
    analysis_start = time.time()
    result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    analysis_duration_seconds = round(time.time() - analysis_start, 2)

    if result.returncode != 0:
        return HTMLResponse(
            f"<h1>Error ejecutando Gate0</h1><pre>{result.stderr}</pre><pre>{result.stdout}</pre>",
            status_code=500
        )

    default_json = ROOT / "data" / "output" / "gate0_report.json"
    default_csv = ROOT / "data" / "output" / "gate0_report.csv"

    if not default_json.exists():
        raise HTTPException(status_code=500, detail="No se encontró gate0_report.json")

    with default_json.open("r", encoding="utf-8") as f:
        data = json.load(f)

    data["file"] = original_filename or input_file_path.name
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



@app.post("/analyze-local-zip")
async def analyze_local_zip(zip_name: str = Form(...), client: str = Form(default="")):
    cleanup_old_runtime_files()

    # seguridad: solo nombre, no path
    zip_name = Path(zip_name).name
    source_zip = MANUAL_UPLOADS_DIR / zip_name

    if not source_zip.exists() or source_zip.suffix.lower() != ".zip":
        raise HTTPException(status_code=404, detail="ZIP local no encontrado.")

    session_id = uuid.uuid4().hex
    extract_dir = TEMP_DIR / session_id

    try:
        safe_extract_zip(source_zip, extract_dir)
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="ZIP inválido o corrupto.")

    inventory = scan_intake_folder(extract_dir)

    paths = session_paths(session_id)
    inventory_data = {
        "session_id": session_id,
        "client": client.strip() if client and client.strip() else "Sin cliente",
        "source_zip": zip_name,
        "inventory": inventory,
        "input_type": "LOCAL_ZIP",
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
