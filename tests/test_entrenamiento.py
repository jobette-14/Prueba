"""Pruebas de entrenamiento del modelo de regresion lineal multiple."""

import numpy as np

from modelo.entrenamiento import ModeloRegresionLineal


def test_preparar_datos_ok(datos_deterministas):
    modelo = ModeloRegresionLineal()
    X, y = modelo.preparar_datos(datos_deterministas)
    assert X is not None and y is not None
    assert X.shape == (40, 4)
    assert y.shape == (40,)


def test_preparar_datos_insuficientes():
    modelo = ModeloRegresionLineal()
    X, y = modelo.preparar_datos([{"temperatura": 20, "personas": 2, "horas_uso": 3,
                                   "consumo_anterior": 5, "consumo_real": 10}])
    assert X is None and y is None


def test_preparar_datos_invalidos():
    modelo = ModeloRegresionLineal()
    datos = [
        {"temperatura": 20, "personas": 2, "horas_uso": 3, "consumo_anterior": 5, "consumo_real": 10},
        {"temperatura": 20, "personas": 2, "horas_uso": 3, "consumo_anterior": 5, "consumo_real": 10},
        {"temperatura": 999, "personas": 2, "horas_uso": 3, "consumo_anterior": 5, "consumo_real": 10},
    ]
    X, y = modelo.preparar_datos(datos)
    assert X is None and y is None


def test_entrenar_modelo(datos_deterministas):
    modelo = ModeloRegresionLineal()
    X, y = modelo.preparar_datos(datos_deterministas)
    resultado = modelo.entrenar(X, y, test_size=0.2)

    assert resultado["exitoso"] is True
    assert modelo.entrenado is True
    assert 0.0 <= resultado["metricas"]["r2"] <= 1.0
    assert resultado["metricas"]["mae"] >= 0
    assert resultado["metricas"]["mse"] >= 0
    assert resultado["metricas"]["rmse"] >= 0


def test_coeficientes_aprendidos(datos_deterministas):
    """Los coeficientes deben acercarse a los valores reales (0.5,1.2,0.8,0.3)."""
    modelo = ModeloRegresionLineal()
    X, y = modelo.preparar_datos(datos_deterministas)
    modelo.entrenar(X, y, test_size=0.2)
    coef = modelo.coeficientes
    assert abs(coef[0] - 0.5) < 0.2   # temperatura
    assert abs(coef[1] - 1.2) < 0.4   # personas
    assert abs(coef[2] - 0.8) < 0.2   # horas_uso
    assert abs(coef[3] - 0.3) < 0.2   # consumo_anterior


def test_sin_fuga_de_informacion(datos_deterministas):
    """Entrenamiento y prueba deben ser conjuntos disjuntos y de tamano correcto."""
    modelo = ModeloRegresionLineal()
    X, y = modelo.preparar_datos(datos_deterministas)
    res = modelo.entrenar(X, y, test_size=0.25)
    assert res["registros_prueba"] == 10
    assert res["registros_entrenamiento"] == 30
    assert res["registros_entrenamiento"] + res["registros_prueba"] == 40


def test_prediccion_sin_entrenar():
    modelo = ModeloRegresionLineal()
    valor, info = modelo.predecir([25, 3, 6, 10])
    assert valor is None


def test_prediccion_con_entrada_invalida(modelo_entrenado):
    valor, info = modelo_entrenado.predecir([999, 3, 6, 10])
    assert valor is None


def test_formula(modelo_entrenado):
    formula = modelo_entrenado.obtener_formula()
    assert "b0" in formula
    assert "temperatura" in formula
