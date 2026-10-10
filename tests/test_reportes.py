"""Pruebas de generacion de reportes."""

import os

from datos.gestor import GestorDatos
from reportes.generador import (
    resumen_datos_historicos, resumen_predicciones,
    generar_reporte_texto, exportar_reporte_csv,
    generar_reporte_pdf, reportlab_disponible,
)


def _gestor_con_datos():
    gestor = GestorDatos()
    for i in range(5):
        gestor.agregar_registro(20 + i, 2 + (i % 3), 4 + i, 8 + i, 15 + 2 * i)
    gestor.agregar_prediccion(25, 3, 6, 10, 21.0, "v1.0.0", "individual", consumo_real=22.0)
    gestor.agregar_prediccion(26, 3, 7, 11, 23.0, "v1.0.0", "lote", lote="lote-1")
    return gestor


def test_resumen_datos_historicos():
    gestor = _gestor_con_datos()
    resumen = resumen_datos_historicos(gestor)
    assert resumen["cantidad"] == 5
    assert "consumo_promedio" in resumen


def test_resumen_datos_vacio():
    assert resumen_datos_historicos(GestorDatos()) == {"cantidad": 0}


def test_resumen_predicciones():
    gestor = _gestor_con_datos()
    resumen = resumen_predicciones(gestor)
    assert resumen["cantidad"] == 2
    assert resumen["individuales"] == 1
    assert resumen["lotes"] == 1
    assert resumen["con_consumo_real"] == 1


def test_generar_reporte_texto():
    gestor = _gestor_con_datos()
    reporte = generar_reporte_texto(gestor, None, None, None)
    assert "REPORTE ELECTROPREDICT" in reporte
    assert "RESUMEN DE DATOS HISTORICOS" in reporte
    assert "HISTORIAL DE PREDICCIONES" in reporte


def test_exportar_reporte_csv_predicciones(tmp_path):
    gestor = _gestor_con_datos()
    ruta = tmp_path / "predicciones.csv"
    assert exportar_reporte_csv(gestor, str(ruta), "predicciones") is True
    contenido = ruta.read_text(encoding="utf-8")
    assert "consumo_estimado" in contenido


def test_exportar_reporte_csv_historicos(tmp_path):
    gestor = _gestor_con_datos()
    ruta = tmp_path / "historicos.csv"
    assert exportar_reporte_csv(gestor, str(ruta), "historicos") is True
    contenido = ruta.read_text(encoding="utf-8")
    assert "consumo_real" in contenido


def test_reporte_texto_usa_algoritmo(datos_deterministas):
    from modelo.entrenamiento import ModeloRegresionLineal
    gestor = _gestor_con_datos()
    modelo = ModeloRegresionLineal(algoritmo="ridge")
    X, y = modelo.preparar_datos(datos_deterministas)
    modelo.entrenar(X, y)
    reporte = generar_reporte_texto(gestor, modelo, modelo.metricas, None)
    assert "Ridge" in reporte


def test_generar_reporte_pdf(tmp_path):
    if not reportlab_disponible():
        import pytest
        pytest.skip("reportlab no instalado")
    gestor = _gestor_con_datos()
    ruta = tmp_path / "reporte.pdf"
    assert generar_reporte_pdf(gestor, None, None, None, str(ruta)) is True
    assert ruta.exists()
    assert ruta.read_bytes().startswith(b"%PDF")


def test_generar_reporte_pdf_con_modelo(datos_deterministas, tmp_path):
    if not reportlab_disponible():
        import pytest
        pytest.skip("reportlab no instalado")
    from modelo.entrenamiento import ModeloRegresionLineal
    gestor = _gestor_con_datos()
    modelo = ModeloRegresionLineal()
    X, y = modelo.preparar_datos(datos_deterministas)
    modelo.entrenar(X, y)
    ruta = tmp_path / "reporte_modelo.pdf"
    assert generar_reporte_pdf(
        gestor, modelo, modelo.metricas, {"num_registros": 40}, str(ruta)) is True
    assert ruta.exists()
