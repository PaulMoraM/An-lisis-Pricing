import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import StringIO
import random
try:
    from faker import Faker
except ImportError:
    class Faker:
        def __init__(self): pass
        def catch_phrase(self): return "Producto Genérico"

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Eunoia Pricing Audit",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. ESTILOS CSS (BRANDING EUNOIA) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
        
        html, body, [class*="css"]  { font-family: 'Montserrat', sans-serif; }

        /* KPI Cards personalizadas */
        [data-testid="stMetricValue"] {
            color: #0080cd; /* Azul Eunoia */
            font-size: 2.2rem;
            font-weight: 700;
        }
        
        /* Botón CTA Principal (Verde Dinero) */
        .cta-button {
            display: block;
            width: 100%;
            background-color: #00c853; 
            color: white !important;
            padding: 15px;
            text-align: center;
            border-radius: 8px;
            font-weight: bold;
            font-size: 18px;
            text-decoration: none;
            margin-top: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            transition: transform 0.2s;
            border: none;
        }
        .cta-button:hover {
            transform: scale(1.02);
            box-shadow: 0 6px 12px rgba(0,200,83,0.4);
            color: white !important;
        }
        
        .stDataFrame { font-size: 0.9rem; }
        
        .locked-box {
            background-color: #1e1e1e; 
            padding: 20px; 
            border-radius: 10px; 
            border: 1px solid #333; 
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

# --- 3. LÓGICA DE NEGOCIO (EL CEREBRO) ---

def ajustar_a_psicologico(precio):
    """Convierte 12.40 -> 12.90 para maximizar margen."""
    if pd.isna(precio): return 0
    entero = int(precio)
    decimal = precio - entero
    if decimal < 0.45: return entero + 0.49
    elif decimal < 0.85: return entero + 0.90
    else: return entero + 0.99

@st.cache_data
def procesar_datos_pricing(df, sensibilidad=1.0):
    
    if df is None or df.empty:
        return None, "No hay datos para procesar. Por favor, carga o pega la información."
        
    df_temp = df.copy()
    df_temp.columns = [str(c).strip().lower() for c in df_temp.columns]
    
    col_precio = next((c for c in df_temp.columns if 'precio' in c or 'pvp' in c or 'venta' in c), None)
    col_volumen = next((c for c in df_temp.columns if 'cant' in c or 'volumen' in c or 'unid' in c or 'rotacion' in c or 'anuales' in c or 'ventas' in c), None)
    col_sku = next((c for c in df_temp.columns if 'sku' in c or 'prod' in c or 'cod' in c or 'ref' in c), 'sku_generado')
    
    if not col_precio or not col_volumen:
        return None, f"❌ Error: No encuentro columnas de 'Precio' o 'Cantidad'. Las columnas detectadas son: {list(df.columns)}"

    if 'elasticidad' not in df_temp.columns:
        df_temp['elasticidad_sim'] = np.random.uniform(0.6, 2.5, size=len(df_temp))
    
    def calcular_estrategia(row):
        try:
            precio = float(row[col_precio])
            vol = float(row[col_volumen])
        except:
            return 0, 0, "ERROR"
            
        elas = row.get('elasticidad_sim', 1.5)
        
        accion_label = "MANTENER"
        precio_final = precio
        
        if elas < 1.0:
            accion_label = "SUBIR PRECIO"
            factor_subida = (1.2 - elas) * 0.25 * sensibilidad
            precio_teorico = precio * (1 + factor_subida)
            precio_final = ajustar_a_psicologico(precio_teorico)
            
            nuevo_vol = vol * (1 - (factor_subida * 0.5)) 
            ganancia = (precio_final * nuevo_vol) - (precio * vol)
            
            return (ganancia if ganancia > 0 else 0), precio_final, f"⚠️ {accion_label}"
        
        elif elas > 2.0:
            accion_label = "BAJAR PRECIO"
            precio_teorico = precio * 0.95
            precio_final = ajustar_a_psicologico(precio_teorico)
            
            return 0, precio_final, f"⬇️ {accion_label}"
            
        return 0, precio, "✅ MANTENER"

    resultados = df_temp.apply(calcular_estrategia, axis=1)
    
    df_temp['dinero_mesa'] = [x[0] for x in resultados]
    df_temp['precio_objetivo_interno'] = [x[1] for x in resultados] 
    df_temp['estado'] = [x[2] for x in resultados]
    
    df_out = df_temp.copy()
    df_out['SKU_VISUAL'] = df_temp[col_sku] if col_sku != 'sku_generado' else [f"REF-{i}" for i in range(len(df_temp))]
    df_out['PRECIO_VISUAL'] = df_temp[col_precio]
    df_out['VOLUMEN_VISUAL'] = df_temp[col_volumen]
    
    return df_out, None

# --- 4. INTERFAZ: BARRA LATERAL (CONFIGURACIÓN) ---
with st.sidebar:
    st.image("https://raw.githubusercontent.com/PaulMoraM/eunoia-branding/main/eunoia-digital-logo.png", use_container_width=True)
    st.header("🎛️ Panel de Control")
    
    modo_entrada = st.radio(
        "Origen de Datos:",
        ["🎲 Simulación (Demo)", "📋 Pegar desde Excel", "📂 Subir Archivo"]
    )
    
    st.markdown("---")
    st.subheader("⚙️ Calibración")
    sensibilidad = st.slider("Agresividad de Estrategia", 0.5, 2.0, 1.0, 0.1, help="Mayor agresividad busca márgenes más altos en productos elásticos.")
    
    st.markdown("---")
    with st.expander("Zona Admin (Solo Eunoia)"):
        modo_admin = st.checkbox("Mostrar Precios Reales", value=False)
        st.caption("Activa esto para ver la solución durante la demo.")

# --- 5. INTERFAZ: CUERPO PRINCIPAL ---
try:
    st.image("https://raw.githubusercontent.com/PaulMoraM/eunoia-branding/main/banner_redes.png", use_container_width=True)
except:
    pass

st.title("💎 Auditoría de Estrategia de Precios")
st.markdown("**Diagnóstico de Elasticidad y Captura de Valor Inmediato.**")

# --- CARGA DE DATOS ---
df_final = None 
error_msg = None
df_raw = None

if modo_entrada == "🎲 Simulación (Demo)":
    data = []
    for _ in range(400):
        costo = random.uniform(10, 100)
        data.append({
            "SKU": f"PR-{random.randint(1000,9999)}",
            "Categoria": random.choice(["Electrónica", "Hogar", "Moda", "Industrial"]),
            "Precio Venta": round(costo * random.uniform(1.2, 1.8), 2),
            "Ventas Anuales": random.randint(50, 1500)
        })
    df_raw = pd.DataFrame(data)
    df_final, error_msg = procesar_datos_pricing(df_raw, sensibilidad)

elif modo_entrada == "📋 Pegar desde Excel":
    st.info("💡 Copia las columnas (SKU, Precio, Cantidad) de tu Excel y pégalas aquí.")
    texto = st.text_area("Pegar datos (Ctrl+V):", height=150)
    if texto:
        try:
            sep = '\t' if '\t' in texto else ','
            df_raw = pd.read_csv(StringIO(texto), sep=sep)
            df_final, error_msg = procesar_datos_pricing(df_raw, sensibilidad)
        except Exception as e:
            error_msg = f"Error al leer/interpretar datos: {e}"
    else:
        df_final = None

elif modo_entrada == "📂 Subir Archivo":
    file = st.file_uploader("Sube tu archivo Excel (.xlsx) o CSV", type=['xlsx', 'csv'])
    if file:
        try:
            if file.name.endswith('csv'):
                df_raw = pd.read_csv(file)
            else:
                df_raw = pd.read_excel(file)
            df_final, error_msg = procesar_datos_pricing(df_raw, sensibilidad)
        except Exception as e:
            error_msg = f"Error leyendo archivo: {e}"
    else:
        df_final = None


# --- DASHBOARD DE RESULTADOS (VERIFICACIÓN CRÍTICA) ---

if error_msg and "❌ Error:" in error_msg:
    st.error(error_msg)
    if df_raw is not None and not df_raw.empty:
        st.warning("Diagnóstico: El problema es el nombre de las columnas. Asegúrate de que contengan estas palabras (sin tildes) en los encabezados:")
        st.markdown(f"**Encabezados detectados:** `{list(df_raw.columns)}`")
        st.markdown("Necesitas que uno contenga *precio*/*venta*/*pvp* y otro *cant*/*volumen*/*unidades*/*anuales*.")

elif df_final is not None and not df_final.empty: 
    
    # Cálculos Globales
    dinero_mesa = df_final['dinero_mesa'].sum()
    skus_afectados = df_final[df_final['estado'] != '✅ MANTENER'].shape[0]
    venta_total = (df_final['PRECIO_VISUAL'] * df_final['VOLUMEN_VISUAL']).sum()
    impacto_pct = (dinero_mesa / venta_total) * 100 if venta_total > 0 else 0
    
    st.divider()
    
    # 1. KPIs DE ALTO IMPACTO
    c1, c2, c3 = st.columns(3)
    c1.metric("Dinero 'Sobre la Mesa'", f"${dinero_mesa:,.0f}", delta="Oportunidad Anual")
    c2.metric("Productos a Optimizar", f"{skus_afectados} SKUs", delta="Requieren Intervención", delta_color="inverse")
    c3.metric("Impacto Directo EBITDA", f"+{impacto_pct:.1f}%", delta="Proyección")
    
    # 2. GRÁFICO DE DISPERSIÓN (EL MAPA DEL TESORO)
    st.subheader("📍 Mapa de Oportunidad de Precios")
    fig = px.scatter(
        df_final, 
        x="PRECIO_VISUAL",