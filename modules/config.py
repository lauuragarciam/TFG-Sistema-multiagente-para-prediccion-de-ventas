"""Lectura y validación básica de config/config.toml."""

import tomllib
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
RUTA_CONFIG = RAIZ / "config" / "config.toml"


class ErrorConfiguracion(ValueError):
    """La configuración no es válida (CU-01, flujo alternativo 2)."""


def cargar_config(ruta: Path | str | None = None) -> dict:
    """Lee la configuración, convierte las rutas en absolutas y valida los tipos."""
    ruta = Path(ruta) if ruta else RUTA_CONFIG
    if not ruta.exists():
        raise ErrorConfiguracion(f"No existe el fichero de configuración: {ruta}")
    with open(ruta, "rb") as f:
        cfg = tomllib.load(f)

    for seccion in ("rutas", "division", "carga", "muestra_eda", "clasificacion", "eda", "outliers"):
        if seccion not in cfg:
            raise ErrorConfiguracion(f"Falta la sección [{seccion}] en {ruta}")

    cfg["rutas"] = {k: (RAIZ / v).resolve() for k, v in cfg["rutas"].items()}

    for clave in ("fin_train", "fin_validacion", "fin_test"):
        valor = cfg["division"].get(clave)
        if not isinstance(valor, date):
            raise ErrorConfiguracion(f"[division].{clave} debe ser una fecha AAAA-MM-DD (valor: {valor!r})")

    fraccion = cfg["muestra_eda"].get("fraccion")
    if not (isinstance(fraccion, float) and 0 < fraccion <= 1):
        raise ErrorConfiguracion(f"[muestra_eda].fraccion debe estar en (0, 1] (valor: {fraccion!r})")
    for clave in ("umbral_adi", "umbral_cv2"):
        if not cfg["clasificacion"].get(clave, 0) > 0:
            raise ErrorConfiguracion(f"[clasificacion].{clave} debe ser positivo")
    return cfg
