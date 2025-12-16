# -*- coding: utf-8 -*-
"""
Created on Tue Dec 16 13:04:49 2025

@author: indu_analistanegocio
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import StringIO
import random
try:
    from faker import Faker
except ImportError:
    # Fallback simple si no está instalado faker en el servidor
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
        
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    col_precio = next((c for c in df.columns if 'precio' in c or 'pvp' in c or 'venta' in c), None)
    col_volumen = next((c for c in df.columns if 'cant' in c or 'vol' in c or 'unid' in c or 'rotacion' in c), None)
    col_sku = next((c for c in df.columns if 'sku' in c or 'prod' in c or 'cod' in c or 'ref' in c), 'sku_generado')
    
    if not col_precio or not col_volumen:
        return None, "❌ Error: No encuentro columnas de 'Precio' o 'Cantidad'. Revisa los encabezados."

    if 'elasticidad' not in df.columns:
        df['elasticidad_sim'] = np.random.uniform(0.6, 2.5, size=len(df))
    
    def calcular_estrategia(row):
        try:
            precio = float(row[col_precio])
            vol = float(row[col_volumen])
        except:
            return 0, 0, "ERROR"
            
        elas = row.get('elasticidad_sim', 1.5)
        
        if elas < 1.0:
            factor_subida = (1.2 - elas) * 0.25 * sensibilidad
            precio_teorico = precio * (1 + factor_subida)
            precio_final = ajustar_a_psicologico(precio_teorico)
            
            nuevo_vol = vol * (1 - (factor_subida * 0.5)) 
            ganancia = (precio_final * nuevo_vol) - (precio * vol)
            
            return (ganancia if ganancia > 0 else 0), precio_final, "⚠️ SUBVALUADO"
        
        return 0, precio, "✅ CORRECTO"

    resultados = df.apply(calcular_estrategia, axis=1)
    
    df['dinero_mesa'] = [x[0] for x in resultados]
    df['precio_objetivo_interno'] = [x[1] for x in resultados] 
    df['estado'] = [x[2] for x in resultados]
    
    df_out = df.copy()
    df_out['SKU_VISUAL'] = df[col_sku] if col_sku != 'sku_generado' else [f"REF-{i}" for i in range(len(df))]
    df_out['PRECIO_VISUAL'] = df[col_precio]
    df_out['VOLUMEN_VISUAL'] = df[col_volumen]
    
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
            # Captura y asigna la falla, reseteando df_final
            error_msg = f"Error al leer/interpretar datos: {e}"
            df_final = None 
    else:
        # Si el text area está vacío, no hay error, pero tampoco hay datos
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
            df_final = None
    else:
        df_final = None

# --- DASHBOARD DE RESULTADOS (VERIFICACIÓN CRÍTICA CORREGIDA) ---
# Usamos un chequeo seguro: si df_final NO es None Y no está vacío.
if df_final is not None and not df_final.empty: 
    
    # Cálculos Globales
    dinero_mesa = df_final['dinero_mesa'].sum()
    skus_afectados = df_final[df_final['estado'] == '⚠️ SUBVALUADO'].shape[0]
    venta_total = (df_final['PRECIO_VISUAL'] * df_final['VOLUMEN_VISUAL']).sum()
    impacto_pct = (dinero_mesa / venta_total) * 100 if venta_total > 0 else 0
    
    st.divider()
    
    # 1. KPIs DE ALTO IMPACTO
    c1, c2, c3 = st.columns(3)
    c1.metric("Dinero 'Sobre la Mesa'", f"${dinero_mesa:,.0f}", delta="Oportunidad Anual")
    c2.metric("Productos Mal Preciados", f"{skus_afectados} SKUs", delta="Requieren Ajuste", delta_color="inverse")
    c3.metric("Impacto Directo EBITDA", f"+{impacto_pct:.1f}%", delta="Proyección")
    
    # 2. GRÁFICO DE DISPERSIÓN (EL MAPA DEL TESORO)
    st.subheader("📍 Mapa de Oportunidad de Precios")
    fig = px.scatter(
        df_final, 
        x="PRECIO_VISUAL", 
        y="VOLUMEN_VISUAL", 
        color="estado",
        size="dinero_mesa",
        color_discrete_map={'⚠️ SUBVALUADO': '#00c853', '✅ CORRECTO': '#444'},
        hover_data=["SKU_VISUAL"],
        log_x=True, log_y=True,
        labels={"PRECIO_VISUAL": "Precio Actual ($)", "VOLUMEN_VISUAL": "Volumen de Venta"},
        height=500
    )
    fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(255,255,255,0.05)')
    st.plotly_chart(fig, use_container_width=True)
    
    # 3. LA TABLA (CENSURADA O ABIERTA SEGÚN ADMIN)
    st.subheader("🔓 Detalle de Acciones Sugeridas (Top 15)")
    
    col_tabla, col_cta = st.columns([3, 1])
    
    with col_tabla:
        df_show = df_final[df_final['estado'] == '⚠️ SUBVALUADO'].sort_values(by='dinero_mesa', ascending=False).head(15).copy()
        
        df_show['Precio Actual'] = df_show['PRECIO_VISUAL'].apply(lambda x: f"${x:,.2f}")
        df_show['Ganancia Extra'] = df_show['dinero_mesa'].apply(lambda x: f"+${x:,.2f}")
        
        # --- LÓGICA DE CENSURA ---
        if modo_admin:
            df_show['Precio Sugerido IA'] = df_show['precio_objetivo_interno'].apply(lambda x: f"${x:.2f}")
            st.success("🔓 MODO ADMIN ACTIVADO: Precios visibles.")
        else:
            df_show['Precio Sugerido IA'] = "🔒 BLOCKED"
            
        st.table(df_show[['SKU_VISUAL', 'Precio Actual', 'Precio Sugerido IA', 'Ganancia Extra']])
        
    with col_cta:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"""
            <div class="locked-box">
                <h3 style="color: #0080cd; margin:0;">Recupera tus ${dinero_mesa:,.0f}</h3>
                <p style="font-size: 0.9rem; color: #ccc; margin-top: 10px;">
                    El algoritmo ya calculó los <b>Precios Psicológicos</b> exactos (.99 / .95) para estos {skus_afectados} productos.
                </p>
                <br>
                <a href="https://wa.me/593983959867?text=Hola,%20vi%20la%20simulación%20de%20precios%20y%20quiero%20el%20reporte%20desbloqueado." target="_blank" class="cta-button">
                    SOLICITAR INFORME
                </a>
            </div>
        """, unsafe_allow_html=True)

elif error_msg:
    # Muestra el error si existe y df_final es None
    st.error(error_msg)