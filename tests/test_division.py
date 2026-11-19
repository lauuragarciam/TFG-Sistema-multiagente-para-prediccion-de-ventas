"""
Tests de la división temporal y de la ausencia de fuga (RF-02, RNF-12).

Fallan si una fecha de validación o test aparece en entrenamiento, si las
fechas de corte se solapan o si los ficheros generados contienen días
posteriores al corte de train.

Ejecución (desde la raíz del repositorio):
    python -m unittest discover -s tests -t . -v

Los tests de la clase TestFicherosGenerados se omiten si aún no existen los
ficheros de data/interim/.
"""

import tempfile
import unittest
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from modules.config import ErrorConfiguracion, cargar_config
from modules.datos.carga import ID_COLS, leer_ventas_ancho
from modules.datos.division import Division


def calendario_sintetico(inicio="2011-01-29", dias=100) -> pd.DataFrame:
    fechas = pd.date_range(inicio, periods=dias, freq="D")
    return pd.DataFrame({
        "date": fechas,
        "dia_num": np.arange(1, dias + 1, dtype="int16"),
        "wm_yr_wk": (11101 + np.arange(dias) // 7).astype("int16"),
    })


def cfg_division(fin_train, fin_val, fin_test) -> dict:
    return {"division": {"fin_train": fin_train, "fin_validacion": fin_val, "fin_test": fin_test}}


class TestDivision(unittest.TestCase):
    def setUp(self):
        self.cal = calendario_sintetico()
        self.div = Division.desde_config(
            cfg_division(date(2011, 3, 31), date(2011, 4, 20), date(2011, 5, 5)), self.cal, ultimo_dia_ventas=100)

    def test_ninguna_fecha_de_validacion_o_test_en_train(self):
        conjunto = self.div.conjunto(self.cal["dia_num"])
        fechas_train = set(self.cal.loc[conjunto == "train", "date"])
        fechas_resto = set(self.cal.loc[np.isin(conjunto, ["validacion", "test"]), "date"])
        self.assertTrue(fechas_train, "train vacío")
        self.assertFalse(fechas_train & fechas_resto, "Fechas de validación/test dentro de train")
        self.assertLessEqual(max(fechas_train), pd.Timestamp(self.div.fin_train))
        self.assertGreater(min(fechas_resto), pd.Timestamp(self.div.fin_train))

    def test_conjuntos_contiguos_y_ordenados(self):
        conjunto = self.div.conjunto(self.cal["dia_num"])
        dentro = conjunto[conjunto != ""]
        orden = {"train": 0, "validacion": 1, "test": 2}
        self.assertTrue((np.diff([orden[c] for c in dentro]) >= 0).all(), "Conjuntos no ordenados en el tiempo")
        for nombre in orden:
            dias = self.cal.loc[conjunto == nombre, "dia_num"].to_numpy()
            self.assertTrue(len(dias) > 0, f"{nombre} vacío")
            self.assertTrue((np.diff(dias) == 1).all(), f"{nombre} no es contiguo")

    def test_indices_de_corte_coinciden_con_las_fechas(self):
        por_dia = self.cal.set_index("dia_num")["date"]
        for dia, fecha in ((self.div.dia_fin_train, self.div.fin_train),
                           (self.div.dia_fin_validacion, self.div.fin_validacion),
                           (self.div.dia_fin_test, self.div.fin_test)):
            self.assertEqual(por_dia[dia], pd.Timestamp(fecha), f"d_{dia} no corresponde a {fecha}")

    def test_semana_de_corte_no_supera_el_ultimo_dia_de_train(self):
        semana_dia_corte = self.cal.loc[self.cal["dia_num"] == self.div.dia_fin_train, "wm_yr_wk"].iloc[0]
        self.assertEqual(self.div.semana_fin_train, semana_dia_corte)

    def test_rechaza_fechas_solapadas_o_desordenadas(self):
        casos = [
            (date(2011, 4, 20), date(2011, 3, 31), date(2011, 5, 5)),   # validación antes que train
            (date(2011, 3, 31), date(2011, 3, 31), date(2011, 5, 5)),   # validación vacía (solapada)
            (date(2011, 3, 31), date(2011, 5, 5), date(2011, 4, 20)),   # test antes que validación
        ]
        for fechas in casos:
            with self.subTest(fechas=fechas), self.assertRaises(ErrorConfiguracion):
                Division.desde_config(cfg_division(*fechas), self.cal, ultimo_dia_ventas=100)

    def test_rechaza_fechas_fuera_de_rango(self):
        with self.assertRaises(ErrorConfiguracion):   # fin_test posterior a la última venta
            Division.desde_config(cfg_division(date(2011, 3, 31), date(2011, 4, 20), date(2011, 5, 5)),
                                  self.cal, ultimo_dia_ventas=90)
        with self.assertRaises(ErrorConfiguracion):   # fecha fuera del calendario
            Division.desde_config(cfg_division(date(2010, 1, 1), date(2011, 4, 20), date(2011, 5, 5)),
                                  self.cal, ultimo_dia_ventas=100)

    def test_firma_cambia_con_las_fechas(self):
        otra = Division.desde_config(
            cfg_division(date(2011, 4, 1), date(2011, 4, 20), date(2011, 5, 5)), self.cal, ultimo_dia_ventas=100)
        self.assertNotEqual(self.div.firma(), otra.firma())


class TestLecturaVentas(unittest.TestCase):
    def test_no_lee_dias_posteriores_al_corte(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "ventas.csv"
            fila = {c: f"x_{c}" for c in ID_COLS} | {f"d_{i}": i for i in range(1, 11)}
            pd.DataFrame([fila, fila | {"id": "y"}]).to_csv(ruta, index=False)
            bloques = list(leer_ventas_ancho(ruta, ultimo_dia=6, filas_por_bloque=1))
        dias = [c for c in bloques[0].columns if c.startswith("d_")]
        self.assertEqual(dias, [f"d_{i}" for i in range(1, 7)])
        self.assertEqual(len(bloques), 2)


class TestFicherosGenerados(unittest.TestCase):
    """Comprueba sobre data/interim/ que ningún fichero de train contiene días posteriores al corte."""

    @classmethod
    def setUpClass(cls):
        cfg = cargar_config()
        cls.interim = cfg["rutas"]["interim"]
        if not (cls.interim / "calendar.parquet").exists():
            raise unittest.SkipTest("No existen los ficheros de data/interim/")
        cal = pd.read_parquet(cls.interim / "calendar.parquet")
        ventas = cfg["rutas"]["raw"] / "sales_train_evaluation.csv"
        ultimo = sum(c.startswith("d_") for c in pd.read_csv(ventas, nrows=0).columns)
        cls.div = Division.desde_config(cfg, cal, ultimo)

    def _leer(self, nombre, columnas):
        ruta = self.interim / nombre
        if not ruta.exists():
            self.skipTest(f"No existe {nombre}")
        return pd.read_parquet(ruta, columns=columnas)

    def test_division_coherente_con_el_calendario(self):
        cal = pd.read_parquet(self.interim / "calendar.parquet", columns=["dia_num", "date"]).set_index("dia_num")
        self.assertEqual(cal.at[self.div.dia_fin_train, "date"], pd.Timestamp(self.div.fin_train))
        self.assertEqual(cal.at[self.div.dia_fin_validacion, "date"], pd.Timestamp(self.div.fin_validacion))

    def test_muestra_larga_solo_train(self):
        df = self._leer("ventas_muestra_largo.parquet", ["dia_num", "date"])
        self.assertLessEqual(int(df["dia_num"].max()), self.div.dia_fin_train)
        self.assertLessEqual(df["date"].max(), pd.Timestamp(self.div.fin_train))

    def test_calendar_train_solo_train(self):
        df = self._leer("calendar_train.parquet", ["dia_num", "date"])
        self.assertLessEqual(int(df["dia_num"].max()), self.div.dia_fin_train)
        self.assertLessEqual(df["date"].max(), pd.Timestamp(self.div.fin_train))

    def test_precios_train_hasta_semana_de_corte(self):
        df = self._leer("sell_prices_train.parquet", ["wm_yr_wk"])
        self.assertLessEqual(int(df["wm_yr_wk"].max()), self.div.semana_fin_train)

    def test_clasificacion_con_la_division_actual(self):
        df = self._leer("clasificacion_series_train.parquet", ["firma_division", "n_periodos"])
        self.assertEqual(set(df["firma_division"].unique()), {self.div.firma()})
        self.assertLessEqual(int(df["n_periodos"].max()), self.div.dia_fin_train)


if __name__ == "__main__":
    unittest.main()
