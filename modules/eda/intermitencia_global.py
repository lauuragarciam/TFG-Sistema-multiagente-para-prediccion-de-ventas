"""
ADI, CV² y tipo de demanda de TODAS las series, solo con train y por bloques.

Días válidos de cada serie: desde su primer precio y con su tienda abierta (se excluyen los
tienda-días con ventas totales 0; registro, C2). Dos pasadas por el fichero de ventas:
la primera detecta las tiendas cerradas y la segunda calcula ADI y CV².

Salidas:
  data/interim/clasificacion_series_train.parquet   una fila por serie (con la firma de la división)
  output/eda/intermitencia_resumen_global.csv
  output/eda/intermitencia_por_categoria.csv
  output/eda/intermitencia_por_tienda.csv

Uso (desde la raíz del repositorio):
    python -m modules.eda.intermitencia_global
"""

import numpy as np
import pandas as pd

from modules.config import cargar_config
from modules.datos.carga import (ID_COLS, cargar_calendar, cargar_precios, comprobar_ficheros,
                                 dias_en_ventas, dias_tienda_cerrada, inicio_disponibilidad, leer_ventas_ancho)
from modules.datos.clasificacion import TIPOS_DEMANDA, clasificar, estadisticos_con_mascara, mascara_dias_validos
from modules.datos.division import Division
from modules.memoria import informar_memoria


def resumen_por(df: pd.DataFrame, grupo: str | None) -> pd.DataFrame:
    claves = [grupo] if grupo else []
    conteo = (df.groupby(claves + ["tipo_demanda"], observed=True).size().unstack(fill_value=0)
              if grupo else df["tipo_demanda"].value_counts().to_frame().T)
    conteo = conteo.reindex(columns=list(TIPOS_DEMANDA), fill_value=0)
    pct = conteo.div(conteo.sum(axis=1), axis=0).mul(100).round(2).add_prefix("pct_")
    salida = pd.concat([conteo.add_prefix("n_"), pct], axis=1)
    salida["n_series"] = conteo.sum(axis=1)
    salida["pct_adi_ge_umbral"] = (pct["pct_intermitente"] + pct["pct_irregular"]).round(2)
    return salida.reset_index(drop=not grupo)


def main():
    cfg = cargar_config()
    rutas = comprobar_ficheros(cfg["rutas"]["raw"])
    dir_interim, dir_eda = cfg["rutas"]["interim"], cfg["rutas"]["eda"]
    dir_interim.mkdir(parents=True, exist_ok=True)
    dir_eda.mkdir(parents=True, exist_ok=True)

    cal = cargar_calendar(rutas["calendar"])
    division = Division.desde_config(cfg, cal, dias_en_ventas(rutas["ventas"]))
    print(division.resumen())

    precios = cargar_precios(rutas["precios"], hasta_semana=division.semana_fin_train)
    inicio = inicio_disponibilidad(precios, cal)
    del precios
    inicio["id"] = inicio["item_id"].astype(str) + "_" + inicio["store_id"].astype(str) + "_evaluation"
    primer_dia_por_id = inicio.set_index("id")["primer_dia"]
    sin_venta = division.dia_fin_train + 1   # marca de "no está a la venta en train"
    informar_memoria("precios e inicio de disponibilidad")

    cerrado = dias_tienda_cerrada(rutas["ventas"], division.dia_fin_train, cfg["carga"]["filas_por_bloque"])
    print(f"Tienda-días cerrados (ventas totales 0) excluidos: {sum(int(m.sum()) for m in cerrado.values())}")
    informar_memoria("pasada 1 (tiendas cerradas)")

    trozos = []
    cols_dias = [f"d_{i}" for i in range(1, division.dia_fin_train + 1)]
    for i, bloque in enumerate(leer_ventas_ancho(rutas["ventas"], division.dia_fin_train,
                                                 cfg["carga"]["filas_por_bloque"]), start=1):
        primer_dia = bloque["id"].astype(str).map(primer_dia_por_id).fillna(sin_venta).to_numpy(np.int32)
        if (primer_dia > sin_venta).any():
            raise AssertionError("Inicio de disponibilidad posterior al corte de train")
        abierto = ~np.vstack([cerrado[str(t)] for t in bloque["store_id"]])
        est = estadisticos_con_mascara(bloque[cols_dias].to_numpy(), mascara_dias_validos(primer_dia, abierto))
        ids = bloque[ID_COLS].astype(str).reset_index(drop=True)
        ids["primer_dia"] = np.where(primer_dia == sin_venta, -1, primer_dia)
        trozos.append(pd.concat([ids, est], axis=1))
        informar_memoria(f"bloque {i}")

    df = pd.concat(trozos, ignore_index=True)
    c = cfg["clasificacion"]
    df["tipo_demanda"], df["aviso"] = clasificar(df["adi"], df["cv2"], c["umbral_adi"], c["umbral_cv2"])
    df["firma_division"] = division.firma()
    for col in ID_COLS[1:] + ["tipo_demanda"]:
        df[col] = df[col].astype("category")
    df.to_parquet(dir_interim / "clasificacion_series_train.parquet", index=False)

    global_ = resumen_por(df, None)
    global_.to_csv(dir_eda / "intermitencia_resumen_global.csv", index=False)
    resumen_por(df, "cat_id").to_csv(dir_eda / "intermitencia_por_categoria.csv", index=False)
    resumen_por(df, "store_id").to_csv(dir_eda / "intermitencia_por_tienda.csv", index=False)

    print(f"\nSeries: {len(df):,}")
    print(f"  sin días a la venta en train: {(df['primer_dia'] == -1).sum()}")
    print(f"  a la venta pero sin ninguna venta: {((df['primer_dia'] != -1) & (df['n_demandas'] == 0)).sum()}")
    print(f"  con una sola venta (CV² = 0): {(df['n_demandas'] == 1).sum()}")
    print(f"  con aviso (ADI/CV² indefinidos, clasificadas como intermitentes): {int(df['aviso'].sum())}")
    print(f"  unidades vendidas antes del primer precio: {int(df['ventas_previas_inicio'].sum())}")
    # Anexo A: aviso por cada serie con ADI/CV² indefinidos (clasificada como intermitente)
    for _, fila in df.loc[df["aviso"]].iterrows():
        motivo = "sin días a la venta en train" if fila["primer_dia"] == -1 else "sin ninguna venta en train"
        print(f"  AVISO: {fila['id']}: {motivo}; ADI/CV² indefinidos -> intermitente")
    for _, fila in df.loc[df["n_demandas"] == 1].iterrows():
        print(f"  AVISO: {fila['id']}: una sola venta en train -> CV² = 0")
    print("\nTipo de demanda (umbrales ADI {umbral_adi}, CV² {umbral_cv2}):".format(**c))
    for t in TIPOS_DEMANDA:
        print(f"  {t:<13} {int(global_[f'n_{t}'].iloc[0]):>6,}  {global_[f'pct_{t}'].iloc[0]:>6.2f} %")
    print(f"  ADI >= {c['umbral_adi']} (intermitente + irregular): {global_['pct_adi_ge_umbral'].iloc[0]:.2f} %")
    informar_memoria("final")


if __name__ == "__main__":
    main()
