"""Repositorio de datos para ElectroPredict.

Maneja todas las operaciones de insercion, consulta y gestion de tablas
en PostgreSQL (Neon) para los historiales de consumos, entrenamientos y
predicciones. Todas las consultas son parametrizadas.
"""

import logging
from typing import List, Optional, Dict, Any

from .conexion import ConexionPostgreSQL, ConexionError

logger = logging.getLogger(__name__)


class RepositorioPostgreSQL:
    """Repositorio que abstrae el acceso a los datos en PostgreSQL."""

    def __init__(self, conexion: ConexionPostgreSQL) -> None:
        self._conexion = conexion
        self._tablas_creadas = False

    @property
    def conexion(self) -> ConexionPostgreSQL:
        return self._conexion

    def inicializar_tablas(self) -> bool:
        """Crea las tablas si no existen. No elimina ni modifica las existentes."""
        if not self._conexion.esta_conectado:
            if not self._conexion.conectar():
                return False

        try:
            for sentencia in self._sentencias_creacion():
                self._conexion.ejecutar_sentencia(sentencia)
            self._tablas_creadas = True
            logger.info("Esquema de base de datos inicializado")
            return True
        except Exception as e:
            logger.error(f"Error inicializando tablas: {e}")
            return False

    @staticmethod
    def _sentencias_creacion() -> List[str]:
        return [
            """
            CREATE TABLE IF NOT EXISTS registros_historicos (
                id SERIAL PRIMARY KEY,
                temperatura NUMERIC NOT NULL,
                personas INTEGER NOT NULL CHECK (personas >= 0),
                horas_uso NUMERIC NOT NULL CHECK (horas_uso >= 0),
                consumo_anterior NUMERIC NOT NULL,
                consumo_real NUMERIC NOT NULL CHECK (consumo_real >= 0),
                fecha_registro TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS entrenamientos (
                id SERIAL PRIMARY KEY,
                fecha_training TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                algoritmo VARCHAR(100) NOT NULL,
                num_registros INTEGER NOT NULL,
                r2_score NUMERIC,
                mae NUMERIC,
                mse NUMERIC,
                rmse NUMERIC,
                version VARCHAR(50) NOT NULL,
                estado VARCHAR(50) DEFAULT 'activo'
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS predicciones (
                id SERIAL PRIMARY KEY,
                fecha_prediccion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                temperatura NUMERIC NOT NULL,
                personas INTEGER NOT NULL,
                horas_uso NUMERIC NOT NULL,
                consumo_anterior NUMERIC NOT NULL,
                consumo_estimado NUMERIC NOT NULL,
                modelo VARCHAR(100) NOT NULL,
                lote_identificador VARCHAR(100),
                consumo_real_posterior NUMERIC,
                error_calculado NUMERIC
            );
            """,
        ]

    # --- Registros historicos ---
    def insertar_registro_historico(
        self, temperatura: float, personas: int, horas_uso: float,
        consumo_anterior: float, consumo_real: float,
    ) -> Optional[int]:
        sentencia = """
        INSERT INTO registros_historicos
            (temperatura, personas, horas_uso, consumo_anterior, consumo_real)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """
        try:
            filas = self._conexion.ejecutar_y_obtener(
                sentencia, (temperatura, personas, horas_uso, consumo_anterior, consumo_real)
            )
            return filas[0][0] if filas else None
        except Exception as e:
            logger.error(f"Error insertando registro historico: {e}")
            return None

    def obtener_todos_registros(self) -> List[Dict[str, Any]]:
        sentencia = """
        SELECT id, temperatura, personas, horas_uso, consumo_anterior,
               consumo_real, fecha_registro
        FROM registros_historicos
        ORDER BY fecha_registro ASC, id ASC;
        """
        columnas = ["id", "temperatura", "personas", "horas_uso",
                    "consumo_anterior", "consumo_real", "fecha_registro"]
        try:
            return [dict(zip(columnas, fila))
                    for fila in self._conexion.ejecutar_y_obtener(sentencia)]
        except Exception as e:
            logger.error(f"Error obteniendo registros: {e}")
            return []

    def obtener_ultimos_registros(self, limite: int = 10) -> List[Dict[str, Any]]:
        sentencia = """
        SELECT id, temperatura, personas, horas_uso, consumo_anterior,
               consumo_real, fecha_registro
        FROM registros_historicos
        ORDER BY fecha_registro DESC
        LIMIT %s;
        """
        columnas = ["id", "temperatura", "personas", "horas_uso",
                    "consumo_anterior", "consumo_real", "fecha_registro"]
        try:
            return [dict(zip(columnas, fila))
                    for fila in self._conexion.ejecutar_y_obtener(sentencia, (limite,))]
        except Exception as e:
            logger.error(f"Error obteniendo ultimos registros: {e}")
            return []

    # --- Entrenamientos ---
    def insertar_entrenamiento(
        self, algoritmo: str, num_registros: int, r2: Optional[float],
        mse: Optional[float], rmse: Optional[float], version: str,
        estado: str = "activo",
    ) -> Optional[int]:
        sentencia = """
        INSERT INTO entrenamientos
            (algoritmo, num_registros, r2_score, mse, rmse, version, estado)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        try:
            filas = self._conexion.ejecutar_y_obtener(
                sentencia, (algoritmo, num_registros, r2, mse, rmse, version, estado)
            )
            return filas[0][0] if filas else None
        except Exception as e:
            logger.error(f"Error insertando entrenamiento: {e}")
            return None

    def obtener_ultimos_entrenamientos(self, limite: int = 5) -> List[Dict[str, Any]]:
        sentencia = """
        SELECT id, fecha_training, algoritmo, num_registros, r2_score,
               mse, rmse, version, estado
        FROM entrenamientos
        ORDER BY fecha_training DESC
        LIMIT %s;
        """
        columnas = ["id", "fecha_training", "algoritmo", "num_registros",
                    "r2_score", "mse", "rmse", "version", "estado"]
        try:
            return [dict(zip(columnas, fila))
                    for fila in self._conexion.ejecutar_y_obtener(sentencia, (limite,))]
        except Exception as e:
            logger.error(f"Error obteniendo entrenamientos: {e}")
            return []

    # --- Predicciones ---
    def insertar_prediccion(
        self, temperatura: float, personas: int, horas_uso: float,
        consumo_anterior: float, consumo_estimado: float, modelo: str,
        lote: Optional[str] = None, consumo_real: Optional[float] = None,
        error: Optional[float] = None,
    ) -> Optional[int]:
        sentencia = """
        INSERT INTO predicciones
            (temperatura, personas, horas_uso, consumo_anterior, consumo_estimado,
             modelo, lote_identificador, consumo_real_posterior, error_calculado)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        try:
            filas = self._conexion.ejecutar_y_obtener(
                sentencia,
                (temperatura, personas, horas_uso, consumo_anterior, consumo_estimado,
                 modelo, lote, consumo_real, error),
            )
            return filas[0][0] if filas else None
        except Exception as e:
            logger.error(f"Error insertando prediccion: {e}")
            return None

    def actualizar_consumo_real_prediccion(
        self, id_prediccion: int, consumo_real: float, error: float,
    ) -> bool:
        sentencia = """
        UPDATE predicciones
        SET consumo_real_posterior = %s, error_calculado = %s
        WHERE id = %s;
        """
        try:
            self._conexion.ejecutar_sentencia(
                sentencia, (consumo_real, error, id_prediccion)
            )
            return True
        except Exception as e:
            logger.error(f"Error actualizando consumo real: {e}")
            return False

    def obtener_historial_predicciones(
        self, limite: int = 100,
        fecha_desde: Optional[str] = None, fecha_hasta: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        sentencia = """
        SELECT id, fecha_prediccion, temperatura, personas, horas_uso,
               consumo_anterior, consumo_estimado, modelo, lote_identificador,
               consumo_real_posterior, error_calculado
        FROM predicciones
        WHERE 1 = 1
        """
        params: List[Any] = []
        if fecha_desde:
            sentencia += " AND fecha_prediccion >= %s"
            params.append(fecha_desde)
        if fecha_hasta:
            sentencia += " AND fecha_prediccion <= %s"
            params.append(fecha_hasta)
        sentencia += " ORDER BY fecha_prediccion DESC LIMIT %s;"
        params.append(limite)

        columnas = ["id", "fecha_prediccion", "temperatura", "personas", "horas_uso",
                    "consumo_anterior", "consumo_estimado", "modelo", "lote_identificador",
                    "consumo_real_posterior", "error_calculado"]
        try:
            return [dict(zip(columnas, fila))
                    for fila in self._conexion.ejecutar_y_obtener(sentencia, tuple(params))]
        except Exception as e:
            logger.error(f"Error obteniendo historial: {e}")
            return []
