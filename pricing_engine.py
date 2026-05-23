import warnings
from dataclasses import dataclass, field
from typing import Optional, Tuple
import numpy as np
import pandas as pd
import statsmodels.api as sm

warnings.filterwarnings("ignore", category=FutureWarning)

@dataclass(frozen=True)
class UmbralesElegibilidad:
    min_observaciones: int = 12
    min_precios_distintos: int = 3
    min_variacion_relativa: float = 0.05
    min_periodo_dias: int = 180
    p_value_max: float = 0.10
    r_cuadrado_min: float = 0.20

UMBRALES_DEFAULT = UmbralesElegibilidad()

@dataclass
class ResultadoSKU:
    sku: str
    elegible: bool
    razon_no_elegible: Optional[str] = None
    elasticidad: Optional[float] = None
    p_value: Optional[float] = None
    r_cuadrado: Optional[float] = None
    n_observaciones: Optional[int] = None
    precio_promedio: Optional[float] = None
    accion_sugerida: Optional[str] = None
    confianza_recomendacion: Optional[str] = None

@dataclass
class ResultadoPortafolio:
    analizables: pd.DataFrame
    no_analizables: pd.DataFrame
    resumen: dict

def validar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    columnas_req = {"sku", "fecha", "precio_unitario", "cantidad"}
    faltantes = columnas_req - set(df.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {faltantes}")
    
    df = df.copy()
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["precio_unitario"] = pd.to_numeric(df["precio_unitario"], errors="coerce")
    df["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce")
    df = df.dropna(subset=["sku", "fecha", "precio_unitario", "cantidad"])
    
    if "stock_out" not in df.columns:
        df["stock_out"] = False
    if "promocion" not in df.columns:
        df["promocion"] = False
        
    return df[(df["precio_unitario"] > 0) & (df["cantidad"] > 0)]

def evaluar_elegibilidad(df_sku: pd.DataFrame, umbrales: UmbralesElegibilidad) -> Tuple[bool, Optional[str]]:
    df_limpio = df_sku[~df_sku["stock_out"] & ~df_sku["promocion"]]
    
    if len(df_limpio) < umbrales.min_observaciones:
        return False, f"Solo {len(df_limpio)} observaciones útiles."
    if df_limpio["precio_unitario"].nunique() < umbrales.min_precios_distintos:
        return False, "Niveles de precio distintos insuficientes."
    
    p_min = df_limpio["precio_unitario"].min()
    variacion = (df_limpio["precio_unitario"].max() - p_min) / p_min if p_min > 0 else 0
    if variacion < umbrales.min_variacion_relativa:
        return False, "Variación de precio insuficiente."
        
    return True, None

def recomendar_accion(beta: float, p_value: float) -> Tuple[str, str]:
    confianza = "Alta" if p_value < 0.05 else "Media"
    if beta > -1:
        accion = "SUBIR PRECIO (demanda inelástica)"
    elif beta < -1.5:
        accion = "MANTENER O BAJAR (demanda elástica)"
    else:
        accion = "MANTENER Y A/B TESTEAR (zona neutral)"
    return accion, confianza

def estimar_elasticidad_sku(df_sku: pd.DataFrame, sku: str, umbrales: UmbralesElegibilidad) -> ResultadoSKU:
    df = df_sku[~df_sku["stock_out"] & ~df_sku["promocion"]].copy()
    
    if df.empty:
        return ResultadoSKU(sku=sku, elegible=False, razon_no_elegible="Sin observaciones válidas.")
        
    df["periodo"] = df["fecha"].dt.to_period("M")
    agg = df.groupby("periodo").agg(
        precio_unitario=("precio_unitario", "mean"),
        cantidad=("cantidad", "sum"),
    ).reset_index()
    
    if len(agg) < umbrales.min_observaciones:
        return ResultadoSKU(sku=sku, elegible=False, razon_no_elegible="Insuficientes períodos tras agregación.")

    agg["ln_P"] = np.log(agg["precio_unitario"])
    agg["ln_Q"] = np.log(agg["cantidad"])
    
    X = sm.add_constant(agg[["ln_P"]])
    y = agg["ln_Q"]
    
    try:
        modelo = sm.OLS(y, X, missing="drop").fit()
    except Exception as exc:
        return ResultadoSKU(sku=sku, elegible=False, razon_no_elegible=f"Error estimación: {exc}")

    beta = modelo.params.get("ln_P")
    p_value = modelo.pvalues.get("ln_P")
    r2 = modelo.rsquared

    if beta is None or np.isnan(beta):
        return ResultadoSKU(sku=sku, elegible=False, razon_no_elegible="Colinealidad o fallo de estimación.")

    if p_value > umbrales.p_value_max or r2 < umbrales.r_cuadrado_min:
        return ResultadoSKU(sku=sku, elegible=False, razon_no_elegible="No cumple significancia estadística o R2.")

    accion, confianza = recomendar_accion(beta, p_value)

    return ResultadoSKU(
        sku=sku, elegible=True, elasticidad=beta, p_value=p_value,
        r_cuadrado=r2, n_observaciones=len(agg),
        precio_promedio=float(agg["precio_unitario"].mean()),
        accion_sugerida=accion, confianza_recomendacion=confianza
    )

def analizar_portafolio(df: pd.DataFrame) -> ResultadoPortafolio:
    df = validar_dataframe(df)
    resultados = []
    
    for sku in df["sku"].unique():
        df_sku = df[df["sku"] == sku]
        elegible, razon = evaluar_elegibilidad(df_sku, UMBRALES_DEFAULT)
        
        if not elegible:
            resultados.append(ResultadoSKU(sku=sku, elegible=False, razon_no_elegible=razon))
            continue
            
        resultados.append(estimar_elasticidad_sku(df_sku, sku, UMBRALES_DEFAULT))

    analizables = [r for r in resultados if r.elegible]
    no_analizables = [r for r in resultados if not r.elegible]

    df_analizables = pd.DataFrame([r.__dict__ for r in analizables])
    df_no_analizables = pd.DataFrame([{"sku": r.sku, "razon": r.razon_no_elegible} for r in no_analizables])

    n_total = len(resultados)
    n_analizables = len(analizables)

    resumen = {
        "skus_totales": n_total,
        "skus_analizables": n_analizables,
        "cobertura_pct": round(100 * n_analizables / n_total, 1) if n_total else 0.0,
    }

    if n_analizables > 0:
        resumen["skus_inelasticos"] = int((df_analizables["elasticidad"] > -1).sum())
        resumen["skus_elasticos"] = int((df_analizables["elasticidad"] < -1.5).sum())

    return ResultadoPortafolio(analizables=df_analizables, no_analizables=df_no_analizables, resumen=resumen)