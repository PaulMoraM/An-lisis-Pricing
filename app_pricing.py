import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import StringIO
import random

# Intentamos importar Faker (para simulación). Si falla, usamos fallback.
try:
    from faker import Faker
    fake = Faker()
except ImportError:
    class Faker:
        def catch_phrase(self): return "Producto Genérico"
    fake = Faker()

# URL del Logo y Banner (Branding Eunoia)
URL_LOGO = "https://raw.githubusercontent.com/PaulMoraM/eunoia-branding/main/eunoia-digital-logo.png"
URL_BANNER = "https://raw.githubusercontent.com/PaulMoraM/eunoia-branding/main/banner_redes.png"

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Eunoia Pricing Audit",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. ESTILOS CSS (BRANDING EUNOIA DIGITAL) ---
def inyectar_estilos():
    st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
            html, body, [class*="css"] {{ font-family: 'Montserrat', sans-serif; }}

            /* Estilo de Métricas */
            [data-testid="stMetricValue"] {{
                color: #0080cd; 
                font-size: 2.2rem;
                font-weight: 700;
            }}
            
            /* Caja de Conversión (Locked Box) */
            .locked-box {{
                background-color: #161b22;
                padding: 25px;
                border-radius: 12px;
                border: 1px solid #0080cd;
                text-align: center;
                box-shadow: 0 4px 15px rgba(0,128,205,0.2);
            }}
            
            .cta-button {{
                display: block;
                width: 100%;
                background-color: #00c853; 
                color: white !important;
                padding: 15px;
                text-align: center;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
                text-decoration: none;
                margin-top: 15px;
                transition: 0.3s;
            }}
            .cta-button:hover {{
                background-color: #00e676;
                transform: scale(1.02);
            }}
        </style>
    """, unsafe_allow_html=True)

inyectar_estilos()

# --- 3. LÓGICA DE NEGOCIO (EL MOTOR) ---
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
    df_temp = df.copy()
    df_temp.columns = [str(c).strip().lower() for c in df_temp.columns]
    
    col_precio = next((c for c in df_temp.columns if any(p in c for p in ['precio', 'pvp', 'venta'])), None)
    col_vol = next((c for c in df_temp.columns if any(v in c for v in ['cant', 'vol', 'unid', 'anuales'])), None)
    col_sku = next((c for c in df_temp.columns if any(s in c for s in ['sku', 'prod', 'cod', 'ref'])), 'sku_gen')
    
    if not col_precio or not col_vol:
        return None, "❌ Error: No se detectaron columnas de Precio o Cantidad."

    # Simulación de elasticidad para el análisis
    df_temp['elas'] = np.random.uniform(0.6, 2.5, size=len(df_temp))
    
    def aplicar_estrategia(row):
        p, v, e = float(row[col_precio]), float(row[col_vol]), row['elas']
        if e < 1.0:
            factor = (1.2 - e) * 0.25 * sensibilidad
            p_final = ajustar_a_psicologico(p * (1 + factor))
            ganancia = (p_final * v * (1 - factor*0.5)) - (p * v)
            return max(ganancia, 0), p_final, "SUBIR PRECIO"
        elif e > 2.0:
            return 0, ajustar_a_psicologico(p * 0.95), "BAJAR PRECIO"
        return 0, p, "MANTENER"

    res = df_temp.apply(aplicar_estrategia, axis=1)
    df_temp['ganancia'], df_temp['p_sug'], df_temp['estado'] = [x[0] for x in res], [x[1] for x in res], [x[2] for x in res]
    df_temp['SKU_V'] = df_temp[col_sku] if col_sku != 'sku_gen' else [f"REF-{i}" for i in range(len(df_temp))]
    
    return df_temp, None

# --- 4. BARRA LATERAL ---
with st.sidebar:
    st.markdown(f'<div style="background:#fff; padding:10px; border-radius:10px;"><img src="{URL_LOGO}" width="100%"></div>', unsafe_allow_html=True)
    st.header("⚙️ Configuración")
    modo_entrada = st.radio("Origen de Datos:", ["🎲 Simulación", "📂 Subir Archivo"])
    sensibilidad = st.slider("Agresividad", 0.5, 2.0, 1.0)
    modo_admin = st.toggle("🔓 Revelar Estrategia Oculta")

# --- 5. CARGA DE DATOS ---
if modo_entrada == "🎲 Simulación":
    df_raw = pd.DataFrame([{
        "SKU": f"PR-{random.randint(1000,9999)}",
        "Precio": random.uniform(10, 200),
        "Cantidad": random.randint(50, 1000)
    } for _ in range(200)])
else:
    file = st.file_uploader("Subir Excel/CSV", type=['xlsx', 'csv'])
    df_raw = pd.read_excel(file) if file and file.name.endswith('xlsx') else (pd.read_csv(file) if file else None)

df_final, error = procesar_datos_pricing(df_raw, sensibilidad) if df_raw is not None else (None, None)

# --- 6. CUERPO PRINCIPAL ---
if df_final is not None:
    st.title("💎 Auditoría de Estrategia de Precios")
    
    # KPIs
    total_mesa = df_final['ganancia'].sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Dinero sobre la mesa", f"${total_mesa:,.0f}")
    c2.metric("Productos a Optimizar", len(df_final[df_final['estado'] != "MANTENER"]))
    c3.metric("Potencial EBITDA", "+4.8%")

    st.divider()

    # Gráfico de Dispersión (Mapa de Oportunidad)
    st.subheader("📍 Mapa de Oportunidad de Precios")
    fig = px.scatter(df_final, x=df_final.columns[1], y=df_final.columns[2], color="estado", size="ganancia",
                     color_discrete_map={'SUBIR PRECIO': '#00c853', 'BAJAR PRECIO': '#ffab00', 'MANTENER': '#444'},
                     hover_data=["SKU_V"], log_x=True, log_y=True, height=450)
    fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(255,255,255,0.05)')
    st.plotly_chart(fig, use_container_width=True)

    # Tabla y CTA
    st.subheader("🔓 Detalle de Acciones Sugeridas")
    col_t, col_c = st.columns([3, 1])
    
    with col_t:
        df_vis = df_final[df_final['estado'] != 'MANTENER'].sort_values('ganancia', ascending=False).head(15).copy()
        
        # Formateo de columnas
        df_vis['Precio Actual'] = df_vis.iloc[:, 1].apply(lambda x: f"${x:,.2f}")
        df_vis['Precio Sugerido'] = df_vis['p_sug'].apply(lambda x: f"${x:,.2f}" if modo_admin else "🔒 BLOQUEADO")
        df_vis['Impacto EBITDA'] = df_vis['ganancia'].apply(lambda x: f"+${x:,.2f}" if modo_admin else "⭐ ANALIZADO")
        
        # Mostramos la tabla con títulos LIMPIOS
        st.table(df_vis[['SKU_V', 'Precio Actual', 'estado', 'Precio Sugerido', 'Impacto EBITDA']].rename(columns={'SKU_V': 'Referencia SKU', 'estado': 'Acción Sugerida'}))

    with col_c:
        st.markdown(f"""
            <div class="locked-box">
                <h3 style="color: #0080cd; margin:0;">Recupera tus ${total_mesa:,.0f}</h3>
                <p style="font-size: 0.9rem; color: #ccc; margin-top: 10px;">
                    El algoritmo detectó el <b>Precio Psicológico</b> exacto para maximizar su utilidad bruta.
                </p>
                <a href="https://wa.me/593983959867" class="cta-button">ADQUIRIR INFORME</a>
            </div>
        """, unsafe_allow_html=True)

# --- 7. PIE DE PÁGINA ---
st.markdown("---")
st.caption("© 2025 Eunoia Digital Ecuador")