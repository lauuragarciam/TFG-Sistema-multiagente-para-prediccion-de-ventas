"""
Estudio de eventos rápido alrededor de cambios de precio (registro, E1). Muestra, solo train.

Unidad: serie x semana Walmart completa (7 días dentro de train).
Evento: semana t con |precio_t / precio_{t-1} - 1| >= 5 %, precio estable (±0,5 %) en las
4 semanas previas y las 9 semanas t-4..t+4 completas y con precio.
Medida: ventas de la semana t+k / media de ventas de t-4..t-1, para k = -4..4.
Agregado: cociente de sumas sobre los eventos (robusto a series pequeñas), con IC 95 %
bootstrap (1.000 remuestreos de eventos, semilla de la configuración), y mediana de cocientes.

Regla de conclusión (fijada antes de mirar el resultado): si el IC de la semana 0 incluye 1
o el efecto es menor del 5 %, se anota como "efecto no atribuible en el EDA".

Salidas (output/eda/): p3_eventos_precio.csv, p3_eventos_precio.png

Uso (desde la raíz del repositorio):
    python -m modules.eda.precio_eventos
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from modules.config import cargar_config
from modules.datos.carga import comprobar_ficheros, dias_en_ventas
from modules.datos.division import Division
from modules.eda.preguntas_eda import SUPERFICIE, TINTA, TINTA_SEC, estilo, guardar, coma

UMBRAL_CAMBIO, TOLERANCIA, PRE, POST, N_BOOT = 0.05, 0.005, 4, 4, 1000
COLORES = {"bajada": "#2a78d6", "subida": "#eb6834"}


def main():
    cfg = cargar_config()
    dir_interim, dir_eda = cfg["rutas"]["interim"], cfg["rutas"]["eda"]
    rutas = comprobar_ficheros(cfg["rutas"]["raw"])
    division = Division.desde_config(cfg, pd.read_parquet(dir_interim / "calendar.parquet"),
                                     dias_en_ventas(rutas["ventas"]))
    rng = np.random.default_rng(cfg["muestra_eda"]["semilla"])

    largo = pd.read_parquet(dir_interim / "ventas_muestra_largo.parquet",
                            columns=["id", "cat_id", "wm_yr_wk", "dia_num", "ventas"])
    if largo["dia_num"].max() > division.dia_fin_train:
        raise AssertionError("Fuga: días posteriores al corte de train")
    largo["id"] = largo["id"].astype(str)
    semanal = largo.groupby(["id", "wm_yr_wk"]).agg(ventas=("ventas", "sum"), dias=("dia_num", "size"),
                                                    cat_id=("cat_id", "first")).reset_index()

    precios = pd.read_parquet(dir_interim / "sell_prices_train.parquet")
    precios["id"] = precios["item_id"].astype(str) + "_" + precios["store_id"].astype(str) + "_evaluation"
    precios = precios.loc[precios["id"].isin(semanal["id"].unique()), ["id", "wm_yr_wk", "sell_price"]]
    df = semanal.merge(precios, on=["id", "wm_yr_wk"], how="left", validate="one_to_one")
    df = df.sort_values(["id", "wm_yr_wk"], ignore_index=True)
    completa = (df["dias"] == 7) & df["sell_price"].notna()

    # Desplazamientos por serie (las semanas de una serie son consecutivas: no hay huecos de precio)
    g = df.groupby("id", sort=False)
    cambio = df["sell_price"] / g["sell_price"].shift(1) - 1
    estable = np.ones(len(df), dtype=bool)
    for j in range(2, PRE + 1):
        estable &= (g["sell_price"].shift(j) / g["sell_price"].shift(1) - 1).abs().fillna(np.inf).to_numpy() <= TOLERANCIA
    ok_ventana = np.ones(len(df), dtype=bool)
    ventas_k = {}
    for k in range(-PRE, POST + 1):
        ok_ventana &= g["dias"].shift(-k).eq(7).to_numpy() & g["sell_price"].shift(-k).notna().to_numpy()
        ventas_k[k] = g["ventas"].shift(-k).to_numpy(dtype=float)
    base = np.nanmean(np.column_stack([ventas_k[k] for k in range(-PRE, 0)]), axis=1)
    evento = completa & (cambio.abs() >= UMBRAL_CAMBIO).to_numpy() & estable & ok_ventana & (base > 0)

    ev = df.loc[evento, ["id", "cat_id", "wm_yr_wk"]].copy()
    ev["tipo"] = np.where(cambio[evento] < 0, "bajada", "subida")
    ev["cambio_precio"] = cambio[evento].to_numpy()
    ev["base"] = base[evento]
    for k in range(-PRE, POST + 1):
        ev[f"v{k}"] = ventas_k[k][evento]

    filas = []
    for (tipo, grupo), d in [((t, "TOTAL"), x) for t, x in ev.groupby("tipo")] + list(ev.groupby(["tipo", "cat_id"])):
        idx = rng.integers(0, len(d), size=(N_BOOT, len(d)))
        for k in range(-PRE, POST + 1):
            v, b = d[f"v{k}"].to_numpy(), d["base"].to_numpy()
            boot = v[idx].sum(axis=1) / b[idx].sum(axis=1)
            filas.append({"tipo": tipo, "grupo": grupo, "semana": k, "n_eventos": len(d),
                          "n_series": d["id"].nunique(), "cambio_precio_mediano": d["cambio_precio"].median(),
                          "ratio_sumas": v.sum() / b.sum(), "ic95_inf": np.quantile(boot, 0.025),
                          "ic95_sup": np.quantile(boot, 0.975), "mediana_ratios": np.median(v / b)})
    res = pd.DataFrame(filas)

    # Conclusión con la regla fijada
    s0 = res[(res["grupo"] == "TOTAL") & (res["semana"] == 0)].set_index("tipo")
    conclusion = {}
    for tipo, r in s0.iterrows():
        incluye_1 = r["ic95_inf"] <= 1 <= r["ic95_sup"]
        pequeno = abs(r["ratio_sumas"] - 1) < 0.05
        conclusion[tipo] = ("efecto no atribuible en el EDA" if incluye_1 or pequeno
                            else f"asociación en la semana del cambio: {100 * (r['ratio_sumas'] - 1):+.1f} %")
    res["conclusion_semana0_total"] = res["tipo"].map(conclusion)
    res.round(4).to_csv(dir_eda / "p3_eventos_precio.csv", index=False)

    fig, ax = plt.subplots(figsize=(9, 5))
    for tipo in ("bajada", "subida"):
        r = res[(res["grupo"] == "TOTAL") & (res["tipo"] == tipo)]
        if r.empty:
            continue
        n = int(r["n_eventos"].iloc[0])
        ax.fill_between(r["semana"], r["ic95_inf"], r["ic95_sup"], color=COLORES[tipo], alpha=0.15, linewidth=0)
        ax.plot(r["semana"], r["ratio_sumas"], color=COLORES[tipo], linewidth=2, marker="o", markersize=6,
                label=f"{tipo} de precio ≥ 5 % ({coma(n, 0)} eventos)")
    ax.axhline(1, color=TINTA, linewidth=0.9, linestyle="--")
    ax.axvline(-0.5, color=TINTA_SEC, linewidth=0.8, linestyle=":")
    ax.set_xticks(range(-PRE, POST + 1))
    estilo(ax, "Ventas alrededor de un cambio de precio (semana 0 = primera semana con el precio nuevo)",
           xlabel="semanas respecto al cambio", ylabel="ventas / media de las 4 semanas previas")
    ax.legend(frameon=False, fontsize=8, labelcolor=TINTA_SEC, loc="upper left")
    ax.text(0, -0.17, "Banda: IC 95 % bootstrap del cociente de sumas. Muestra, solo train. Asociación, no causalidad.",
            transform=ax.transAxes, fontsize=7, color=TINTA_SEC)
    guardar(fig, dir_eda / "p3_eventos_precio.png")

    print(f"Eventos: {len(ev):,} ({ev['tipo'].value_counts().to_dict()}) en {ev['id'].nunique():,} series")
    print(res[res["grupo"] == "TOTAL"][["tipo", "semana", "n_eventos", "ratio_sumas", "ic95_inf", "ic95_sup",
                                        "mediana_ratios"]].round(3).to_string(index=False))
    print("\nSemana 0 por categoría:")
    print(res[(res["semana"] == 0) & (res["grupo"] != "TOTAL")][["tipo", "grupo", "n_eventos", "ratio_sumas",
                                                                  "ic95_inf", "ic95_sup"]].round(3).to_string(index=False))
    print("\nConclusión (regla fijada):", conclusion)


if __name__ == "__main__":
    main()
