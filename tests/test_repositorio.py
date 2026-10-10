"""Pruebas del repositorio PostgreSQL con una conexion simulada.

No requieren una cuenta real de Neon: usan un doble que registra las
consultas y devuelve datos predefinidos.
"""

from base_datos.repositorio import RepositorioPostgreSQL


class ConexionSimulada:
    """Doble de conexion que registra sentencias y devuelve filas falsas."""

    def __init__(self, filas_retorno=None):
        self.sentencias = []
        self.esta_conectado = True
        self._filas = filas_retorno or []

    def conectar(self):
        return True

    def ejecutar_sentencia(self, sentencia, params=None):
        self.sentencias.append((sentencia.strip(), params))
        return None

    def ejecutar_y_obtener(self, sentencia, params=None):
        self.sentencias.append((sentencia.strip(), params))
        return list(self._filas)


def test_inicializar_tablas():
    conexion = ConexionSimulada()
    repo = RepositorioPostgreSQL(conexion)
    assert repo.inicializar_tablas() is True
    sentencias = " ".join(s for s, _ in conexion.sentencias)
    assert "CREATE TABLE IF NOT EXISTS registros_historicos" in sentencias
    assert "CREATE TABLE IF NOT EXISTS entrenamientos" in sentencias
    assert "CREATE TABLE IF NOT EXISTS predicciones" in sentencias


def test_insertar_registro_historico():
    conexion = ConexionSimulada(filas_retorno=[(1,)])
    repo = RepositorioPostgreSQL(conexion)
    id_reg = repo.insertar_registro_historico(25, 3, 6, 10.5, 22.3)
    assert id_reg == 1
    sentencia, params = conexion.sentencias[-1]
    assert "INSERT INTO registros_historicos" in sentencia
    assert params == (25, 3, 6, 10.5, 22.3)


def test_obtener_registros():
    filas = [(1, 25, 3, 6, 10.5, 22.3, "2024-01-01")]
    conexion = ConexionSimulada(filas_retorno=filas)
    repo = RepositorioPostgreSQL(conexion)
    registros = repo.obtener_todos_registros()
    assert registros[0]["temperatura"] == 25
    assert registros[0]["consumo_real"] == 22.3


def test_insertar_prediccion():
    conexion = ConexionSimulada(filas_retorno=[(5,)])
    repo = RepositorioPostgreSQL(conexion)
    id_pred = repo.insertar_prediccion(25, 3, 6, 10, 21.5, "v1.0.0", "lote-1")
    assert id_pred == 5
    sentencia, params = conexion.sentencias[-1]
    assert "INSERT INTO predicciones" in sentencia
    assert "lote-1" in params


def test_insertar_entrenamiento():
    conexion = ConexionSimulada(filas_retorno=[(2,)])
    repo = RepositorioPostgreSQL(conexion)
    id_ent = repo.insertar_entrenamiento("Regresion Lineal Multiple", 40, 0.99, 0.1, 0.32, "1.0.0")
    assert id_ent == 2
    assert "INSERT INTO entrenamientos" in conexion.sentencias[-1][0]


def test_consultas_parametrizadas():
    """Ninguna consulta debe interpolar valores directamente."""
    conexion = ConexionSimulada(filas_retorno=[(1,)])
    repo = RepositorioPostgreSQL(conexion)
    repo.insertar_registro_historico(25, 3, 6, 10.5, 22.3)
    sentencia, params = conexion.sentencias[-1]
    assert "%s" in sentencia
    assert "25" not in sentencia
