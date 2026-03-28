import streamlit as st
import json
from pathlib import Path
import folium
from folium.features import DivIcon
from streamlit_folium import st_folium

# CONFIG
st.set_page_config(layout="wide")

BASE_DIR = Path(__file__).resolve().parent
ZONAS_FILE = BASE_DIR / "zonas.json"

def read_json(path):
    if not path.exists():
        path.write_text("[]", encoding="utf-8")
    return json.loads(path.read_text(encoding="utf-8") or "[]")

zonas = read_json(ZONAS_FILE)

# =========================
# 🎯 ICONO TIPO EQUIPO (IGUAL VISUAL)
# =========================
def icono_equipo():
    return """
    <div style="text-align:center;">
        <div style="
            font-size:20px;
            filter: drop-shadow(0px 2px 3px rgba(0,0,0,0.5));
        ">📡</div>
    </div>
    """

# =========================
# 🏷️ ETIQUETA NEGRA (CLON)
# =========================
def etiqueta(nombre):
    return f"""
    <div style="
        background:#1f2937;
        color:white;
        padding:4px 8px;
        border-radius:10px;
        font-size:11px;
        font-weight:600;
        white-space:nowrap;
        box-shadow:0 2px 6px rgba(0,0,0,0.4);
        margin-top:-5px;
    ">
        {nombre}
    </div>
    """

# =========================
# UI
# =========================
st.title("TouchBox - Vista Operativa")

col1, col2 = st.columns([4,1])

# =========================
# MAPA
# =========================
with col1:

    mapa = folium.Map(
        location=[-12.0, -77.0],
        zoom_start=19,
        tiles="CartoDB positron"  # similar a tu fondo
    )

    total = 0
    ok = 0

    for z in zonas:
        coords = z.get("coords", [])

        # 🔷 ZONA (colores como tu sistema)
        folium.Polygon(
            locations=coords,
            color="#4f46e5",
            fill=True,
            fill_color="#60a5fa",
            fill_opacity=0.25
        ).add_to(mapa)

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

            # 🔴 o 🔵 color
            color = "red" if estado != "ok" else "blue"

            # 🔥 ICONO (tipo torre)
            folium.Marker(
                location=[lat, lng],
                icon=DivIcon(html=icono_equipo())
            ).add_to(mapa)

            # 🔥 ETIQUETA NEGRA
            folium.Marker(
                location=[lat, lng],
                icon=DivIcon(html=etiqueta(nombre))
            ).add_to(mapa)

    st_folium(mapa, width=1200, height=650)

# =========================
# PANEL DERECHO (CLON)
# =========================
with col2:

    st.markdown("### TouchBox ACEDIM")

    error = total - ok

    st.metric("Total", total)
    st.metric("Operativos", ok)
    st.metric("Inoperativos", error)

    st.markdown("#### Red")
    st.metric("Wi-Fi", 1)
    st.metric("LAN", total-1)

    st.divider()

    st.button("Editar")
    st.button("Guardar")

    st.button("Exportar Excel")
    st.button("Exportar PDF")
