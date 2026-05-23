"""
pricing_engine.py
=================
Motor de elasticidad-precio para Eunoia Digital — Sentinel V2.

Single Source of Truth (SSoT) econométrica:
  - Regresión OLS log-log con controles estacionales mensuales.
  - Filtros de elegibilidad por SKU (datos insuficientes se etiquetan, no se inventan).
  - Diagnósticos: R², p-value, Durbin-Watson, Breusch-Pagan, intervalo confianza 95%.
  - Recomendación de acción solo cuando significancia estadística lo permite.

NO contiene datos aleatorios, simulaciones, ni números fabricados.
Cualquier output sin elegibilidad estadística se marca explícitamente.

Autor: Eunoia Digital
Versión: 2.0 (mayo 2026)
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.stattools import durbin_watson

warnings.filterwarnings("ignore", category=FutureWarning)


# ---------------------------------------------------------------------------
# UMBRALES DE ELEGIBILIDAD
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class UmbralesElegibilidad:
    """Umbrales mínimos para que un SKU sea analizable."""

    min_observaciones: int = 12
    min_precios_distintos: int = 3
    min_variacion_relativa: float = 0.05
    min_periodo_dias: int = 180
    p_value_max: float = 0.10
    r_cuadrado_min: float = 0.20


UMBRALES_DEFAULT = UmbralesElegibilidad()


# ---------------------------------------------------------------------------
# ESTRUCTURAS DE RESULTADO
# ---------------------------------------------------------------------------

@dataclass
class ResultadoSKU:
    """Resultado de análisis de un SKU individual."""

    sku: str
    elegible: bool
    razon_no_elegible: Optional[str] = None

    # Solo si elegible
    elasticidad: Optional[float] = None
    elasticidad_ic_inferior: Optional[float] = None
    elasticidad_ic_superior: Optional[float] = None
    p_value: Optional[float] = None
    r_cuadrado: Optional[float] = None
    n_observaciones: Optional[int] = None
    precio_promedio: Optional[float] = None
    cantidad_promedio: Optional[float] = None
    precio_min_observado: Optional[float] = None
    precio_max_observado: Optional[float] = None
    durbin_watson: Optional[float] = None
    breusch_pagan_pvalue: Optional[float] = None

    accion_sugerida: Optional[str] = None
    confianza_recomendacion: Optional[str] = None


@dataclass
class ResultadoPortafolio:
    """Resultado agregado del análisis de un portafolio."""

    analizables: pd.DataFrame
    no_analizables: pd.DataFrame
    resumen: dict
    metodologia: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# VALIDACIÓN DE INPUT
# ---------------------------------------------------------------------------

COLUMNAS_REQUERIDAS = {"sku", "fecha", "precio_unitario", "cantidad"}
COLUMNAS_OPCIONALES = {"costo_unitario", "stock_out", "promocion", "categoria"}


def validar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Valida y normaliza el DataFrame de transacciones."""

    faltantes = COLUMNAS_REQUERIDAS - set(df.columns)
    if faltantes:
        raise ValueError(
            f"Faltan columnas requeridas: {sorted(faltantes)}. "
            f"Columnas mínimas: {sorted(COLUMNAS_REQUERIDAS)}. "
            f"Recomendadas adicionales: {sorted(COLUMNAS_OPCIONALES)}."
        )

    df = df.copy()
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["precio_unitario"] = pd.to_numeric(df["precio_unitario"], errors="coerce")
    df["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce")

    df = df.dropna(subset=["sku", "fecha", "precio_unitario", "cantidad"])
    df = df[(df["precio_unitario"] > 0) & (df["cantidad"] > 0)]

    if "stock_out" not in df.columns:
        df["stock_out"] = False
    if "promocion" not in df.columns:
        df["promocion"] = False

    df["stock_out"] = df["stock_out"].astype(bool)
    df["promocion"] = df["promocion"].astype(bool)

    return df


# ---------------------------------------------------------------------------
# FILTRO DE ELEGIBILIDAD
# ---------------------------------------------------------------------------

def evaluar_elegibilidad(
    df_sku: pd.DataFrame, umbrales: UmbralesElegibilidad
) -> tuple[bool, Optional[str]]:
    """Pre-filtro de un SKU antes de intentar regresión."""

    df_limpio = df_sku[~df_sku["stock_out"] & ~df_sku["promocion"]]

    if len(df_limpio) < umbrales.min_observaciones:
        return (
            False,
            f"Solo {len(df_limpio)} observaciones útiles (mínimo {umbrales.min_observaciones}).",
        )

    precios_distintos = df_limpio["precio_unitario"].nunique()
    if precios_distintos < umbrales.min_precios_distintos:
        return (
            False,
            f"Solo {precios_distintos} niveles de precio distintos (mínimo {umbrales.min_precios_distintos}).",
        )

    p_min = df_limpio["precio_unitario"].min()
    p_max = df_limpio["precio_unitario"].max()
    variacion = (p_max - p_min) / p_min if p_min > 0 else 0
    if variacion < umbrales.min_variacion_relativa:
        return (
            False,
            f"Variación de precio insuficiente ({variacion:.1%}, mínimo {umbrales.min_variacion_relativa:.1%}).",
        )

    periodo_dias = (df_limpio["fecha"].max() - df_limpio["fecha"].min()).days
    if periodo_dias < umbrales.min_periodo_dias:
        return (
            False,
            f"Período cubierto insuficiente ({periodo_dias} días, mínimo {umbrales.min_periodo_dias}).",
        )

    return True, None


# ---------------------------------------------------------------------------
# REGRESIÓN LOG-LOG CON CONTROLES
# ---------------------------------------------------------------------------

def estimar_elasticidad_sku(
    df_sku: pd.DataFrame, sku: str, umbrales: UmbralesElegibilidad
) -> ResultadoSKU:
    """Estima elasticidad-precio vía regresión log-log con controles estacionales.

    Modelo: ln(Q_t) = α + β·ln(P_t) + γ·D_mes_t + ε_t
    """

    df = df_sku[~df_sku["stock_out"] & ~df_sku["promocion"]].copy()

    if df.empty:
        return ResultadoSKU(
            sku=sku, elegible=False, razon_no_elegible="Sin observaciones útiles."
        )

    # Agregación temporal según extensión del histórico
    rango_dias = (df["fecha"].max() - df["fecha"].min()).days
    if rango_dias > 730:
        df["periodo"] = df["fecha"].dt.to_period("W")
    else:
        df["periodo"] = df["fecha"].dt.to_period("M")

    agg = (
        df.groupby("periodo")
        .agg(
            precio_unitario=("precio_unitario", "mean"),
            cantidad=("cantidad", "sum"),
        )
        .reset_index()
    )

    if len(agg) < umbrales.min_observaciones:
        return ResultadoSKU(
            sku=sku,
            elegible=False,
            razon_no_elegible=f"Tras agregación temporal: {len(agg)} períodos (mínimo {umbrales.min_observaciones}).",
        )

    agg["ln_P"] = np.log(agg["precio_unitario"])
    agg["ln_Q"] = np.log(agg["cantidad"])

    # Dummies estacionales mensuales (base = enero)
    agg["mes"] = agg["periodo"].dt.month
    dummies_mes = pd.get_dummies(agg["mes"], prefix="mes", drop_first=True).astype(float)

    X = pd.concat([agg[["ln_P"]], dummies_mes], axis=1)
    X = sm.add_constant(X)
    y = agg["ln_Q"]

    try:
        modelo = sm.OLS(y, X, missing="drop").fit()
    except Exception as exc:
        return ResultadoSKU(
            sku=sku, elegible=False, razon_no_elegible=f"Error de estimación: {exc}"
        )

    beta = modelo.params.get("ln_P")
    p_value = modelo.pvalues.get("ln_P")
    r2 = modelo.rsquared

    if beta is None or np.isnan(beta):
        return ResultadoSKU(
            sku=sku,
            elegible=False,
            razon_no_elegible="Coeficiente no estimable (colinealidad).",
        )

    dw = durbin_watson(modelo.resid)
    try:
        _, bp_pvalue, _, _ = het_breuschpagan(modelo.resid, modelo.model.exog)
    except Exception:
        bp_pvalue = np.nan

    ic = modelo.conf_int(alpha=0.05).loc["ln_P"]
    ic_inf, ic_sup = float(ic.iloc[0]), float(ic.iloc[1])

    # Validaciones finales
    if p_value > umbrales.p_value_max:
        return ResultadoSKU(
            sku=sku,
            elegible=False,
            razon_no_elegible=f"Coeficiente no significativo (p={p_value:.3f}, máximo {umbrales.p_value_max}).",
            elasticidad=float(beta),
            p_value=float(p_value),
            r_cuadrado=float(r2),
            n_observaciones=len(agg),
        )

    if r2 < umbrales.r_cuadrado_min:
        return ResultadoSKU(
            sku=sku,
            elegible=False,
            razon_no_elegible=f"R² insuficiente ({r2:.2f}, mínimo {umbrales.r_cuadrado_min}).",
            elasticidad=float(beta),
            p_value=float(p_value),
            r_cuadrado=float(r2),
            n_observaciones=len(agg),
        )

    accion, confianza = recomendar_accion(float(beta), ic_inf, ic_sup)

    return ResultadoSKU(
        sku=sku,
        elegible=True,
        elasticidad=float(beta),
        elasticidad_ic_inferior=ic_inf,
        elasticidad_ic_superior=ic_sup,
        p_value=float(p_value),
        r_cuadrado=float(r2),
        n_observaciones=len(agg),
        precio_promedio=float(agg["precio_unitario"].mean()),
        cantidad_promedio=float(agg["cantidad"].mean()),
        precio_min_observado=float(agg["precio_unitario"].min()),
        precio_max_observado=float(agg["precio_unitario"].max()),
        durbin_watson=float(dw),
        breusch_pagan_pvalue=float(bp_pvalue) if not np.isnan(bp_pvalue) else None,
        accion_sugerida=accion,
        confianza_recomendacion=confianza,
    )


def recomendar_accion(
    beta: float, ic_inf: float, ic_sup: float
) -> tuple[str, str]:
    """Recomendación honesta basada en magnitud y confianza."""

    ancho_ic = abs(ic_sup - ic_inf)

    if ancho_ic > 1.5:
        confianza = "Baja (IC muy ancho)"
    elif (ic_inf < -1 < ic_sup) and ancho_ic > 0.5:
        confianza = "Media"
    else:
        confianza = "Alta"

    if beta > -1:
        accion = "SUBIR PRECIO (demanda inelástica)"
    elif beta < -1.5:
        accion = "MANTENER O BAJAR (demanda elástica)"
    else:
        accion = "MANTENER Y A/B TESTEAR (zona neutral)"

    return accion, confianza


# ---------------------------------------------------------------------------
# FUNCIÓN PRINCIPAL
# ---------------------------------------------------------------------------

def analizar_portafolio(
    df: pd.DataFrame, umbrales: UmbralesElegibilidad = UMBRALES_DEFAULT
) -> ResultadoPortafolio:
    """Analiza un portafolio completo. Separa analizables de no analizables."""

    df = validar_dataframe(df)
    resultados: list[ResultadoSKU] = []

    for sku in df["sku"].unique():
        df_sku = df[df["sku"] == sku]

        elegible, razon = evaluar_elegibilidad(df_sku, umbrales)
        if not elegible:
            resultados.append(
                ResultadoSKU(sku=sku, elegible=False, razon_no_elegible=razon)
            )
            continue

        resultados.append(estimar_elasticidad_sku(df_sku, sku, umbrales))

    analizables = [r for r in resultados if r.elegible]
    no_analizables = [r for r in resultados if not r.elegible]

    df_analizables = pd.DataFrame([r.__dict__ for r in analizables])
    df_no_analizables = pd.DataFrame(
        [{"sku": r.sku, "razon": r.razon_no_elegible} for r in no_analizables]
    )

    n_total = len(resultados)
    n_analizables = len(analizables)

    resumen = {
        "skus_totales": int(n_total),
        "skus_analizables": int(n_analizables),
        "skus_no_analizables": int(n_total - n_analizables),
        "cobertura_pct": float(round(100 * n_analizables / n_total, 1)) if n_total else 0.0,
    }

    if n_analizables > 0:
        resumen["elasticidad_mediana"] = float(round(df_analizables["elasticidad"].median(), 3))
        resumen["skus_inelasticos"] = int((df_analizables["elasticidad"] > -1).sum())
        resumen["skus_elasticos"] = int((df_analizables["elasticidad"] < -1.5).sum())
        resumen["skus_zona_neutral"] = int(
            ((df_analizables["elasticidad"] >= -1.5) & (df_analizables["elasticidad"] <= -1)).sum()
        )

    metodologia = {
        "modelo": "Regresión log-log OLS con dummies estacionales mensuales",
        "umbrales_elegibilidad": umbrales.__dict__,
        "controles_aplicados": [
            "Exclusión de períodos con stock-out marcado",
            "Exclusión de períodos con promoción activa",
            "Dummies estacionales mensuales (base = enero)",
            "Agregación temporal semanal (>2 años) o mensual (<=2 años)",
        ],
        "diagnosticos_calculados": [
            "R² (varianza explicada)",
            "p-value del coeficiente de elasticidad",
            "Durbin-Watson (autocorrelación residuos)",
            "Breusch-Pagan (heteroscedasticidad)",
            "Intervalo de confianza al 95% para β",
        ],
        "limitaciones_conocidas": [
            "Asume estabilidad estructural en el período analizado",
            "No corrige por endogeneidad simultánea (oferta-demanda)",
            "No incorpora elasticidades cruzadas entre SKU",
            "Sensible a outliers no marcados como stock-out o promoción",
            "Extrapolación fuera del rango histórico observado requiere piloto controlado",
        ],
    }

    return ResultadoPortafolio(
        analizables=df_analizables,
        no_analizables=df_no_analizables,
        resumen=resumen,
        metodologia=metodologia,
    )
