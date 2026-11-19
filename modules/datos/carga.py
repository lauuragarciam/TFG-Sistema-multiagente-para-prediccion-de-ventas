"""
Carga de los ficheros del M5 con tipos de datos reducidos (RF-02, RNF-07).

Tipos:
  - identificadores (id, item_id, dept_id, cat_id, store_id, state_id): category
  - ventas diarias: int16 (se comprueba el rango antes de reducir)
  - precios: float32 (se comprueba que conserva los 2 decimales)
  - semana Walmart (wm_yr_wk): int16; índice de día (dia_num, el n de d_n): int16

Las ventas se leen solo hasta el último día pedido (usecols), de modo que los
días posteriores al corte no llegan a memoria (RNF-12).
"""

from collections.abc import Iterator
from pathlib import Path

import numpy as np
import pandas as pd

FICHEROS = {
    "calendar": "calendar.csv",
    "precios": "sell_prices.csv",
    "ventas": "sales_train_evaluation.csv",
}
ID_COLS = ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"]

TIPOS_CALENDAR = {
    "wm_yr_wk": "int16", "weekday": "category", "wday": "int8", "month": "int8",
    "year": "int16", "d": "string",
    "event_name_1": "category", "event_type_1": "category",
    "event_name_2": "category", "event_type_2": "category",
    "snap_CA": "int8", "snap_TX": "int8", "snap_WI": "int8",
}
TIPOS_PRECIOS = {"store_id": "category", "item_id": "category", "wm_yr_wk": "int16", "sell_price": "float64"}


class ErrorFicheros(FileNotFoundError):
    """Faltan ficheros de entrada (CU-01, flujo alternativo 1)."""


def comprobar_ficheros(dir_raw: Path) -> dict[str, Path]:
    """Devuelve la ruta de cada fichero o lanza ErrorFicheros con los que faltan."""
    rutas = {clave: Path(dir_raw) / nombre for clave, nombre in FICHEROS.items()}
    faltan = [str(r) for r in rutas.values() if not r.exists()]
    if faltan:
        raise ErrorFicheros("Faltan ficheros de entrada del M5:\n  " + "\n  ".join(faltan))
    return rutas


# ---------------------------------------------------------------- calendar

def cargar_calendar(ruta: Path) -> pd.DataFrame:
    """Calendario completo (una fila = un día) con comprobaciones de clave y continuidad."""
    cal = pd.read_csv(ruta, parse_dates=["date"], dtype=TIPOS_CALENDAR)
    if not (cal["date"].is_unique and cal["d"].is_unique):
        raise ValueError("calendar: fechas o códigos d duplicados")
    if not (cal["date"].diff().dropna() == pd.Timedelta(days=1)).all():
        raise ValueError("calendar: hay huecos entre fechas consecutivas")
    # Nulos estructurales: un evento secundario solo existe si hay evento principal
    if not cal.loc[cal["event_name_1"].isna(), "event_name_2"].isna().all():
        raise ValueError("calendar: event_name_2 informado en un día sin event_name_1")
    cal["dia_num"] = cal["d"].str[2:].astype("int16")
    return cal


# ---------------------------------------------------------------- precios

def cargar_precios(ruta: Path, hasta_semana: int | None = None) -> pd.DataFrame:
    """Precios semanales (una fila = tienda x producto x semana).

    hasta_semana: si se indica, solo se conservan las semanas wm_yr_wk <= hasta_semana.
    """
    precios = pd.read_csv(ruta, dtype=TIPOS_PRECIOS)
    if hasta_semana is not None:
        precios = precios.loc[precios["wm_yr_wk"] <= hasta_semana].reset_index(drop=True)
    p32 = precios["sell_price"].astype("float32")
    if not np.allclose(p32.astype("float64").round(2), precios["sell_price"].round(2), rtol=0, atol=1e-9):
        raise ValueError("sell_prices: float32 no conserva los 2 decimales")
    precios["sell_price"] = p32
    n_dup = int(precios.duplicated(["store_id", "item_id", "wm_yr_wk"]).sum())
    if n_dup:
        raise ValueError(f"sell_prices: {n_dup} claves tienda-producto-semana duplicadas")
    for c in ("store_id", "item_id"):
        precios[c] = precios[c].cat.remove_unused_categories()
    return precios


def estructura_precios(ruta: Path) -> pd.DataFrame:
    """Perfil solo estructural de sell_prices completo: sin estadísticos de precio.

    Devuelve una tabla columna -> tipo, nulos, valores distintos, y filas
    globales (número de filas, claves duplicadas, rango de semanas, pares tienda-producto).
    """
    precios = pd.read_csv(ruta, dtype=TIPOS_PRECIOS)
    filas = [{
        "elemento": c,
        "tipo": "float32" if c == "sell_price" else str(precios[c].dtype),
        "nulos": int(precios[c].isna().sum()),
        "valores_distintos": int(precios[c].nunique()) if c != "sell_price" else None,
    } for c in precios.columns]
    filas += [
        {"elemento": "n_filas", "valor": len(precios)},
        {"elemento": "claves_duplicadas_tienda_producto_semana",
         "valor": int(precios.duplicated(["store_id", "item_id", "wm_yr_wk"]).sum())},
        {"elemento": "pares_tienda_producto",
         "valor": int(precios.groupby(["store_id", "item_id"], observed=True).ngroups)},
        {"elemento": "semana_min", "valor": int(precios["wm_yr_wk"].min())},
        {"elemento": "semana_max", "valor": int(precios["wm_yr_wk"].max())},
    ]
    return pd.DataFrame(filas)


def inicio_disponibilidad(precios: pd.DataFrame, calendar: pd.DataFrame) -> pd.DataFrame:
    """Primer día a la venta de cada tienda-producto: primer día de su primera semana con precio.

    Para no usar información futura, `precios` debe venir ya filtrado hasta la semana de corte.
    Devuelve store_id, item_id, primera_semana, primer_dia (dia_num).
    """
    primera = (precios.groupby(["store_id", "item_id"], observed=True)["wm_yr_wk"]
               .min().rename("primera_semana").reset_index())
    dia_semana = calendar.groupby("wm_yr_wk")["dia_num"].min().rename("primer_dia")
    primera = primera.join(dia_semana, on="primera_semana", validate="many_to_one")
    if primera["primer_dia"].isna().any():
        raise ValueError("Hay semanas de precio que no están en el calendario")
    primera["primer_dia"] = primera["primer_dia"].astype("int16")
    return primera


# ---------------------------------------------------------------- ventas

def dias_en_ventas(ruta: Path) -> int:
    """Número de columnas d_n del fichero de ventas (lee solo la cabecera)."""
    cabecera = pd.read_csv(ruta, nrows=0).columns
    return sum(c.startswith("d_") for c in cabecera)


def leer_ids_ventas(ruta: Path) -> pd.DataFrame:
    """Solo las columnas identificadoras de las series, sin ninguna venta."""
    return pd.read_csv(ruta, usecols=ID_COLS, dtype={c: "category" for c in ID_COLS})


def _reducir_ventas(bloque: pd.DataFrame, cols_dias: list[str]) -> pd.DataFrame:
    valores = bloque[cols_dias].to_numpy()
    if valores.min() < 0:
        raise ValueError(f"Ventas negativas (mín = {valores.min()})")
    if valores.max() > np.iinfo(np.int16).max:
        raise ValueError(f"Ventas fuera del rango de int16 (máx = {valores.max()})")
    bloque[cols_dias] = bloque[cols_dias].astype("int16")
    return bloque


def leer_ventas_ancho(ruta: Path, ultimo_dia: int, filas_por_bloque: int) -> Iterator[pd.DataFrame]:
    """Ventas en formato ancho, por bloques de series, con los días d_1..d_{ultimo_dia}.

    Cada bloque: columnas ID_COLS (category) + d_1..d_{ultimo_dia} (int16).
    """
    cols_dias = [f"d_{i}" for i in range(1, ultimo_dia + 1)]
    tipos = {**{c: "category" for c in ID_COLS}, **{c: "int32" for c in cols_dias}}
    with pd.read_csv(ruta, usecols=ID_COLS + cols_dias, dtype=tipos, chunksize=filas_por_bloque) as lector:
        for bloque in lector:
            yield _reducir_ventas(bloque[ID_COLS + cols_dias], cols_dias)


def dias_tienda_cerrada(ruta: Path, ultimo_dia: int, filas_por_bloque: int) -> dict[str, np.ndarray]:
    """Días en que cada tienda tiene ventas totales 0 (tienda cerrada), entre d_1 y d_{ultimo_dia}.

    Devuelve {store_id: vector booleano de `ultimo_dia` posiciones}; la posición j es el día d_{j+1}.
    Solo lee las columnas hasta `ultimo_dia` (registro, C2).
    """
    cols_dias = [f"d_{i}" for i in range(1, ultimo_dia + 1)]
    total: dict[str, np.ndarray] = {}
    for bloque in leer_ventas_ancho(ruta, ultimo_dia, filas_por_bloque):
        for tienda, d in bloque.groupby("store_id", observed=True):
            suma = d[cols_dias].to_numpy(np.int64).sum(axis=0)
            total[str(tienda)] = total.get(str(tienda), 0) + suma
    return {t: s == 0 for t, s in total.items()}


def ancho_a_largo(bloque: pd.DataFrame, calendar: pd.DataFrame) -> pd.DataFrame:
    """Formato largo (una fila = serie x día) con fecha, semana y dia_num."""
    largo = bloque.melt(id_vars=ID_COLS, var_name="d", value_name="ventas")
    largo["dia_num"] = largo["d"].str[2:].astype("int16")
    largo = largo.drop(columns="d").merge(
        calendar[["dia_num", "date", "wm_yr_wk"]], on="dia_num", how="left", validate="many_to_one")
    largo["ventas"] = largo["ventas"].astype("int16")
    return largo
