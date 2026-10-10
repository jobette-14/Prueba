"""Pruebas del gestor de datos (en memoria y con repositorio simulado)."""

from datos.gestor import GestorDatos


def test_agregar_registro():
    gestor = GestorDatos()
    reg = gestor.agregar_registro(25, 3, 6, 10.5, 22.3)
    assert reg["temperatura"] == 25.0
    assert gestor.cantidad_registros() == 1


def test_agregar_registros_masivo():
    gestor = GestorDatos()
    datos = [
        {"temperatura": 25, "personas": 3, "horas_uso": 6, "consumo_anterior": 10, "consumo_real": 20},
        {"temperatura": 30, "personas": 4, "horas_uso": 7, "consumo_anterior": 11, "consumo_real": 24},
    ]
    cantidad = gestor.agregar_registros_masivo(datos)
    assert cantidad == 2
    assert gestor.cantidad_registros() == 2


def test_prediccion_y_error():
    gestor = GestorDatos()
    pred = gestor.agregar_prediccion(25, 3, 6, 10, 20.0, modelo="v1.0.0",
                                     tipo="individual", consumo_real=22.0)
    assert pred["error"] == 2.0
    assert gestor.cantidad_predicciones() == 1


def test_registrar_consumo_real_posterior():
    gestor = GestorDatos()
    pred = gestor.agregar_prediccion(25, 3, 6, 10, 20.0, modelo="v1.0.0")
    assert pred["error"] is None
    actualizada = gestor.registrar_consumo_real(pred["id"], 23.5)
    assert actualizada["consumo_real"] == 23.5
    assert actualizada["error"] == 3.5


def test_registrar_consumo_real_inexistente():
    gestor = GestorDatos()
    assert gestor.registrar_consumo_real(999, 10.0) is None


def test_ultimo_consumo():
    gestor = GestorDatos()
    assert gestor.ultimo_consumo() is None
    gestor.agregar_registro(25, 3, 6, 10, 20, fecha="2024-01-01 10:00")
    gestor.agregar_registro(30, 4, 7, 11, 25, fecha="2024-02-01 10:00")
    ultimo = gestor.ultimo_consumo()
    assert ultimo["consumo_real"] == 25.0


def test_registrar_entrenamiento():
    gestor = GestorDatos()
    info = {"exitoso": True, "num_registros": 40, "version": "1.0.0",
            "metricas": {"r2": 0.99, "mae": 0.1, "mse": 0.01, "rmse": 0.1}}
    reg = gestor.registrar_entrenamiento(info)
    assert reg["estado"] == "activo"
    assert gestor.ultimo_entrenamiento()["r2"] == 0.99


def test_datos_para_entrenamiento():
    gestor = GestorDatos()
    gestor.agregar_registro(25, 3, 6, 10, 20)
    datos = gestor.datos_para_entrenamiento()
    assert len(datos) == 1
    assert set(datos[0].keys()) == {"temperatura", "personas", "horas_uso",
                                    "consumo_anterior", "consumo_real"}


def test_persistencia_sin_conexion():
    """Sin repositorio, la persistencia esta deshabilitada y no falla."""
    gestor = GestorDatos()
    assert gestor.tiene_persistencia is False
    reg = gestor.agregar_registro(25, 3, 6, 10, 20)
    assert "id_bd" not in reg


class _ConexionFalsa:
    """Objeto de conexion simulado con estado 'conectado'."""

    def __init__(self):
        self.closed = 0


class _RepositorioFalso:
    """Repositorio simulado que registra llamadas (sin base de datos real)."""

    def __init__(self):
        self.registros = []
        self.predicciones = []
        self.entrenamientos = []
        from base_datos.conexion import ConexionPostgreSQL
        self._conexion = ConexionPostgreSQL()
        self._conexion._conexion = _ConexionFalsa()

    def insertar_registro_historico(self, *args):
        self.registros.append(args)
        return len(self.registros)

    def insertar_prediccion(self, *args):
        self.predicciones.append(args)
        return len(self.predicciones)

    def insertar_entrenamiento(self, *args):
        self.entrenamientos.append(args)
        return len(self.entrenamientos)

    def obtener_todos_registros(self):
        return []


def test_persistencia_con_repositorio_falso():
    repo = _RepositorioFalso()
    gestor = GestorDatos(repo)
    assert gestor.tiene_persistencia is True
    reg = gestor.agregar_registro(25, 3, 6, 10, 20)
    assert "id_bd" in reg
    assert len(repo.registros) == 1
