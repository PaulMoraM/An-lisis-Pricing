import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import random
from faker import Faker

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Diagnóstico Eunoia Digital",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. VARIABLES DE IMÁGENES (DEFINICIÓN) ---
# Definimos las URLs aquí arriba para evitar errores
URL_LOGO = "https://raw.githubusercontent.com/PaulMoraM/eunoia-branding/main/eunoia-digital-logo.png"
URL_BANNER = "https://raw.githubusercontent.com/PaulMoraM/eunoia-branding/main/banner_redes.png"

# --- 3. ESTILOS CSS (MODO OSCURO EUNOIA) ---
def inyectar_estilos():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
            
            html, body, [class*="css"]  {
                font-family: 'Montserrat', sans-serif;
            }

            /* Botones */
            div.stButton > button:first-child {
                background-color: #0080cd;
                color: white;
                border-radius: 8px;
                border: none;
                font-weight: bold;
                height: 3em;
                transition: 0.3s;
            }
            div.stButton > button:first-child:hover {
                background-color: #006bb3;
                box-shadow: 0 0 12px #0080cd;
            }

            /* Botón CTA HTML */
            .cta-button {
                background-color: #0080cd;
                color: white !important;
                padding: 15px 32px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                border: 2px solid #0080cd;
                transition-duration: 0.4s;
                width: 100%;
            }
            .cta-button:hover {
                background-color: black;
                border: 2px solid #0080cd;
                color: #0080cd !important;
                box-shadow: 0 0 15px #0080cd;
            }

            /* Métricas */
            [data-testid="stMetricValue"] {
                color: #0080cd;
                font-size: 2.2rem;
                font-weight: 700;
            }
            [data-testid="stMetricLabel"] {
                color: #e0e0e0;
            }

            /* Limpieza */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .block-container {padding-top: 1rem;}
            [data-testid="stDataFrame"] {border: 1px solid #333;}
        </style>
    """, unsafe_allow_html=True)

inyectar_estilos()

# --- 4. FUNCIÓN DATOS SIMULADOS ---
@st.cache_data
def generar_datos_simulados():
    fake = Faker('es_ES')
    datos = []
    categorias = ['ACCESORIOS DE VIAJE', 'ROPA DEPORTIVA TÉCNICA', 'EQUIPAMIENTO OUTDOOR', 'CALZADO ESCOLAR']
    
    for i in range(600):
        margen_base = random.uniform(0.05, 0.45) 
        cantidad = random.randint(50, 3500)
        precio = round(random.uniform(15, 120), 2)
        ventas = round(cantidad * precio, 2)
        costo = round(ventas * (1 - margen_base), 2)
        
        datos.append({
            'SKU': f"SKU-{random.randint(1000, 9999)}-{random.choice(['A','B','C'])}",
            'Categoria': random.choice(categorias),
            'Ventas ($)': ventas,
            'Costo ($)': costo,
            'Unidades': cantidad,
            'Margen ($)': ventas - costo
        })
    
    df = pd.DataFrame(datos)
    df['Margen %'] = (df['Margen ($)'] / df['Ventas ($)']) * 100
    return df

# --- 5. BARRA LATERAL (CON FIX DE LOGO BLANCO) ---
with st.sidebar:
    # --- LOGO CON FONDO BLANCO ---
    # Contenedor HTML para crear la tarjeta blanca
    st.markdown(f"""
        <div style="
            background-color: #ffffff;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 25px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(255,255,255,0.1);
        ">
            <img src="{URL_LOGO}" style="width: 100%; height: auto; display: block;">
        </div>
    """, unsafe_allow_html=True)
    # -----------------------------
    
    st.header("⚙️ Configuración")
    modo_real = st.toggle("📂 Activar Modo Auditoría Real")
    
    df = None 
    
    if modo_real:
        st.info("Sube tu archivo Excel/CSV")
        archivo = st.file_uploader("Cargar Archivo", type=["xlsx", "csv"])
        if archivo:
            try:
                if archivo.name.endswith('.csv'):
                    df = pd.read_csv(archivo)
                else:
                    df = pd.read_excel(archivo)
                
                # Normalización básica de nombres
                df = df.rename(columns={'Ventas': 'Ventas ($)', 'Costo': 'Costo ($)', 'Cantidad': 'Unidades'})
                if 'Margen ($)' not in df.columns: df['Margen ($)'] = df['Ventas ($)'] - df['Costo ($)']
                if 'Margen %' not in df.columns: df['Margen %'] = (df['Margen ($)'] / df['Ventas ($)']) * 100
                st.success("Datos cargados")
            except Exception as e:
                st.error(f"Error: {e}")
                st.stop()
        else:
            st.warning("Esperando archivo...")
            st.stop()
    else:
        st.caption("🟢 Live Demo: Datos sintéticos")
        df = generar_datos_simulados()
    
    st.markdown("---")
    # CORRECCIÓN 1: Enlace en la barra lateral con el nuevo número y mensaje
    st.markdown("💬 [WhatsApp Directo](https://wa.me/593983959867?text=Hola,%20quiero%20informaci%C3%B3n%20sobre%20el%20Diagn%C3%B3stico%20Express)")

# --- 6. CUERPO PRINCIPAL ---
try:
    st.image(URL_BANNER, use_container_width=True)
except:
    pass

st.title("🚀 Auditoría de Rentabilidad de Inventarios")
st.markdown("Diagnóstico financiero del portafolio.")
st.markdown("---")

# KPIs
total_ventas = df['Ventas ($)'].sum()
total_margen = df['Margen ($)'].sum()
margen_avg = (total_margen / total_ventas) * 100

c1, c2, c3, c4 = st.columns(4)
c1.metric("Ventas Totales", f"${total_ventas:,.0f}")
c2.metric("Margen Bruto", f"${total_margen:,.0f}")
c3.metric("Margen Global", f"{margen_avg:.1f}%")
c4.metric("SKUs", f"{df.shape[0]}")

# GRÁFICO
med_v = df['Ventas ($)'].median()
med_m = df['Margen ($)'].median()

def clasificar(row):
    if row['Margen ($)'] >= med_m and row['Ventas ($)'] >= med_v: return "ESTRELLA (Ganar)"
    if row['Margen ($)'] < med_m and row['Ventas ($)'] >= med_v: return "DILEMA (Optimizar)"
    if row['Margen ($)'] < med_m and row['Ventas ($)'] < med_v: return "PERRO (Eliminar)"
    return "NICHO (Potenciar)"

df['Clasificación'] = df.apply(clasificar, axis=1)
colors = {'ESTRELLA (Ganar)': '#00c853', 'DILEMA (Optimizar)': '#ffab00', 'PERRO (Eliminar)': '#ff1744', 'NICHO (Potenciar)': '#0080cd'}

st.subheader("1. Matriz de Impacto")
fig = px.scatter(df, x="Margen ($)", y="Ventas ($)", color="Clasificación", size="Unidades",
                 color_discrete_map=colors, log_x=True, log_y=True, height=550)

fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(255,255,255,0.05)')
st.plotly_chart(fig, use_container_width=True)

# ALERTA Y CIERRE
toxicos = df[df['Clasificación'].isin(['PERRO (Eliminar)', 'DILEMA (Optimizar)'])].shape[0]
st.error(f"⚠️ **DIAGNÓSTICO:** {toxicos} productos requieren intervención.")

st.markdown("---")
c_left, c_right = st.columns([2, 1])

with c_left:
    st.write("Muestra de productos críticos (Ocultos):")
    # Filtramos y copiamos para evitar warning de pandas
    ver = df[df['Clasificación'].str.contains("PERRO|DILEMA")].head(5).copy()
    ver['SKU'] = ver['SKU'].apply(lambda x: f"{str(x)[:6]}...🔒")
    st.table(ver[['Categoria', 'SKU', 'Margen %']])

with c_right:
    st.info("🔓 **Obtener Reporte Completo**")
    # AQUÍ ESTABA EL ERROR: Se ha corregido el cierre de comillas y el HTML
    st.markdown("""
        <a href="https://wa.me/593983959867?text=Hola,%20quiero%20informaci%C3%B3n%20sobre%20el%20Diagn%C3%B3stico%20Express" class="cta-button" target="_blank">
            👉 Solicitar Diagnóstico
        </a>
    """, unsafe_allow_html=True)

st.caption("© 2025 Eunoia Digital Ecuador")