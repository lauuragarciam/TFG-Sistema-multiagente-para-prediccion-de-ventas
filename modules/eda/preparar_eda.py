"""
Prepara los ficheros del EDA del Sprint 1.

Salidas:
  data/interim/calendar.parquet             calendario completo (una fila = un día), sin perfilar
  data/interim/calendar_train.parquet       calendario d_1..d_fin_train: entrada de todo perfil de calendar
  output/eda/calendar_perfil_train.csv      conteos de días, eventos y SNAP solo en train
  output/eda/sell_prices_estructura.csv     sell_prices completo: SOLO estructura
  data/interim/sell_prices_train.parquet    precios de las semanas <= semana del corte de train
  data/interim/ventas_muestra_largo.parquet muestra (una fila = serie x día), solo train, solo días a la venta
  data/interim/metadatos_eda.json           firma de la división y cifras de la muestra

Selección de la muestra: en cada estrato (dept_id x store_id) se toma la fracción
configurada de series, al azar, sin reemplazo y con semilla fija, usando SOLO las
columnas identificadoras (ninguna venta ni precio interviene en la selección).

Uso (desde la raíz del repositorio):
    python -m modules.eda.preparar_eda
"""

import json

import pandas as pd

from modules.config import cargar_config
from modules.datos.carga import (ID_COLS, ancho_a_largo, cargar_calendar, cargar_precios,
                                 comprobar_ficheros, dias_en_ventas, estructura_precios,
                                 inicio_disponibilidad, leer_ids_ventas, leer_ventas_ancho)
from modules.datos.division import Division
from modules.memoria import informar_memoria, pico_memoria_mb


def muestra_estratificada(ids: pd.DataFrame, estratos: list[str], fraccion: float, semilla: int) -> pd.DataFrame:
    """Fracción de series de cada estrato, al azar y sin reemplazo (round(fraccion x tamaño))."""
    return (ids.groupby(estratos, observed=True)
               .sample(frac=fraccion, random_state=semilla)
               .sort_index())


def perfil_calendar(cal: pd.DataFrame) -> pd.DataFrame:
    """Conteos del calendario (días, eventos por tipo, días SNAP por estado) del periodo recibido."""
    filas = [
        ("dias", len(cal)),
        ("fecha_min", str(cal["date"].min().date())),
        ("fecha_max", str(cal["date"].max().date())),
        ("dias_con_evento", int(cal["event_name_1"].notna().sum())),
        ("dias_con_dos_eventos", int(cal["event_name_2"].notna().sum())),
        ("eventos_distintos", int(pd.concat([cal["event_name_1"], cal["event_name_2"]]).dropna().nunique())),
    ]
    tipos = pd.concat([cal["event_type_1"], cal["event_type_2"]]).dropna().astype(str).value_counts().sort_index()
    filas += [(f"dias_evento_tipo_{t}", int(n)) for t, n in tipos.items()]
    filas += [(f"dias_{c}", int(cal[c].sum())) for c in ("snap_CA", "snap_TX", "snap_WI")]
    return pd.DataFrame(filas, columns=["indicador", "valor"])


def main():
    cfg = cargar_config()
    rutas = comprobar_ficheros(cfg["rutas"]["raw"])
    dir_interim, dir_eda = cfg["rutas"]["interim"], cfg["rutas"]["eda"]
    dir_interim.mkdir(parents=True, exist_ok=True)
    dir_eda.mkdir(parents=True, exist_ok=True)

    print("1/5 calendar")
    cal = cargar_calendar(rutas["calendar"])
    cal.to_parquet(dir_interim / "calendar.parquet", index=False)   # completo, sin perfilar
    division = Division.desde_config(cfg, cal, dias_en_ventas(rutas["ventas"]))
    print(f"  {division.resumen()}")
    # El perfil de calendar usa solo los días de train
    cal_train = cal.loc[cal["dia_num"] <= division.dia_fin_train].reset_index(drop=True)
    if not (cal_train["dia_num"].to_numpy() == range(1, division.dia_fin_train + 1)).all():
        raise AssertionError("calendar de train no cubre d_1..d_fin_train de forma continua")
    cal_train.to_parquet(dir_interim / "calendar_train.parquet", index=False)
    perfil_calendar(cal_train).to_csv(dir_eda / "calendar_perfil_train.csv", index=False)
    print(f"  perfil de calendar con {len(cal_train):,} días ({cal_train['date'].min().date()} a "
          f"{cal_train['date'].max().date()})")
    informar_memoria("calendar")

    print("2/5 sell_prices completo: solo estructura")
    estructura_precios(rutas["precios"]).to_csv(dir_eda / "sell_prices_estructura.csv", index=False)
    informar_memoria("estructura sell_prices")

    print(f"3/5 sell_prices de train (semanas <= {division.semana_fin_train})")
    precios = cargar_precios(rutas["precios"], hasta_semana=division.semana_fin_train)
    precios.to_parquet(dir_interim / "sell_prices_train.parquet", index=False)
    print(f"  {len(precios):,} filas; {precios.groupby(['store_id', 'item_id'], observed=True).ngroups:,} "
          f"pares tienda-producto con precio en train")
    inicio = inicio_disponibilidad(precios, cal)
    del precios
    inicio["id"] = inicio["item_id"].astype(str) + "_" + inicio["store_id"].astype(str) + "_evaluation"
    primer_dia_por_id = inicio.set_index("id")["primer_dia"]
    informar_memoria("sell_prices train")

    print("4/5 selección de la muestra (solo columnas identificadoras)")
    m = cfg["muestra_eda"]
    ids = leer_ids_ventas(rutas["ventas"])
    seleccion = muestra_estratificada(ids, m["estratos"], m["fraccion"], m["semilla"])
    n_estratos = ids.groupby(m["estratos"], observed=True).ngroups
    print(f"  {len(seleccion):,} de {len(ids):,} series ({len(seleccion) / len(ids):.2%}) "
          f"en {n_estratos} estratos {m['estratos']}, semilla {m['semilla']}")
    print("  por tienda: " + ", ".join(f"{k} {v}" for k, v in seleccion["store_id"].value_counts().sort_index().items()))
    print("  por departamento: " + ", ".join(f"{k} {v}" for k, v in seleccion["dept_id"].value_counts().sort_index().items()))
    ids_sel = set(seleccion["id"].astype(str))

    print(f"5/5 muestra en formato largo (d_1-d_{division.dia_fin_train}, por bloques)")
    trozos, filas_total, filas_previas, ventas_previas = [], 0, 0, 0
    for bloque in leer_ventas_ancho(rutas["ventas"], division.dia_fin_train, cfg["carga"]["filas_por_bloque"]):
        bloque = bloque.loc[bloque["id"].astype(str).isin(ids_sel)]
        if bloque.empty:
            continue
        largo = ancho_a_largo(bloque, cal)
        primer_dia = largo["id"].astype(str).map(primer_dia_por_id)
        # Unión con la información de precios: ni filas nuevas ni días posteriores al corte
        if len(largo) != len(bloque) * division.dia_fin_train or largo["dia_num"].max() > division.dia_fin_train:
            raise AssertionError("La unión ventas-precios ha generado filas nuevas o posteriores al corte de train")
        if (primer_dia.dropna() > division.dia_fin_train).any():
            raise AssertionError("Inicio de disponibilidad posterior al corte de train")
        previo = primer_dia.isna() | (largo["dia_num"] < primer_dia)   # sin precio en train -> no está a la venta
        filas_total += len(largo)
        filas_previas += int(previo.sum())
        ventas_previas += int(largo.loc[previo, "ventas"].sum())
        trozos.append(largo.loc[~previo])
    largo = pd.concat(trozos, ignore_index=True)
    for c in ID_COLS:
        largo[c] = largo[c].astype(str).astype("category")

    if largo["dia_num"].max() > division.dia_fin_train:
        raise AssertionError("Fuga: la muestra contiene días posteriores al corte de train")
    largo.to_parquet(dir_interim / "ventas_muestra_largo.parquet", index=False)

    series_con_filas = largo["id"].nunique()
    print(f"  {len(largo):,} filas de {series_con_filas:,} series; excluidas {filas_previas:,} filas previas "
          f"al primer precio ({filas_previas / filas_total:.1%}), con {ventas_previas} unidades vendidas")
    print(f"  memoria del DataFrame: {largo.memory_usage(deep=True).sum() / 1_048_576:,.0f} MB")
    informar_memoria("muestra larga")

    metadatos = {
        "firma_division": division.firma(),
        "division": division.resumen(),
        "muestra": {"estratos": m["estratos"], "fraccion": m["fraccion"], "semilla": m["semilla"],
                    "series_seleccionadas": len(seleccion), "series_con_filas": int(series_con_filas),
                    "filas": len(largo), "filas_excluidas_previas": filas_previas,
                    "ventas_en_filas_excluidas": ventas_previas},
        "pico_memoria_mb": pico_memoria_mb(),
    }
    (dir_interim / "metadatos_eda.json").write_text(json.dumps(metadatos, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Hecho.")


if __name__ == "__main__":
    main()
