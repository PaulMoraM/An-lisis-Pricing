import streamlit as st
import pandas as pd

# --- 1. CONFIGURACIÓN Y ESTILOS (BASADO EN APP.PY) ---
st.set_page_config(page_title="Eunoia Pricing Audit", page_icon="💎", layout="wide")

def inyectar_estilos_premium():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
            html, body, [class*="css"] { font-family: 'Montserrat', sans-serif; background-color: #0e1117; }
            
            /* Estilo de la Tabla Eunoia */
            .eunoia-table {
                width: 100%;
                border-collapse: collapse;
                color: #e0e0e0;
                background-color: #161b22;
                border-radius: 10px;
                overflow: hidden;
            }
            .eunoia-table th {
                background-color: #0d1117;
                color: #0080cd;
                padding: 15px;
                text-align: left;
                border-bottom: 2px solid #30363d;
                vertical-align: top;
            }
            .eunoia-table td {
                padding: 12px 15px;
                border-bottom: 1px solid #30363d;
            }
            .sub-header {
                display: block;
                font-size: 0.75rem;
                color: #8b949e;
                font-weight: 400;
                margin-top: 4px;
            }
            .locked-box {
                background-color: #161b22;
                padding: 25px;
                border-radius: 12px;
                border: 1px solid #0080cd;
                text-align: center;
            }
            .btn-cta {
                background-color: #0080cd;
                color: white !important;
                padding: 12px 24px;
                border-radius: 8px;
                text-decoration: none;
                display: inline-block;
                margin-top: 15px;
                font-weight: bold;
            }
        </style>
    """, unsafe_allow_html=True)

inyectar_estilos_premium()

# --- 2. PREPARACIÓN DE DATOS (EJEMPLO) ---
# Aquí iría tu lógica de carga de archivo
data = {
    'SKU': ['PR-8204', 'PR-5569', 'PR-4361', 'PR-3103'],
    'Precio_Actual': [109.70, 121.81, 77.68, 104.68],
    'Accion': ['BAJAR PRECIO', 'SUBIR PRECIO', 'SUBIR PRECIO', 'BAJAR PRECIO'],
    'Sugerido': [104.49, 135.49, 87.49, 99.49],
    'Impacto': [4279, 534, 653, 5562]
}
df = pd.DataFrame(data)

# --- 3. INTERFAZ ---
st.title("💎 Auditoría de Estrategia de Precios")
st.sidebar.image("https://raw.githubusercontent.com/PaulMoraM/eunoia-branding/main/eunoia-digital-logo.png")
modo_admin = st.sidebar.toggle("🔓 Modo Consultor")

col_tabla, col_cta = st.columns([2.5, 1])

with col_tabla:
    # --- CONSTRUCCIÓN DE TABLA HTML (SOLUCIÓN AL ERROR DE TÍTULOS) ---
    html_tabla = f"""
    <table class="eunoia-table">
        <thead>
            <tr>
                <th>SKU</th>
                <th>Precio Actual <span class="sub-header">($ USD)</span></th>
                <th>Acción Sugerida <span class="sub-header">(Subir Precio / Bajar Precio)</span></th>
                <th>Precio Sugerido <span class="sub-header">(Psicológico .99)</span></th>
                <th>Ganancia Extra <span class="sub-header">(EBITDA Anual)</span></th>
            </tr>
        </thead>
        <tbody>
    """
    
    for _, row in df.iterrows():
        # Lógica de seguridad "Blur/Candado"
        sugerido = f"${row['Sugerido']:.2f}" if modo_admin else "🔒 BLOQUEADO"
        ganancia = f"${row['Impacto']:,}" if modo_admin else "⭐ ANALIZADO"
        color_accion = "#00c853" if "SUBIR" in row['Accion'] else "#ff4b4b"
        
        html_tabla += f"""
            <tr>
                <td>{row['SKU']}</td>
                <td>${row['Precio_Actual']:.2f}</td>
                <td style="color:{color_accion}; font-weight:700;">{row['Accion']}</td>
                <td>{sugerido}</td>
                <td style="color:#0080cd; font-weight:700;">{ganancia}</td>
            </tr>
        """
    
    html_tabla += "</tbody></table>"
    st.markdown(html_tabla, unsafe_allow_html=True)

with col_cta:
    st.markdown(f"""
        <div class="locked-box">
            <h4 style="margin:0; color:#8b949e;">Oportunidad Detectada</h4>
            <h2 style="color:white; margin:10px 0;">${df['Impacto'].sum():,}</h2>
            <p style="font-size:0.85rem; color:#ccc;">Incremento potencial de utilidad bruta mediante optimización de precios.</p>
            <hr style="border:0.5px solid #333">
            <a href="#" class="btn-cta">ADQUIRIR ANÁLISIS</a>
        </div>
    """, unsafe_allow_html=True)