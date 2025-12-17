import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import random

# --- 1. CONFIGURACIÓN EUNOIA ---
st.set_page_config(page_title="Eunoia Pricing Audit", page_icon="💎", layout="wide")

def inyectar_estilos():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
            html, body, [class*="css"] { font-family: 'Montserrat', sans-serif; background-color: #0e1117; }
            
            /* Ajuste de métricas para que brillen */
            [data-testid="stMetricValue"] { color: #00a2ff; font-size: 2.2rem; font-weight: 700; text-shadow: 0px 0px 10px rgba(0,162,255,0.3); }
            
            .locked-box {
                background-color: #161b22; padding: 25px; border-radius: 12px;
                border: 1px solid #0080cd; text-align: center;
            }
            .cta-button {
                display: block; width: 100%; background-color: #00c853; 
                color: white !important; padding: 15px; text-align: center;
                border-radius: 8px; font-weight: bold; text-decoration: none;
                margin-top: 15px; transition: 0.3s;
            }
            .cta-button:hover { background-color: #00ff88; box-shadow: 0 0 20px rgba(0,255,136,0.4); }
        </style>
    """, unsafe_allow_html=True)

inyectar_estilos()

# --- 2. MOTOR DE DATOS (Mantenemos tu lógica) ---
@st.cache_data
def generar_data_auditoria():
    np.random.seed(42)
    df = pd.DataFrame({
        "SKU": [f"PR-{random.randint(1000,9999)}" for _ in range(120)],
        "Precio Actual": np.random.uniform(20, 500, 120),
        "Volumen Ventas": np.random.randint(100, 5000, 120),
        "Elasticidad": np.random.uniform(0.5, 3.0, 120)
    })
    
    def clasificar(row):
        if row['Elasticidad'] < 1.1: return "SUBIR PRECIO", row['Precio Actual'] * 1.12, row['Volumen Ventas'] * 15.5
        if row['Elasticidad'] > 2.1: return "BAJAR PRECIO", row['Precio Actual'] * 0.90, 0
        return "MANTENER", row['Precio Actual'], 0

    res = df.apply(clasificar, axis=1)
    df['Acción'], df['Precio Sugerido'], df['Profit'] = [x[0] for x in res], [x[1] for x in res], [x[2] for x in res]
    return df

df = generar_data_auditoria()

# --- 3. DASHBOARD ---
st.title("💎 Auditoría de Estrategia de Precios")

c1, c2, c3 = st.columns(3)
c1.metric("Dinero sobre la mesa", f"${df['Profit'].sum():,.0f}")
c2.metric("Oportunidades de Alza", len(df[df['Acción'] == "SUBIR PRECIO"]))
c3.metric("Impacto EBITDA", "+6.1%")

st.divider()

# --- GRÁFICO CON FONDO AJUSTADO (MÁS CLARO Y PROFESIONAL) ---
st.subheader("📍 Mapa Estratégico de Oportunidad")

# Paleta de colores optimizada para legibilidad
color_map = {
    'SUBIR PRECIO': '#00ffcc', # Turquesa neón (máxima visibilidad)
    'BAJAR PRECIO': '#ff4d4d', # Rojo coral
    'MANTENER': '#ffffff'      # Blanco puro para contraste
}

fig = px.scatter(df, x="Precio Actual", y="Volumen Ventas", color="Acción", 
                 size="Profit", size_max=40, color_discrete_map=color_map,
                 hover_data=["SKU"], log_x=True, height=550)

# AJUSTE TÉCNICO DEL FONDO Y REJILLA
fig.update_layout(
    template="plotly_dark",
    paper_bgcolor='#0e1117',  # Fondo del contenedor
    plot_bgcolor='#161b22',   # FONDO DEL GRÁFICO (Un gris azulado sutil que hace resaltar los colores)
    xaxis=dict(gridcolor='#2d333b', showgrid=True), # Rejillas visibles pero discretas
    yaxis=dict(gridcolor='#2d333b', showgrid=True),
    legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color="white")),
    margin=dict(l=20, r=20, t=20, b=20)
)

st.plotly_chart(fig, use_container_width=True)



# --- TABLA Y CTA ---
col_t, col_c = st.columns([2.5, 1])

with col_t:
    st.subheader("🔓 Detalle del Análisis")
    modo_admin = st.toggle("🔓 Revelar Precios Estratégicos")
    
    df_v = df[df['Acción'] != "MANTENER"].sort_values("Profit", ascending=False).head(15).copy()
    df_v['Precio Sugerido'] = df_v['Precio Sugerido'].map("${:,.2f}".format) if modo_admin else "🔒 BLOQUEADO"
    df_v['Impacto'] = df_v['Profit'].map("+${:,.0f}".format) if modo_admin else "⭐ ANALIZADO"
    
    st.dataframe(
        df_v[['SKU', 'Precio Actual', 'Acción', 'Precio Sugerido', 'Impacto']].rename(columns={'Acción': 'Acción Sugerida'}),
        use_container_width=True, hide_index=True
    )

with col_c:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class="locked-box">
            <h3 style="color: white; margin:0;">Recupera tus <br><span style="color:#00a2ff;">${df['Profit'].sum():,.0f}</span></h3>
            <p style="font-size: 0.85rem; color: #ccc; margin-top: 15px;">
                El algoritmo ha identificado los productos donde el cliente está dispuesto a pagar más sin perder volumen.
            </p>
            <a href="https://wa.me/593983959867" class="cta-button">ADQUIRIR PLAN COMPLETO</a>
        </div>
    """, unsafe_allow_html=True)

# --- PIE DE PÁGINA ---
st.markdown("<br>---")
st.caption("© 2025 Eunoia Digital Ecuador")