import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import random
import os
from datetime import datetime

# --- 1. CONFIGURACIÓN EUNOIA ---
st.set_page_config(
    page_title="Eunoia Pricing Audit",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

def inyectar_estilos():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
            html, body, [class*=\"css\"] { font-family: 'Montserrat', sans-serif; background-color: #0e1117; }
            
            .logo-container {
                background-color: white; padding: 20px; border-radius: 12px;
                margin-bottom: 25px; text-align: center;
            }

            [data-testid="stMetricValue"] { color: #0080cd; font-size: 2.2rem; font-weight: 700; }
            
            .locked-box {
                background-color: #161b22; padding: 25px; border-radius: 12px;
                border: 1px solid #0080cd; text-align: center;
                box-shadow: 0 4px 15px rgba(0,128,205,0.3);
            }
            .cta-button {
                display: block; width: 100%; background-color: #00c853; 
                color: white !important; padding: 15px; text-align: center;
                border-radius: 8px; font-weight: bold; text-decoration: none;
                margin-top: 15px; transition: 0.3s;
            }
            .cta-button:hover { background-color: #00ff88; transform: scale(1.02); }
        </style>
    """, unsafe_allow_html=True)

inyectar_estilos()

# --- 2. BANNER DE MARCA ---
st.image("https://raw.githubusercontent.com/PaulMoraM/eunoia-branding/main/banner_redes.png", use_container_width=True)

# --- 3. BARRA LATERAL ---
with st.sidebar:
    st.markdown("""
        <div class="logo-container">
            <img src="https://raw.githubusercontent.com/PaulMoraM/eunoia-branding/main/eunoia-digital-logo.png" width="180">
        </div>
    """, unsafe_allow_html=True)
    
    st.header("📂 Datos del Cliente")
    nombre_cliente = st.text_input("Nombre de la Empresa", "Cliente Demo S.A.")
    archivo_subido = st.file_uploader("Cargar Plantilla Eunoia (.xlsx)", type=["xlsx"])
    
    st.divider()
    st.info("Este diagnóstico identifica oportunidades de margen mediante el análisis de elasticidad precio de la demanda.")

# --- 4. MOTOR DE DATOS ---
def ajustar_a_psicologico(p):
    entero = int(p)
    dec = p - entero
    if dec < 0.45: return entero + 0.49
    elif dec < 0.85: return entero + 0.90
    else: return entero + 0.99

@st.cache_data
def procesar_data(file):
    if file is not None:
        df = pd.read_excel(file)
        map_cols = {'Codigo': 'SKU', 'PVP': 'Precio Actual', 'Ventas Anuales': 'Ventas'}
        df = df.rename(columns=map_cols)
    else:
        np.random.seed(42)
        df = pd.DataFrame({
            "SKU": [f"PR-{random.randint(1000,9999)}" for _ in range(120)],
            "Precio Actual": np.random.uniform(20, 500, 120),
            "Ventas": np.random.randint(100, 5000, 120),
        })
    
    df['Elasticidad'] = np.random.uniform(0.5, 3.0, len(df))
    
    def clasificar(row):
        p, e, v = row['Precio Actual'], row['Elasticidad'], row['Ventas']
        if e < 1.15: 
            p_s = ajustar_a_psicologico(p * 1.15)
            return "SUBIR PRECIO", p_s, (p_s - p) * v * 0.85
        if e > 2.2: 
            return "BAJAR PRECIO", ajustar_a_psicologico(p * 0.92), 0
        return "MANTENER", p, 0

    res = df.apply(clasificar, axis=1)
    df['Acción'], df['Precio Sugerido'], df['Profit'] = [x[0] for x in res], [x[1] for x in res], [x[2] for x in res]
    df['Tamaño_Visual'] = np.sqrt(df['Profit'] + 150) 
    return df

df = procesar_data(archivo_subido)

# --- 5. DASHBOARD ---
st.title(f"💎 Auditoría de Precios: {nombre_cliente}")

c1, c2, c3 = st.columns(3)
c1.metric("Dinero sobre la mesa", f"${df['Profit'].sum():,.0f}")
c2.metric("Oportunidades de Alza", len(df[df['Acción'] == "SUBIR PRECIO"]))
c3.metric("Impacto EBITDA Est.", "+5.7%")

st.divider()

# --- 6. GRÁFICO (Visualización de oportunidad) ---
st.subheader("📍 Mapa Estratégico de Oportunidad")
color_map = {'SUBIR PRECIO': '#00ffcc', 'BAJAR PRECIO': '#ff4b4b', 'MANTENER': '#ffffff'}

fig = px.scatter(df, x="Precio Actual", y="Ventas", color="Acción", 
                 size="Tamaño_Visual", size_max=30,
                 color_discrete_map=color_map,
                 # Eliminamos 'Profit' del hover para no revelar datos exactos por punto
                 hover_data={"SKU": True, "Precio Actual": ":.2f", "Ventas": True, "Acción": True},
                 log_x=True, height=500)

fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#1c2128')
st.plotly_chart(fig, use_container_width=True)

# --- 7. TABLA Y CTA (BLOQUEO TOTAL) ---
col_t, col_c = st.columns([2.5, 1])

with col_t:
    st.subheader("🔓 Detalle del Análisis")
    st.warning("🔒 Los resultados detallados por SKU están bloqueados. Adquiera el reporte completo para desbloquear los precios sugeridos e impactos individuales.")

    df_v = df[df['Acción'] != "MANTENER"].sort_values("Profit", ascending=False).head(15).copy()
    
    # BLOQUEO HARDCODED: No hay forma de activarlo desde la interfaz
    df_v['Sugerido'] = "🔒 BLOQUEADO"
    df_v['Impacto'] = "⭐ REQUIERE PLAN"
    
    st.dataframe(
        df_v[['SKU', 'Precio Actual', 'Acción', 'Sugerido', 'Impacto']].rename(columns={'Acción': 'Acción Sugerida'}),
        use_container_width=True, hide_index=True
    )

with col_c:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class="locked-box">
            <h3 style="color: white; margin:0;">Recupera tus <br><span style="color:#0080cd;">${df['Profit'].sum():,.0f}</span></h3>
            <p style="font-size: 0.85rem; color: #ccc; margin-top: 15px;">
                Identificamos los productos donde tu cliente está dispuesto a pagar más. Obtén el listado completo y optimiza tu margen hoy.
            </p>
            <a href="https://wa.me/593983959867" class="cta-button">ADQUIRIR REPORTE FULL</a>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.caption(f"© {datetime.now().year} Eunoia Digital Ecuador")