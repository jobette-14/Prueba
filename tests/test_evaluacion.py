"""Pruebas de calculo de metricas de evaluacion."""

import numpy as np

from modelo.evaluacion import (
    calcular_metrica_r2, calcular_metrica_mae, calcular_metrica_mse,
    calcular_metrica_rmse, evaluar_modelo,
)


def test_r2_perfecto():
    y = np.array([1.0, 2.0, 3.0, 4.0])
    assert calcular_metrica_r2(y, y) == 1.0


def test_r2_negativo():
    """Un modelo peor que la media produce R2 negativo."""
    y_real = np.array([1.0, 2.0, 3.0, 4.0])
    y_pred = np.array([4.0, 3.0, 2.0, 1.0])
    assert calcular_metrica_r2(y_real, y_pred) < 0


def test_mae():
    y_real = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([2.0, 2.0, 2.0])
    assert calcular_metrica_mae(y_real, y_pred) == 2.0 / 3.0


def test_mse():
    y_real = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([2.0, 2.0, 2.0])
    assert calcular_metrica_mse(y_real, y_pred) == 2.0 / 3.0


def test_rmse():
    y_real = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([2.0, 2.0, 2.0])
    assert abs(calcular_metrica_rmse(y_real, y_pred) - np.sqrt(2.0 / 3.0)) < 1e-9


def test_metricas_listas_vacias():
    vacio = np.array([])
    assert calcular_metrica_r2(vacio, vacio) == 0.0
    assert calcular_metrica_mae(vacio, vacio) == 0.0


def test_evaluar_modelo(modelo_entrenado):
    X_test, y_test = modelo_entrenado.datos_prueba
    resultado = evaluar_modelo(modelo_entrenado, X_test, y_test)
    assert resultado["exitoso"] is True
    assert "r2" in resultado["metricas"]


def test_evaluar_modelo_sin_entrenar():
    from modelo.entrenamiento import ModeloRegresionLineal
    resultado = evaluar_modelo(ModeloRegresionLineal(), np.array([[1, 2, 3, 4]]), np.array([1]))
    assert resultado["exitoso"] is False
