"""
Sensibilidad de ADI y de la clasificación a ceros que no son demanda (solo train).
NO escribe la clasificación vigente (data/interim/clasificacion_series_train.parquet).

Variantes de los días contados por serie:
  A  desde el primer día con precio hasta d_fin_train (definición anterior a C2)
  B  acotada: desde el primer hasta el último día con precio (última semana con precio, sin pasar del corte)
  C  A sin los días en que la tienda está cerrada (ventas totales de la tienda = 0): VIGENTE desde C2
  D  acotada y sin días de tienda cerrada

Comprobación: la variante C debe reproducir exactamente la clasificación vigente.

Salidas (output/eda/):
  ceros_ultimo_precio.csv          series cuyo último precio es anterior a la última semana de train
  ceros_tiendas_cerradas.csv       días con ventas totales 0 por tienda (fecha y evento)
  ceros_sensibilidad_global.csv    proporción por tipo de demanda en cada variante (global y por categoría)
  ceros_cambios_clase.csv          matriz de cambios de clase de A a cada variante

Uso (desde la raíz del repositorio):
    python -m modules.eda.sensibilidad_ceros
"""

import numpy as np
import pandas as pd

from modules.config import cargar_config
from modules.datos.carga import (ID_COLS, cargar_calendar, cargar_precios, comprobar_ficheros,
                                 dias_en_ventas, dias_tienda_cerrada, leer_ventas_ancho)
from modules.datos.clasificacion import TIPOS_DEMANDA, clasificar, estadisticos_con_mascara
from modules.datos.division import Division
from modules.memoria import informar_memoria

VARIANTES = {"A": "desde el primer precio (anterior a C2)", "B": "acotada al último precio",
             "C": "sin tienda cerrada (vigente)", "D": "acotada y sin tienda cerrada"}


def proporciones(df: pd.DataFrame, columna: str) -> pd.DataFrame:
    filas = []
    for grupo, d in [("TOTAL", df)] + [(c, df[df["cat_id"] == c]) for c in sorted(df["cat_id"].unique())]:
        conteo = d[columna].value_counts().reindex(TIPOS_DEMANDA, fill_value=0)
        fila = {"grupo": grupo, "n_series": len(d)}
        fila.update({f"pct_{t}": 100 * conteo[t] / len(d) for t in TIPOS_DEMANDA})
        fila["pct_adi_ge_umbral"] = fila["pct_intermitente"] + fila["pct_irregular"]
        filas.append(fila)
    return pd.DataFrame(filas)


def main():
    cfg = cargar_config()
    rutas = comprobar_ficheros(cfg["rutas"]["raw"])
    dir_interim, dir_eda = cfg["rutas"]["interim"], cfg["rutas"]["eda"]
    cal = cargar_calendar(rutas["calendar"])
    division = Division.desde_config(cfg, cal, dias_en_ventas(rutas["ventas"]))
    T, filas_bloque = division.dia_fin_train, cfg["carga"]["filas_por_bloque"]
    print(division.resumen())

    # Primer y último día con precio (solo semanas de train)
    precios = cargar_precios(rutas["precios"], hasta_semana=division.semana_fin_train)
    semanas = precios.groupby(["store_id", "item_id"], observed=True)["wm_yr_wk"].agg(["min", "max"]).reset_index()
    del precios
    dias_semana = cal.groupby("wm_yr_wk")["dia_num"].agg(["min", "max"])
    semanas["primer_dia"] = semanas["min"].map(dias_semana["min"])
    semanas["ultimo_dia"] = np.minimum(semanas["max"].map(dias_semana["max"]), T)
    semanas["id"] = semanas["item_id"].astype(str) + "_" + semanas["store_id"].astype(str) + "_evaluation"
    semanas = semanas.set_index("id")
    informar_memoria("precios")

    # Pasada 1: ventas totales por tienda y día -> días de tienda cerrada
    cerrado = dias_tienda_cerrada(rutas["ventas"], T, filas_bloque)   # vector de T booleanos por tienda
    filas_cerr = [{"store_id": t, "dia_num": int(i + 1)} for t, m in cerrado.items() for i in np.flatnonzero(m)]
    cerr = pd.DataFrame(filas_cerr).merge(cal[["dia_num", "date", "event_name_1"]], on="dia_num", how="left")
    cerr.to_csv(dir_eda / "ceros_tiendas_cerradas.csv", index=False)
    informar_memoria("pasada 1 (tiendas cerradas)")

    # Pasada 2: ADI y CV² en las cuatro variantes
    dia = np.arange(1, T + 1, dtype=np.int32)
    trozos = []
    for bloque in leer_ventas_ancho(rutas["ventas"], T, filas_bloque):
        cols = [f"d_{i}" for i in range(1, T + 1)]
        ventas = bloque[cols].to_numpy()
        ids = bloque["id"].astype(str)
        info = semanas.reindex(ids)
        primer = info["primer_dia"].fillna(T + 1).to_numpy(np.int32)
        ultimo = info["ultimo_dia"].fillna(0).to_numpy(np.int32)
        abierto = ~np.vstack([cerrado[str(t)] for t in bloque["store_id"]])
        desde = dia[None, :] >= primer[:, None]
        hasta = dia[None, :] <= ultimo[:, None]
        mascaras = {"A": desde, "B": desde & hasta, "C": desde & abierto, "D": desde & hasta & abierto}
        base = bloque[ID_COLS].astype(str).reset_index(drop=True)
        for v, m in mascaras.items():
            est = estadisticos_con_mascara(ventas, m)
            base[f"n_periodos_{v}"] = est["n_periodos"]
            base[f"n_demandas_{v}"] = est["n_demandas"]
            base[f"adi_{v}"] = est["adi"]
            base[f"cv2_{v}"] = est["cv2"]
            base[f"ventas_fuera_{v}"] = est["ventas_previas_inicio"]
        trozos.append(base)
    df = pd.concat(trozos, ignore_index=True)
    c = cfg["clasificacion"]
    for v in VARIANTES:
        df[f"tipo_{v}"], df[f"aviso_{v}"] = clasificar(df[f"adi_{v}"], df[f"cv2_{v}"], c["umbral_adi"], c["umbral_cv2"])
    informar_memoria("pasada 2 (variantes)")

    # La variante C debe reproducir exactamente la clasificación vigente (C2)
    vigente = pd.read_parquet(dir_interim / "clasificacion_series_train.parquet",
                              columns=["id", "adi", "cv2", "n_periodos", "tipo_demanda", "firma_division"])
    if set(vigente["firma_division"].unique()) != {division.firma()}:
        raise AssertionError("La clasificación vigente se generó con otra división temporal (RNF-12)")
    vigente = vigente.set_index("id")
    a = df.set_index("id")
    v = vigente.reindex(a.index)
    comprobaciones = {
        "mismas series": len(vigente) == len(a) and v["tipo_demanda"].notna().all(),
        "tipo": (a["tipo_C"] == v["tipo_demanda"].astype(str)).all(),
        "n_periodos": (a["n_periodos_C"].to_numpy() == v["n_periodos"].to_numpy()).all(),
        "adi": np.allclose(a["adi_C"], v["adi"], rtol=0, atol=1e-12, equal_nan=True),
        "cv2": np.allclose(a["cv2_C"], v["cv2"], rtol=0, atol=1e-12, equal_nan=True),
    }
    if not all(comprobaciones.values()):
        raise AssertionError(f"La variante C no reproduce la clasificación vigente: {comprobaciones}")
    print("Variante C = clasificación vigente (tipo, n_periodos, ADI y CV²): OK")

    # (1) Series con último precio anterior a la última semana de train
    acotadas = df[df["n_periodos_B"] < df["n_periodos_A"]].copy()
    acotadas["dias_tras_ultimo_precio"] = acotadas["n_periodos_A"] - acotadas["n_periodos_B"]
    acotadas = acotadas.join(semanas[["max"]].rename(columns={"max": "ultima_semana_precio"}), on="id")
    acotadas[["id", "cat_id", "store_id", "ultima_semana_precio", "n_periodos_A", "n_periodos_B",
              "dias_tras_ultimo_precio", "ventas_fuera_B", "adi_A", "adi_B", "tipo_A", "tipo_B"]] \
        .round(4).to_csv(dir_eda / "ceros_ultimo_precio.csv", index=False)

    # Proporciones y cambios de clase
    resumen = pd.concat([proporciones(df, f"tipo_{v}").assign(variante=f"{v}: {n}") for v, n in VARIANTES.items()])
    resumen = resumen[["variante"] + [c for c in resumen.columns if c != "variante"]]
    resumen.round(4).to_csv(dir_eda / "ceros_sensibilidad_global.csv", index=False)
    cambios = pd.concat([pd.crosstab(df["tipo_A"], df[f"tipo_{v}"]).assign(variante=v) for v in "BCD"])
    cambios.to_csv(dir_eda / "ceros_cambios_clase.csv")

    print(f"\n(1) Series con último precio antes de la semana {division.semana_fin_train}: {len(acotadas)}")
    if len(acotadas):
        print(f"    días de train tras el último precio: total {int(acotadas['dias_tras_ultimo_precio'].sum()):,}, "
              f"mediana {acotadas['dias_tras_ultimo_precio'].median():.0f}, máx {acotadas['dias_tras_ultimo_precio'].max()}")
        print(f"    unidades vendidas tras el último precio: {int(acotadas['ventas_fuera_B'].sum())}")
        print(f"    series que cambian de clase (A -> B): {int((df['tipo_A'] != df['tipo_B']).sum())}")
    print(f"\n(2) Días de tienda cerrada (ventas totales 0) en train: {len(cerr)} tienda-días")
    print(cerr.groupby("store_id").size().to_string())
    print("    eventos en esos días:", cerr["event_name_1"].astype(object).fillna("(sin evento)").value_counts().to_dict())
    for v in "CD":
        print(f"    series que cambian de clase (A -> {v}): {int((df['tipo_A'] != df[f'tipo_{v}']).sum())}")
    print("\nProporción por tipo de demanda (%):")
    print(resumen.round(2).to_string(index=False))
    informar_memoria("final")


if __name__ == "__main__":
    main()
