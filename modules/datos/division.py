"""
División temporal en entrenamiento, validación y test (RF-02, RNF-12).

Las fechas de corte vienen de [division] en config/config.toml y son inclusivas.
La división se traduce a índices de día (dia_num, el n de d_n) y a la semana
Walmart del último día de train, que es la última semana de precios utilizable
en los análisis de entrenamiento.
"""

import hashlib
from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from modules.config import ErrorConfiguracion

CONJUNTOS = ("train", "validacion", "test")


@dataclass(frozen=True)
class Division:
    fin_train: date
    fin_validacion: date
    fin_test: date
    dia_fin_train: int
    dia_fin_validacion: int
    dia_fin_test: int
    semana_fin_train: int

    @classmethod
    def desde_config(cls, cfg: dict, calendar: pd.DataFrame, ultimo_dia_ventas: int) -> "Division":
        """Valida las fechas de corte (CU-01, flujo alternativo 2) y construye la división."""
        d = cfg["division"]
        fechas = {k: pd.Timestamp(d[k]) for k in ("fin_train", "fin_validacion", "fin_test")}
        if not fechas["fin_train"] < fechas["fin_validacion"] < fechas["fin_test"]:
            raise ErrorConfiguracion(
                "Las fechas de corte deben cumplir fin_train < fin_validacion < fin_test "
                f"(valores: {d['fin_train']}, {d['fin_validacion']}, {d['fin_test']})")

        por_fecha = calendar.set_index("date")
        dias = {}
        for clave, fecha in fechas.items():
            if fecha not in por_fecha.index:
                raise ErrorConfiguracion(f"[division].{clave} = {fecha.date()} no está en el calendario")
            dias[clave] = int(por_fecha.at[fecha, "dia_num"])

        if dias["fin_test"] > ultimo_dia_ventas:
            ultima = calendar.loc[calendar["dia_num"] == ultimo_dia_ventas, "date"].iloc[0].date()
            raise ErrorConfiguracion(
                f"fin_test ({fechas['fin_test'].date()}) es posterior al último día con ventas ({ultima})")
        if dias["fin_train"] < 1:
            raise ErrorConfiguracion("El conjunto de entrenamiento está vacío")

        return cls(
            fin_train=fechas["fin_train"].date(),
            fin_validacion=fechas["fin_validacion"].date(),
            fin_test=fechas["fin_test"].date(),
            dia_fin_train=dias["fin_train"],
            dia_fin_validacion=dias["fin_validacion"],
            dia_fin_test=dias["fin_test"],
            semana_fin_train=int(por_fecha.at[fechas["fin_train"], "wm_yr_wk"]),
        )

    def conjunto(self, dia_num) -> np.ndarray:
        """Nombre del conjunto de cada dia_num ('train', 'validacion', 'test' o '' si queda fuera)."""
        dia = np.asarray(dia_num)
        return np.select(
            [dia <= self.dia_fin_train, dia <= self.dia_fin_validacion, dia <= self.dia_fin_test],
            list(CONJUNTOS), default="")

    def firma(self) -> str:
        """Huella de la división para sellar datos y modelos (RNF-12): mismas fechas, misma firma."""
        texto = f"{self.fin_train}|{self.fin_validacion}|{self.fin_test}"
        return hashlib.sha256(texto.encode()).hexdigest()[:16]

    def resumen(self) -> str:
        return (f"train: d_1-d_{self.dia_fin_train} (hasta {self.fin_train}) | "
                f"validación: d_{self.dia_fin_train + 1}-d_{self.dia_fin_validacion} (hasta {self.fin_validacion}) | "
                f"test: d_{self.dia_fin_validacion + 1}-d_{self.dia_fin_test} (hasta {self.fin_test}) | "
                f"última semana de precios en train: {self.semana_fin_train} | firma {self.firma()}")
