import pandas as pd
import numpy as np
from datetime import date, timedelta

def generar_dataset_pyme(n_skus: int = 150, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    transacciones = []
    
    for sku_id in range(1, n_skus + 1):
        sku = f"SKU-{sku_id:04d}"
        precio_base = rng.uniform(10, 100)
        cantidad_base = rng.uniform(50, 300)
        
        # Forzamos que los primeros 30 SKUs pasen la auditoría estadística
        es_analizable = sku_id <= 30
        
        for mes_idx in range(24):
            fecha_mes = date(2024, 1, 1) + timedelta(days=mes_idx * 30)
            
            if es_analizable:
                # Variación clara de precio (15%) y sin ruido en la demanda
                precio_factor = 1.0 + 0.15 * np.sin(mes_idx) 
                beta_real = -2.0 if sku_id <= 15 else -0.5 
                ruido = 0.0 
            else:
                # SKUs planos o con demasiado ruido (simula la realidad PYME)
                precio_factor = 1.0 + rng.normal(0, 0.005)
                beta_real = -1.2
                ruido = rng.normal(0, 0.15)
                
            precio_t = precio_base * precio_factor
            cantidad_t = int(cantidad_base * (precio_factor ** beta_real) * np.exp(ruido))
            
            transacciones.append({
                "sku": sku,
                "fecha": fecha_mes,
                "precio_unitario": round(precio_t, 2),
                "cantidad": max(1, cantidad_t)
            })
            
    return pd.DataFrame(transacciones)