# gmaps_flask/app.py
from flask import Flask, render_template, jsonify, request, send_file
from pathlib import Path
from datetime import datetime
import json, os, io

# === Dependencias para exportación ===
# pip install openpyxl reportlab
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static",
)

BASE_DIR      = Path(__file__).resolve().parent
ZONAS_FILE    = BASE_DIR / "zonas.json"
MARKERS_FILE  = BASE_DIR / "marcadores.json"
CIRCLES_FILE  = BASE_DIR / "circulos.json"

def read_json(path: Path):
    try:
        if not path.exists():
            path.write_text("[]", encoding="utf-8")
        data = json.loads(path.read_text(encoding="utf-8") or "[]")
        if not isinstance(data, list):
            data = []
        return data
    except Exception as e:
        app.logger.exception("Error leyendo %s: %s", path.name, e)
        return []

def write_json_atomic(path: Path, data):
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)

@app.get("/")
def index():
    return render_template("map.html")

# ========== APIs existentes ==========
@app.get("/api/zonas")
def api_zonas_get():
    return jsonify(read_json(ZONAS_FILE))

@app.post("/api/zonas/save")
def api_zonas_save():
    data = request.get_json(silent=True, force=True)
    if not isinstance(data, list):
        return jsonify({"ok": False, "error": "Payload debe ser una lista"}), 400
    write_json_atomic(ZONAS_FILE, data)
    return jsonify({"ok": True})

@app.get("/api/markers")
def api_markers_get():
    return jsonify(read_json(MARKERS_FILE))

@app.post("/api/markers/save")
def api_markers_save():
    data = request.get_json(silent=True, force=True)
    if not isinstance(data, list):
        return jsonify({"ok": False, "error": "Payload debe ser una lista"}), 400
    write_json_atomic(MARKERS_FILE, data)
    return jsonify({"ok": True})

@app.get("/api/circles")
def api_circles_get():
    return jsonify(read_json(CIRCLES_FILE))

@app.post("/api/circles/save")
def api_circles_save():
    data = request.get_json(silent=True, force=True)
    if not isinstance(data, list):
        return jsonify({"ok": False, "error": "Payload debe ser una lista"}), 400
    write_json_atomic(CIRCLES_FILE, data)
    return jsonify({"ok": True})

# ========== Helpers de reporte ==========
def flatten_zonas_for_report():
    """Aplana zonas→tags en filas para exportación."""
    filas = []
    for z in read_json(ZONAS_FILE):
        zona = z.get("nombre") or ""
        for t in (z.get("tags") or []):
            filas.append({
                "Nombre":    t.get("nombre") or t.get("hostname") or "",
                "Hostname":  t.get("hostname") or "",
                "IP":        t.get("ip") or "",
                "MAC":       t.get("mac") or "",
                "Estado":    t.get("estado") or "",
                "Tipo":      t.get("tipo") or "",
                "Zona":      zona,
                "Lat":       t.get("lat") or "",
                "Lng":       t.get("lng") or "",
            })
    return filas

# ========== Exportar a Excel ==========
@app.get("/export/excel")
def export_excel():
    filas = flatten_zonas_for_report()
    headers = ["Nombre", "Hostname", "IP", "MAC", "Estado", "Tipo", "Zona", "Lat", "Lng"]  # <-- coma corregida y orden claro

    wb = Workbook()
    ws = wb.active
    ws.title = "Inventario"
    ws.append(headers)
    for f in filas:
        ws.append([f[h] for h in headers])

    # ancho de columnas
    for idx, h in enumerate(headers, start=1):
        ws.column_dimensions["ABCDEFGHIJKLMNOPQRSTUVWXYZ"[idx-1]].width = max(12, len(h) + 6)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    fname = f"reporte_tags_{datetime.now().strftime('%Y-%m-%d_%H%M')}.xlsx"
    return send_file(
        buf,
        as_attachment=True,
        download_name=fname,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ========== Exportar a PDF ==========
@app.get("/export/pdf")
def export_pdf():
    filas = flatten_zonas_for_report()

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4

    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, H-2*cm, "Inventario de TAGs (zonas)")
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, H-2.6*cm, datetime.now().strftime("%Y-%m-%d %H:%M"))

    # Encabezados (columnas separadas)
    y = H-3.4*cm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2.0*cm,  y, "Nombre")
    c.drawString(8.0*cm,  y, "Hostname")
    c.drawString(12.0*cm, y, "IP")
    c.drawString(15.2*cm, y, "Estado")
    c.drawString(17.5*cm, y, "Zona")
    y -= 0.45*cm
    c.line(2*cm, y, 19*cm, y)
    y -= 0.45*cm #Espacio de Linea

    # Filas
    c.setFont("Helvetica", 10)
    for f in filas:
        if y < 2*cm:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = H-2*cm
            # reimprimir encabezados en página nueva
            c.setFont("Helvetica-Bold", 10)
            c.drawString(2.0*cm,  y, "Nombre")
            c.drawString(8.0*cm,  y, "Hostname")
            c.drawString(12.0*cm, y, "IP")
            c.drawString(15.2*cm, y, "Estado")
            c.drawString(17.5*cm, y, "Zona")
            y -= 0.45*cm
            c.line(2*cm, y, 19*cm, y)
            y -= 0.25*cm
            c.setFont("Helvetica", 10)

        c.drawString(2.0*cm,   y, str(f["Nombre"])[:32])
        c.drawString(8.0*cm,   y, str(f["Hostname"])[:18])
        c.drawString(12.0*cm,  y, str(f["IP"])[:16])
        c.drawString(15.2*cm,  y, str(f["Estado"])[:12])
        c.drawString(17.5*cm,  y, str(f["Zona"])[:16])
        y -= 0.5*cm

    c.save()
    buf.seek(0)
    fname = f"reporte_tags_{datetime.now().strftime('%Y-%m-%d_%H%M')}.pdf"
    return send_file(buf, as_attachment=True, download_name=fname, mimetype="application/pdf")

if __name__ == "__main__":
    app.run(debug=True)
