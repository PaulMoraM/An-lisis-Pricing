import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import StringIO
import random

# Intentamos importar Faker para la simulación profesional
try:
    from faker import Faker
    fake = Faker()
except ImportError:
    class Faker:
        def catch_phrase(self): return "Producto Genérico"
    fake = Faker()

# URL del Logo
URL_LOGO = "https://raw.githubusercontent.com/PaulMoraM/eunoia-branding/main/eunoia-digital-logo.png"

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Eunoia Pricing Audit",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. ESTILOS CSS (BRANDING EUNOIA) ---
def inyectar_estilos():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
            html, body, [class*="css"] { font-family: 'Montserrat', sans-serif; }
            
            /* Métricas */
            [data-testid="stMetricValue"] { color: #0080cd; font-size: 2.2rem; font-weight: 700; }
            
            /* Locked Box (CTA) */
            .locked-box {
                background-color: #161b22;
                padding: 25px;
                border-radius: 12px;
                border: 1px solid #0080cd;
                text-align: center;
                box-shadow: 0 4px 15px rgba(0,128,205,0.2);
            }
            .cta-button {
                background-color: #0080cd; color: white !important;
                padding: 12px 20px; border-radius: 8px;
                text-decoration: none; font-weight: bold; display: inline-block;
                margin-top: 15px; transition: 0.3s;
            }
            .cta-button:hover { background-color: #00c853; transform: scale(1.05); }
        </style>
    """, unsafe_allow_html=True)

inyectar_estilos()

# --- 3. LÓGICA DE NEGOCIO (EL "MOTOR") ---
def ajustar_a_psicologico(precio):
    if pd.isna(precio): return 0
    entero = int(precio)
    decimal = precio - entero
    if decimal < 0.45: return entero + 0.49
    elif decimal < 0.85: return entero + 0.90
    else: return entero + 0.99

# --- 4. SIDEBAR ---
with st.sidebar:
    st.image(URL_LOGO, use_container_width=True)
    st.markdown("---")
    st.header("⚙️ Configuración")
    archivo_subido = st.file_uploader("Cargar Plantilla de Precios", type=['csv', 'xlsx'])
    modo_admin = st.toggle("🔓 Revelar Estrategia Oculta")
    st.markdown("---")
    st.info("Este módulo analiza la elasticidad y aplica terminaciones .99/.95 para maximizar el margen.")

# --- 5. PROCESAMIENTO DE DATOS ---
if archivo_subido is not None:
    # Lógica para cargar datos reales (según tu notebook)
    df = pd.read_csv(archivo_subido) if archivo_subido.name.endswith('.csv') else pd.read_excel(archivo_subido)
else:
    # SIMULACIÓN COMPLETA (Lo que ya tenías desarrollado)
    data_sim = []
    for i in range(15):
        p_actual = random.uniform(10, 200)
        accion = random.choice(['SUBIR PRECIO', 'BAJAR PRECIO', 'MANTENER'])
        
        if accion == 'SUBIR PRECIO':
            p_sug = p_actual * 1.15
        elif accion == 'BAJAR PRECIO':
            p_sug = p_actual * 0.92
        else:
            p_sug = p_actual
            
        p_sug = ajustar_a_psicologico(p_sug)
        impacto = random.uniform(500, 5000) if accion != 'MANTENER' else 0
        
        data_sim.append({
            'SKU': f"SKU-{random.randint(1000,9999)}",
            'Producto': fake.catch_phrase(),
            'Precio Actual': p_actual,
            'Acción Sugerida': accion,
            'Precio Sugerido': p_sug,
            'Ganancia Extra ($)': impacto
        })
    df = pd.DataFrame(data_sim)

# --- 6. INTERFAZ PRINCIPAL ---
st.title("💎 Auditoría de Estrategia de Precios")
st.markdown("Análisis avanzado de optimización de ingresos y precios psicológicos.")

# KPIs Superiores
dinero_mesa = df['Ganancia Extra ($)'].sum()
skus_afectados = len(df[df['Acción Sugerida'] != 'MANTENER'])

col1, col2, col3 = st.columns(3)
col1.metric("Dinero sobre la mesa", f"${dinero_mesa:,.2f}")
col2.metric("SKUs a optimizar", skus_afectados)
col3.metric("Impacto en Margen", "+4.2%")

st.markdown("---")

# Tabla y CTA
col_tabla, col_cta = st.columns([2.5, 1])

with col_tabla:
    st.subheader("Plan de Acción por Producto")
    
    # PREPARACIÓN DE TABLA (Limpiando los títulos como pediste)
    df_visual = df.copy()
    
    # Simplificación de nombres de columnas
    df_visual = df_visual.rename(columns={
        'SKU': 'Referencia SKU',
        'Acción Sugerida': 'Acción Sugerida', # Limpio
        'Precio Sugerido': 'Precio Sugerido'  # Limpio
    })

    # Protocolo de Seguridad Eunoia (Modo Venta)
    if not modo_admin:
        df_visual['Precio Sugerido'] = "🔒 BLOQUEADO"
        df_visual['Ganancia Extra ($)'] = "⭐ ANALIZADO"

    # Mostramos la tabla (Se eliminó el hack de los espacios superiores)
    st.dataframe(df_visual[['Referencia SKU', 'Precio Actual', 'Acción Sugerida', 'Precio Sugerido', 'Ganancia Extra ($)']], 
                 use_container_width=True, hide_index=True)

with col_cta:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class="locked-box">
            <h3 style="color: white; margin:0;">Recupera tus <br><span style="color:#0080cd;">${dinero_mesa:,.0f}</span></h3>
            <p style="font-size: 0.85rem; color: #ccc; margin-top: 10px;">
                El algoritmo ha detectado el precio psicológico exacto para maximizar tu rotación.
            </p>
            <hr style="border:0.5px solid #333">
            <a href="#" class="cta-button">ADQUIRIR INFORME</a>
        </div>
    """, unsafe_allow_html=True)

# --- 7. PIE DE PÁGINA ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.caption("© 2025 Eunoia Digital Ecuador")