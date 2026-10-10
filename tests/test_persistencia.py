"""Pruebas de la persistencia de modelos en disco."""

import json

import joblib

from modelo.entrenamiento import ModeloRegresionLineal
from modelo.persistencia import (
    guardar_modelo, cargar_modelo, listar_modelos,
)


def test_no_guardar_modelo_sin_entrenar(tmp_path):
    modelo = ModeloRegresionLineal()
    assert guardar_modelo(modelo, ruta=str(tmp_path / "x.pkl")) is None


def test_guardar_y_cargar_modelo(datos_deterministas, tmp_path):
    modelo = ModeloRegresionLineal(algoritmo="ridge", imputar=False)
    X, y = modelo.preparar_datos(datos_deterministas)
    modelo.entrenar(X, y)

    ruta = tmp_path / "modelo.pkl"
    guardado = guardar_modelo(modelo, ruta=str(ruta))
    assert guardado is not None
    assert ruta.exists()

    cargado = cargar_modelo(str(ruta))
    assert cargado is not None
    assert cargado.algoritmo == "ridge"
    assert cargado.entrenado is True
    assert cargado.metricas == modelo.metricas

    pred_original, _ = modelo.predecir([25, 3, 6, 10])
    pred_cargado, _ = cargado.predecir([25, 3, 6, 10])
    assert pred_original == pred_cargado


def test_metadata_json_se_crea(datos_deterministas, tmp_path):
    modelo = ModeloRegresionLineal()
    X, y = modelo.preparar_datos(datos_deterministas)
    modelo.entrenar(X, y)
    ruta = tmp_path / "modelo.pkl"
    guardar_modelo(modelo, ruta=str(ruta))

    meta_path = ruta.with_suffix(".json")
    assert meta_path.exists()
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["algoritmo"] == "lineal"
    assert "metricas" in meta
    assert "fecha_guardado" in meta


def test_listar_modelos(datos_deterministas, tmp_path):
    modelo = ModeloRegresionLineal()
    X, y = modelo.preparar_datos(datos_deterministas)
    modelo.entrenar(X, y)
    guardar_modelo(modelo, ruta=str(tmp_path / "uno.pkl"))
    guardar_modelo(modelo, ruta=str(tmp_path / "dos.pkl"))

    listado = listar_modelos(str(tmp_path))
    assert len(listado) == 2
    assert all("archivo" in m for m in listado)


def test_cargar_archivo_inexistente(tmp_path):
    assert cargar_modelo(str(tmp_path / "no_existe.pkl")) is None


def test_cargar_objeto_no_valido(tmp_path):
    ruta = tmp_path / "malo.pkl"
    joblib.dump({"no": "es un modelo"}, str(ruta))
    assert cargar_modelo(str(ruta)) is None


def test_listar_modelos_directorio_vacio(tmp_path):
    assert listar_modelos(str(tmp_path)) == []
