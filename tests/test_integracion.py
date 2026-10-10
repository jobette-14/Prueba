"""Pruebas de integracion: flujo completo datos -> entrenamiento -> prediccion."""

from datos.gestor import GestorDatos
from modelo.entrenamiento import ModeloRegresionLineal
from modelo.prediccion import predecir_individual, predecir_lotes
from modelo.evaluacion import evaluar_modelo


def test_flujo_completo(datos_deterministas, csv_prediccion, tmp_path):
    # 1. Cargar datos en el gestor
    gestor = GestorDatos()
    gestor.agregar_registros_masivo(datos_deterministas)
    assert gestor.cantidad_registros() == 40

    # 2. Entrenar
    modelo = ModeloRegresionLineal()
    X, y = modelo.preparar_datos(gestor.datos_para_entrenamiento())
    resultado = modelo.entrenar(X, y, test_size=0.2)
    assert resultado["exitoso"]
    assert modelo.entrenado

    # 3. Evaluar
    X_test, y_test = modelo.datos_prueba
    evaluacion = evaluar_modelo(modelo, X_test, y_test)
    assert evaluacion["exitoso"]
    assert evaluacion["metricas"]["rmse"] >= 0

    # 4. Prediccion individual y registro
    estimado, _ = predecir_individual(modelo, 25, 3, 6, 10.0)
    assert estimado is not None
    gestor.agregar_prediccion(25, 3, 6, 10.0, estimado, modelo=f"v{modelo.version}",
                              tipo="individual")

    # 5. Prediccion por lotes
    resultados, _ = predecir_lotes(modelo, csv_prediccion)
    assert resultados is not None and len(resultados) == 3

    # 6. Reporte
    from reportes.generador import generar_reporte_texto
    reporte = generar_reporte_texto(gestor, modelo, evaluacion["metricas"], resultado)
    assert "REPORTE ELECTROPREDICT" in reporte


def test_modelo_reutilizado_tras_reentrenamiento(datos_deterministas):
    modelo = ModeloRegresionLineal()
    X, y = modelo.preparar_datos(datos_deterministas[:20])
    modelo.entrenar(X, y)
    primero = modelo.predecir([25, 3, 6, 10])[0]

    X2, y2 = modelo.preparar_datos(datos_deterministas)
    modelo.entrenar(X2, y2)
    segundo = modelo.predecir([25, 3, 6, 10])[0]

    assert primero is not None and segundo is not None
    # Ambos son predicciones validas (pueden diferir por el conjunto de entrenamiento)
    assert segundo > 0
