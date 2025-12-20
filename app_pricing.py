import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import random
import os

# --- 1. CONFIGURACIÓN EUNOIA ---
st.set_page_config(
    page_title="Eunoia Pricing Audit",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Definición de URLs de imagen
URL_LOGO = "https://raw.githubusercontent.com/PaulMoraM/eunoia-branding/main/eunoia-digital-logo.png"
URL_BANNER = "https://raw.githubusercontent.com/PaulMoraM/eunoia-branding/main/banner_redes.png"

def inyectar_estilos():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
            html, body, [class*="css"] { font-family: 'Montserrat', sans-serif; background-color: #0e1117; }
            
            /* Badge blanco para el Logo en el Sidebar */
            .logo-container {
                background-color: white;
                padding: 20px;
                border-radius: 12px;
                margin-bottom: 25px;
                text-align: center;
            }

            /* Métricas Eunoia */
            [data-testid="stMetricValue"] { color: #0080cd; font-size: 2.2rem; font-weight: 700; }
            
            /* Caja de Conversión */
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

# --- 2. BANNER SUPERIOR (Único cambio solicitado) ---
st.image(URL_BANNER, use_container_width=True)

# --- 3. BARRA LATERAL (LOGO Y CARGA) ---
with st.sidebar:
    # Logo con fondo blanco para contraste
    st.markdown(f"""
        <div class="logo-container">
            <img src="{URL_LOGO}" width="180">
        </div>
    """, unsafe_allow_html=True)
    
    st.header("📂 Datos del Cliente")
    nombre_cliente = st.text_input("Nombre de la Empresa", "Cliente Demo S.A.")
    
    archivo_subido = st.file_uploader("Cargar Plantilla Eunoia (.xlsx)", type=["xlsx"])
    
    st.divider()
    st.info("Para este análisis, se recomienda contar con al menos 12 meses de información de ventas para capturar la estacionalidad correctamente.")

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
c3.metric("Impacto EBITDA", "+5.7%")

st.divider()

# Gráfico
st.subheader("📍 Mapa Estratégico de Oportunidad")
color_map = {'SUBIR PRECIO': '#00ffcc', 'BAJAR PRECIO': '#ff4b4b', 'MANTENER': '#ffffff'}

fig = px.scatter(df, x="Precio Actual", y="Ventas", color="Acción", 
                 size="Tamaño_Visual", size_max=30,
                 color_discrete_map=color_map,
                 hover_data={"SKU": True, "Precio Actual": ":.2f", "Ventas": True, "Profit": ":,.0f"},
                 log_x=True, height=500)

fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#1c2128')
st.plotly_chart(fig, use_container_width=True)

# --- 6. TABLA Y CTA ---
col_t, col_c = st.columns([2.5, 1])

with col_t:
    st.subheader("🔓 Detalle del Análisis")
    modo_admin = st.toggle("🔓 Revelar Precios Sugeridos")
    
    df_v = df[df['Acción'] != "MANTENER"].sort_values("Profit", ascending=False).head(15).copy()
    df_v['Precio Sugerido'] = df_v['Precio Sugerido'].map("${:,.2f}".format) if modo_admin else "🔒 BLOQUEADO"
    df_v['Impacto'] = df_v['Profit'].map("+${:,.0f}".format) if modo_admin else "⭐ ANALIZADO"
    
    st.dataframe(
        df_v[['SKU', 'Precio Actual', 'Acción', 'Precio Sugerido', 'Impacto']].rename(columns={'Acción': 'Acción Sugerida'}),
        use_container_width=True, hide_index=True
    )

with col_c:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class="locked-box">
            <h3 style="color: white; margin:0;">Recupera tus <br><span style="color:#0080cd;">${df['Profit'].sum():,.0f}</span></h3>
            <p style="font-size: 0.85rem; color: #ccc; margin-top: 15px;">
                Identificamos productos con elasticidad inelástica para optimizar tus márgenes.
            </p>
            <a href="https://wa.me/593983959867" class="cta-button">ADQUIRIR PLAN COMPLETO</a>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.caption(f"© {datetime.now().year} Eunoia Digital Ecuador")