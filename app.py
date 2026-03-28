import streamlit as st
import json
from pathlib import Path
import folium
from folium.features import DivIcon
from streamlit_folium import st_folium

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="TouchBox PRO", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
ZONAS_FILE = BASE_DIR / "zonas.json"

def read_json(path):
    if not path.exists():
        path.write_text("[]", encoding="utf-8")
    return json.loads(path.read_text(encoding="utf-8") or "[]")

zonas = read_json(ZONAS_FILE)

# =========================
# ESTILO (🔥 etiquetas tipo tu sistema)
# =========================
def etiqueta_html(nombre, estado):
    color = "#22c55e" if estado == "ok" else "#ef4444"

    return f"""
    <div style="
        background: #111827;
        color: white;
        padding: 4px 8px;
        border-radius: 8px;
        font-size: 11px;
        font-weight: bold;
        box-shadow: 0 2px 6px rgba(0,0,0,0.4);
        border-left: 4px solid {color};
        white-space: nowrap;
    ">
        {nombre}
    </div>
    """

# =========================
# UI
# =========================
st.title("📡 TouchBox - Vista Operativa")

col1, col2 = st.columns([4,1])

# =========================
# MAPA
# =========================
with col1:
    mapa = folium.Map(
        location=[-12.0, -77.0],
        zoom_start=19,
        tiles="CartoDB dark_matter"  # 🔥 estilo oscuro PRO
    )

    total = 0
    ok = 0

    for z in zonas:
        coords = z.get("coords", [])

        # 🔷 ZONA
        if coords:
            folium.Polygon(
                locations=coords,
                color="#3b82f6",
                fill=True,
                fill_opacity=0.15
            ).add_to(mapa)

        # 🔹 TAGS
        for t in z.get("tags", []):
            lat = t.get("lat")
            lng = t.get("lng")
            nombre = t.get("nombre")
            estado = t.get("estado", "ok")

            if not lat or not lng:
                continue

            total += 1
            if estado == "ok":
                ok += 1

            # 🔥 ICONO BASE (tipo equipo)
            folium.CircleMarker(
                location=[lat, lng],
                radius=6,
                color="#22c55e" if estado == "ok" else "#ef4444",
                fill=True
            ).add_to(mapa)

            # 🔥 ETIQUETA FLOTANTE (CLAVE)
            folium.Marker(
                location=[lat, lng],
                icon=DivIcon(
                    html=etiqueta_html(nombre, estado)
                )
            ).add_to(mapa)

    st_folium(mapa, width=1200, height=650)

# =========================
# PANEL DERECHO (igual al tuyo)
# =========================
with col2:
    st.subheader("📊 Estado")

    error = total - ok

    st.metric("Total", total)
    st.metric("Operativos", ok)
    st.metric("Inoperativos", error)

    st.divider()

    st.button("💾 Guardar")
    st.button("📥 Exportar Excel")
    st.button("📄 Exportar PDF")
