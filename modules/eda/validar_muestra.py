"""
Representatividad de la muestra (D4) y memoria de la tabla larga (RNF-07).

Entradas (solo train):
  data/interim/clasificacion_series_train.parquet  conteos por serie de la pasada por bloques
                                                   (n_periodos, n_demandas, media_no_nula)
  data/interim/ventas_muestra_largo.parquet        muestra serie x día

Salidas:
  output/eda/muestra_vs_total.csv        % de días sin venta y media de ventas, muestra frente a total
                                         (ambas sin los tienda-días cerrados, C2)
  output/eda/memoria_tabla_larga.csv     bytes por fila por columna y extrapolación a las 30.490 series

Uso:
    python -m modules.eda.validar_muestra
"""

import pandas as pd

from modules.config import cargar_config
from modules.datos.carga import comprobar_ficheros, dias_en_ventas, dias_tienda_cerrada
from modules.datos.clasificacion import tienda_abierta_largo
from modules.datos.division import Division
from modules.memoria import informar_memoria


def indicadores(n_periodos: pd.Series, n_demandas: pd.Series, unidades: pd.Series) -> dict:
    """Indicadores sobre series-día a la venta (agregados y media por serie)."""
    validas = n_periodos > 0
    pct_cero_serie = 100 * (1 - n_demandas[validas] / n_periodos[validas])
    return {
        "series_con_dias": int(validas.sum()),
        "filas_serie_dia": int(n_periodos.sum()),
        "pct_dias_sin_venta_total": 100 * (1 - n_demandas.sum() / n_periodos.sum()),
        "pct_dias_sin_venta_media_series": pct_cero_serie.mean(),
        "pct_dias_sin_venta_mediana_series": pct_cero_serie.median(),
        "ventas_medias_por_serie_dia": unidades.sum() / n_periodos.sum(),
        "ventas_medias_media_series": (unidades[validas] / n_periodos[validas]).mean(),
    }


def main():
    cfg = cargar_config()
    dir_interim, dir_eda = cfg["rutas"]["interim"], cfg["rutas"]["eda"]

    rutas = comprobar_ficheros(cfg["rutas"]["raw"])
    division = Division.desde_config(cfg, pd.read_parquet(dir_interim / "calendar.parquet"),
                                     dias_en_ventas(rutas["ventas"]))
    dias_train = division.dia_fin_train

    clas = pd.read_parquet(dir_interim / "clasificacion_series_train.parquet")
    if set(clas["firma_division"].unique()) != {division.firma()}:
        raise AssertionError("La clasificación se generó con otra división temporal (RNF-12)")
    clas["unidades"] = clas["media_no_nula"].fillna(0) * clas["n_demandas"]
    largo = pd.read_parquet(dir_interim / "ventas_muestra_largo.parquet")

    # Conteos de la muestra calculados directamente sobre la tabla larga, con los mismos días
    # que la clasificación: sin los tienda-días cerrados (C2)
    cerrado = dias_tienda_cerrada(rutas["ventas"], dias_train, cfg["carga"]["filas_por_bloque"])
    abierto = tienda_abierta_largo(largo["store_id"], largo["dia_num"], cerrado)
    print(f"Filas de la muestra en tienda-días cerrados (excluidas de la comparación, C2): {int((~abierto).sum()):,}")
    g = largo[abierto].assign(con_venta=lambda d: d["ventas"] > 0).groupby("id", observed=True)
    muestra = pd.DataFrame({"n_periodos": g.size(), "n_demandas": g["con_venta"].sum(),
                            "unidades": g["ventas"].sum()})
    muestra = muestra.join(clas.set_index("id")["cat_id"].astype(str))

    filas = []
    for nombre, cat_total, cat_muestra in [("global", clas, muestra)] + [
            (c, clas[clas["cat_id"] == c], muestra[muestra["cat_id"] == c]) for c in sorted(clas["cat_id"].astype(str).unique())]:
        for origen, df in (("total_30490", cat_total), ("muestra", cat_muestra)):
            filas.append({"grupo": nombre, "origen": origen,
                          **indicadores(df["n_periodos"], df["n_demandas"], df["unidades"])})
    comp = pd.DataFrame(filas)
    comp.round(4).to_csv(dir_eda / "muestra_vs_total.csv", index=False)
    print("Muestra frente a total (solo train, días a la venta):")
    print(comp.round(3).to_string(index=False))

    # Memoria por fila de la tabla larga y extrapolación
    bytes_col = largo.memory_usage(deep=True, index=False)
    bytes_fila = bytes_col / len(largo)
    # Filas de la tabla larga: todos los días desde el primer precio (la tabla incluye los días
    # de tienda cerrada aunque ADI no los cuente), así que no se usa n_periodos
    con_precio = clas["primer_dia"] > 0
    filas_total_train = int((dias_train - clas.loc[con_precio, "primer_dia"] + 1).sum())
    filas_total_sin_filtrar = len(clas) * dias_train
    mem = pd.DataFrame({"columna": bytes_col.index, "tipo": [str(largo[c].dtype) for c in bytes_col.index],
                        "bytes_muestra": bytes_col.values, "bytes_por_fila": bytes_fila.values.round(3)})
    total = {"columna": "TOTAL", "tipo": "", "bytes_muestra": int(bytes_col.sum()),
             "bytes_por_fila": round(bytes_fila.sum(), 3)}
    mem = pd.concat([mem, pd.DataFrame([total])], ignore_index=True)
    mem["filas_muestra"] = len(largo)
    mem["mb_total_train_en_venta"] = (mem["bytes_por_fila"] * filas_total_train / 1_048_576).round(1)
    mem["mb_total_train_sin_filtrar"] = (mem["bytes_por_fila"] * filas_total_sin_filtrar / 1_048_576).round(1)
    mem.to_csv(dir_eda / "memoria_tabla_larga.csv", index=False)
    print(f"\nTabla larga de la muestra: {len(largo):,} filas, {bytes_col.sum() / 1_048_576:,.1f} MB, "
          f"{bytes_fila.sum():.2f} bytes por fila")
    print(mem[["columna", "tipo", "bytes_por_fila"]].to_string(index=False))
    print(f"Extrapolación a 30.490 series, train, solo días a la venta ({filas_total_train:,} filas): "
          f"{bytes_fila.sum() * filas_total_train / 1_048_576:,.0f} MB")
    print(f"Extrapolación a 30.490 series x {dias_train} días sin excluir ({filas_total_sin_filtrar:,} filas): "
          f"{bytes_fila.sum() * filas_total_sin_filtrar / 1_048_576:,.0f} MB")
    informar_memoria("validar_muestra")


if __name__ == "__main__":
    main()
