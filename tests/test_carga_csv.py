"""Pruebas de carga y exportacion de CSV."""

import os
import tempfile

from datos.carga_csv import (
    leer_csv, leer_csv_prediccion, obtener_columnas_csv,
    detectar_duplicados, exportar_a_csv,
)


CSV_VALIDO = """temperatura,personas,horas_uso,consumo_anterior,consumo_real
25,3,6,10.5,22.3
30,5,8,12.1,28.7
20,2,4,8.0,15.2
"""

CSV_CON_INVALIDOS = """temperatura,personas,horas_uso,consumo_anterior,consumo_real
25,3,6,10.5,22.3
30,abc,8,12.1,28.7
,2,4,8.0,15.2
"""

CSV_SIN_CONSUMO_REAL = """temperatura,personas,horas_uso,consumo_anterior
29,4,6,10.2
31,5,8,12.1
"""


def _escribir(texto: str) -> str:
    fd, ruta = tempfile.mkstemp(suffix=".csv")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(texto)
    return ruta


def test_leer_csv_valido():
    ruta = _escribir(CSV_VALIDO)
    datos, resumen = leer_csv(ruta)
    assert resumen["total"] == 3
    assert resumen["validos"] == 3
    assert resumen["invalidos"] == 0
    assert datos[0]["temperatura"] == 25.0
    assert datos[0]["personas"] == 3
    os.remove(ruta)


def test_leer_csv_con_invalidos():
    ruta = _escribir(CSV_CON_INVALIDOS)
    datos, resumen = leer_csv(ruta)
    assert resumen["validos"] == 1
    assert resumen["invalidos"] == 2
    os.remove(ruta)


def test_leer_csv_archivo_inexistente():
    datos, resumen = leer_csv("no_existe_12345.csv")
    assert datos == []
    assert resumen["errores"]


def test_leer_csv_vacio():
    ruta = _escribir("")
    datos, resumen = leer_csv(ruta)
    assert datos == []
    assert resumen["total"] == 0
    os.remove(ruta)


def test_leer_csv_columnas_faltantes():
    ruta = _escribir("temperatura,personas\n25,3\n")
    datos, resumen = leer_csv(ruta)
    assert any(e.get("tipo") == "columnas" for e in resumen["errores"])
    os.remove(ruta)


def test_leer_csv_prediccion_sin_real():
    ruta = _escribir(CSV_SIN_CONSUMO_REAL)
    datos, resumen = leer_csv_prediccion(ruta)
    assert resumen["validos"] == 2
    assert resumen["tiene_consumo_real"] is False
    assert datos[0]["consumo_real"] is None
    os.remove(ruta)


def test_leer_csv_prediccion_con_real():
    ruta = _escribir(CSV_VALIDO)
    datos, resumen = leer_csv_prediccion(ruta)
    assert resumen["tiene_consumo_real"] is True
    assert datos[0]["consumo_real"] == 22.3
    os.remove(ruta)


def test_obtener_columnas_csv():
    ruta = _escribir(CSV_VALIDO)
    columnas = obtener_columnas_csv(ruta)
    assert columnas == ["temperatura", "personas", "horas_uso",
                        "consumo_anterior", "consumo_real"]
    os.remove(ruta)


def test_detectar_duplicados():
    datos = [
        {"temperatura": 25, "personas": 3, "horas_uso": 6, "consumo_anterior": 10, "consumo_real": 20},
        {"temperatura": 25, "personas": 3, "horas_uso": 6, "consumo_anterior": 10, "consumo_real": 20},
        {"temperatura": 30, "personas": 4, "horas_uso": 7, "consumo_anterior": 11, "consumo_real": 22},
    ]
    dups = detectar_duplicados(datos)
    assert len(dups) == 1


def test_exportar_a_csv():
    fd, ruta = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    datos = [{"temperatura": 25, "personas": 3, "horas_uso": 6,
              "consumo_anterior": 10.5, "consumo_real": 22.3}]
    assert exportar_a_csv(datos, ruta) is True
    with open(ruta, encoding="utf-8") as f:
        contenido = f.read()
    assert "temperatura" in contenido
    assert "22.3" in contenido
    os.remove(ruta)


def test_exportar_a_csv_sin_datos():
    assert exportar_a_csv([], "cualquiera.csv") is False
