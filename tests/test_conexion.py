"""Pruebas de la conexion a base de datos (sin Neon real)."""

import os

from base_datos.conexion import ConexionPostgreSQL, limpiar_url


def test_sin_url_no_configurada(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    conexion = ConexionPostgreSQL()
    assert conexion.configurada() is False
    assert conexion.esta_conectado is False


def test_conectar_sin_url_falla(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    conexion = ConexionPostgreSQL()
    assert conexion.conectar() is False


def test_limpiar_url_oculta_credenciales():
    url = "postgresql://usuario:secreto@ep-xxx.neon.tech/dbname"
    limpia = limpiar_url(url)
    assert "secreto" not in limpia
    assert "usuario" not in limpia
    assert "neon.tech" in limpia


def test_limpiar_url_vacia():
    assert limpiar_url(None) == "(no configurada)"
    assert limpiar_url("") == "(no configurada)"


def test_url_segura_no_expone_password(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:password@host:5432/db")
    conexion = ConexionPostgreSQL()
    segura = conexion.obtener_url_segura()
    assert "password" not in segura


def test_ejecutar_sin_conexion_lanza_error(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    import pytest
    from base_datos.conexion import ConexionError
    conexion = ConexionPostgreSQL()
    with pytest.raises(ConexionError):
        conexion.ejecutar_y_obtener("SELECT 1")
