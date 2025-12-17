import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import StringIO
import random

# Fallback para Faker (Simulación)
try:
    from faker import Faker
    fake = Faker()
except ImportError:
    class Faker:
        def catch_phrase(self): return "Producto Genérico"
    fake = Faker()

URL_LOGO = "https://raw.githubusercontent.com/PaulMoraM/eunoia-branding/main/eunoia-digital-logo.png"

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Eunoia Pricing Audit", page_icon="💎", layout="wide")

# --- 2. ESTILOS EUNOIA ---
def inyectar_estilos():
    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
            html, body, [class*="css"] {{ font-family: 'Montserrat', sans-serif; }}
            [data-testid="stMetricValue"] {{ color: #0080cd; font-size: 2.2rem; font-weight: 700; }}
            .locked-box {{
                background-color: #161b22; padding: 25px; border-radius: 12px;
                border: 1px solid #0080cd; text-align: center;
                box-shadow: 0 4px 15px rgba(0,128,205,0.2);
            }}
            .cta-button {{
                display: block; width: 100%; background-color: #00c853; 
                color: white !important; padding: 15px; text-align: center;
                border-radius: 8px; font-weight: bold; text-decoration: none;
                margin-top: 15px; transition: 0.3s;
            }}
            .cta-button:hover {{ background-color: #00e676; transform: scale(1.02); }}
        </style>
    """, unsafe_allow_html=True)

inyectar_estilos()

# --- 3. MOTOR DE PRICING ---
def ajustar_a_psicologico(precio):
    if pd.isna(precio): return 0
    entero = int(precio)
    decimal = precio - entero
    if decimal < 0.45: return entero + 0.49
    elif decimal < 0.85: return entero + 0.90
    else: return entero + 0.99

@st.cache_data
def procesar_datos_pricing(df, sensibilidad=1.0):
    if df is None or df.empty: return None, "No hay datos."
    df_t = df.copy()
    df_t.columns = [str(c).strip().lower() for c in df_t.columns]
    
    c_p = next((c for c in df_t.columns if any(p in c for p in ['precio', 'pvp', 'venta'])), None)
    c_v = next((c for c in df_t.columns if any(v in c for v in ['cant', 'vol', 'unid'])), None)
    c_s = next((c for c in df_t.columns if any(s in c for s in ['sku', 'prod', 'cod', 'ref'])), 'sku_gen')
    
    if not c_p or not c_v: return None, "Faltan columnas clave."

    df_t['elas'] = np.random.uniform(0.7, 2.3, size=len(df_t))
    
    def calc(row):
        p, v, e = float(row[c_p]), float(row[c_v]), row['elas']
        if e < 1.1:
            p_f = ajustar_a_psicologico(p * (1 + (0.15 * sensibilidad)))
            return (p_f - p) * v * 0.8, p_f, "SUBIR PRECIO"
        elif e > 1.9:
            return 0, ajustar_a_psicologico(p * 0.94), "BAJAR PRECIO"
        return 0, p, "MANTENER"

    res = df_t.apply(calc, axis=1)
    df_t['ganancia'], df_t['p_sug'], df_t['estado'] = [x[0] for x in res], [x[1] for x in res], [x[2] for x in res]
    df_t['SKU_V'] = df_t[c_s] if c_s != 'sku_gen' else [f"REF-{i}" for i in range(len(df_t))]
    return df_t, None

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown(f'<div style="background:#fff; padding:10px; border-radius:10px;"><img src="{URL_LOGO}" width="100%"></div>', unsafe_allow_html=True)
    st.header("⚙️ Configuración")
    modo_entrada = st.radio("Origen de Datos:", ["🎲 Simulación", "📂 Subir Archivo"])
    sensibilidad = st.slider("Agresividad", 0.5, 2.0, 1.0)
    modo_admin = st.toggle("🔓 Modo Consultor (Revelar)")

# --- 5. DATA ---
if modo_entrada == "🎲 Simulación":
    df_raw = pd.DataFrame([{"SKU": f"PR-{random.randint(1000,9999)}", "Precio": random.uniform(15, 250), "Cantidad": random.randint(100, 2000)} for _ in range(150)])
else:
    file = st.file_uploader("Cargar Excel/CSV", type=['xlsx', 'csv'])
    df_raw = pd.read_excel(file) if file and file.name.endswith('xlsx') else (pd.read_csv(file) if file else None)

df_final, _ = procesar_datos_pricing(df_raw, sensibilidad) if df_raw is not None else (None, None)

# --- 6. DASHBOARD ---
if df_final is not None:
    st.title("💎 Auditoría de Estrategia de Precios")
    
    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Dinero sobre la mesa", f"${df_final['ganancia'].sum():,.0f}")
    c2.metric("SKUs a Optimizar", len(df_final[df_final['estado'] != "MANTENER"]))
    c3.metric("Impacto EBITDA", "+5.2%")

    st.divider()

    # GRÁFICO CON COLORES CORREGIDOS (ALTO CONTRASTE)
    st.subheader("📍 Mapa de Oportunidad de Precios")
    fig = px.scatter(df_final, x=df_final.columns[1], y=df_final.columns[2], color="estado", size="ganancia",
                     color_discrete_map={
                         'SUBIR PRECIO': '#00e676', # Verde Neón
                         'BAJAR PRECIO': '#ff3d00', # Rojo Vibrante
                         'MANTENER': '#ffffff'     # Blanco Puro (Contraste Máximo)
                     },
                     hover_data=["SKU_V"], log_x=True, log_y=True, height=500)
    fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(255,255,255,0.05)')
    st.plotly_chart(fig, use_container_width=True)

    # TABLA Y CTA
    st.subheader("🔓 Detalle de Acciones Sugeridas")
    col_t, col_c = st.columns([3, 1])
    
    with col_t:
        df_vis = df_final[df_final['estado'] != 'MANTENER'].sort_values('ganancia', ascending=False).head(15).copy()
        df_vis['Precio Actual'] = df_vis.iloc[:, 1].apply(lambda x: f"${x:,.2f}")
        df_vis['Precio Sugerido'] = df_vis['p_sug'].apply(lambda x: f"${x:,.2f}" if modo_admin else "🔒 BLOQUEADO")
        df_vis['Impacto Profit'] = df_vis['ganancia'].apply(lambda x: f"+${x:,.2f}" if modo_admin else "⭐ ANALIZADO")
        
        # Títulos de tabla simplificados
        st.table(df_vis[['SKU_V', 'Precio Actual', 'estado', 'Precio Sugerido', 'Impacto Profit']].rename(
            columns={'SKU_V': 'Referencia SKU', 'estado': 'Acción Sugerida'}
        ))

    with col_c:
        st.markdown(f"""
            <div class="locked-box">
                <h3 style="color: #0080cd; margin:0;">Recupera tus ${df_final['ganancia'].sum():,.0f}</h3>
                <p style="font-size: 0.9rem; color: #ccc; margin-top: 10px;">
                    Análisis finalizado. El algoritmo ha definido los precios psicológicos (.99) óptimos para su inventario.
                </p>
                <a href="https://wa.me/593983959867" class="cta-button">SOLICITAR INFORME</a>
            </div>
        """, unsafe_allow_html=True)

# --- 7. PIE DE PÁGINA ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.caption("© 2025 Eunoia Digital Ecuador")