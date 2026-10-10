"""Verifica que la version web y la de escritorio dan resultados consistentes.

Ambas reutilizan el mismo nucleo (ModeloRegresionLineal), por lo que entrenando
con los mismos datos deben producir las mismas metricas y predicciones.
"""

import pytest

from modelo.entrenamiento import ModeloRegresionLineal
from web.api.config import Configuracion
from web.api.estado import EstadoApp
from tests.test_api import _generar_datos, _config


def test_mismas_metricas_y_predicciones(datos_deterministas):
    # Version "escritorio": se entrena directamente con el nucleo.
    escritorio = ModeloRegresionLineal(algoritmo="lineal")
    X, y = escritorio.preparar_datos(datos_deterministas)
    escritorio.entrenar(X, y, test_size=0.2)

    # Version "web": el estado de la API usa exactamente la misma clase.
    cfg = _config()
    estado = EstadoApp(cfg)
    estado.agregar_registros_masivo(datos_deterministas)
    resultado = estado.entrenar(algoritmo="lineal", test_size=0.2, guardar=False)
    assert resultado["exitoso"]

    # Metricas identicas
    assert estado.metricas["r2"] == pytest.approx(escritorio.metricas["r2"], rel=1e-9)
    assert estado.metricas["rmse"] == pytest.approx(escritorio.metricas["rmse"], rel=1e-9)

    # Predicciones identicas para varias entradas validas
    entradas = [
        (20, 2, 4, 8), (28, 4, 7, 11), (33, 5, 9, 13), (25, 3, 6, 10),
    ]
    for t, p, h, ca in entradas:
        web, _ = estado.modelo.predecir([t, p, h, ca])
        desk, _ = escritorio.predecir([t, p, h, ca])
        assert web == pytest.approx(desk, rel=1e-12)


def test_mismas_metricas_random_forest(datos_deterministas):
    escritorio = ModeloRegresionLineal(algoritmo="random_forest")
    X, y = escritorio.preparar_datos(datos_deterministas)
    escritorio.entrenar(X, y, test_size=0.2)

    cfg = _config()
    estado = EstadoApp(cfg)
    estado.agregar_registros_masivo(datos_deterministas)
    estado.entrenar(algoritmo="random_forest", test_size=0.2, guardar=False)

    assert estado.metricas["r2"] == pytest.approx(escritorio.metricas["r2"], rel=1e-9)

    web, _ = estado.modelo.predecir([25, 3, 6, 10])
    desk, _ = escritorio.predecir([25, 3, 6, 10])
    assert web == pytest.approx(desk, rel=1e-12)
