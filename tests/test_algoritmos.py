"""Pruebas de los distintos algoritmos de regresion soportados."""

import pytest

from modelo.entrenamiento import (
    ModeloRegresionLineal, ALGORITMOS, comparar_algoritmos,
)


@pytest.mark.parametrize("algoritmo", list(ALGORITMOS.keys()))
def test_entrenar_todos_los_algoritmos(algoritmo, datos_deterministas):
    modelo = ModeloRegresionLineal(algoritmo=algoritmo)
    X, y = modelo.preparar_datos(datos_deterministas)
    resultado = modelo.entrenar(X, y, test_size=0.2)
    assert resultado["exitoso"] is True
    assert modelo.entrenado is True
    assert modelo.metricas is not None
    assert modelo.metricas["r2"] > 0.5
    assert resultado["algoritmo"] == algoritmo


def test_algoritmo_invalido_lanza_error():
    with pytest.raises(ValueError):
        ModeloRegresionLineal(algoritmo="no_existe")


def test_lineal_expone_coeficientes(datos_deterministas):
    modelo = ModeloRegresionLineal(algoritmo="lineal")
    X, y = modelo.preparar_datos(datos_deterministas)
    modelo.entrenar(X, y)
    assert modelo.coeficientes is not None
    assert modelo.intercepto is not None
    assert "consumo_estimado" in modelo.obtener_formula()


def test_random_forest_no_expone_coeficientes(datos_deterministas):
    modelo = ModeloRegresionLineal(algoritmo="random_forest")
    X, y = modelo.preparar_datos(datos_deterministas)
    modelo.entrenar(X, y)
    assert modelo.coeficientes is None
    assert "no expone" in modelo.obtener_formula()


def test_prediccion_con_ridge(datos_deterministas):
    modelo = ModeloRegresionLineal(algoritmo="ridge")
    X, y = modelo.preparar_datos(datos_deterministas)
    modelo.entrenar(X, y)
    estimado, info = modelo.predecir([25, 3, 6, 10])
    assert estimado is not None
    assert estimado > 0
    assert info["algoritmo"] == "ridge"


def test_comparar_algoritmos(datos_deterministas):
    resultados = comparar_algoritmos(datos_deterministas)
    assert len(resultados) == len(ALGORITMOS)
    assert all(r["exitoso"] for r in resultados)
    nombres = {r["algoritmo"] for r in resultados}
    assert nombres == set(ALGORITMOS.keys())
