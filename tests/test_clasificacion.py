"""
Tests del cálculo de ADI/CV² con días válidos (RF-03, Anexo A, registro C2 y T10).

Ejecución (desde la raíz del repositorio):
    python -m unittest discover -s tests -t . -v
"""

import unittest

import numpy as np
import pandas as pd

from modules.config import cargar_config
from modules.datos.clasificacion import clasificar, estadisticos_con_mascara, mascara_dias_validos
from modules.datos.division import Division


class TestMascaraDiasValidos(unittest.TestCase):
    def test_excluye_dias_antes_del_primer_precio_y_de_tienda_cerrada(self):
        abierto = np.ones((2, 6), dtype=bool)
        abierto[:, 3] = False                     # d_4 cerrado
        m = mascara_dias_validos(np.array([1, 3]), abierto)
        np.testing.assert_array_equal(m[0], [True, True, True, False, True, True])
        np.testing.assert_array_equal(m[1], [False, False, True, False, True, True])

    def test_serie_no_a_la_venta(self):
        m = mascara_dias_validos(np.array([7]), np.ones((1, 6), dtype=bool))
        self.assertFalse(m.any())

    def test_dia_cerrado_no_cuenta_en_adi(self):
        ventas = np.array([[0, 2, 0, 0, 4, 0]])
        abierto = np.ones((1, 6), dtype=bool)
        abierto[0, 3] = False
        con = estadisticos_con_mascara(ventas, mascara_dias_validos(np.array([1]), abierto))
        sin = estadisticos_con_mascara(ventas, mascara_dias_validos(np.array([1]), np.ones((1, 6), dtype=bool)))
        self.assertEqual(con["n_periodos"].iloc[0], 5)
        self.assertAlmostEqual(con["adi"].iloc[0], 5 / 2)
        self.assertAlmostEqual(sin["adi"].iloc[0], 6 / 2)
        self.assertAlmostEqual(con["cv2"].iloc[0], sin["cv2"].iloc[0])   # el CV² no depende de los ceros

    def test_casos_limite_anexo_a(self):
        ventas = np.array([[0, 0, 0], [0, 3, 0]])
        est = estadisticos_con_mascara(ventas, np.ones((2, 3), dtype=bool))
        self.assertTrue(np.isnan(est["adi"].iloc[0]))          # sin ventas: indefinido
        self.assertEqual(est["cv2"].iloc[1], 0.0)              # una sola venta: CV² = 0
        tipo, aviso = clasificar(est["adi"], est["cv2"], 1.32, 0.49)
        self.assertEqual(tipo[0], "intermitente")
        self.assertTrue(aviso[0])


class TestClasificacionVigente(unittest.TestCase):
    """Comprueba sobre la clasificación generada que excluye los días de tienda cerrada (C2)."""

    def test_n_periodos_descuenta_tienda_cerrada(self):
        cfg = cargar_config()
        ruta_clas = cfg["rutas"]["interim"] / "clasificacion_series_train.parquet"
        ruta_cerr = cfg["rutas"]["eda"] / "ceros_tiendas_cerradas.csv"
        if not (ruta_clas.exists() and ruta_cerr.exists()):
            self.skipTest("Faltan clasificacion_series_train.parquet o ceros_tiendas_cerradas.csv")
        cal = pd.read_parquet(cfg["rutas"]["interim"] / "calendar.parquet")
        ventas = cfg["rutas"]["raw"] / "sales_train_evaluation.csv"
        ultimo = sum(c.startswith("d_") for c in pd.read_csv(ventas, nrows=0).columns)
        fin_train = Division.desde_config(cfg, cal, ultimo).dia_fin_train

        clas = pd.read_parquet(ruta_clas, columns=["store_id", "primer_dia", "n_periodos"])
        clas = clas[clas["primer_dia"] > 0]
        cerr = pd.read_csv(ruta_cerr)
        self.assertTrue((cerr["dia_num"] <= fin_train).all())
        cerrados = np.zeros(len(clas), dtype=int)
        tiendas = clas["store_id"].astype(str).to_numpy()
        for tienda, dias in cerr.groupby("store_id")["dia_num"]:
            dias = np.sort(dias.to_numpy())
            sel = tiendas == tienda
            cerrados[sel] = len(dias) - np.searchsorted(dias, clas["primer_dia"].to_numpy()[sel], side="left")
        esperado = fin_train - clas["primer_dia"].to_numpy() + 1 - cerrados
        np.testing.assert_array_equal(clas["n_periodos"].to_numpy(), esperado)


if __name__ == "__main__":
    unittest.main()
