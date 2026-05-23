"""
synthetic_data.py
=================
Generador de dataset sintético realista para PYME LatAm.

Propiedades del dataset generado:
  - 600 SKU (PYME promedio)
  - ~70% sin variación de precio significativa (realidad PYME)
  - ~20% con variación moderada (analizables marginalmente)
  - ~10% con alta variación (claramente analizables)
  - Estacionalidad mensual sintética
  - Stock-outs aleatorios pero plausibles
  - Promociones esporádicas
  - Ruido log-normal en demanda
  - Elasticidad verdadera (β real) varía por categoría:
      * Commodities/básicos: β ≈ -1.8 (elásticos)
      * Diferenciados/marca: β ≈ -0.7 (inelásticos)
      * Premium/aspiracionales: β ≈ -1.2 (zona neutral)

NO se basa en datos confidenciales de ningún cliente real.
Sólo testing y demo del motor econométrico.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd


CATEGORIAS = {
    "COMMODITY": {"beta_real": -1.8, "precio_base_rango": (5, 30)},
    "DIFERENCIADO": {"beta_real": -0.7, "precio_base_rango": (30, 150)},
    "PREMIUM": {"beta_real": -1.2, "precio_base_rango": (100, 500)},
}


def generar_dataset_pyme(
    n_skus: int = 600,
    fecha_inicio: date = date(2023, 1, 1),
    fecha_fin: date = date(2025, 12, 31),
    seed: int = 42,
) -> pd.DataFrame:
    """Genera dataset transaccional sintético para una PYME LatAm.

    Estructura: una fila por (SKU, mes).
    Columnas: sku, fecha, precio_unitario, cantidad, costo_unitario,
              stock_out, promocion, categoria
    """

    rng = np.random.default_rng(seed)

    # Distribución 70/20/10 realista PYME
    n_sin_var = int(0.70 * n_skus)
    n_var_moderada = int(0.20 * n_skus)
    n_alta_var = n_skus - n_sin_var - n_var_moderada
    proporciones = {
        "sin_variacion": n_sin_var,
        "variacion_moderada": n_var_moderada,
        "alta_variacion": n_alta_var,
    }

    transacciones = []
    sku_id = 1

    for tipo_variacion, cantidad_skus in proporciones.items():
        for _ in range(cantidad_skus):
            categoria = rng.choice(list(CATEGORIAS.keys()), p=[0.35, 0.45, 0.20])
            config = CATEGORIAS[categoria]

            sku = f"SKU-{sku_id:04d}"
            sku_id += 1

            precio_base = rng.uniform(*config["precio_base_rango"])
            costo_base = precio_base * rng.uniform(0.55, 0.75)
            beta_real = config["beta_real"] + rng.normal(0, 0.15)

            cantidad_base = rng.uniform(50, 500)

            dias_total = (fecha_fin - fecha_inicio).days
            n_meses = dias_total // 30

            for mes_idx in range(n_meses):
                fecha_mes = fecha_inicio + timedelta(days=mes_idx * 30)

                # Variación de precio según tipo
                if tipo_variacion == "sin_variacion":
                    precio_factor = 1.0 + rng.normal(0, 0.005)
                elif tipo_variacion == "variacion_moderada":
                    semestre = mes_idx // 6
                    precio_factor = 1.0 + 0.05 * (semestre % 3 - 1) + rng.normal(0, 0.01)
                else:
                    precio_factor = 1.0 + 0.10 * np.sin(mes_idx / 3) + rng.normal(0, 0.02)

                precio_t = precio_base * precio_factor
                costo_t = costo_base * (1 + rng.normal(0, 0.02))

                # Estacionalidad
                mes = fecha_mes.month
                factor_estacional = 1.0 + 0.15 * np.cos((mes - 11) * np.pi / 6)

                # Demanda con elasticidad real + ruido log-normal
                cantidad_esperada = (
                    cantidad_base
                    * factor_estacional
                    * (precio_factor ** beta_real)
                    * np.exp(rng.normal(0, 0.15))
                )
                cantidad_t = max(1, int(cantidad_esperada))

                # Stock-out: 5% probabilidad
                stock_out = rng.random() < 0.05
                if stock_out:
                    cantidad_t = int(cantidad_t * rng.uniform(0.1, 0.4))

                # Promoción esporádica (solo diferenciados/premium)
                promocion = (
                    categoria in ("DIFERENCIADO", "PREMIUM") and rng.random() < 0.08
                )
                if promocion:
                    precio_t *= 0.80
                    cantidad_t = int(cantidad_t * rng.uniform(1.5, 2.5))

                transacciones.append({
                    "sku": sku,
                    "fecha": fecha_mes,
                    "precio_unitario": round(precio_t, 2),
                    "cantidad": cantidad_t,
                    "costo_unitario": round(costo_t, 2),
                    "stock_out": stock_out,
                    "promocion": promocion,
                    "categoria": categoria,
                })

    df = pd.DataFrame(transacciones)
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df
