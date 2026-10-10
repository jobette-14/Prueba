"""Pruebas de la imputacion de valores faltantes (ajustada solo en train)."""

import numpy as np
import pytest

from modelo.entrenamiento import ModeloRegresionLineal


def _datos_con_faltantes():
    """Datos deterministas donde algunas entradas estan vacias o invalidas."""
    datos = []
    for i in range(30):
        fila = {
            "temperatura": 20 + (i % 10),
            "personas": 1 + (i % 5),
            "horas_uso": 2 + (i % 8),
            "consumo_anterior": 8 + (i % 6),
            "consumo_real": 2.0 + 0.5 * (20 + (i % 10)) + 1.2 * (1 + (i % 5))
                            + 0.8 * (2 + (i % 8)) + 0.3 * (8 + (i % 6)),
        }
        if i % 7 == 0:
            fila["temperatura"] = ""      # valor faltante
        if i % 5 == 0:
            fila["horas_uso"] = "abc"     # valor invalido
        datos.append(fila)
    return datos


def test_sin_imputacion_rechaza_faltantes():
    datos = _datos_con_faltantes()
    modelo = ModeloRegresionLineal(imputar=False)
    X, y = modelo.preparar_datos(datos)
    assert X is None
    assert y is None


def test_con_imputacion_entrena_correctamente():
    datos = _datos_con_faltantes()
    modelo = ModeloRegresionLineal(algoritmo="lineal", imputar=True)
    X, y = modelo.preparar_datos(datos)
    assert X is not None
    assert y is not None
    assert np.isnan(X).any()

    resultado = modelo.entrenar(X, y)
    assert resultado["exitoso"] is True
    assert resultado["imputacion"] is True
    assert modelo.entrenado is True


def test_imputador_se_ajusta_solo_con_entrenamiento(datos_deterministas):
    """El imputador no debe ver el conjunto de prueba al ajustarse."""
    datos = _datos_con_faltantes()
    modelo = ModeloRegresionLineal(imputar=True)
    X, y = modelo.preparar_datos(datos)
    modelo.entrenar(X, y, test_size=0.2)

    imputador = modelo._imputador
    assert imputador is not None
    # La media aprendida debe provenir solo de filas sin NaN del train,
    # por lo que coincide con la media de las columnas completas del train.
    X_train = modelo._X_train
    medias_esperadas = np.ma.masked_invalid(X_train).mean(axis=0).data
    for valor_aprendido, esperado in zip(imputador.statistics_, medias_esperadas):
        assert valor_aprendido == pytest.approx(esperado, rel=1e-6)


def test_prediccion_con_imputacion_activa(datos_deterministas):
    datos = _datos_con_faltantes()
    modelo = ModeloRegresionLineal(imputar=True)
    X, y = modelo.preparar_datos(datos)
    modelo.entrenar(X, y)
    estimado, _ = modelo.predecir([25, 3, 6, 10])
    assert estimado is not None
    assert estimado > 0


def test_predecir_array_aplica_imputacion(datos_deterministas):
    datos = _datos_con_faltantes()
    modelo = ModeloRegresionLineal(imputar=True)
    X, y = modelo.preparar_datos(datos)
    modelo.entrenar(X, y)
    X_test, _ = modelo.datos_prueba
    y_pred = modelo.predecir_array(X_test)
    assert y_pred is not None
    assert len(y_pred) == len(X_test)
    assert not np.isnan(y_pred).any()
