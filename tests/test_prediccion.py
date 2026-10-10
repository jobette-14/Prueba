"""Pruebas de prediccion individual y por lotes."""

from modelo.prediccion import predecir_individual, predecir_lotes


def test_prediccion_individual(modelo_entrenado):
    valor, mensaje = predecir_individual(modelo_entrenado, 25, 3, 6, 10.0)
    assert valor is not None
    assert valor > 0
    assert "Consumo estimado" in mensaje
    assert "kWh" in mensaje


def test_prediccion_individual_sin_modelo():
    valor, mensaje = predecir_individual(None, 25, 3, 6, 10.0)
    assert valor is None
    assert "modelo" in mensaje.lower()


def test_prediccion_individual_sin_entrenar():
    from modelo.entrenamiento import ModeloRegresionLineal
    valor, mensaje = predecir_individual(ModeloRegresionLineal(), 25, 3, 6, 10.0)
    assert valor is None


def test_prediccion_individual_invalida(modelo_entrenado):
    valor, mensaje = predecir_individual(modelo_entrenado, 999, 3, 6, 10.0)
    assert valor is None


def test_prediccion_por_lotes(modelo_entrenado, csv_prediccion):
    resultados, resumen = predecir_lotes(modelo_entrenado, csv_prediccion)
    assert resultados is not None
    assert len(resultados) == 3
    for r in resultados:
        assert r["consumo_estimado"] is not None
        assert r["consumo_estimado"] > 0
    assert "Exitosas: 3" in resumen


def test_prediccion_por_lotes_archivo_inexistente(modelo_entrenado):
    resultados, resumen = predecir_lotes(modelo_entrenado, "no_existe.csv")
    assert resultados is None


def test_prediccion_por_lotes_sin_modelo(csv_prediccion):
    resultados, resumen = predecir_lotes(None, csv_prediccion)
    assert resultados is None


def test_prediccion_por_lotes_con_consumo_real(modelo_entrenado, tmp_path):
    contenido = (
        "temperatura,personas,horas_uso,consumo_anterior,consumo_real\n"
        "29,4,6,10.2,25.0\n"
        "31,5,8,12.1,26.0\n"
    )
    ruta = tmp_path / "con_real.csv"
    ruta.write_text(contenido, encoding="utf-8")
    resultados, resumen = predecir_lotes(modelo_entrenado, str(ruta))
    assert resultados is not None
    assert resultados[0].get("consumo_real") == 25.0
    assert "error" in resultados[0]
