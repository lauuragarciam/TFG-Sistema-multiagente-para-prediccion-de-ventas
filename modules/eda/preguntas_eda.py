"""
Preguntas P2, P3 y P4 del EDA del Sprint 1, con la muestra y solo con d_1..d_fin_train.

P2  Ventas medias por día de la semana, por evento y por día SNAP.
P3  Efecto de la variación de precio dentro de cada serie (respecto a su precio habitual).
P4  Estacionalidad semanal y anual agregando por departamento y por tienda.

Entradas (data/interim/): ventas_muestra_largo, calendar_train, sell_prices_train.
Salidas (output/eda/): p2_*.csv/png, p3_*.csv/png, p4_*.csv/png.

Índices normalizados por serie (registro, E2), para que no dominen las series grandes:
  indice        ventas / media de la serie en sus días a la venta
  indice_dow    ventas / media de la serie en ese día de la semana  (controla el día de la semana)
  indice_local  ventas / media móvil centrada de 57 días de la serie (controla tendencia y nivel local)

Uso (desde la raíz del repositorio):
    python -m modules.eda.preguntas_eda
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.ticker import FuncFormatter

from modules.config import cargar_config
from modules.datos.carga import comprobar_ficheros, dias_en_ventas
from modules.datos.division import Division
from modules.memoria import informar_memoria

DIAS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DIAS_ES = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
MESES_ES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
CATS = ["FOODS", "HOBBIES", "HOUSEHOLD"]
PERFIL_DIAS_PREVIOS = 7     # el perfil día a día de los previos a evento se guarda hasta 7 días
VENTANA_LOCAL = 57          # días de la media móvil centrada (±28)
TRAMOS_PRECIO = [-np.inf, -0.15, -0.05, -0.005, 0.005, 0.05, 0.15, np.inf]
ETIQUETAS_PRECIO = ["≤ −15 %", "−15 a −5 %", "−5 a −0,5 %", "habitual (±0,5 %)", "+0,5 a +5 %", "+5 a +15 %", "> +15 %"]

# Paleta de referencia de la skill dataviz (modo claro): orden categórico fijo
SUPERFICIE, TINTA, TINTA_SEC, EJE, REJILLA = "#fcfcfb", "#0b0b0b", "#52514e", "#c3c2b7", "#e6e5e0"
COLOR_CAT = {"FOODS": "#2a78d6", "HOBBIES": "#eb6834", "HOUSEHOLD": "#1baf7a"}
DIVERGENTE = LinearSegmentedColormap.from_list("azul_gris_rojo", ["#1c5cab", "#86b6ef", "#f0efec", "#ef9a96", "#c22f2f"])


# ------------------------------------------------------------------ utilidades

def coma(x: float, dec: int = 2) -> str:
    return f"{x:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def estilo(ax, titulo: str, xlabel: str = "", ylabel: str = ""):
    ax.set_facecolor(SUPERFICIE)
    ax.set_title(titulo, color=TINTA, fontsize=11, loc="left")
    ax.set_xlabel(xlabel, color=TINTA_SEC)
    ax.set_ylabel(ylabel, color=TINTA_SEC)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color(EJE)
    ax.tick_params(colors=TINTA_SEC, labelsize=8)
    ax.grid(axis="y", color=REJILLA, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: coma(y, 2)))


def guardar(fig, ruta):
    fig.patch.set_facecolor(SUPERFICIE)
    fig.tight_layout()
    fig.savefig(ruta, facecolor=SUPERFICIE, dpi=150)
    plt.close(fig)


def barras_por_categoria(tabla: pd.DataFrame, x: str, orden: list, etiquetas: list, valor: str,
                         titulo: str, ylabel: str, ruta, referencia: float | None = 1.0):
    fig, ax = plt.subplots(figsize=(10, 5))
    ancho = 0.8 / len(CATS)
    pos = np.arange(len(orden))
    for i, cat in enumerate(CATS):
        sub = tabla[tabla["grupo"] == cat].set_index(x).reindex(orden)
        ax.bar(pos + (i - 1) * ancho, sub[valor], width=ancho * 0.92, color=COLOR_CAT[cat],
               edgecolor=SUPERFICIE, linewidth=0.8, label=cat)
    if referencia is not None:
        ax.axhline(referencia, color=TINTA, linewidth=0.9, linestyle="--")
    ax.set_xticks(pos, etiquetas)
    estilo(ax, titulo, ylabel=ylabel)
    ax.legend(frameon=False, fontsize=8, labelcolor=TINTA_SEC, ncols=3, loc="upper left")
    guardar(fig, ruta)


def heatmap(matriz: pd.DataFrame, columnas: list, titulo: str, ruta, separacion: int | None = None):
    valores = matriz.to_numpy(dtype=float)
    extremo = max(abs(np.nanmin(valores) - 1), abs(np.nanmax(valores) - 1))
    norm = TwoSlopeNorm(vcenter=1.0, vmin=1 - extremo, vmax=1 + extremo)
    fig, ax = plt.subplots(figsize=(1.1 + 0.62 * len(columnas), 0.9 + 0.36 * len(matriz)))
    im = ax.imshow(valores, cmap=DIVERGENTE, norm=norm, aspect="auto")
    for (i, j), v in np.ndenumerate(valores):
        r, g, b, _ = DIVERGENTE(norm(v))
        claro = 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.55
        ax.text(j, i, coma(v, 2), ha="center", va="center", fontsize=7, color=TINTA if claro else "white")
    ax.set_xticks(range(len(columnas)), columnas)
    ax.set_yticks(range(len(matriz)), matriz.index)
    if separacion is not None:
        ax.axhline(separacion - 0.5, color=SUPERFICIE, linewidth=3)
    ax.tick_params(colors=TINTA_SEC, labelsize=8, length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(titulo, color=TINTA, fontsize=10, loc="left")
    barra = fig.colorbar(im, ax=ax, shrink=0.8)
    barra.ax.tick_params(labelsize=7, colors=TINTA_SEC)
    barra.ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: coma(y, 2)))
    barra.set_label("índice (1 = media del grupo)", color=TINTA_SEC, fontsize=8)
    guardar(fig, ruta)


def agregar(df: pd.DataFrame, claves: list, por_categoria: bool = True) -> pd.DataFrame:
    """Medias por grupo, global y por categoría (columna 'grupo')."""
    def calc(d, grupo):
        t = d.groupby(claves, observed=True).agg(
            n_filas=("ventas", "size"), n_series=("id", "nunique"), ventas_medias=("ventas", "mean"),
            indice=("indice", "mean"), indice_dow=("indice_dow", "mean")).reset_index()
        t.insert(0, "grupo", grupo)
        return t
    partes = [calc(df, "TOTAL")]
    if por_categoria:
        partes += [calc(df[df["cat_id"] == c], c) for c in CATS]
    return pd.concat(partes, ignore_index=True)


# ------------------------------------------------------------------ carga

def cargar(cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, Division]:
    """Muestra larga de train con calendario, SNAP del estado e índices por serie.

    La ventana de días previos a evento sale de [eda].ventana_previa_evento (registro, N5).
    `dias_hasta_evento` (0 = día de evento) permite construir otras ventanas sin recargar.
    """
    ventana = cfg["eda"]["ventana_previa_evento"]
    dir_interim = cfg["rutas"]["interim"]
    rutas = comprobar_ficheros(cfg["rutas"]["raw"])
    cal_completo = pd.read_parquet(dir_interim / "calendar.parquet")
    division = Division.desde_config(cfg, cal_completo, dias_en_ventas(rutas["ventas"]))
    del cal_completo

    cal = pd.read_parquet(dir_interim / "calendar_train.parquet")
    largo = pd.read_parquet(dir_interim / "ventas_muestra_largo.parquet")
    if cal["dia_num"].max() > division.dia_fin_train or largo["dia_num"].max() > division.dia_fin_train:
        raise AssertionError("Fuga: datos posteriores al corte de train")

    # Eventos: tipo del día o ventana de días previos (solo con eventos de train)
    eventos = np.sort(cal.loc[cal["event_name_1"].notna(), "dia_num"].to_numpy())
    siguiente = np.searchsorted(eventos, cal["dia_num"].to_numpy(), side="right")
    dist = np.where(siguiente < len(eventos), eventos[np.minimum(siguiente, len(eventos) - 1)] - cal["dia_num"], 10**6)
    cal["categoria_evento"] = np.where(
        cal["event_type_1"].notna(), cal["event_type_1"].astype(str),
        np.where(dist <= ventana, f"{ventana} días previos", "sin evento"))
    cal["dias_hasta_evento"] = np.where(cal["event_type_1"].notna(), 0, dist)

    n = len(largo)
    largo = largo.merge(
        cal[["dia_num", "weekday", "month", "year", "event_name_1", "categoria_evento",
             "dias_hasta_evento", "snap_CA", "snap_TX", "snap_WI"]],
        on="dia_num", how="left", validate="many_to_one")
    if len(largo) != n:
        raise AssertionError("La unión con calendar ha cambiado el número de filas")
    estado = largo["state_id"].astype(str)
    largo["snap"] = np.select([estado == "CA", estado == "TX", estado == "WI"],
                              [largo["snap_CA"], largo["snap_TX"], largo["snap_WI"]], default=0).astype("int8")
    largo = largo.drop(columns=["snap_CA", "snap_TX", "snap_WI"])
    largo["weekday"] = pd.Categorical(largo["weekday"].astype(str), categories=DIAS, ordered=True)
    largo["dia_mes"] = largo["date"].dt.day.astype("int8")

    # Índices por serie
    largo = largo.sort_values(["id", "dia_num"], ignore_index=True)
    media = largo.groupby("id", observed=True)["ventas"].transform("mean")
    media_dow = largo.groupby(["id", "weekday"], observed=True)["ventas"].transform("mean")
    media_local = (largo.groupby("id", observed=True)["ventas"]
                   .transform(lambda s: s.rolling(VENTANA_LOCAL, center=True, min_periods=15).mean()))
    with np.errstate(divide="ignore", invalid="ignore"):
        largo["indice"] = (largo["ventas"] / media).where(media > 0).astype("float32")
        largo["indice_dow"] = (largo["ventas"] / media_dow).where(media_dow > 0).astype("float32")
        largo["indice_local"] = (largo["ventas"] / media_local).where(media_local > 0).astype("float32")
    print(f"Muestra: {len(largo):,} filas, {largo['id'].nunique():,} series; "
          f"series sin ninguna venta (sin índice): {int((media == 0).groupby(largo['id'], observed=True).any().sum())}")
    return largo, cal, division


# ------------------------------------------------------------------ P2

def p2(largo: pd.DataFrame, dir_eda, ventana: int):
    # Día de la semana
    dow = agregar(largo, ["weekday"])
    dow["dia"] = dow["weekday"].map(dict(zip(DIAS, DIAS_ES)))
    dow.round(4).to_csv(dir_eda / "p2_dia_semana.csv", index=False)
    barras_por_categoria(dow, "weekday", DIAS, DIAS_ES, "indice",
                         "Ventas por día de la semana (índice: ventas / media de la serie)",
                         "índice medio", dir_eda / "p2_dia_semana.png")

    # Eventos por tipo (incluye National sin Navidad, que tiene las tiendas cerradas)
    tipos = agregar(largo, ["categoria_evento"])
    sin_navidad = largo[(largo["categoria_evento"] == "National") & (largo["event_name_1"].astype(str) != "Christmas")]
    extra = agregar(sin_navidad, ["categoria_evento"])
    extra["categoria_evento"] = "National sin Christmas"
    tipos = pd.concat([tipos, extra], ignore_index=True)
    tipos.round(4).to_csv(dir_eda / "p2_eventos_por_tipo.csv", index=False)
    orden = ["Cultural", "National", "National sin Christmas", "Religious", "Sporting",
             f"{ventana} días previos", "sin evento"]
    etiquetas = ["Cultural", "National", "National\nsin Navidad", "Religious", "Sporting",
                 f"{ventana} días\nprevios", "sin evento"]
    barras_por_categoria(tipos, "categoria_evento", orden, etiquetas, "indice_dow",
                         "Ventas en días de evento (índice: ventas / media de la serie en ese día de la semana)",
                         "índice medio", dir_eda / "p2_eventos.png")

    # Eventos por nombre y perfil de los días previos
    por_nombre = agregar(largo[largo["event_name_1"].notna()], ["event_name_1", "categoria_evento"])
    por_nombre["n_dias"] = por_nombre["event_name_1"].map(
        largo.loc[largo["event_name_1"].notna()].groupby("event_name_1", observed=True)["dia_num"].nunique())
    por_nombre.sort_values(["grupo", "indice_dow"]).round(4).to_csv(dir_eda / "p2_eventos_por_nombre.csv", index=False)
    previos = agregar(largo[largo["dias_hasta_evento"] <= PERFIL_DIAS_PREVIOS], ["dias_hasta_evento"])
    previos.round(4).to_csv(dir_eda / "p2_eventos_dias_previos.csv", index=False)

    # SNAP: todos los días y control por mitad del mes (E3); el índice dow controla el día de la semana
    filas = []
    for control, datos in (("todos los días", largo), ("días 1-15 del mes", largo[largo["dia_mes"] <= 15])):
        for (estado, cat), d in datos.groupby(["state_id", "cat_id"], observed=True):
            s, ns = d[d["snap"] == 1], d[d["snap"] == 0]
            filas.append({"control": control, "estado": estado, "grupo": cat,
                          "n_filas_snap": len(s), "n_filas_no_snap": len(ns),
                          "ventas_medias_snap": s["ventas"].mean(), "ventas_medias_no_snap": ns["ventas"].mean(),
                          "indice_dow_snap": s["indice_dow"].mean(), "indice_dow_no_snap": ns["indice_dow"].mean()})
    snap = pd.DataFrame(filas)
    snap["ratio_indice_snap_no_snap"] = snap["indice_dow_snap"] / snap["indice_dow_no_snap"]
    snap.round(4).to_csv(dir_eda / "p2_snap.csv", index=False)

    ctrl = snap[snap["control"] == "días 1-15 del mes"].copy()
    ctrl["clave"] = ctrl["estado"].astype(str)
    barras_por_categoria(ctrl.rename(columns={"clave": "estado_"}), "estado_", ["CA", "TX", "WI"], ["CA", "TX", "WI"],
                         "ratio_indice_snap_no_snap",
                         "Ventas en días SNAP frente a no SNAP (días 1-15 del mes, mismo día de la semana)",
                         "ratio de índices SNAP / no SNAP", dir_eda / "p2_snap.png")
    return dow, tipos, snap


# ------------------------------------------------------------------ P3

def p3(largo: pd.DataFrame, cfg: dict, division: Division, dir_eda, ventana: int):
    precios = pd.read_parquet(cfg["rutas"]["interim"] / "sell_prices_train.parquet")
    if precios["wm_yr_wk"].max() > division.semana_fin_train:
        raise AssertionError("Fuga: precios posteriores a la semana de corte")
    precios["id"] = precios["item_id"].astype(str) + "_" + precios["store_id"].astype(str) + "_evaluation"
    precios = precios[precios["id"].isin(largo["id"].cat.categories)]
    precios["id"] = pd.Categorical(precios["id"], categories=largo["id"].cat.categories)

    # Precio habitual: mediana de los precios semanales de la serie en train (registro, N4)
    referencia = precios.groupby("id", observed=True)["sell_price"].median().rename("precio_ref")

    n = len(largo)
    df = largo.merge(precios[["id", "wm_yr_wk", "sell_price"]], on=["id", "wm_yr_wk"], how="left",
                     validate="many_to_one")
    if len(df) != n or df["dia_num"].max() > division.dia_fin_train:
        raise AssertionError("La unión ventas-precios ha generado filas nuevas o posteriores al corte")
    sin_precio = int(df["sell_price"].isna().sum())
    df = df.join(referencia, on="id")
    df["var_precio"] = df["sell_price"] / df["precio_ref"] - 1
    df["tramo_precio"] = pd.cut(df["var_precio"], TRAMOS_PRECIO, labels=ETIQUETAS_PRECIO)
    print(f"P3: filas sin precio tras la unión: {sin_precio}")

    filas = []
    for version, datos in (("todos los días", df),
                           (f"sin eventos ni {ventana} días previos", df[df["categoria_evento"] == "sin evento"])):
        for grupo, d in [("TOTAL", datos)] + [(c, datos[datos["cat_id"] == c]) for c in CATS]:
            t = d.groupby("tramo_precio", observed=False).agg(
                n_filas=("ventas", "size"), n_series=("id", "nunique"),
                indice_dow=("indice_dow", "mean"), indice_local=("indice_local", "mean")).reset_index()
            t.insert(0, "grupo", grupo)
            t.insert(0, "version", version)
            filas.append(t)
    tramos = pd.concat(filas, ignore_index=True)
    tramos.round(4).to_csv(dir_eda / "p3_precio_por_tramo.csv", index=False)

    # Correlación dentro de cada serie (Spearman) entre variación de precio e índice local, sin días de evento
    base = df[(df["categoria_evento"] == "sin evento")].dropna(subset=["var_precio", "indice_local"])
    var_serie = base.groupby("id", observed=True)["var_precio"].agg(lambda s: s.nunique() > 1)
    con_cambio = var_serie[var_serie].index
    corr = (base[base["id"].isin(con_cambio)].groupby("id", observed=True)
            .apply(lambda g: g["var_precio"].corr(g["indice_local"], method="spearman"), include_groups=False)
            .rename("spearman").reset_index())
    corr["cat_id"] = corr["id"].map(largo.drop_duplicates("id").set_index("id")["cat_id"].astype(str))
    corr.round(4).to_csv(dir_eda / "p3_correlacion_por_serie.csv", index=False)
    n_series = largo.drop_duplicates("id").groupby("cat_id", observed=True).size()
    resumen = []
    for grupo, c in [("TOTAL", corr)] + [(cat, corr[corr["cat_id"] == cat]) for cat in CATS]:
        total = int(n_series.sum()) if grupo == "TOTAL" else int(n_series[grupo])
        resumen.append({"grupo": grupo, "series": total, "series_con_cambio_precio": len(c),
                        "pct_sin_cambio_precio": 100 * (1 - len(c) / total),
                        "spearman_mediana": c["spearman"].median(), "spearman_p25": c["spearman"].quantile(0.25),
                        "spearman_p75": c["spearman"].quantile(0.75), "pct_correlacion_negativa": 100 * (c["spearman"] < 0).mean()})
    resumen = pd.DataFrame(resumen)
    resumen.round(4).to_csv(dir_eda / "p3_correlacion_resumen.csv", index=False)

    # Gráfico: índice local por tramo de variación de precio, sin días de evento
    sub = tramos[tramos["version"].str.startswith("sin eventos")]
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(ETIQUETAS_PRECIO))
    for cat in CATS:
        s = sub[sub["grupo"] == cat].set_index("tramo_precio").reindex(ETIQUETAS_PRECIO)
        visibles = s["n_filas"] >= 500
        ax.plot(x[visibles], s.loc[visibles, "indice_local"], color=COLOR_CAT[cat], linewidth=2,
                marker="o", markersize=6, label=cat)
    ax.axhline(1, color=TINTA, linewidth=0.9, linestyle="--")
    ax.set_xticks(x, ETIQUETAS_PRECIO, fontsize=8)
    estilo(ax, "Ventas según la variación del precio respecto al habitual (sin días de evento)",
           xlabel="precio de la semana frente a la mediana de la serie en train",
           ylabel="índice local medio (ventas / media móvil 57 días)")
    ax.legend(frameon=False, fontsize=8, labelcolor=TINTA_SEC, ncols=3, loc="upper right")
    ax.text(0, -0.2, "Tramos con menos de 500 filas no se dibujan. Asociación, no efecto causal (registro, E1).",
            transform=ax.transAxes, fontsize=7, color=TINTA_SEC)
    guardar(fig, dir_eda / "p3_precio.png")
    return tramos, resumen, sin_precio


# ------------------------------------------------------------------ P4

def p4(largo: pd.DataFrame, dir_eda):
    def indice_por(clave: str, periodo: str) -> pd.DataFrame:
        media_periodo = largo.groupby([clave, periodo], observed=True)["ventas"].mean().unstack()
        return media_periodo.div(largo.groupby(clave, observed=True)["ventas"].mean(), axis=0)

    salidas = {}
    for periodo, columnas, nombre in (("weekday", DIAS_ES, "semanal"), ("month", MESES_ES, "anual")):
        partes = []
        for clave in ("dept_id", "store_id"):
            m = indice_por(clave, periodo)
            m.columns = columnas
            m.index = m.index.astype(str)
            m.round(4).to_csv(dir_eda / f"p4_{nombre}_{'departamento' if clave == 'dept_id' else 'tienda'}.csv",
                              index_label=clave)
            partes.append(m)
        matriz = pd.concat(partes)
        salidas[nombre] = matriz
        titulo = ("Estacionalidad semanal\nventas medias por día de la semana / media del grupo"
                  if nombre == "semanal" else
                  "Estacionalidad anual: ventas medias por mes / media del grupo (feb-2011 a ene-2016)")
        heatmap(matriz, columnas, titulo, dir_eda / f"p4_{nombre}.png", separacion=len(partes[0]))

    # E4: índice mensual normalizado por la media de cada año. Solo años completos de train,
    # para que cada mes pese lo mismo (cada mes aparece una vez por año).
    completos = sorted(y for y, n in largo.groupby("year", observed=True)["dia_num"].nunique().items() if n >= 365)
    anios = largo[largo["year"].isin(completos)]
    partes = []
    for clave in ("dept_id", "store_id"):
        media_mes = anios.groupby([clave, "year", "month"], observed=True)["ventas"].mean()
        media_anio = anios.groupby([clave, "year"], observed=True)["ventas"].mean()
        indice = (media_mes / media_anio.reindex(media_mes.index.droplevel("month")).to_numpy())
        m = indice.groupby([clave, "month"], observed=True).mean().unstack()
        m.columns = MESES_ES
        m.index = m.index.astype(str)
        m.round(4).to_csv(dir_eda / f"p4_anual_ajustado_{'departamento' if clave == 'dept_id' else 'tienda'}.csv",
                          index_label=clave)
        partes.append(m)
    salidas["anual_ajustado"] = pd.concat(partes)
    heatmap(salidas["anual_ajustado"], MESES_ES,
            f"Estacionalidad anual normalizada por año ({completos[0]}-{completos[-1]})\n"
            "ventas medias del mes / media de su año, promediado entre años",
            dir_eda / "p4_anual_ajustado.png", separacion=len(partes[0]))

    # Nivel por año (ventas medias por serie-día y series activas), por departamento
    anual = largo.groupby(["dept_id", "year"], observed=True).agg(
        ventas_medias=("ventas", "mean"), series_activas=("id", "nunique"), dias=("dia_num", "nunique")).reset_index()
    anual.round(4).to_csv(dir_eda / "p4_nivel_por_anio_departamento.csv", index=False)
    return salidas, anual


# ------------------------------------------------------------------ main

def main():
    cfg = cargar_config()
    dir_eda = cfg["rutas"]["eda"]
    dir_eda.mkdir(parents=True, exist_ok=True)
    largo, cal, division = cargar(cfg)
    print(division.resumen())
    informar_memoria("carga e índices")

    ventana = cfg["eda"]["ventana_previa_evento"]
    dow, tipos, snap = p2(largo, dir_eda, ventana)
    informar_memoria("P2")
    print("\nP2 índice por día de la semana (TOTAL):",
          ", ".join(f"{d} {coma(v)}" for d, v in zip(DIAS_ES, dow[dow["grupo"] == "TOTAL"]["indice"])))
    print("P2 índice dow por tipo de evento (TOTAL):")
    print(tipos[tipos["grupo"] == "TOTAL"][["categoria_evento", "n_filas", "indice_dow"]].round(3).to_string(index=False))
    print("P2 SNAP, ratio de índices (días 1-15):")
    print(snap[snap["control"] == "días 1-15 del mes"].pivot(index="estado", columns="grupo",
                                                              values="ratio_indice_snap_no_snap").round(3).to_string())

    tramos, resumen, _ = p3(largo, cfg, division, dir_eda, ventana)
    informar_memoria("P3")
    print("\nP3 índice local por tramo (sin eventos, TOTAL):")
    print(tramos[(tramos["grupo"] == "TOTAL") & tramos["version"].str.startswith("sin")]
          [["tramo_precio", "n_filas", "n_series", "indice_local", "indice_dow"]].round(3).to_string(index=False))
    print(resumen.round(3).to_string(index=False))

    salidas, anual = p4(largo, dir_eda)
    informar_memoria("P4")
    for nombre, m in salidas.items():
        print(f"\nP4 {nombre}: rango del índice {coma(m.min().min())} a {coma(m.max().max())}")
    print("Ficheros en", dir_eda)


if __name__ == "__main__":
    main()
