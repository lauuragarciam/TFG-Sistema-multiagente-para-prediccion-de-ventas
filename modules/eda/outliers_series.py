"""
Outliers de ventas serie a serie (registro, D3): se detectan, se cuentan y se cruzan
con el contexto. NO se eliminan ni se modifican los datos.

Criterio, por serie y solo con sus días con venta > 0 en train:
    umbral = mediana + k x max(1,4826 x MAD, 1)
  - 1,4826 x MAD estima la desviación típica de forma robusta.
  - El mínimo de 1 unidad evita que una serie que casi siempre vende 1 marque cualquier 2.
  - Series con menos de `minimo_dias_con_venta` días con venta no se evalúan.
  - k y el mínimo vienen de [outliers] en config/config.toml.

Contexto de cada día outlier: evento (tipo o días previos), SNAP del estado, fin de
semana y descuento (precio <= -5 % respecto a la mediana de la serie en train). Para
cada contexto se compara su peso entre los días outlier con su peso entre todos los
días con venta (lift = % en outliers / % en la base).

Entradas (data/interim/, solo train): ventas_muestra_largo, calendar_train,
sell_prices_train, clasificacion_series_train.
Salidas (output/eda/):
  outliers_por_serie.csv     umbral, nº y % de días outlier por serie
  outliers_contexto.csv      peso de cada contexto en outliers frente a la base (lift)
  outliers_top.csv           los 50 días con mayor ventas / umbral, con su contexto
  outliers_contexto.png      lift por contexto y categoría

Uso (desde la raíz del repositorio):
    python -m modules.eda.outliers_series
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from modules.config import cargar_config
from modules.eda.preguntas_eda import CATS, barras_por_categoria, cargar
from modules.memoria import informar_memoria

UMBRAL_DESCUENTO = -0.05


def unir_precio(largo: pd.DataFrame, cfg: dict, division) -> pd.DataFrame:
    """Añade var_precio (precio / mediana de la serie en train - 1) sin crear filas."""
    precios = pd.read_parquet(cfg["rutas"]["interim"] / "sell_prices_train.parquet")
    if precios["wm_yr_wk"].max() > division.semana_fin_train:
        raise AssertionError("Fuga: precios posteriores a la semana de corte")
    precios["id"] = precios["item_id"].astype(str) + "_" + precios["store_id"].astype(str) + "_evaluation"
    precios = precios[precios["id"].isin(largo["id"].cat.categories)]
    precios["id"] = pd.Categorical(precios["id"], categories=largo["id"].cat.categories)
    ref = precios.groupby("id", observed=True)["sell_price"].median().rename("precio_ref")
    n = len(largo)
    df = largo.merge(precios[["id", "wm_yr_wk", "sell_price"]], on=["id", "wm_yr_wk"], how="left",
                     validate="many_to_one").join(ref, on="id")
    if len(df) != n or df["dia_num"].max() > division.dia_fin_train:
        raise AssertionError("La unión ventas-precios ha generado filas nuevas o posteriores al corte")
    df["var_precio"] = df["sell_price"] / df["precio_ref"] - 1
    return df


def umbrales_por_serie(df: pd.DataFrame, k: float, minimo: int) -> pd.DataFrame:
    pos = df.loc[df["ventas"] > 0, ["id", "ventas"]]
    g = pos.groupby("id", observed=True)["ventas"]
    t = pd.DataFrame({"n_demandas": g.size(), "mediana_pos": g.median()})
    t["mad_pos"] = (pos.assign(dev=(pos["ventas"] - pos["id"].map(t["mediana_pos"]).astype(float)).abs())
                    .groupby("id", observed=True)["dev"].median())
    t["escala"] = np.maximum(1.4826 * t["mad_pos"], 1.0)
    t["umbral"] = t["mediana_pos"] + k * t["escala"]
    t["evaluada"] = t["n_demandas"] >= minimo
    return t


def main():
    cfg = cargar_config()
    dir_eda = cfg["rutas"]["eda"]
    k, minimo = cfg["outliers"]["k_mad"], cfg["outliers"]["minimo_dias_con_venta"]

    largo, _, division = cargar(cfg)
    df = unir_precio(largo, cfg, division)
    del largo
    clas = pd.read_parquet(cfg["rutas"]["interim"] / "clasificacion_series_train.parquet",
                           columns=["id", "tipo_demanda", "firma_division"])
    if set(clas["firma_division"].unique()) != {division.firma()}:
        raise AssertionError("La clasificación se generó con otra división temporal (RNF-12)")
    informar_memoria("carga")

    umbrales = umbrales_por_serie(df, k, minimo)
    df = df.join(umbrales[["umbral", "evaluada"]], on="id")
    df["evaluada"] = df["evaluada"].fillna(False).astype(bool)
    df["outlier"] = df["evaluada"] & (df["ventas"] > df["umbral"])
    df["ratio_umbral"] = df["ventas"] / df["umbral"]

    # Por serie
    por_serie = umbrales.join(df.groupby("id", observed=True).agg(
        dias=("ventas", "size"), n_outliers=("outlier", "sum"), max_ventas=("ventas", "max"),
        max_ratio_umbral=("ratio_umbral", "max"), cat_id=("cat_id", "first")))
    por_serie["pct_dias_outlier"] = 100 * por_serie["n_outliers"] / por_serie["dias"]
    por_serie = por_serie.join(clas.set_index("id")["tipo_demanda"].astype(str))
    por_serie.round(4).to_csv(dir_eda / "outliers_por_serie.csv", index_label="id")

    # Contexto de los días outlier frente a todos los días con venta de series evaluadas
    base = df[df["evaluada"] & (df["ventas"] > 0)].copy()
    ventana = cfg["eda"]["ventana_previa_evento"]
    contextos = {
        "día de evento": base["dias_hasta_evento"] == 0,
        f"{ventana} días previos a evento": base["dias_hasta_evento"].between(1, ventana),
        "día SNAP": base["snap"] == 1,
        "fin de semana": base["weekday"].isin(["Saturday", "Sunday"]),
        "descuento ≥ 5 %": base["var_precio"] <= UMBRAL_DESCUENTO,
    }
    # Ventanas alternativas, solo para comparar (no se dibujan)
    alternativas = {f"{v} días previos a evento (comparación)": base["dias_hasta_evento"].between(1, v)
                    for v in cfg["outliers"]["ventanas_previas_comparacion"]}
    filas = []
    for grupo, mascara_grupo in [("TOTAL", pd.Series(True, index=base.index))] + [
            (c, base["cat_id"] == c) for c in CATS]:
        sub, es_out = base[mascara_grupo], base.loc[mascara_grupo, "outlier"]
        for nombre, m in (contextos | alternativas).items():
            m = m[mascara_grupo]
            pct_out = 100 * m[es_out].mean() if es_out.any() else np.nan
            pct_base = 100 * m.mean()
            filas.append({"grupo": grupo, "contexto": nombre, "dias_outlier": int(es_out.sum()),
                          "pct_en_outliers": pct_out, "pct_en_base": pct_base, "lift": pct_out / pct_base})
    contexto = pd.DataFrame(filas)
    contexto.round(4).to_csv(dir_eda / "outliers_contexto.csv", index=False)

    top = (df[df["outlier"]].nlargest(50, "ratio_umbral")
           [["id", "cat_id", "date", "ventas", "umbral", "ratio_umbral", "event_name_1", "categoria_evento",
             "snap", "weekday", "var_precio"]])
    top.round(4).to_csv(dir_eda / "outliers_top.csv", index=False)

    # Sensibilidad: nº de outliers con otros k (no se guardan marcas, solo conteos)
    con_venta = df["evaluada"] & (df["ventas"] > 0)
    sens = []
    for k_alt in sorted(set(cfg["outliers"]["k_sensibilidad"]) | {k}):
        umbral_alt = df["id"].map(umbrales["mediana_pos"] + k_alt * umbrales["escala"]).astype(float)
        marca = df["evaluada"] & (df["ventas"] > umbral_alt)
        sens.append({"k": k_alt, "dias_outlier": int(marca.sum()), "pct_dias_con_venta": 100 * marca.sum() / con_venta.sum(),
                     "series_con_outlier": int(marca.groupby(df["id"], observed=True).any().sum()),
                     "vigente": k_alt == k})
    sens = pd.DataFrame(sens)
    sens.round(4).to_csv(dir_eda / "outliers_sensibilidad_k.csv", index=False)

    barras_por_categoria(contexto, "contexto", list(contextos), [c.replace(" a ", "\na ") for c in contextos],
                         "lift", "Contexto de los días outlier (lift = % en outliers / % en todos los días con venta)",
                         "lift", dir_eda / "outliers_contexto.png")
    informar_memoria("final")

    evaluadas = int(umbrales["evaluada"].sum())
    print(f"\nSeries evaluadas: {evaluadas:,} de {len(por_serie):,} (mínimo {minimo} días con venta); k = {k}")
    print(f"Días outlier: {int(df['outlier'].sum()):,} de {int((df['evaluada'] & (df['ventas'] > 0)).sum()):,} "
          f"días con venta ({100 * df['outlier'].sum() / max((df['evaluada'] & (df['ventas'] > 0)).sum(), 1):.2f} %)")
    print(f"Series con al menos un outlier: {int((por_serie['n_outliers'] > 0).sum()):,}")
    print("\nLift por contexto (TOTAL):")
    print(contexto[contexto["grupo"] == "TOTAL"][["contexto", "pct_en_outliers", "pct_en_base", "lift"]]
          .round(3).to_string(index=False))
    print("\nSensibilidad al valor de k:")
    print(sens.round(3).to_string(index=False))
    print("\nLos datos no se modifican: este script solo escribe en output/eda/.")


if __name__ == "__main__":
    main()
