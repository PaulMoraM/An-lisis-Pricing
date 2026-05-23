"""
app_pricing.py
==============
Lead magnet web de Eunoia Digital — Sentinel V2 (Pricing Audit).

Single Source of Truth: el motor pricing_engine se ejecuta SIEMPRE,
tanto en demo (sobre datos sintéticos) como con archivo del cliente.
NO existen bypass, ni profits inventados, ni np.random fuera del sintético.

Versión híbrida del demo:
  - Total monetario se muestra como RANGO ($XXk - $YYk), no cifra exacta.
  - Detalle por SKU bloqueado tras el paywall.
  - Acción específica oculta en demo (solo "Identificado").

Autor: Eunoia Digital
Versión: 2.0 (mayo 2026)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
from typing import Optional

from pricing_engine import analizar_portafolio, ResultadoPortafolio
from synthetic_data import generar_dataset_pyme


# ---------------------------------------------------------------------------
# CONFIGURACIÓN GLOBAL
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Eunoia Pricing Audit",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Plotly default template una sola vez (optimización)
pio.templates.default = "plotly_dark"

URL_LOGO = "https://raw.githubusercontent.com/PaulMoraM/eunoia-branding/main/eunoia-digital-logo.png"
URL_BANNER = "https://raw.githubusercontent.com/PaulMoraM/eunoia-branding/main/banner_redes.png"
URL_CALENDLY = "https://calendly.com/paul-eunoia-data/30min"


# ---------------------------------------------------------------------------
# ESTILOS
# ---------------------------------------------------------------------------

def inyectar_estilos() -> None:
    """Tipografía Montserrat + paleta corporativa Eunoia."""
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;700&display=swap');
            html, body, [class*="css"] { font-family: 'Montserrat', sans-serif; background-color: #0e1117; }

            .logo-container {
                background-color: white; padding: 20px; border-radius: 12px;
                margin-bottom: 25px; text-align: center; display: block;
            }
            .logo-container img { max-width: 100%; height: auto; display: block; margin: 0 auto; }

            [data-testid="stMetricValue"] { color: #0080cd; font-size: 2.2rem; font-weight: 700; }

            .locked-box {
                background-color: #161b22; padding: 25px; border-radius: 12px;
                border: 1px solid #0080cd; text-align: center;
                box-shadow: 0 4px 12px rgba(0, 128, 205, 0.15);
                margin-top: 15px;
            }
            .btn-cta {
                display: inline-block; background-color: #0080cd; color: white !important;
                padding: 12px 24px; font-weight: 700; border-radius: 6px;
                text-decoration: none; margin-top: 15px; transition: background 0.3s;
            }
            .btn-cta:hover { background-color: #0066a3; }

            .metodologia-nota {
                background-color: #0e1f30; padding: 12px 16px; border-radius: 8px;
                border-left: 3px solid #0080cd; font-size: 0.85rem; color: #c0c8d0;
                margin-top: 10px;
            }
        </style>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# CARGA Y VALIDACIÓN DE ARCHIVO
# ---------------------------------------------------------------------------

def cargar_archivo_cliente(archivo) -> Optional[pd.DataFrame]:
    """Lee CSV o XLSX y valida schema mínimo antes de pasar al motor."""
    try:
        if archivo.name.endswith('.csv'):
            df = pd.read_csv(archivo)
        elif archivo.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(archivo)
        else:
            st.error("Formato de archivo no reconocido. Use CSV o Excel.")
            return None
    except Exception as exc:
        st.error(f"Error al leer el archivo: {exc}")
        return None

    columnas_req = {"sku", "fecha", "precio_unitario", "cantidad"}
    faltantes = columnas_req - set(df.columns)
    if faltantes:
        st.error(
            f"⚠️ Faltan columnas requeridas: {sorted(faltantes)}. "
            "Use la plantilla oficial Eunoia o asegúrese de tener las columnas: "
            "sku, fecha, precio_unitario, cantidad."
        )
        return None

    return df


# ---------------------------------------------------------------------------
# ANÁLISIS CACHEADO
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Ejecutando análisis econométrico...")
def ejecutar_analisis_cached(df: pd.DataFrame, cache_key: str) -> ResultadoPortafolio:
    """Wrapper cacheado del motor. cache_key permite invalidar cuando cambia el archivo."""
    return analizar_portafolio(df)


@st.cache_data(show_spinner="Generando dataset demo...")
def generar_demo_cached() -> pd.DataFrame:
    """Sintético cacheado para demo."""
    return generar_dataset_pyme(n_skus=600)


# ---------------------------------------------------------------------------
# CÁLCULO DE OPORTUNIDAD COMO RANGO (HÍBRIDO)
# ---------------------------------------------------------------------------

def calcular_rango_oportunidad(
    resultado: ResultadoPortafolio, es_demo: bool
) -> tuple[float, float, int]:
    """Calcula un RANGO de oportunidad de captura de margen.

    Versión híbrida: NO muestra cifra exacta, muestra rango basado en
    elasticidades reales calculadas y volumen observado.

    Retorna (limite_inferior, limite_superior, n_skus_optimizables).
    """
    if resultado.analizables.empty:
        return (0.0, 0.0, 0)

    df = resultado.analizables.copy()

    # Solo SKU candidatos a SUBIR PRECIO (inelásticos) generan oportunidad clara
    mask_subir = df["accion_sugerida"].str.contains("SUBIR", na=False)
    df_subir = df[mask_subir]

    if df_subir.empty:
        return (0.0, 0.0, 0)

    # Modelo: shock conservador (+5%) vs agresivo (+10%)
    # Q2 = Q1 * (P2/P1)^β
    # Margen ganado = (P2 - costo) * Q2 - (P1 - costo) * Q1
    # En demo no tenemos costo real → asumimos margen base 35% (rango típico LatAm)
    # NOTA: en producción con archivo real con columna costo_unitario, usar el real

    margen_estimado_pct = 0.35
    volumen_anual = df_subir["cantidad_promedio"] * 12

    # Escenario conservador: shock +5%
    factor_5 = (1.05) ** df_subir["elasticidad"]
    margen_actual_5 = df_subir["precio_promedio"] * margen_estimado_pct * volumen_anual
    margen_nuevo_5 = (df_subir["precio_promedio"] * 1.05 - df_subir["precio_promedio"] * (1 - margen_estimado_pct)) * (volumen_anual * factor_5)
    profit_5 = (margen_nuevo_5 - margen_actual_5).clip(lower=0).sum()

    # Escenario agresivo: shock +10%
    factor_10 = (1.10) ** df_subir["elasticidad"]
    margen_actual_10 = df_subir["precio_promedio"] * margen_estimado_pct * volumen_anual
    margen_nuevo_10 = (df_subir["precio_promedio"] * 1.10 - df_subir["precio_promedio"] * (1 - margen_estimado_pct)) * (volumen_anual * factor_10)
    profit_10 = (margen_nuevo_10 - margen_actual_10).clip(lower=0).sum()

    # Rango: el menor como inferior, el mayor como superior
    limite_inf = min(profit_5, profit_10)
    limite_sup = max(profit_5, profit_10)

    # Suavizar el rango a múltiplos de $5K para presentación
    limite_inf_redondeado = max(0, np.floor(limite_inf / 5000) * 5000)
    limite_sup_redondeado = np.ceil(limite_sup / 5000) * 5000

    return (float(limite_inf_redondeado), float(limite_sup_redondeado), int(len(df_subir)))


# ---------------------------------------------------------------------------
# RENDERIZADO PRINCIPAL
# ---------------------------------------------------------------------------

def main() -> None:
    inyectar_estilos()

    # Sidebar
    with st.sidebar:
        st.markdown(f"""
            <div class="logo-container">
                <img src="{URL_LOGO}">
            </div>
        """, unsafe_allow_html=True)

        st.markdown("### 📊 Control de Ingesta")
        archivo_subido = st.file_uploader(
            "Sube tu histórico transaccional (.csv, .xlsx)",
            type=["csv", "xlsx"],
            help="Columnas requeridas: sku, fecha, precio_unitario, cantidad. Opcionales: costo_unitario, stock_out, promocion, categoria."
        )

        st.markdown("---")
        st.markdown(
            "<div class='metodologia-nota'>"
            "<strong>Metodología:</strong> Regresión OLS log-log con controles "
            "estacionales mensuales. Diagnósticos completos por SKU. "
            "Los SKU sin datos suficientes se etiquetan, no se inventan."
            "</div>",
            unsafe_allow_html=True,
        )

    # Banner
    st.image(URL_BANNER, use_container_width=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.title("Sentinel | Auditoría de Pricing")
    st.markdown("### Diagnóstico de Elasticidad-Precio y Recuperación de Margen")
    st.markdown("---")

    # Determinar fuente de datos
    if archivo_subido is not None:
        df_raw = cargar_archivo_cliente(archivo_subido)
        if df_raw is None:
            st.stop()
        es_demo = False
        cache_key = f"cliente_{archivo_subido.name}_{archivo_subido.size}"
        st.success(f"✅ Archivo cargado: {archivo_subido.name} ({len(df_raw):,} filas)")
    else:
        st.info(
            "🟢 **Modo Demo** — Mostrando análisis sobre dataset sintético de 600 SKU "
            "representativo de una PYME LatAm. Suba su propio archivo para análisis real."
        )
        df_raw = generar_demo_cached()
        es_demo = True
        cache_key = "demo_default"

    # Ejecutar motor (SIEMPRE, sin bypass)
    try:
        resultado = ejecutar_analisis_cached(df_raw, cache_key)
    except ValueError as exc:
        st.error(f"⚠️ Error en validación de datos: {exc}")
        st.stop()
    except Exception as exc:
        st.error(f"⚠️ Error inesperado en el análisis: {exc}")
        st.stop()

    # ----- KPIs honestos -----
    resumen = resultado.resumen

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("SKUs Totales", f"{resumen['skus_totales']:,}")
    c2.metric("SKUs Analizables", f"{resumen['skus_analizables']:,}")
    c3.metric("Cobertura del Portafolio", f"{resumen['cobertura_pct']:.1f}%")

    inelasticos = resumen.get("skus_inelasticos", 0)
    c4.metric("Candidatos a Optimización", f"{inelasticos:,}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ----- Alerta de cobertura -----
    if resumen["cobertura_pct"] < 25:
        st.warning(
            f"📌 **Cobertura del portafolio: {resumen['cobertura_pct']:.1f}%.** "
            f"Solo {resumen['skus_analizables']} de {resumen['skus_totales']} SKU "
            "tienen suficiente variación histórica de precio para análisis econométrico. "
            "Los restantes requieren piloto controlado de A/B testing de precios. "
            "Esto es normal en PYME — la mayoría de los SKU mantienen precio fijo."
        )

    # ----- Gráfico de distribución de elasticidades (analizables solamente) -----
    if not resultado.analizables.empty:
        st.subheader("📊 Distribución de Elasticidad-Precio del Portafolio Analizable")

        df_plot = resultado.analizables.copy()
        df_plot["zona"] = pd.cut(
            df_plot["elasticidad"],
            bins=[-np.inf, -1.5, -1.0, 0],
            labels=["Elástico (β < -1.5)", "Zona neutral (-1.5 a -1)", "Inelástico (β > -1)"],
        )

        fig = px.histogram(
            df_plot,
            x="elasticidad",
            color="zona",
            nbins=30,
            title="Histograma de elasticidades estimadas (solo SKU analizables)",
            color_discrete_map={
                "Elástico (β < -1.5)": "#ff4b4b",
                "Zona neutral (-1.5 a -1)": "#ffab00",
                "Inelástico (β > -1)": "#00c853",
            },
            labels={"elasticidad": "Elasticidad estimada (β)", "count": "Número de SKU"},
        )
        fig.update_layout(font_family="Montserrat", showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ----- DETALLE BLOQUEADO + CTA HÍBRIDO -----
    col_t, col_c = st.columns([2.5, 1])

    with col_t:
        st.subheader("🔓 Detalle por SKU")
        st.warning(
            "🔒 El detalle por SKU (elasticidades específicas, precios sugeridos, "
            "intervalos de confianza, magnitud del impacto financiero) se entrega "
            "como parte del **Diagnostic Sprint** ($1,497, 5 días, garantía 3x). "
            "Aquí solo se muestra el conteo agregado por categoría."
        )

        if not resultado.analizables.empty:
            # Vista censurada: solo categorías agregadas, sin SKU específicos
            df_vista = resultado.analizables.copy()
            df_vista["categoria_elasticidad"] = pd.cut(
                df_vista["elasticidad"],
                bins=[-np.inf, -1.5, -1.0, 0],
                labels=["Demanda elástica (mantener o bajar)", "Zona neutral (A/B testear)", "Demanda inelástica (subir precio)"],
            )

            tabla_agregada = (
                df_vista.groupby("categoria_elasticidad", observed=True)
                .agg(
                    cantidad_skus=("sku", "count"),
                    elasticidad_promedio=("elasticidad", "mean"),
                    confianza_modal=("confianza_recomendacion", lambda x: x.mode().iloc[0] if not x.empty else "—"),
                )
                .reset_index()
            )
            tabla_agregada["elasticidad_promedio"] = tabla_agregada["elasticidad_promedio"].round(2)

            st.dataframe(
                tabla_agregada.rename(columns={
                    "categoria_elasticidad": "Categoría",
                    "cantidad_skus": "SKU",
                    "elasticidad_promedio": "β promedio",
                    "confianza_modal": "Confianza típica",
                }),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No hay SKU analizables en este portafolio. Se recomienda piloto controlado.")

    with col_c:
        # Rango híbrido (no cifra exacta)
        limite_inf, limite_sup, n_optimizables = calcular_rango_oportunidad(resultado, es_demo)

        if n_optimizables > 0:
            st.markdown(f"""
                <div class="locked-box">
                    <h3 style="color: white; margin:0; font-family:'Montserrat'; font-weight:400; font-size:1.1rem;">
                        Oportunidad de Captura Anual Estimada
                    </h3>
                    <h2 style="color: #0080cd; margin: 10px 0; font-size: 1.8rem; font-weight: 700;">
                        ${limite_inf/1000:,.0f}K — ${limite_sup/1000:,.0f}K
                    </h2>
                    <p style="font-size: 0.8rem; color: #8a99ad; line-height: 1.4; font-family:'Montserrat';">
                        Rango estimado sobre {n_optimizables} SKU candidatos a optimización
                        de precio en demanda inelástica.
                        Cifra precisa requiere estructura de costos del cliente.
                    </p>
                    <p style="color: #ffffff; font-size: 0.8rem; font-weight: 700; margin-top: 10px; font-family:'Montserrat';">
                        Garantía de Retorno 3x — Diagnostic Sprint
                    </p>
                    <a href="{URL_CALENDLY}" target="_blank" class="btn-cta">Agendar Diagnostic Sprint</a>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="locked-box">
                    <h3 style="color: white; margin:0; font-family:'Montserrat'; font-weight:400; font-size:1.1rem;">
                        Diagnóstico de Portafolio Completo
                    </h3>
                    <p style="font-size: 0.85rem; color: #c0c8d0; line-height: 1.4; font-family:'Montserrat';">
                        Identificamos su estructura de elasticidades y recomendamos
                        diseño de piloto controlado para los SKU sin variación histórica.
                    </p>
                    <a href="{URL_CALENDLY}" target="_blank" class="btn-cta">Agendar Diagnostic Sprint</a>
                </div>
            """, unsafe_allow_html=True)

    # ----- Nota metodológica al pie -----
    st.markdown("---")
    with st.expander("📖 Metodología y limitaciones"):
        meta = resultado.metodologia
        st.markdown(f"**Modelo:** {meta['modelo']}")
        st.markdown("**Controles aplicados:**")
        for c in meta["controles_aplicados"]:
            st.markdown(f"- {c}")
        st.markdown("**Diagnósticos calculados:**")
        for d in meta["diagnosticos_calculados"]:
            st.markdown(f"- {d}")
        st.markdown("**Limitaciones conocidas:**")
        for l in meta["limitaciones_conocidas"]:
            st.markdown(f"- {l}")


if __name__ == "__main__":
    main()
