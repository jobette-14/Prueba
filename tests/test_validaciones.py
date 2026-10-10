"""Pruebas de validaciones de datos."""

import math

from datos.validaciones import (
    validar_valor_numerico, validar_entero, validar_temperatura,
    validar_personas, validar_horas_uso, validar_consumo,
    validar_consumo_anterior, validar_csv_columnas,
)


def test_validar_valor_numerico_correcto():
    valor, err = validar_valor_numerico("25.5", "Prueba", minimo=0, maximo=100)
    assert err is None
    assert valor == 25.5


def test_validar_valor_vacio():
    valor, err = validar_valor_numerico("", "Prueba")
    assert valor is None
    assert "vacio" in err


def test_validar_valor_no_numerico():
    valor, err = validar_valor_numerico("abc", "Prueba")
    assert valor is None
    assert "numerico" in err


def test_validar_valor_negativo_no_permitido():
    valor, err = validar_valor_numerico("-5", "Prueba")
    assert valor is None
    assert "negativo" in err


def test_validar_valor_negativo_permitido():
    valor, err = validar_valor_numerico("-5", "Prueba", permitir_negativo=True)
    assert err is None
    assert valor == -5


def test_validar_valor_infinito():
    valor, err = validar_valor_numerico("inf", "Prueba", permitir_negativo=True)
    assert valor is None
    assert err is not None


def test_validar_valor_nan():
    valor, err = validar_valor_numerico("nan", "Prueba", permitir_negativo=True)
    assert valor is None


def test_validar_rango():
    valor, err = validar_valor_numerico("150", "Prueba", minimo=0, maximo=100)
    assert valor is None
    assert "menor o igual" in err


def test_validar_entero():
    valor, err = validar_entero("5", "Enteros", minimo=1, maximo=10)
    assert err is None and valor == 5


def test_validar_entero_decimal():
    valor, err = validar_entero("3.7", "Enteros")
    assert err is None and valor == 3


def test_validar_temperatura_valida():
    assert validar_temperatura("22.5") == (22.5, None)


def test_validar_temperatura_negativa_valida():
    valor, err = validar_temperatura("-10")
    assert err is None and valor == -10.0


def test_validar_temperatura_excedida():
    valor, err = validar_temperatura("100")
    assert valor is None


def test_validar_personas():
    assert validar_personas("3") == (3, None)
    assert validar_personas("0")[0] is None
    assert validar_personas("51")[0] is None


def test_validar_horas_uso():
    assert validar_horas_uso("8") == (8.0, None)
    assert validar_horas_uso("25")[0] is None
    assert validar_horas_uso("-1")[0] is None


def test_validar_consumo_anterior():
    assert validar_consumo_anterior("12.5") == (12.5, None)
    assert validar_consumo_anterior("-1")[0] is None


def test_validar_csv_columnas_ok():
    assert validar_csv_columnas(["temperatura", "personas", "horas_uso",
                                 "consumo_anterior", "consumo_real"]) is None


def test_validar_csv_columnas_faltantes():
    err = validar_csv_columnas(["temperatura", "personas"])
    assert err is not None and "faltantes" in err
