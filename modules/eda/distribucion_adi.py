"""
Comprobaciones sobre ADI y frecuencia de venta (Sprint 1, P1).

Entradas (ya generadas, solo train):
  data/interim/ventas_muestra_largo.parquet        muestra serie x día, días a la venta
  data/interim/clasificacion_series_train.parquet  ADI y CV² de las 30.490 series

Días de la muestra: los mismos que usa la clasificación (desde el primer precio y sin los
tienda-días cerrados; registro, C2). Los días cerrados se detectan con una pasada por las
ventas de train (`dias_tienda_cerrada`).

Salidas:
  output/eda/muestra_dias_con_venta.csv   % de días con venta y con venta cero por serie de la muestra
  output/eda/adi_cuantiles.csv            cuantiles de ADI (global y por categoría)
  output/eda/adi_histograma.png           histograma de ADI con el umbral marcado

Relación usada: ADI = días a la venta / días con venta = 1 / p, siendo p la
fracción de días con venta. Por tanto ADI >= u  <=>  p <= 1/u (con u = 1,32, p <= 75,76 %).

Uso (desde la raíz del repositorio):
    python -m modules.eda.distribucion_adi
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

from modules.config import cargar_config
from modules.datos.carga import comprobar_ficheros, dias_en_ventas, dias_tienda_cerrada
from modules.datos.clasificacion import tienda_abierta_largo
from modules.datos.division import Division

CUANTILES = [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]

# Paleta de referencia (skill dataviz, modo claro): una sola serie
SUPERFICIE, TINTA, TINTA_SEC, SERIE = "#fcfcfb", "#0b0b0b", "#52514e", "#2a78d6"


def coma(x: float, decimales: int = 2) -> str:
    return f"{x:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def cuantiles_adi(clas: pd.DataFrame) -> pd.DataFrame:
    def fila(nombre, s):
        d = {"grupo": nombre, "n_series": int(s.size), "media": s.mean(), "min": s.min()}
        d.update({f"p{int(q * 100):02d}": s.quantile(q) for q in CUANTILES})
        d["max"] = s.max()
        return d
    validas = clas.dropna(subset=["adi"])
    filas = [fila("global", validas["adi"])]
    filas += [fila(cat, g["adi"]) for cat, g in validas.groupby("cat_id", observed=True)]
    return pd.DataFrame(filas).round(4)


def histograma(adi: pd.Series, umbral: float, ruta) -> None:
    adi = adi.dropna()
    bins = np.logspace(0, np.log10(adi.max()) + 1e-9, 60)
    pct_sobre = (adi >= umbral).mean() * 100

    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    fig.patch.set_facecolor(SUPERFICIE)
    ax.set_facecolor(SUPERFICIE)
    ax.hist(adi, bins=bins, color=SERIE, edgecolor=SUPERFICIE, linewidth=0.8)
    ax.set_xscale("log")
    ax.axvline(umbral, color=TINTA, linestyle="--", linewidth=1.2)
    # Anotación en la zona vacía de la cola, sin tapar barras
    ax.text(0.98, 0.95, f"Línea discontinua: umbral ADI = {coma(umbral)}", transform=ax.transAxes,
            color=TINTA, fontsize=9, ha="right", va="top")
    ax.text(0.98, 0.88,
            f"ADI ≥ {coma(umbral)}: {coma(pct_sobre, 1)} % de las series\n"
            f"ADI < {coma(umbral)}: {coma(100 - pct_sobre, 1)} %", transform=ax.transAxes,
            color=TINTA_SEC, fontsize=9, ha="right", va="top")

    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: coma(x, 0) if x >= 1 else coma(x, 1)))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: coma(y, 0)))
    ax.set_xlabel("ADI (escala logarítmica)", color=TINTA_SEC)
    ax.set_ylabel("Número de series", color=TINTA_SEC)
    ax.set_title(f"Distribución de ADI en entrenamiento ({coma(len(adi), 0)} series con ADI definido)",
                 color=TINTA, fontsize=11, loc="left")
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color("#c3c2b7")
    ax.tick_params(colors=TINTA_SEC, labelsize=8)
    ax.grid(axis="y", color="#e6e5e0", linewidth=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(ruta, facecolor=SUPERFICIE)
    plt.close(fig)


def main():
    cfg = cargar_config()
    dir_interim, dir_eda = cfg["rutas"]["interim"], cfg["rutas"]["eda"]
    umbral = cfg["clasificacion"]["umbral_adi"]
    p_max = 1 / umbral

    rutas = comprobar_ficheros(cfg["rutas"]["raw"])
    division = Division.desde_config(cfg, pd.read_parquet(dir_interim / "calendar.parquet"),
                                     dias_en_ventas(rutas["ventas"]))
    clas = pd.read_parquet(dir_interim / "clasificacion_series_train.parquet",
                           columns=["id", "cat_id", "n_periodos", "n_demandas", "adi", "tipo_demanda", "aviso",
                                    "firma_division"])
    if set(clas["firma_division"].unique()) != {division.firma()}:
        raise AssertionError("La clasificación se generó con otra división temporal (RNF-12)")
    clas = clas.drop(columns="firma_division")
    muestra = pd.read_parquet(dir_interim / "ventas_muestra_largo.parquet", columns=["id", "store_id", "dia_num", "ventas"])
    if muestra["dia_num"].max() > division.dia_fin_train:
        raise AssertionError("Fuga: días posteriores al corte de train")
    cerrado = dias_tienda_cerrada(rutas["ventas"], division.dia_fin_train, cfg["carga"]["filas_por_bloque"])
    abierto = tienda_abierta_largo(muestra["store_id"], muestra["dia_num"], cerrado)
    print(f"Filas de la muestra en tienda-días cerrados (excluidas, C2): {int((~abierto).sum()):,}")
    muestra = muestra.loc[abierto, ["id", "ventas"]]
    muestra["id"] = muestra["id"].astype(str)

    # % de días con venta por serie de la muestra
    muestra["con_venta"] = muestra["ventas"] > 0
    por_serie = muestra.groupby("id")["con_venta"].agg(dias="size", dias_con_venta="sum").reset_index()
    por_serie["pct_dias_con_venta"] = 100 * por_serie["dias_con_venta"] / por_serie["dias"]
    por_serie["pct_dias_venta_cero"] = 100 - por_serie["pct_dias_con_venta"]
    por_serie = por_serie.merge(clas, on="id", how="left", validate="one_to_one")

    # Coherencia entre la muestra y el cálculo de todas las series
    incoherentes = ((por_serie["dias"] != por_serie["n_periodos"])
                    | (por_serie["dias_con_venta"] != por_serie["n_demandas"])).sum()
    print(f"Series de la muestra: {len(por_serie):,}; con días o ventas distintos a la clasificación global: {incoherentes}")

    # Equivalencia ADI >= umbral <=> p <= 1/umbral (series con ADI definido)
    definidas = por_serie.dropna(subset=["adi"])
    adi_ge = definidas["adi"] >= umbral
    p = definidas["dias_con_venta"] / definidas["dias"]
    exacta = (adi_ge == (p <= p_max)).mean() * 100
    con_76 = adi_ge == (definidas["pct_dias_con_venta"] <= 76)
    print(f"Series con ADI definido: {len(definidas):,} (sin definir: {len(por_serie) - len(definidas)})")
    print(f"ADI >= {umbral}  <=>  vende en <= {100 * p_max:.4f} % de los días: coincide en el {exacta:.2f} % de las series")
    print(f"ADI >= {umbral}  <=>  vende en <= 76 % de los días: coincide en el {con_76.mean() * 100:.2f} % "
          f"({(~con_76).sum()} discrepancias)")
    if (~con_76).any():
        print(definidas.loc[~con_76, ["id", "dias", "dias_con_venta", "pct_dias_con_venta", "adi", "tipo_demanda"]]
              .to_string(index=False))
    franja = definidas["pct_dias_con_venta"].between(100 * p_max, 76, inclusive="neither").sum()
    print(f"Series con % de días con venta en ({100 * p_max:.2f} %, 76 %): {franja}")

    # % de días con venta cero
    print(f"\n% medio de días con venta cero por serie (muestra): {por_serie['pct_dias_venta_cero'].mean():.2f} %")
    print(f"  mediana por serie: {por_serie['pct_dias_venta_cero'].median():.2f} %")
    print(f"  sobre el total de filas serie-día: {100 * (~muestra['con_venta']).mean():.2f} %")
    por_serie.round(4).to_csv(dir_eda / "muestra_dias_con_venta.csv", index=False)

    # Distribución de ADI de todas las series
    cuant = cuantiles_adi(clas)
    cuant.to_csv(dir_eda / "adi_cuantiles.csv", index=False)
    print("\nCuantiles de ADI (series con ADI definido):")
    print(cuant.to_string(index=False))
    histograma(clas["adi"], umbral, dir_eda / "adi_histograma.png")
    print(f"\nHistograma: {dir_eda / 'adi_histograma.png'}")


if __name__ == "__main__":
    main()
