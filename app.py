import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import io

# Para mapa
import folium
from streamlit_folium import st_folium

# CONFIG
st.set_page_config(page_title="TouchBox", layout="wide")

# RUTAS
BASE_DIR = Path(__file__).resolve().parent
ZONAS_FILE = BASE_DIR / "zonas.json"
MARKERS_FILE = BASE_DIR / "marcadores.json"
CIRCLES_FILE = BASE_DIR / "circulos.json"

# =========================
# FUNCIONES JSON
# =========================
def read_json(path):
    if not path.exists():
        path.write_text("[]", encoding="utf-8")
    return json.loads(path.read_text(encoding="utf-8") or "[]")

def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

# =========================
# CARGAR DATA
# =========================
zonas = read_json(ZONAS_FILE)
markers = read_json(MARKERS_FILE)
circles = read_json(CIRCLES_FILE)

# =========================
# UI
# =========================
st.title("📡 TouchBox - Mapa Inteligente")

col1, col2 = st.columns([3,1])

# =========================
# MAPA
# =========================
with col1:
    mapa = folium.Map(location=[-12.0, -77.0], zoom_start=19)

    # 🔵 ZONAS (polígonos)
    for z in zonas:
        coords = z.get("coords", [])
        if coords:
            folium.Polygon(
                locations=coords,
                color="blue",
                fill=True,
                fill_opacity=0.2,
                tooltip=z.get("nombre", "Zona")
            ).add_to(mapa)

        # 🔹 TAGS dentro de zonas
        for t in z.get("tags", []):
            color = "green" if t.get("estado") == "ok" else "red"

            folium.Marker(
                location=[t.get("lat"), t.get("lng")],
                popup=f"{t.get('nombre')} ({t.get('estado')})",
                icon=folium.Icon(color=color)
            ).add_to(mapa)

    # 🔴 MARKERS independientes
    for m in markers:
        folium.Marker(
            location=[m.get("lat"), m.get("lng")],
            popup=m.get("nombre"),
            icon=folium.Icon(color="blue")
        ).add_to(mapa)

    # 🟢 CÍRCULOS
    for c in circles:
        folium.Circle(
            location=[c.get("lat"), c.get("lng")],
            radius=c.get("radio", 10),
            color="green",
            fill=True,
            fill_opacity=0.2
        ).add_to(mapa)

    st_folium(mapa, width=1000, height=600)

# =========================
# PANEL LATERAL
# =========================
with col2:
    st.subheader("📊 Estado")

    total = sum(len(z.get("tags", [])) for z in zonas)
    ok = sum(1 for z in zonas for t in z.get("tags", []) if t.get("estado") == "ok")
    error = total - ok

    st.metric("Total", total)
    st.metric("Operativos", ok)
    st.metric("Inoperativos", error)

    st.divider()

    # =========================
    # EXPORTAR EXCEL
    # =========================
    def flatten():
        filas = []
        for z in zonas:
            for t in z.get("tags", []):
                filas.append({
                    "Nombre": t.get("nombre"),
                    "Hostname": t.get("hostname"),
                    "IP": t.get("ip"),
                    "MAC": t.get("mac"),
                    "Estado": t.get("estado"),
                    "Zona": z.get("nombre"),
                })
        return pd.DataFrame(filas)

    df = flatten()

    st.download_button(
        "📥 Exportar Excel",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"reporte_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )

    st.download_button(
        "📄 Exportar JSON",
        data=json.dumps(zonas, indent=2).encode("utf-8"),
        file_name="zonas.json",
        mime="application/json"
    )
