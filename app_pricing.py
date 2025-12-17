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
            
            /* Métricas con resplandor Eunoia */
            [data-testid="stMetricValue"] { 
                color: #0080cd; 
                font-size: 2.5rem; 
                font-weight: 700;
                text-shadow: 0px 2px 4px rgba(0,0,0,0.3);
            }
            
            /* Caja de Conversión Profesional */
            .locked-box {
                background-color: #161b22; padding: 25px; border-radius: 12px;
                border: 1px solid #0080cd; text-align: center;
                box-shadow: 0 10px 20px rgba(0,0,0,0.5);
            }
            .cta-button {
                display: block; width: 100%; background-color: #00c853; 
                color: white !important; padding: 15px; text-align: center;
                border-radius: 8px; font-weight: bold; text-decoration: none;
                margin-top: 15px; transition: 0.3s;
            }
            .cta-button:hover { background-color: #00e676; transform: translateY(-2px); }
        </style>
    """, unsafe_allow_html=True)

inyectar_estilos()

# --- 2. GENERACIÓN DE DATA DE AUDITORÍA ---
@st.cache_data
def generar_data():
    np.random.seed(123)
    df = pd.DataFrame({
        "SKU": [f"REF-{random.randint(100,999)}" for _ in range(100)],
        "Precio": np.random.uniform(50, 400, 100),
        "Ventas": np.random.randint(200, 4000, 100),
        "Elasticidad": np.random.uniform(0.5, 2.8, 100)
    })
    def rule(row):
        if row['Elasticidad'] < 1.0: return "SUBIR PRECIO", row['Precio'] * 1.15, row['Ventas'] * 22
        if row['Elasticidad'] > 2.2: return "BAJAR PRECIO", row['Precio'] * 0.92, 0
        return "MANTENER", row['Precio'], 0
    res = df.apply(rule, axis=1)
    df['Acción'], df['Sugerido'], df['Profit'] = [x[0] for x in res], [x[1] for x in res], [x[2] for x in res]
    return df

df = generar_data()

# --- 3. DASHBOARD ---
st.title("💎 Auditoría de Estrategia de Precios")

c1, c2, c3 = st.columns(3)
c1.metric("Dinero sobre la mesa", f"${df['Profit'].sum():,.0f}")
c2.metric("Oportunidades de Alza", len(df[df['Acción'] == "SUBIR PRECIO"]))
c3.metric("Impacto EBITDA", "+5.8%")

st.divider()

# --- 4. GRÁFICO: LIENZO DE LUZ (SOLUCIÓN AL COLOR OSCURO) ---
st.subheader("📍 Mapa de Oportunidad Estratégica")

# Paleta Profesional de Alta Saturación (Business Colors)
color_map = {
    'SUBIR PRECIO': '#10ac84', # Verde Esmeralda Profundo
    'BAJAR PRECIO': '#ee5253', # Rojo Coral Intenso
    'MANTENER': '#576574'      # Gris Carbón (Contraste perfecto)
}

fig = px.scatter(df, x="Precio", y="Ventas", color="Acción", 
                 size="Profit", size_max=35, color_discrete_map=color_map,
                 hover_data=["SKU"], log_x=True, height=500)

# AJUSTE DE FONDO: Pasamos a un "Surface" claro para que el color destaque
fig.update_layout(
    template="plotly_white",  # Cambiamos a plantilla clara para el gráfico
    paper_bgcolor='rgba(0,0,0,0)', # El contenedor sigue siendo oscuro
    plot_bgcolor='#f8f9fa',       # EL FONDO DEL GRÁFICO AHORA ES LUZ (Gris Hueso muy claro)
    margin=dict(l=40, r=40, t=20, b=40),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="white")),
    xaxis=dict(gridcolor='#e9ecef', title_font=dict(color="white")),
    yaxis=dict(gridcolor='#e9ecef', title_font=dict(color="white"))
)

# Añadimos bordes a los puntos para que resalten aún más
fig.update_traces(marker=dict(line=dict(width=1, color='white'), opacity=0.85))

st.plotly_chart(fig, use_container_width=True)



# --- 5. TABLA Y CTA ---
col_t, col_c = st.columns([2.5, 1])

with col_t:
    st.subheader("🔓 Detalle de Productos Críticos")
    modo_admin = st.toggle("🔓 Revelar Precios Estratégicos")
    
    df_v = df[df['Acción'] != "MANTENER"].sort_values("Profit", ascending=False).head(15).copy()
    df_v['Sugerido'] = df_v['Sugerido'].map("${:,.2f}".format) if modo_admin else "🔒 BLOQUEADO"
    df_v['Profit'] = df_v['Profit'].map("+${:,.0f}".format) if modo_admin else "⭐ ANALIZADO"
    
    st.dataframe(
        df_v[['SKU', 'Precio', 'Acción', 'Sugerido', 'Profit']].rename(columns={'Acción': 'Acción Sugerida', 'Profit': 'Ganancia Extra'}),
        use_container_width=True, hide_index=True
    )

with col_c:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(f"""
        <div class="locked-box">
            <h3 style="color: white; margin:0;">Captura tus <br><span style="color:#0080cd;">${df['Profit'].sum():,.0f}</span></h3>
            <p style="font-size: 0.85rem; color: #ccc; margin-top: 15px;">
                Su empresa tiene capital atrapado en precios que no corresponden a la elasticidad de su mercado.
            </p>
            <a href="https://wa.me/593983959867" class="cta-button">GENERAR INFORME PDF</a>
        </div>
    """, unsafe_allow_html=True)

# --- 6. PIE DE PÁGINA ---
st.markdown("<br>---")
st.caption("© 2025 Eunoia Digital Ecuador")