from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from gate0_demo_security import install_demo_security
from pathlib import Path
import shutil
import subprocess
import sys
import json
import time
import uuid
import zipfile
import fitz
import html
import csv
from datetime import datetime
from gate0.services.history_service import HistoryService
from gate0.services.runtime_service import RuntimeService
from gate0.services.zip_inventory_service import ZIPInventoryService
from gate0.services.separation_intelligence_service import SeparationIntelligenceService
from gate0.services.comparison_service import ComparisonService
from gate0_orchestrator import Gate0Orchestrator
from gate0.agents.inspection_agent import InspectionAgent

app = FastAPI(title="Gate0 Packaging QA")
install_demo_security(app)

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
runtime_service = RuntimeService(UPLOADS_DIR, REPORTS_DIR, TEMP_DIR, TTL_SECONDS)
zip_inventory_service = ZIPInventoryService()
separation_intelligence_service = SeparationIntelligenceService()
comparison_service = ComparisonService()
inspection_agent = InspectionAgent()
orchestrator = Gate0Orchestrator(ROOT)

app.mount("/dashboard", StaticFiles(directory=str(DASHBOARD_DIR), html=True), name="dashboard")

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "gate0"}



def cleanup_old_runtime_files():
    runtime_service.cleanup_old_files()

def append_analysis_history(data):
    history_service.save_analysis(data)

def update_feedback_history(session_id, feedback_score, feedback_comment):
    return history_service.update_feedback(session_id, feedback_score, feedback_comment)

def session_paths(session_id):
    return runtime_service.session_paths(session_id)



ANALYZABLE_EXTENSIONS = {".pdf", ".ai"}
IMAGE_EXTENSIONS = {".psd", ".tif", ".tiff", ".jpg", ".jpeg", ".png"}
FONT_EXTENSIONS = {".otf", ".ttf"}


def safe_extract_zip(zip_path, extract_dir):
    return zip_inventory_service.safe_extract_zip(zip_path, extract_dir)

def scan_intake_folder(folder):
    return zip_inventory_service.scan_folder(folder)

def possible_duplicate_note(analyzable):
    return zip_inventory_service.possible_duplicate_note(analyzable)

def render_zip_selection(session_id, client, inventory):
    analyzable = inventory.get("analyzable", [])
    duplicate_note = possible_duplicate_note(analyzable)
    candidate_pairs = comparison_service.find_candidate_pairs(analyzable)

    pair_html = ""
    for pair in candidate_pairs:
        files = "".join(
            f"<li>{html.escape(f.get('name', ''))} <span>{html.escape(f.get('extension', '').upper().replace('.', ''))}</span></li>"
            for f in pair.get("files", [])
        )
        ai_file = next((f for f in pair.get("files", []) if f.get("extension") == ".ai"), None)
        pdf_file = next((f for f in pair.get("files", []) if f.get("extension") == ".pdf"), None)

        compare_button = ""
        if ai_file and pdf_file:
            compare_button = f"""
            <form action="/compare-candidate" method="post">
              <input type="hidden" name="sid" value="{html.escape(session_id)}"/>
              <input type="hidden" name="client" value="{html.escape(client)}"/>
              <input type="hidden" name="ai_file" value="{html.escape(ai_file.get('relative_path', ''))}"/>
              <input type="hidden" name="pdf_file" value="{html.escape(pdf_file.get('relative_path', ''))}"/>
              <button type="submit" class="secondary-button">Comparar AI vs PDF antes de analizar</button>
            </form>
            """

        pair_html += f"""
        <div class="pair-box">
          <b>Posible pareja AI/PDF detectada</b>
          <p>{html.escape(pair.get("reason", ""))}</p>
          <ul>{files}</ul>
          {compare_button}
        </div>
        """

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
.pair-box{{background:#eff6ff;border:1px solid #bfdbfe;border-radius:16px;padding:12px;margin:14px 0;color:#1e3a8a}}
.pair-box p{{margin:6px 0;color:#1e40af;font-size:13px}}
.pair-box ul{{margin:6px 0 0;padding-left:18px;font-size:13px}}
.pair-box li span{{color:#64748b;font-size:11px;font-weight:850}}
button{{width:100%;border:0;border-radius:999px;background:#111827;color:#fff;padding:15px 18px;font-weight:950;font-size:16px;cursor:pointer;margin-top:16px}}
.empty{{padding:18px;background:#f8fafc;border-radius:16px;color:#667085}}
.support-box{{margin-top:20px;background:#f8fafc;border:1px solid #edf2f7;border-radius:18px;padding:16px}}
.support-box h3{{margin:0 0 8px;font-size:16px}}
.support-grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.support-box ul{{margin:8px 0 0;padding-left:18px;color:#334155;font-size:13px;line-height:1.45;max-height:220px;overflow:auto}}
.support-box li span{{color:#667085;font-size:12px}}
@media(max-width:800px){{.summary,.support-grid{{grid-template-columns:1fr}}}}


/* Sprint 27A.1 — Compare file cards responsive fix */
.compare-files,
.file-pair,
.inspected-files{{
  display:grid;
  grid-template-columns:minmax(0,1fr) minmax(0,1fr);
  gap:12px;
  width:100%;
  overflow:hidden;
}}

.compare-file,
.file-card,
.inspected-file,
.ai-card,
.pdf-card{{
  min-width:0;
  overflow:hidden;
  border:1px solid #e5e7eb;
  border-radius:18px;
  padding:14px 16px;
  background:#fff;
}}

.compare-file b,
.file-card b,
.inspected-file b,
.ai-card b,
.pdf-card b{{
  display:block;
  font-size:14px;
  line-height:1.25;
  word-break:break-word;
  overflow-wrap:anywhere;
}}

.compare-file h2,
.file-card h2,
.inspected-file h2,
.ai-card h2,
.pdf-card h2{{
  font-size:16px;
  line-height:1.25;
  word-break:break-word;
  overflow-wrap:anywhere;
}}

.compare-file-name,
.file-name,
.inspected-file-name{{
  font-size:16px !important;
  line-height:1.25 !important;
  font-weight:900;
  word-break:break-word;
  overflow-wrap:anywhere;
}}

table{{
  width:100%;
  table-layout:fixed;
}}

td,th{{
  word-break:break-word;
  overflow-wrap:anywhere;
  vertical-align:top;
}}

@media(max-width:900px){{
  .compare-files,
  .file-pair,
  .inspected-files{{
    grid-template-columns:1fr;
  }}
}}


</style>
</head>
<body>
<main class="card">
  <h1>ZIP Intake — selecciona archivo principal</h1>
  <p>Gate0 encontró archivos dentro del ZIP. Elige el PDF final o AI principal que quieres analizar. En esta versión se procesa un archivo a la vez.</p>

  <div class="summary">
    <div><b>{len(inventory.get("analyzable", []))}</b><span>Archivos principales</span></div>
    <div><b>{len(inventory.get("images", []))}</b><span>Imágenes soporte</span></div>
    <div><b>{len(inventory.get("fonts", []))}</b><span>Fuentes soporte</span></div>
  </div>

  {f'<div class="note">{html.escape(duplicate_note)}</div>' if duplicate_note else ''}
  {pair_html}

  <form action="/analyze-selected" method="post">
    <input type="hidden" name="sid" value="{html.escape(session_id)}"/>
    <input type="hidden" name="client" value="{html.escape(client)}"/>
    {options}
    <button type="submit" {"disabled" if not analyzable else ""}>Analizar archivo seleccionado</button>
  </form>

  <div class="support-box">
    <h3>Archivos soporte encontrados</h3>
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
  <div style="display:inline-flex;border-radius:999px;background:#eef2ff;color:#3730a3;font-size:12px;font-weight:950;padding:7px 11px;margin-bottom:14px">Demo privada · Gate0 staging</div>
  <h1>Gate0 Packaging QA</h1>
  <p>Sube un PDF o ZIP de arte. Si subes un PDF, Gate0 analiza directo; si subes un ZIP, detecta los archivos principales y te deja elegir cuál analizar.</p>

  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:18px 0 4px">
    <div style="background:#f8fafc;border:1px solid #edf2f7;border-radius:16px;padding:13px"><b>PDF</b><span style="display:block;color:#667085;font-size:12px;line-height:1.35;margin-top:5px">Análisis directo del archivo cargado.</span></div>
    <div style="background:#f8fafc;border:1px solid #edf2f7;border-radius:16px;padding:13px"><b>ZIP</b><span style="display:block;color:#667085;font-size:12px;line-height:1.35;margin-top:5px">Gate0 abre un selector con PDF/AI detectados.</span></div>
    <div style="background:#f8fafc;border:1px solid #edf2f7;border-radius:16px;padding:13px"><b>Demo web</b><span style="display:block;color:#667085;font-size:12px;line-height:1.35;margin-top:5px">El análisis puede tardar más en Render Free.</span></div>
  </div>

  <form class="drop" action="/analyze" method="post" enctype="multipart/form-data">
    <label>Cliente / Proyecto opcional</label>
    <input type="text" name="client" placeholder="Ejemplo: Control Test"/>
    <label>Archivo PDF o ZIP</label>
    <input type="file" name="file" accept="application/pdf,.pdf,.zip,application/zip"/>
    <button type="submit">Analizar PDF o abrir ZIP</button>
    <div class="note">Para ZIPs grandes, el tiempo de carga/análisis puede ser mayor en Render Free. Después de hacer clic, espera a que Gate0 procese el archivo.</div>
  </form>

  <div class="divider"></div>

  <form action="/analyze-local-zip" method="post">
    <label>Cliente / Proyecto opcional</label>
    <input type="text" name="client" placeholder="Ejemplo: Cliente ZIP"/>
    <h2>Opción avanzada: ZIP local grande</h2>
    <p>Uso técnico para Codespaces o servidor propio: coloca ZIPs grandes en <b>data/runtime/manual_uploads/</b> y aparecerán aquí. En Render Free normalmente usa la carga directa superior.</p>
    {zip_cards}
    <button type="submit">Abrir ZIP local seleccionado</button>
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

    analysis_start = time.time()

    # Sprint 27B — Runtime Isolation v1
    # The legacy subprocess writes into a session-specific directory.
    session_output_dir = REPORTS_DIR / session_id

    try:
        data = orchestrator.run(paths["pdf"], output_dir=session_output_dir)
    except Exception as exc:
        return HTMLResponse(
            f"<h1>Error ejecutando Gate0</h1><pre>{exc}</pre>",
            status_code=500
        )

    analysis_duration_seconds = round(time.time() - analysis_start, 2)

    session_csv = session_output_dir / "gate0_report.csv"

    data["file"] = original_filename or input_file_path.name
    data["client"] = client.strip() if client and client.strip() else "Sin cliente"
    data["process"] = data.get("business_assessment", {}).get("process", "flexo")
    data["session_id"] = session_id
    data["runtime_ttl_minutes"] = 30
    data["analysis_duration_seconds"] = analysis_duration_seconds
    data["input_type"] = input_type
    data["files_detected"] = files_detected
    separation_context = {}

    for item in (
        data.get("findings", [])
        + data.get("readiness_summary", {}).get("top_risks", [])
    ):
        if item.get("check") == "SEPARATION_COUNT_RISK":
            separation_context = item
            break

    data["separation_summary"] = separation_intelligence_service.build_summary(
        data.get("separations", []),
        printable_separation_count=(
            separation_context.get("printable_separation_count")
            if separation_context.get("printable_separation_count") is not None
            else (
                data.get("printable_separation_count")
                if data.get("printable_separation_count") is not None
                else data.get("number_of_separations")
            )
        ),
        process_count=(
            separation_context.get("process_count")
            if separation_context.get("process_count") is not None
            else data.get("process_count")
        ),
        process_count_source=(
            separation_context.get("process_count_source")
            or data.get("process_count_source")
        ),
    )

    with paths["json"].open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    append_analysis_history(data)

    if session_csv.exists():
        shutil.copy(session_csv, paths["csv"])

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





# Sprint 27A.1 — Compare page file display helpers
def _compare_display_filename(value):
    try:
        return Path(str(value or "")).name or "—"
    except Exception:
        return str(value or "—")


@app.post("/compare-candidate")
async def compare_candidate(
    sid: str = Form(...),
    ai_file: str = Form(...),
    pdf_file: str = Form(...),
    client: str = Form(default="")
):
    cleanup_old_runtime_files()

    extract_dir = TEMP_DIR / sid
    ai_path = extract_dir / ai_file
    pdf_path = extract_dir / pdf_file

    if not ai_path.exists() or not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Archivos para comparación no encontrados o expirados.")

    left = inspection_agent.inspect(ai_path)
    right = inspection_agent.inspect(pdf_path)

    result = comparison_service.compare_inspection_results(left, right)

    status_class = {
        "OK": "ok",
        "REVIEW_REQUIRED": "review",
        "HIGH_RISK": "risk",
    }.get(result.overall_status, "review")

    rows = ""
    for check in result.checks:
        row_class = {
            "OK": "ok",
            "WARNING": "review",
            "CRITICAL": "risk",
        }.get(str(check.get("status", "")), "review")

        rows += f"""
        <tr>
          <td><b>{html.escape(str(check.get("category", "")))}</b></td>
          <td>{html.escape(str(check.get("name", "")))}</td>
          <td><span class="pill {row_class}">{html.escape(str(check.get("status", "")))}</span></td>
          <td>{html.escape(str(check.get("left", "")))}</td>
          <td>{html.escape(str(check.get("right", "")))}</td>
          <td>{html.escape(str(check.get("message", "")))}</td>
        </tr>
        """

    warnings = "".join(f"<li>{html.escape(w)}</li>" for w in result.warnings) or "<li>Sin advertencias estructurales relevantes.</li>"

    return HTMLResponse(f"""
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Artwork Consistency</title>
<style>
body{{margin:0;min-height:100vh;font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;background:#f6f7fb;color:#0f172a;display:grid;place-items:center}}
.card{{width:min(1120px,94vw);background:white;border:1px solid #e5e7eb;border-radius:28px;padding:32px;box-shadow:0 24px 70px rgba(15,23,42,.10)}}
h1{{font-size:34px;margin:0 0 8px;letter-spacing:-.05em}}
.subtitle{{color:#667085;margin:0 0 18px}}
.score{{font-size:54px;font-weight:950;margin:8px 0 0}}
.badge{{display:inline-block;border-radius:999px;padding:8px 12px;font-weight:950}}
.badge.ok{{background:#ecfdf3;color:#027a48}}
.badge.review{{background:#fffbeb;color:#92400e}}
.badge.risk{{background:#fef3f2;color:#b42318}}
.decision{{margin-top:18px;padding:18px;border-radius:18px;background:#f8fafc;border:1px solid #e5e7eb}}
.decision b{{display:block;font-size:20px;margin-bottom:6px}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:18px}}
.metric{{border:1px solid #e5e7eb;border-radius:18px;padding:16px;background:#fff}}
.metric small{{display:block;color:#667085;font-weight:800;text-transform:uppercase;letter-spacing:.08em}}
.metric span{{display:block;font-size:24px;font-weight:950;margin-top:4px}}
table{{width:100%;border-collapse:collapse;margin-top:22px}}
td,th{{border-bottom:1px solid #e5e7eb;padding:12px;text-align:left;font-size:14px;vertical-align:top}}
th{{color:#667085;text-transform:uppercase;font-size:12px;letter-spacing:.08em}}
.pill{{display:inline-block;border-radius:999px;padding:5px 9px;font-weight:950;font-size:12px}}
.pill.ok{{background:#ecfdf3;color:#027a48}}
.pill.review{{background:#fffbeb;color:#92400e}}
.pill.risk{{background:#fef3f2;color:#b42318}}
.warning{{background:#fffbeb;border:1px solid #fde68a;border-radius:16px;padding:14px;margin-top:18px;color:#92400e}}
a{{display:inline-block;margin-top:20px;color:#1d4ed8;font-weight:900;text-decoration:none}}
</style>
</head>
<body>
<main class="card">
  <h1>Artwork Consistency</h1>
  <p class="subtitle">Comparación estructural entre AI y PDF. No incluye comparación visual píxel a píxel todavía.</p>

  <span class="badge {status_class}">{html.escape(result.overall_status)}</span>
  <div class="score">{result.score}/100</div>

  <section class="decision">
    <b>{html.escape(result.decision)}</b>
    <p>{html.escape(result.summary)}</p>
    <p><b>Recomendación:</b> {html.escape(result.recommendation)}</p>
  </section>

  <section class="grid">
    <div class="metric">
      <small>AI inspeccionado</small>
      <span>{html.escape(_compare_display_filename(result.left_file))}</span>
    </div>
    <div class="metric">
      <small>PDF inspeccionado</small>
      <span>{html.escape(_compare_display_filename(result.right_file))}</span>
    </div>
  </section>

  <table>
    <thead>
      <tr>
        <th>Categoría</th>
        <th>Check</th>
        <th>Estado</th>
        <th>AI</th>
        <th>PDF</th>
        <th>Lectura preprensa</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>

  <div class="warning">
    <b>Observaciones</b>
    <ul>{warnings}</ul>
  </div>

  <a href="/">← Volver al intake</a>
</main>
</body>
</html>
""")


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





@app.get("/api/risk-preview")
def get_risk_preview(sid: str, page: int = 1, bbox: str = ""):
    """
    Genera una vista previa PNG recortada alrededor del bbox.
    v1.1: no muestra toda la página; hace zoom contextual sobre la zona del riesgo.
    """
    cleanup_old_runtime_files()

    if not bbox:
        raise HTTPException(status_code=400, detail="Falta bbox")

    try:
        coords = [float(x.strip()) for x in bbox.split(",")]
    except Exception:
        raise HTTPException(status_code=400, detail="bbox inválido")

    if len(coords) != 4:
        raise HTTPException(status_code=400, detail="bbox debe tener 4 valores")

    paths = session_paths(sid)
    pdf_path = paths["pdf"]

    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF expirado o inexistente")

    try:
        doc = fitz.open(str(pdf_path))
    except Exception:
        raise HTTPException(status_code=500, detail="No se pudo abrir PDF")

    try:
        if len(doc) == 0:
            raise HTTPException(status_code=404, detail="PDF sin páginas")

        page_index = max(0, min(int(page or 1) - 1, len(doc) - 1))
        pdf_page = doc[page_index]

        x0, y0, x1, y1 = coords
        risk_rect = fitz.Rect(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
        page_rect = pdf_page.rect

        # Asegurar que el bbox sea válido y esté dentro de página.
        risk_rect = risk_rect & page_rect
        if risk_rect.is_empty or risk_rect.width <= 0 or risk_rect.height <= 0:
            raise HTTPException(status_code=400, detail="bbox fuera de página")

        # Crop contextual: si el bbox es pequeño, expandir bastante alrededor.
        min_w = max(90, page_rect.width * 0.16)
        min_h = max(70, page_rect.height * 0.12)

        crop_w = max(risk_rect.width * 7, min_w)
        crop_h = max(risk_rect.height * 10, min_h)

        cx = (risk_rect.x0 + risk_rect.x1) / 2
        cy = (risk_rect.y0 + risk_rect.y1) / 2

        crop = fitz.Rect(
            cx - crop_w / 2,
            cy - crop_h / 2,
            cx + crop_w / 2,
            cy + crop_h / 2,
        )

        # Ajustar crop a límites de página.
        if crop.x0 < page_rect.x0:
            crop.x1 += page_rect.x0 - crop.x0
            crop.x0 = page_rect.x0
        if crop.y0 < page_rect.y0:
            crop.y1 += page_rect.y0 - crop.y0
            crop.y0 = page_rect.y0
        if crop.x1 > page_rect.x1:
            crop.x0 -= crop.x1 - page_rect.x1
            crop.x1 = page_rect.x1
        if crop.y1 > page_rect.y1:
            crop.y0 -= crop.y1 - page_rect.y1
            crop.y1 = page_rect.y1

        crop = crop & page_rect

        # Dibujar recuadro sobre el PDF antes de renderizar el crop.
        pad = 2
        draw_rect = fitz.Rect(
            max(page_rect.x0, risk_rect.x0 - pad),
            max(page_rect.y0, risk_rect.y0 - pad),
            min(page_rect.x1, risk_rect.x1 + pad),
            min(page_rect.y1, risk_rect.y1 + pad),
        )

        pdf_page.draw_rect(draw_rect, color=(1, 0, 0), width=2.5, overlay=True)

        pix = pdf_page.get_pixmap(
            matrix=fitz.Matrix(3.0, 3.0),
            clip=crop,
            alpha=False
        )
        content = pix.tobytes("png")

        return Response(
            content=content,
            media_type="image/png",
            headers={"Cache-Control": "no-store"},
        )
    finally:
        try:
            doc.close()
        except Exception:
            pass

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
