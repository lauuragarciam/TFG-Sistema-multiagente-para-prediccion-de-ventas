"""
Posibles salidas de venta (solo d_1..d_fin_train). NO cambia la clasificación vigente.

Para cada serie:
  L     = días desde su última venta hasta d_fin_train (0 si vendió el último día)
  prob  = (1 - 1/ADI)^L, con el ADI vigente: probabilidad de encadenar L días sin venta si
          cada día vendiera con probabilidad 1/ADI, de forma independiente
Se marca "posible salida de venta" con criterio doble (registro, D7):
  prob < [salida_venta].umbral_probabilidad  y  L >= [salida_venta].L_minimo_dias
El mínimo de L evita marcar rachas cortas en series de venta frecuente, que la fórmula
(días independientes) da por improbables. M5 no distingue retirada de falta de stock.
El ADI vigente incluye la racha final sin ventas, lo que hace la marca conservadora
(un ADI mayor da una probabilidad mayor).

Solo para las series marcadas se recalculan ADI, CV² y el tipo acotando cada serie entre su
primer precio y su última venta (sin los tienda-días cerrados, igual que la vigente; C2), y se
comparan con la clasificación vigente. L se cuenta en días de calendario.

Series sin ninguna venta en train (ADI indefinido): L y prob no se calculan; se cuentan aparte.

Salidas (output/eda/):
  salida_venta_series.csv       una fila por serie con L, prob, marca y, si está marcada, la clasificación acotada
  salida_venta_resumen.csv      series marcadas por categoría y por tienda
  salida_venta_L_cuantiles.csv  distribución de L (todas las series con ventas y marcadas)
  salida_venta_cambios.csv      tipo vigente frente a tipo acotado (series marcadas)
  salida_venta_L.png            histograma de L

Uso (desde la raíz del repositorio):
    python -m modules.eda.salida_venta
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

from modules.config import cargar_config
from modules.datos.carga import (cargar_calendar, cargar_precios, comprobar_ficheros, dias_en_ventas,
                                 dias_tienda_cerrada, inicio_disponibilidad, leer_ventas_ancho)
from modules.datos.clasificacion import TIPOS_DEMANDA, clasificar, estadisticos_con_mascara, mascara_dias_validos
from modules.datos.division import Division
from modules.eda.preguntas_eda import COLOR_CAT, SUPERFICIE, TINTA, TINTA_SEC, coma, estilo, guardar
from modules.memoria import informar_memoria

SERIE = COLOR_CAT["FOODS"]   # primer color categórico de la paleta (una sola serie)

CUANTILES = [0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]


def main():
    cfg = cargar_config()
    rutas = comprobar_ficheros(cfg["rutas"]["raw"])
    dir_interim, dir_eda = cfg["rutas"]["interim"], cfg["rutas"]["eda"]
    umbral = cfg["salida_venta"]["umbral_probabilidad"]
    l_minimo = cfg["salida_venta"]["L_minimo_dias"]
    cal = cargar_calendar(rutas["calendar"])
    division = Division.desde_config(cfg, cal, dias_en_ventas(rutas["ventas"]))
    T = division.dia_fin_train
    print(division.resumen())

    vigente = pd.read_parquet(dir_interim / "clasificacion_series_train.parquet",
                              columns=["id", "cat_id", "store_id", "adi", "cv2", "tipo_demanda", "firma_division"])
    if set(vigente["firma_division"].unique()) != {division.firma()}:
        raise AssertionError("La clasificación vigente se generó con otra división temporal (RNF-12)")
    vigente = vigente.set_index("id")

    inicio = inicio_disponibilidad(cargar_precios(rutas["precios"], hasta_semana=division.semana_fin_train), cal)
    inicio["id"] = inicio["item_id"].astype(str) + "_" + inicio["store_id"].astype(str) + "_evaluation"
    primer_dia_por_id = inicio.set_index("id")["primer_dia"]
    informar_memoria("carga")
    cerrado = dias_tienda_cerrada(rutas["ventas"], T, cfg["carga"]["filas_por_bloque"])

    dia = np.arange(1, T + 1, dtype=np.int32)
    cols = [f"d_{i}" for i in range(1, T + 1)]
    trozos = []
    for bloque in leer_ventas_ancho(rutas["ventas"], T, cfg["carga"]["filas_por_bloque"]):
        ventas = bloque[cols].to_numpy()
        ids = bloque["id"].astype(str).to_numpy()
        hay_venta = ventas > 0
        ultima = np.where(hay_venta.any(axis=1), T - np.argmax(hay_venta[:, ::-1], axis=1), 0)   # dia_num; 0 = nunca
        primer = pd.Series(ids).map(primer_dia_por_id).fillna(T + 1).to_numpy(np.int32)
        abierto = ~np.vstack([cerrado[str(t)] for t in bloque["store_id"]])
        mascara = mascara_dias_validos(primer, abierto) & (dia[None, :] <= ultima[:, None])
        est = estadisticos_con_mascara(ventas, mascara)
        trozos.append(pd.DataFrame({"id": ids, "primer_dia": primer, "ultima_venta": ultima,
                                    "adi_acotado": est["adi"], "cv2_acotado": est["cv2"],
                                    "n_periodos_acotado": est["n_periodos"]}))
    df = pd.concat(trozos, ignore_index=True).set_index("id").join(vigente)
    informar_memoria("pasada por bloques")

    con_ventas = df["ultima_venta"] > 0
    df["L"] = np.where(con_ventas, T - df["ultima_venta"], np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        df["prob"] = np.where(con_ventas & df["adi"].notna(), (1 - 1 / df["adi"]) ** df["L"], np.nan)
    df["marca_probabilidad"] = df["prob"] < umbral
    df["posible_salida"] = df["marca_probabilidad"] & (df["L"] >= l_minimo)

    c = cfg["clasificacion"]
    tipo_acot, _ = clasificar(df["adi_acotado"], df["cv2_acotado"], c["umbral_adi"], c["umbral_cv2"])
    df["tipo_acotado"] = np.where(df["posible_salida"], tipo_acot, "")
    for col in ("adi_acotado", "cv2_acotado", "n_periodos_acotado"):
        df.loc[~df["posible_salida"], col] = np.nan
    df["tipo_demanda"] = df["tipo_demanda"].astype(str)
    df.round(6).to_csv(dir_eda / "salida_venta_series.csv", index_label="id")

    marcadas = df[df["posible_salida"]]
    resumen = pd.concat([
        pd.DataFrame([{"nivel": "TOTAL", "grupo": "TOTAL", "series": len(df), "marcadas": len(marcadas)}]),
        df.groupby("cat_id", observed=True)["posible_salida"].agg(series="size", marcadas="sum")
          .reset_index().rename(columns={"cat_id": "grupo"}).assign(nivel="categoria"),
        df.groupby("store_id", observed=True)["posible_salida"].agg(series="size", marcadas="sum")
          .reset_index().rename(columns={"store_id": "grupo"}).assign(nivel="tienda"),
    ], ignore_index=True)[["nivel", "grupo", "series", "marcadas"]]
    resumen["pct_marcadas"] = 100 * resumen["marcadas"] / resumen["series"]
    resumen.round(4).to_csv(dir_eda / "salida_venta_resumen.csv", index=False)

    def cuantiles(s, nombre):
        d = {"conjunto": nombre, "n_series": int(s.size), "media": s.mean(), "min": s.min()}
        d.update({f"p{int(q * 100):02d}": s.quantile(q) for q in CUANTILES})
        d["max"] = s.max()
        return d
    dist = pd.DataFrame([cuantiles(df.loc[con_ventas, "L"], "todas con ventas"),
                         cuantiles(marcadas["L"], "posible salida")])
    dist.round(2).to_csv(dir_eda / "salida_venta_L_cuantiles.csv", index=False)

    cambios = pd.crosstab(marcadas["tipo_demanda"], marcadas["tipo_acotado"]).reindex(
        index=list(TIPOS_DEMANDA), columns=list(TIPOS_DEMANDA), fill_value=0)
    cambios.to_csv(dir_eda / "salida_venta_cambios.csv", index_label="vigente \\ acotado")

    # Proporciones globales si a las marcadas se les aplicara la clasificación acotada (hipotético)
    hipotetico = df["tipo_demanda"].where(~df["posible_salida"], df["tipo_acotado"])
    comparacion = pd.DataFrame({
        "vigente": df["tipo_demanda"].value_counts(normalize=True).reindex(TIPOS_DEMANDA, fill_value=0) * 100,
        "marcadas_acotadas": hipotetico.value_counts(normalize=True).reindex(TIPOS_DEMANDA, fill_value=0) * 100})

    # Histograma de L (escala log en L + 1)
    fig, ax = plt.subplots(figsize=(9, 5))
    l1 = df.loc[con_ventas, "L"] + 1
    bins = np.logspace(0, np.log10(l1.max()) + 1e-9, 50)
    ax.hist(l1, bins=bins, color=SERIE, edgecolor=SUPERFICIE, linewidth=0.8)
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: coma(x, 0)))
    estilo(ax, f"Días desde la última venta hasta el fin de train (L), {coma(int(con_ventas.sum()), 0)} series",
           xlabel="L + 1 (escala logarítmica)", ylabel="número de series")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: coma(y, 0)))
    ax.axvline(l_minimo + 1, color=TINTA, linewidth=0.9, linestyle="--")
    ax.text(0.98, 0.95, f"Posible salida de venta (prob < {coma(umbral, 2)} y L ≥ {l_minimo}): "
            f"{coma(len(marcadas), 0)} series",
            transform=ax.transAxes, ha="right", va="top", fontsize=9, color=TINTA)
    ax.text(0.98, 0.88, f"Mediana de L: {coma(df.loc[con_ventas, 'L'].median(), 0)} días; "
            f"en las marcadas: {coma(marcadas['L'].median(), 0)} días",
            transform=ax.transAxes, ha="right", va="top", fontsize=9, color=TINTA_SEC)
    guardar(fig, dir_eda / "salida_venta_L.png")

    print(f"\nSeries sin ninguna venta en train (sin L): {int((~con_ventas).sum())}")
    print(f"Solo probabilidad < {umbral}: {int(df['marca_probabilidad'].sum()):,} series")
    print(f"Posible salida de venta (prob < {umbral} y L >= {l_minimo}): {len(marcadas):,} de {int(con_ventas.sum()):,} "
          f"series con ventas ({100 * len(marcadas) / con_ventas.sum():.2f} %)")
    print(resumen.round(2).to_string(index=False))
    print("\nDistribución de L:")
    print(dist.round(1).to_string(index=False))
    print("\nTipo vigente (filas) frente a tipo acotado a la última venta (columnas), series marcadas:")
    print(cambios.to_string())
    print(f"Series marcadas que cambian de tipo: {int((marcadas['tipo_demanda'] != marcadas['tipo_acotado']).sum())}")
    print(f"ADI de las marcadas: mediana vigente {marcadas['adi'].median():.2f} -> acotada {marcadas['adi_acotado'].median():.2f}")
    print("\nProporción global por tipo (%), vigente frente a hipotética con las marcadas acotadas:")
    print(comparacion.round(2).to_string())
    informar_memoria("final")


if __name__ == "__main__":
    main()
