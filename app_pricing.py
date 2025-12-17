import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import random

# Fallback para Faker
try:
    from faker import Faker
    fake = Faker()
except ImportError:
    class Faker:
        def catch_phrase(self): return "Producto Genérico"
    fake = Faker()

# --- 1. CONFIGURACIÓN Y ESTILOS ---
st.set_page_config(page_title="Eunoia Pricing Audit", page_icon="💎", layout="wide")

def inyectar_estilos():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
            html, body, [class*="css"] { font-family: 'Montserrat', sans-serif; }
            [data-testid="stMetricValue"] { color: #0080cd; font-size: 2.2rem; font-weight: 700; }
            
            /* Caja de Conversión Eunoia */
            .locked-box {
                background-color: #161b22; padding: 25px; border-radius: 12px;
                border: 1px solid #0080cd; text-align: center;
                box-shadow: 0 4px 15px rgba(0,128,205,0.2);
            }
            .cta-button {
                display: block; width: 100%; background-color: #00c853; 
                color: white !important; padding: 15px; text-align: center;
                border-radius: 8px; font-weight: bold; text-decoration: none;
                margin-top: 15px; transition: 0.3s;
            }
            .cta-button:hover { background-color: #00e676; transform: scale(1.02); }
        </style>
    """, unsafe_allow_html=True)

inyectar_estilos()

# --- 2. MOTOR DE CÁLCULO ---
def ajustar_a_psicologico(precio):
    if pd.isna(precio): return 0
    entero = int(precio)
    decimal = precio - entero
    if decimal < 0.45: return entero + 0.49
    elif decimal < 0.85: return entero + 0.90
    else: return entero + 0.99

@st.cache_data
def procesar_data(df, agresividad=1.0):
    df_t = df.copy()
    df_t.columns = [str(c).strip().lower() for c in df_t.columns]
    
    # Mapeo inteligente de columnas
    c_p = next((c for c in df_t.columns if any(p in c for p in ['precio', 'pvp', 'venta'])), 'precio')
    c_v = next((c for c in df_t.columns if any(v in c for v in ['cant', 'vol', 'unid'])), 'cantidad')
    c_s = next((c for c in df_t.columns if any(s in c for s in ['sku', 'prod', 'cod'])), 'sku')
    
    # Simulación de elasticidad para el gráfico
    np.random.seed(42)
    df_t['elas'] = np.random.uniform(0.7, 2.5, size=len(df_t))
    
    def estrategia(row):
        p, v, e = float(row[c_p]), float(row[c_v]), row['elas']
        if e < 1.15:
            p_f = ajustar_a_psicologico(p * (1 + (0.12 * agresividad)))
            return (p_f - p) * v * 0.9, p_f, "SUBIR PRECIO"
        elif e > 1.85:
            return 0, ajustar_a_psicologico(p * 0.92), "BAJAR PRECIO"
        return 0, p, "MANTENER"

    res = df_t.apply(estrategia, axis=1)
    df_t['Impacto Profit'], df_t['p_sug'], df_t['Acción Sugerida'] = [x[0] for x in res], [x[1] for x in res], [x[2] for x in res]
    df_t['SKU_V'] = df_t[c_s]
    return df_t

# --- 3. SIDEBAR ---
with st.sidebar:
    st.image("https://raw.githubusercontent.com/PaulMoraM/eunoia-branding/main/eunoia-digital-logo.png", use_container_width=True)
    st.header("⚙️ Configuración")
    modo_admin = st.toggle("🔓 Revelar Estrategia Oculta")
    agresividad = st.slider("Agresividad del Algoritmo", 0.5, 2.0, 1.0)
    st.info("Módulo de Pricing: Optimización de margen mediante elasticidad.")

# --- 4. DATA DE PRUEBA (DATASET MÁS AMPLIO) ---
df_raw = pd.DataFrame([{
    "SKU": f"PR-{random.randint(1000,9999)}",
    "Precio": random.uniform(20, 300),
    "Cantidad": random.randint(100, 3000)
} for _ in range(100)])

df_final = procesar_data(df_raw, agresividad)

# --- 5. DASHBOARD ---
st.title("💎 Auditoría de Estrategia de Precios")

# KPIs
total_extra = df_final['Impacto Profit'].sum()
c1, c2, c3 = st.columns(3)
c1.metric("Dinero sobre la mesa", f"${total_extra:,.0f}")
c2.metric("Productos Críticos", len(df_final[df_final['Acción Sugerida'] != "MANTENER"]))
c3.metric("EBITDA Incremental", "+5.4%")

st.divider()

# --- GRÁFICO DE ALTO CONTRASTE ---
st.subheader("📍 Mapa de Oportunidad de Precios")
# Colores corregidos: Verde Neón, Rojo Intenso y Gris Claro para contraste máximo
color_map = {
    'SUBIR PRECIO': '#00ff88', # Verde flúor
    'BAJAR PRECIO': '#ff1744', # Rojo vibrante
    'MANTENER': '#607d8b'      # Gris azulado (no se pierde en el fondo)
}

fig = px.scatter(df_final, x='precio', y='cantidad', color='Acción Sugerida', 
                 size='Impacto Profit', hover_data=['SKU_V'],
                 color_discrete_map=color_map, log_x=True, log_y=True, height=500)

fig.update_layout(
    template="plotly_dark",
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(255,255,255,0.05)',
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig, use_container_width=True)



# --- TABLA PROFESIONAL ---
st.subheader("🔓 Plan de Optimización Detallado")
col_t, col_c = st.columns([2.5, 1])

with col_t:
    # Preparar tabla visual
    df_out = df_final[df_final['Acción Sugerida'] != 'MANTENER'].sort_values('Impacto Profit', ascending=False).head(20).copy()
    
    # Formateo de columnas para que se vean "Agradables"
    df_out['Precio Actual'] = df_out['precio'].map("${:,.2f}".format)
    
    if modo_admin:
        df_out['Precio Sugerido'] = df_out['p_sug'].map("${:,.2f}".format)
        df_out['Ganancia Extra'] = df_out['Impacto Profit'].map("+ ${:,.0f}".format)
    else:
        df_out['Precio Sugerido'] = "🔒 BLOQUEADO"
        df_out['Ganancia Extra'] = "⭐ ANALIZADO"

    # Seleccionamos y renombramos con títulos limpios
    tabla_final = df_out[['SKU_V', 'Precio Actual', 'Acción Sugerida', 'Precio Sugerido', 'Ganancia Extra']]
    tabla_final.columns = ['Referencia SKU', 'Precio Actual', 'Acción Sugerida', 'Precio Sugerido', 'Ganancia Extra']

    # Usamos st.dataframe para un look moderno (con búsqueda y ordenamiento)
    st.dataframe(tabla_final, use_container_width=True, hide_index=True)

with col_c:
    st.markdown(f"""
        <div class="locked-box">
            <h3 style="color: white; margin:0;">Recupera tus <br><span style="color:#0080cd;">${total_extra:,.0f}</span></h3>
            <p style="font-size: 0.85rem; color: #ccc; margin-top: 10px;">
                Hemos detectado ineficiencias en su política de precios. El 15% de su catálogo está subvalorado.
            </p>
            <hr style="border:0.1px solid #333">
            <a href="https://wa.me/593983959867" class="cta-button">ADQUIRIR PLAN</a>
        </div>
    """, unsafe_allow_html=True)

# --- 6. PIE DE PÁGINA ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.caption("© 2025 Eunoia Digital Ecuador")