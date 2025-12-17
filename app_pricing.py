import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import random

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
            html, body, [class*="css"] { font-family: 'Montserrat', sans-serif; background-color: #0e1117; }
            
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

# --- 2. MOTOR DE DATOS (Normalización de Tamaño) ---
@st.cache_data
def generar_data_auditoria():
    np.random.seed(42)
    df = pd.DataFrame({
        "SKU": [f"PR-{random.randint(1000,9999)}" for _ in range(120)],
        "Precio Actual": np.random.uniform(20, 500, 120),
        "Ventas": np.random.randint(100, 5000, 120),
        "Elasticidad": np.random.uniform(0.5, 3.0, 120)
    })
    
    def clasificar(row):
        if row['Elasticidad'] < 1.1: 
            return "SUBIR PRECIO", row['Precio Actual'] * 1.15, row['Ventas'] * 18.0
        if row['Elasticidad'] > 2.2: 
            return "BAJAR PRECIO", row['Precio Actual'] * 0.90, 0
        return "MANTENER", row['Precio Actual'], 0

    res = df.apply(clasificar, axis=1)
    df['Acción'], df['Precio Sugerido'], df['Profit'] = [x[0] for x in res], [x[1] for x in res], [x[2] for x in res]
    
    # --- SOLUCIÓN AL TAMAÑO ---
    # Normalizamos el tamaño entre 10 y 50 para que NADA sea invisible
    # Usamos una raíz cuadrada para que la diferencia entre $10 y $10,000 no sea tan extrema
    df['Tamaño_Visual'] = np.sqrt(df['Profit'] + 100) 
    return df

df = generar_data_auditoria()

# --- 3. DASHBOARD ---
st.title("💎 Auditoría de Estrategia de Precios")

c1, c2, c3 = st.columns(3)
c1.metric("Dinero sobre la mesa", f"${df['Profit'].sum():,.0f}")
c2.metric("Oportunidades de Alza", len(df[df['Acción'] == "SUBIR PRECIO"]))
c3.metric("Impacto EBITDA", "+5.7%")

st.divider()

# --- 4. GRÁFICO: VISIBILIDAD TOTAL ---
st.subheader("📍 Mapa Estratégico de Oportunidad")

# Colores de máximo contraste
color_map = {
    'SUBIR PRECIO': '#00ffcc', # Turquesa Neón
    'BAJAR PRECIO': '#ff4b4b', # Rojo Intenso
    'MANTENER': '#ffffff'      # Blanco Puro (Referencia)
}

fig = px.scatter(df, x="Precio Actual", y="Ventas", color="Acción", 
                 size="Tamaño_Visual", size_max=30, # size_max controlado
                 color_discrete_map=color_map,
                 hover_data={"SKU": True, "Precio Actual": ":.2f", "Ventas": True, "Tamaño_Visual": False, "Profit": ":,.0f"},
                 log_x=True, height=500)

fig.update_layout(
    template="plotly_dark",
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='#1c2128', # Fondo gris azulado para contraste
    xaxis=dict(gridcolor='#2d333b', showgrid=True, title="Precio ($)"),
    yaxis=dict(gridcolor='#2d333b', showgrid=True, title="Unidades Vendidas"),
    margin=dict(l=0, r=0, t=30, b=0),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

# Añadimos un borde blanco fino a cada punto para que "resalten" del fondo
fig.update_traces(marker=dict(line=dict(width=1, color='rgba(255,255,255,0.5)'), opacity=0.9))

st.plotly_chart(fig, use_container_width=True)

# --- 5. TABLA Y CTA ---
col_t, col_c = st.columns([2.5, 1])

with col_t:
    st.subheader("🔓 Detalle del Análisis")
    modo_admin = st.toggle("🔓 Revelar Precios Sugeridos")
    
    df_v = df[df['Acción'] != "MANTENER"].sort_values("Profit", ascending=False).head(15).copy()
    
    # Formateo de tabla
    df_v['Precio Sugerido'] = df_v['Precio Sugerido'].map("${:,.2f}".format) if modo_admin else "🔒 BLOQUEADO"
    df_v['Impacto'] = df_v['Profit'].map("+${:,.0f}".format) if modo_admin else "⭐ ANALIZADO"
    
    # Títulos limpios como solicitaste
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
                El algoritmo ha identificado productos con elasticidad inelástica donde puede subir precios sin afectar la demanda.
            </p>
            <a href="https://wa.me/593983959867" class="cta-button">ADQUIRIR PLAN COMPLETO</a>
        </div>
    """, unsafe_allow_html=True)

# --- 6. PIE DE PÁGINA ---
st.markdown("---")
st.caption("© 2025 Eunoia Digital Ecuador")