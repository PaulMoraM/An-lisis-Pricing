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
            [data-testid="stMetricValue"] { color: #0080cd; font-size: 2.2rem; font-weight: 700; }
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

# --- 2. GENERACIÓN DE DATA (Lógica de Visibilidad) ---
@st.cache_data
def generar_data_auditoria():
    np.random.seed(42)
    df = pd.DataFrame({
        "SKU": [f"PR-{random.randint(1000,9999)}" for _ in range(150)],
        "Precio Actual": np.random.uniform(20, 500, 150),
        "Volumen": np.random.randint(100, 5000, 150),
        "Elasticidad": np.random.uniform(0.5, 3.0, 150)
    })
    
    def clasificar(row):
        if row['Elasticidad'] < 1.1: 
            return "SUBIR PRECIO", row['Precio Actual'] * 1.15, row['Volumen'] * 25.0
        if row['Elasticidad'] > 2.2: 
            return "BAJAR PRECIO", row['Precio Actual'] * 0.90, 5.0 # Mínimo impacto para visibilidad
        return "MANTENER", row['Precio Actual'], 2.0 # Mínimo impacto para visibilidad

    res = df.apply(clasificar, axis=1)
    df['Acción'], df['Sugerido'], df['Profit'] = [x[0] for x in res], [x[1] for x in res], [x[2] for x in res]
    
    # NUEVA COLUMNA: Tamaño Visual (Para que nada sea invisible)
    df['Tamaño_Grafico'] = df['Profit'].apply(lambda x: x if x > 20 else 20)
    return df

df = generar_data_auditoria()

# --- 3. DASHBOARD ---
st.title("💎 Auditoría de Estrategia de Precios")

c1, c2, c3 = st.columns(3)
c1.metric("Dinero sobre la mesa", f"${df[df['Acción']=='SUBIR PRECIO']['Profit'].sum():,.0f}")
c2.metric("Oportunidades de Alza", len(df[df['Acción'] == "SUBIR PRECIO"]))
c3.metric("Impacto EBITDA", "+5.4%")

st.divider()

# --- 4. GRÁFICO: CONTRASTE MÁXIMO ---
st.subheader("📍 Mapa Estratégico de Oportunidad")

# Colores de Alta Visibilidad
color_map = {
    'SUBIR PRECIO': '#00FFAA', # Turquesa Neón (Acción)
    'BAJAR PRECIO': '#FF3333', # Rojo Eléctrico (Corrección)
    'MANTENER': '#E0E0E0'      # Platino Brillante (Referencia)
}

fig = px.scatter(df, x="Precio Actual", y="Volumen", color="Acción", 
                 size="Tamaño_Grafico", size_max=35, 
                 color_discrete_map=color_map,
                 hover_data=["SKU"], log_x=True, height=550)

# Ajuste de fondo para que no "absorba" el color
fig.update_layout(
    template="plotly_dark",
    paper_bgcolor='#0e1117',  # Fondo exterior
    plot_bgcolor='#1c2128',   # FONDO DEL GRÁFICO: Un gris azulado que separa los puntos del negro
    xaxis=dict(gridcolor='#2d333b', showgrid=True, title="Precio de Venta ($)"),
    yaxis=dict(gridcolor='#2d333b', showgrid=True, title="Volumen de Unidades"),
    margin=dict(l=20, r=20, t=20, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

# Truco de Visibilidad: Añadir borde a los puntos
fig.update_traces(marker=dict(line=dict(width=1, color='white'), opacity=0.9))

st.plotly_chart(fig, use_container_width=True)



# --- 5. TABLA Y CTA ---
col_t, col_c = st.columns([2.5, 1])

with col_t:
    st.subheader("🔓 Detalle del Análisis")
    modo_admin = st.toggle("🔓 Revelar Estrategia Oculta")
    
    df_v = df[df['Acción'] != "MANTENER"].sort_values("Profit", ascending=False).head(15).copy()
    
    # Formateo Limpio
    df_v['Precio Sugerido'] = df_v['Sugerido'].map("${:,.2f}".format) if modo_admin else "🔒 BLOQUEADO"
    df_v['Impacto'] = df_v['Profit'].map("+${:,.0f}".format) if modo_admin else "⭐ ANALIZADO"
    
    st.dataframe(
        df_v[['SKU', 'Precio Actual', 'Acción', 'Precio Sugerido', 'Impacto']].rename(columns={'Acción': 'Acción Sugerida'}),
        use_container_width=True, hide_index=True
    )

with col_c:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class="locked-box">
            <h3 style="color: white; margin:0;">Recupera tus <br><span style="color:#0080cd;">${df[df['Acción']=='SUBIR PRECIO']['Profit'].sum():,.0f}</span></h3>
            <p style="font-size: 0.85rem; color: #ccc; margin-top: 15px;">
                El análisis ha detectado productos con baja elasticidad donde el cliente tolera un ajuste al alza.
            </p>
            <a href="https://wa.me/593983959867" class="cta-button">ADQUIRIR PLAN COMPLETO</a>
        </div>
    """, unsafe_allow_html=True)

# --- 6. PIE DE PÁGINA ---
st.markdown("<br>---")
st.caption("© 2025 Eunoia Digital Ecuador")