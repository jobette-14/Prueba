"""Pruebas de la API web (sin Neon real: estado en memoria)."""

import pytest
from fastapi.testclient import TestClient

from web.api.config import Configuracion
from web.api.estado import EstadoApp
from web.api.main import create_app


def _generar_datos(n=40, semilla=7):
    import numpy as np
    rng = np.random.default_rng(semilla)
    filas = []
    for _ in range(n):
        t = float(rng.integers(15, 35))
        p = int(rng.integers(1, 6))
        h = float(rng.integers(1, 12))
        ca = round(5 + t * 0.2 + rng.normal(0, 0.3), 2)
        real = round(2.0 + 0.5 * t + 1.2 * p + 0.8 * h + 0.3 * ca + rng.normal(0, 0.2), 3)
        filas.append({"temperatura": t, "personas": p, "horas_uso": h,
                      "consumo_anterior": ca, "consumo_real": real})
    return filas


def _config(**extra):
    base = dict(entorno="prueba", api_key="", directorio_modelos="",
                directorio_frontend="", database_url="", chat_enabled=False,
                chat_api_key="")
    base.update(extra)
    return Configuracion(**base)


@pytest.fixture
def cliente(tmp_path):
    cfg = _config(directorio_modelos=str(tmp_path))
    estado = EstadoApp(cfg)
    estado.agregar_registros_masivo(_generar_datos())
    app = create_app(config=cfg, estado=estado)
    with TestClient(app) as c:
        yield c


def test_salud(cliente):
    r = cliente.get("/api/salud")
    assert r.status_code == 200
    assert r.json()["estado"] == "ok"


def test_config_publica_no_expone_secretos():
    cfg = _config(api_key="secreta-123", database_url="postgresql://user:pw@host/db")
    estado = EstadoApp(cfg)
    app = create_app(config=cfg, estado=estado)
    with TestClient(app) as c:
        r = c.get("/api/config-publica")
        assert r.status_code == 200
        cuerpo = r.text
        assert "secreta-123" not in cuerpo
        assert "pw" not in cuerpo
        assert "postgresql://" not in cuerpo


def test_prediccion_sin_modelo_409(cliente):
    r = cliente.post("/api/prediccion", json={
        "temperatura": 25, "personas": 3, "horas_uso": 6, "consumo_anterior": 10})
    assert r.status_code == 409


def test_flujo_completo(cliente):
    r = cliente.post("/api/modelo/entrenar", json={"algoritmo": "lineal"})
    assert r.status_code == 200 and r.json()["exitoso"]

    r = cliente.post("/api/prediccion", json={
        "temperatura": 25, "personas": 3, "horas_uso": 6, "consumo_anterior": 10,
        "consumo_real": 24})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["consumo_estimado"] > 0
    assert cuerpo["error"] == pytest.approx(24 - cuerpo["consumo_estimado"], abs=1e-3)

    r = cliente.get("/api/historial")
    assert r.status_code == 200 and len(r.json()["predicciones"]) == 1

    r = cliente.get("/api/estadisticas")
    assert r.status_code == 200
    assert r.json()["modelo"]["entrenado"] is True

    assert cliente.get("/api/reportes/txt").status_code == 200
    assert cliente.get("/api/reportes/csv?tipo=predicciones").status_code == 200
    assert cliente.get("/api/reportes/pdf").status_code in (200, 503)


def test_validacion_de_rangos(cliente):
    r = cliente.post("/api/prediccion", json={
        "temperatura": 999, "personas": 3, "horas_uso": 6, "consumo_anterior": 10})
    assert r.status_code == 422


def test_api_key_protege_escritura(tmp_path):
    cfg = _config(api_key="clave-segura", directorio_modelos=str(tmp_path))
    estado = EstadoApp(cfg)
    app = create_app(config=cfg, estado=estado)
    with TestClient(app) as c:
        cuerpo = {"temperatura": 25, "personas": 3, "horas_uso": 6,
                  "consumo_anterior": 10, "consumo_real": 22}
        assert c.post("/api/registros", json=cuerpo).status_code == 401
        r = c.post("/api/registros", json=cuerpo, headers={"X-API-Key": "clave-segura"})
        assert r.status_code == 200


def test_importar_registros_csv(cliente):
    contenido = ("temperatura,personas,horas_uso,consumo_anterior,consumo_real\n"
                 "29,4,6,10.2,22.5\n"
                 "31,5,8,12.1,26.0\n")
    archivos = {"archivo": ("datos.csv", contenido, "text/csv")}
    r = cliente.post("/api/registros/importar", files=archivos)
    assert r.status_code == 200
    assert r.json()["agregados"] == 2


def test_prediccion_lotes_json(cliente):
    cliente.post("/api/modelo/entrenar", json={"algoritmo": "ridge"})
    payload = {"filas": [
        {"temperatura": 25, "personas": 3, "horas_uso": 6, "consumo_anterior": 10},
        {"temperatura": 30, "personas": 4, "horas_uso": 7, "consumo_anterior": 12},
    ]}
    r = cliente.post("/api/prediccion/lotes/json", json=payload)
    assert r.status_code == 200
    assert len(r.json()["resultados"]) == 2


def test_chat_sin_configuracion(cliente):
    r = cliente.post("/api/chat", json={"mensaje": "Hola"})
    assert r.status_code == 200
    assert r.json()["disponible"] is False


def test_consumo_real_en_historial(cliente):
    cliente.post("/api/modelo/entrenar", json={"algoritmo": "lineal"})
    p = cliente.post("/api/prediccion", json={
        "temperatura": 25, "personas": 3, "horas_uso": 6, "consumo_anterior": 10}).json()
    r = cliente.post("/api/historial/consumo-real",
                     json={"id_prediccion": 1, "consumo_real": 20})
    assert r.status_code == 200
    assert r.json()["prediccion"]["consumo_real"] == 20
