"""
ADI, CV² y clasificación del tipo de demanda de cada serie (RF-03, Anexo A).

Definiciones, con los días contados desde el inicio de disponibilidad de la serie
(primer día de su primera semana con precio) hasta el último día de train, excluyendo
los días en que su tienda está cerrada (ventas totales de la tienda = 0; registro, C2):
  - ADI = nº de días / nº de días con venta > 0
  - CV² = (desviación típica muestral / media)² de las ventas > 0

Casos límite (Anexo A):
  - sin días a la venta o sin ninguna venta: ADI y CV² indefinidos -> 'intermitente' con aviso
  - una única venta: CV² = 0
"""

import numpy as np
import pandas as pd

TIPOS_DEMANDA = ("suave", "erratica", "intermitente", "irregular")


def estadisticos_bloque(ventas: np.ndarray, primer_dia: np.ndarray) -> pd.DataFrame:
    """ADI y CV² de un bloque de series contando todos los días desde el primer precio.

    No excluye los días de tienda cerrada: es la definición anterior a C2 (variante A de
    sensibilidad_ceros.py). La clasificación vigente usa `mascara_dias_validos`.

    ventas: matriz (series x días); la columna j es el día d_{j+1}.
    primer_dia: dia_num del primer día a la venta de cada serie. Un valor mayor
        que el número de columnas indica que la serie no está a la venta en el periodo.
    """
    n_dias = ventas.shape[1]
    dia = np.arange(1, n_dias + 1, dtype=np.int32)
    en_venta = dia[None, :] >= primer_dia[:, None]
    return estadisticos_con_mascara(ventas, en_venta)


def mascara_dias_validos(primer_dia: np.ndarray, abierto: np.ndarray) -> np.ndarray:
    """Días válidos para ADI/CV² (registro, C2): desde el primer precio y con la tienda abierta.

    primer_dia: dia_num del primer día a la venta de cada serie (un valor mayor que el
        número de días indica que no está a la venta en el periodo).
    abierto: matriz booleana (series x días); False si la tienda de la serie está cerrada ese día.
    """
    dia = np.arange(1, abierto.shape[1] + 1, dtype=np.int32)
    return (dia[None, :] >= np.asarray(primer_dia)[:, None]) & abierto


def tienda_abierta_largo(store_id, dia_num, cerrado: dict[str, np.ndarray]) -> np.ndarray:
    """Para una tabla larga (serie x día): True si la tienda de la fila está abierta ese día (C2).

    cerrado: salida de `carga.dias_tienda_cerrada` ({store_id: vector booleano, posición j = d_{j+1}}).
    """
    tiendas = np.asarray(store_id).astype(str)
    dias = np.asarray(dia_num, dtype=np.int64)
    abierto = np.ones(len(dias), dtype=bool)
    for tienda, m in cerrado.items():
        sel = tiendas == tienda
        abierto[sel] = ~m[dias[sel] - 1]
    return abierto


def estadisticos_con_mascara(ventas: np.ndarray, en_venta: np.ndarray) -> pd.DataFrame:
    """ADI y CV² contando solo los días marcados como válidos en `en_venta` (misma forma que `ventas`).

    `ventas_previas_inicio` suma las unidades vendidas en días no válidos.
    """
    v = np.where(en_venta, ventas, 0).astype(np.float64)
    ventas_previas = np.where(en_venta, 0, ventas).sum(axis=1)

    n_periodos = en_venta.sum(axis=1)
    n_demandas = (v > 0).sum(axis=1)
    suma, suma_cuad = v.sum(axis=1), (v ** 2).sum(axis=1)

    with np.errstate(divide="ignore", invalid="ignore"):
        adi = np.where(n_demandas > 0, n_periodos / n_demandas, np.nan)
        media = np.where(n_demandas > 0, suma / n_demandas, np.nan)
        var = np.where(n_demandas > 1,
                       np.clip(suma_cuad - n_demandas * media ** 2, 0, None) / (n_demandas - 1), np.nan)
        cv2 = np.where(n_demandas > 1, var / media ** 2, np.where(n_demandas == 1, 0.0, np.nan))

    return pd.DataFrame({
        "n_periodos": n_periodos.astype(np.int32),
        "n_demandas": n_demandas.astype(np.int32),
        "ventas_previas_inicio": ventas_previas.astype(np.int64),
        "media_no_nula": media,
        "adi": adi,
        "cv2": cv2,
    })


def clasificar(adi: np.ndarray, cv2: np.ndarray, umbral_adi: float, umbral_cv2: float) -> tuple[np.ndarray, np.ndarray]:
    """Tipo de demanda de cada serie y marca de aviso (ADI/CV² indefinidos)."""
    adi, cv2 = np.asarray(adi, dtype=float), np.asarray(cv2, dtype=float)
    aviso = np.isnan(adi) | np.isnan(cv2)
    tipo = np.select(
        [aviso,
         (adi < umbral_adi) & (cv2 < umbral_cv2),
         (adi < umbral_adi) & (cv2 >= umbral_cv2),
         (adi >= umbral_adi) & (cv2 < umbral_cv2)],
        ["intermitente", "suave", "erratica", "intermitente"],
        default="irregular")
    return tipo, aviso
