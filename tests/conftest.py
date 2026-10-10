"""Configuracion comun y fixtures de las pruebas de ElectroPredict.

Agrega la raiz del proyecto al sys.path para poder importar los modulos
(datos, modelo, base_datos, etc.) desde la carpeta tests, y define datos
deterministas de prueba (independientes de cualquier dato real).
"""

import os
import sys

import numpy as np
import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)


def _generar_datos(n: int = 40, semilla: int = 42):
    """Genera datos deterministas con una relacion conocida."""
    rng = np.random.default_rng(semilla)
    filas = []
    for _ in range(n):
        t = float(rng.integers(15, 35))
        p = int(rng.integers(1, 6))
        h = float(rng.integers(1, 12))
        ca = round(5 + t * 0.2 + rng.normal(0, 0.3), 2)
        real = round(2.0 + 0.5 * t + 1.2 * p + 0.8 * h + 0.3 * ca + rng.normal(0, 0.2), 3)
        filas.append({
            "temperatura": t, "personas": p, "horas_uso": h,
            "consumo_anterior": ca, "consumo_real": real,
        })
    return filas


@pytest.fixture
def datos_deterministas():
    """40 registros deterministas con variables validas."""
    return _generar_datos(40)


@pytest.fixture
def modelo_entrenado(datos_deterministas):
    """Modelo ya entrenado con los datos deterministas."""
    from modelo.entrenamiento import ModeloRegresionLineal
    modelo = ModeloRegresionLineal()
    X, y = modelo.preparar_datos(datos_deterministas)
    modelo.entrenar(X, y, test_size=0.2)
    return modelo


@pytest.fixture
def csv_prediccion(tmp_path):
    """Ruta a un CSV de prediccion por lotes (sin consumo_real)."""
    contenido = (
        "temperatura,personas,horas_uso,consumo_anterior\n"
        "29,4,6,10.2\n"
        "31,5,8,12.1\n"
        "28,3,5,9.4\n"
    )
    ruta = tmp_path / "lote.csv"
    ruta.write_text(contenido, encoding="utf-8")
    return str(ruta)
