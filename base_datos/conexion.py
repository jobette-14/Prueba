"""Modulo de conexion a PostgreSQL para ElectroPredict.

Utiliza psycopg2 para la conexion directa y gestiona SSL segun los requisitos
de Neon. Las credenciales se obtienen de variables de entorno.
"""

import os
import ssl
import logging
from typing import Optional, Any, List, Tuple

logger = logging.getLogger(__name__)

try:
    import psycopg2
    from psycopg2.extensions import connection as Psycopg2Connection

    PSYCOPG2_DISPONIBLE = True
except ImportError:  # pragma: no cover - depende del entorno
    psycopg2 = None
    Psycopg2Connection = Any
    PSYCOPG2_DISPONIBLE = False
    logger.warning("psycopg2 no esta instalado. La base de datos no estara disponible.")


class ConexionError(Exception):
    """Error de conexion a la base de datos."""
    pass


class ConfiguracionError(Exception):
    """Error cuando faltan configuraciones requeridas."""
    pass


def limpiar_url(url: Optional[str]) -> str:
    """Oculta credenciales de una URL para mostrarla en mensajes seguros."""
    if not url:
        return "(no configurada)"
    try:
        if "@" in url:
            pre, post = url.split("@", 1)
            if "//" in pre:
                esquema, _ = pre.split("//", 1)
                return f"{esquema}//***@{post}"
    except Exception:
        pass
    return "***"


class ConexionPostgreSQL:
    """Gestiona la conexion con una base de datos PostgreSQL (Neon)."""

    def __init__(self, url: Optional[str] = None) -> None:
        self._url = url or os.getenv("DATABASE_URL")
        self._conexion = None

    @property
    def esta_conectado(self) -> bool:
        """Verifica si hay una conexion activa."""
        return self._conexion is not None and not getattr(self._conexion, "closed", True)

    def configurada(self) -> bool:
        """Indica si hay una URL de base de datos configurada."""
        return bool(self._url)

    def obtener_url_segura(self) -> str:
        """Devuelve la URL sin credenciales, para mensajes."""
        return limpiar_url(self._url)

    def conectar(self) -> bool:
        """Establece la conexion con la base de datos.

        Returns:
            True si la conexion se establecio correctamente.
        """
        if not PSYCOPG2_DISPONIBLE:
            logger.error("psycopg2 no disponible. Ejecute: pip install psycopg2-binary")
            return False

        if not self._url:
            logger.error("DATABASE_URL no configurada en variables de entorno")
            return False

        try:
            self._conexion = psycopg2.connect(
                self._url,
                ssl_context=ssl.create_default_context(),
                connect_timeout=10,
            )
            self._conexion.autocommit = False
            logger.info("Conexion a PostgreSQL establecida correctamente")
            return True
        except psycopg2.OperationalError as e:
            logger.error(f"Error de conexion: {e}")
            self._conexion = None
            return False
        except Exception as e:
            logger.error(f"Error inesperado al conectar: {e}")
            self._conexion = None
            return False

    def desconectar(self) -> None:
        """Cierra la conexion con la base de datos."""
        if self._conexion is not None and not getattr(self._conexion, "closed", True):
            try:
                self._conexion.close()
            except Exception:
                pass
            self._conexion = None
            logger.info("Conexion a PostgreSQL cerrada")

    def ejecutar_sentencia(self, sentencia: str, params: Optional[tuple] = None) -> Any:
        """Ejecuta una sentencia SQL parametrizada y confirma la transaccion.

        Args:
            sentencia: SQL con marcadores %s.
            params: Tupla de parametros.

        Returns:
            El cursor con los resultados disponibles (si los hay).
        """
        if not self.esta_conectado:
            raise ConexionError("No hay conexion activa a la base de datos")

        try:
            cursor = self._conexion.cursor()
            cursor.execute(sentencia, params or ())
            self._conexion.commit()
            return cursor
        except Exception as e:
            self._conexion.rollback()
            logger.error(f"Error ejecutando SQL: {e}")
            raise

    def ejecutar_y_obtener(self, sentencia: str, params: Optional[tuple] = None) -> List[Tuple]:
        """Ejecuta una consulta de solo lectura y devuelve los resultados."""
        if not self.esta_conectado:
            raise ConexionError("No hay conexion activa a la base de datos")

        try:
            with self._conexion.cursor() as cursor:
                cursor.execute(sentencia, params or ())
                resultados = list(cursor.fetchall())
            self._conexion.commit()
            return resultados
        except Exception as e:
            self._conexion.rollback()
            logger.error(f"Error obteniendo resultados: {e}")
            raise

    def verificar_conexion_salud(self) -> bool:
        """Verifica que la conexion sea saludable con una consulta simple."""
        if not self.esta_conectado:
            return False
        try:
            with self._conexion.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return True
        except Exception:
            return False
