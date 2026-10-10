"""Estado compartido de la API.

Centraliza el acceso a la MISMA logica de negocio que usa la aplicacion de
escritorio (modelo, gestor de datos, repositorio y reportes). No reimplementa
el calculo: importa los modulos existentes del nucleo.
"""

import os
import tempfile
import threading
import logging
from typing import Any, Dict, List, Optional

from modelo.entrenamiento import ModeloRegresionLineal
from modelo.prediccion import predecir_individual, predecir_lotes
from modelo.persistencia import (
    guardar_modelo, cargar_modelo, listar_modelos,
)
from base_datos.conexion import ConexionPostgreSQL
from base_datos.repositorio import RepositorioPostgreSQL
from datos.gestor import GestorDatos
from reportes.generador import resumen_datos_historicos, resumen_predicciones

from .config import Configuracion

logger = logging.getLogger(__name__)


class EstadoApp:
    """Contenedor con el estado mutable compartido por la API."""

    def __init__(self, config: Configuracion) -> None:
        self.config = config
        self._lock = threading.RLock()

        self.conexion = ConexionPostgreSQL(config.database_url or None)
        self.repositorio = RepositorioPostgreSQL(self.conexion)
        self.gestor = GestorDatos(self.repositorio)

        self.modelo = ModeloRegresionLineal()
        self.metricas: Optional[Dict[str, float]] = None
        self.info_entrenamiento: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------
    # Inicializacion
    # ------------------------------------------------------------------
    def inicializar(self) -> Dict[str, Any]:
        """Conecta a la BD (si esta configurada) y carga el ultimo modelo."""
        estado_bd = self._conectar_bd()
        estado_modelo = self._cargar_ultimo_modelo()
        return {"base_datos": estado_bd, "modelo": estado_modelo}

    def _conectar_bd(self) -> Dict[str, Any]:
        if not self.config.database_url:
            logger.warning("DATABASE_URL no configurada; se trabaja en memoria")
            return {"configurada": False, "conectada": False, "mensaje":
                    "Base de datos no configurada. Se usa almacenamiento en memoria."}
        if not self.conexion.conectar():
            return {"configurada": True, "conectada": False, "mensaje":
                    "No se pudo conectar a la base de datos. Se usa memoria."}
        self.repositorio.inicializar_tablas()
        cargados = self.gestor.cargar_desde_bd()
        return {"configurada": True, "conectada": True,
                "mensaje": f"Conectada. Registros cargados: {cargados}."}

    def _cargar_ultimo_modelo(self) -> Dict[str, Any]:
        directorio = self.config.directorio_modelos
        if not directorio or not os.path.isdir(directorio):
            return {"cargado": False, "mensaje": "No hay modelos guardados."}
        modelos = listar_modelos(directorio)
        if not modelos:
            return {"cargado": False, "mensaje": "No hay modelos guardados."}
        modelo = cargar_modelo(modelos[0]["ruta"])
        if modelo is None:
            return {"cargado": False, "mensaje": "No se pudo cargar el modelo."}
        self._fijar_modelo(modelo)
        return {"cargado": True,
                "mensaje": f"Modelo '{modelo.algoritmo_nombre}' cargado."}

    def _fijar_modelo(self, modelo: ModeloRegresionLineal) -> None:
        self.modelo = modelo
        self.metricas = modelo.metricas
        coef = (dict(zip(modelo.feature_names, modelo.coeficientes))
                if modelo.coeficientes is not None else {})
        self.info_entrenamiento = {
            "algoritmo": modelo.algoritmo,
            "algoritmo_nombre": modelo.algoritmo_nombre,
            "imputacion": modelo.imputar,
            "num_registros": modelo.n_entrenamiento + modelo.n_prueba,
            "registros_entrenamiento": modelo.n_entrenamiento,
            "registros_prueba": modelo.n_prueba,
            "coeficientes": coef,
            "intercepto": modelo.intercepto,
            "version": modelo.version,
        }

    # ------------------------------------------------------------------
    # Entrenamiento
    # ------------------------------------------------------------------
    def entrenar(
        self, algoritmo: str = "lineal", imputar: bool = False,
        test_size: float = 0.2, guardar: bool = True,
    ) -> Dict[str, Any]:
        with self._lock:
            datos = self.gestor.datos_para_entrenamiento()
            if len(datos) < 3:
                return {"exitoso": False,
                        "error": "Se requieren al menos 3 registros historicos.",
                        "metricas": None}

            modelo = ModeloRegresionLineal(algoritmo=algoritmo, imputar=imputar)
            X, y = modelo.preparar_datos(datos)
            if X is None or y is None:
                return {"exitoso": False,
                        "error": "Datos invalidos para entrenar.", "metricas": None}

            resultado = modelo.entrenar(X, y, test_size=test_size)
            if not resultado.get("exitoso"):
                return resultado

            self._fijar_modelo(modelo)
            if self.gestor.tiene_persistencia:
                self.gestor.registrar_entrenamiento(resultado)
            if guardar:
                guardar_modelo(modelo, ruta=None,
                               directorio=self.config.directorio_modelos or None)
            return resultado

    # ------------------------------------------------------------------
    # Prediccion
    # ------------------------------------------------------------------
    def predecir(
        self, temperatura: float, personas: int, horas_uso: float,
        consumo_anterior: float, consumo_real: Optional[float] = None,
        persistir: bool = True,
    ) -> Dict[str, Any]:
        with self._lock:
            if not self.modelo.entrenado:
                return {"exitoso": False, "error": "El modelo no esta entrenado."}

            estimado, mensaje = predecir_individual(
                self.modelo, temperatura, personas, horas_uso, consumo_anterior)
            if estimado is None:
                return {"exitoso": False, "error": mensaje}

            error = None
            if consumo_real is not None:
                error = round(float(consumo_real) - float(estimado), 4)

            if persistir:
                self.gestor.agregar_prediccion(
                    temperatura, personas, horas_uso, consumo_anterior,
                    estimado, modelo=f"v{self.modelo.version}", tipo="individual",
                    consumo_real=consumo_real, persistir=persistir)

            return {
                "exitoso": True,
                "consumo_estimado": round(float(estimado), 4),
                "consumo_real": consumo_real,
                "error": error,
                "error_absoluto": None if error is None else round(abs(error), 4),
                "algoritmo": self.modelo.algoritmo_nombre,
                "version": self.modelo.version,
            }

    def predecir_desde_csv(self, archivo: str, lote: Optional[str] = None) -> Dict[str, Any]:
        with self._lock:
            resultados, resumen = predecir_lotes(self.modelo, archivo)
            if resultados is None:
                return {"exitoso": False, "error": resumen}

            for r in resultados:
                if r.get("consumo_estimado") is not None:
                    self.gestor.agregar_prediccion(
                        r["temperatura"], r["personas"], r["horas_uso"],
                        r["consumo_anterior"], r["consumo_estimado"],
                        modelo=f"v{self.modelo.version}", tipo="lote", lote=lote,
                        consumo_real=r.get("consumo_real"))

            return {"exitoso": True, "resumen": resumen, "resultados": resultados}

    def predecir_lote_filas(self, filas: List[Dict[str, Any]],
                            lote: Optional[str] = None) -> Dict[str, Any]:
        """Recibe filas en memoria, las escribe a un CSV temporal y reutiliza
        la misma logica de validacion/prediccion por lotes."""
        columnas = ["temperatura", "personas", "horas_uso", "consumo_anterior", "consumo_real"]
        with tempfile.NamedTemporaryFile(
                "w", suffix=".csv", delete=False, encoding="utf-8", newline="") as f:
            cabecera = [c for c in columnas
                        if any(c in fila for fila in filas)]
            f.write(",".join(cabecera) + "\n")
            for fila in filas:
                f.write(",".join(str(fila.get(c, "")) for c in cabecera) + "\n")
            ruta = f.name
        try:
            return self.predecir_desde_csv(ruta, lote=lote)
        finally:
            try:
                os.remove(ruta)
            except OSError:
                pass

    # ------------------------------------------------------------------
    # Historial y estadisticas
    # ------------------------------------------------------------------
    def registrar_consumo_real(self, id_prediccion: int, consumo_real: float):
        with self._lock:
            return self.gestor.registrar_consumo_real(id_prediccion, consumo_real)

    def historial(self, limite: int = 100) -> List[Dict[str, Any]]:
        datos = self.gestor.predicciones()
        datos = sorted(datos, key=lambda p: p["id"], reverse=True)
        return datos[:limite]

    def estadisticas(self) -> Dict[str, Any]:
        resumen_datos = resumen_datos_historicos(self.gestor)
        resumen_pred = resumen_predicciones(self.gestor)
        return {
            "datos": resumen_datos,
            "predicciones": resumen_pred,
            "modelo": {
                "entrenado": self.modelo.entrenado,
                "algoritmo": self.modelo.algoritmo_nombre,
                "version": self.modelo.version,
                "metricas": self.metricas,
                "imputacion": self.modelo.imputar,
            },
            "base_datos": {
                "configurada": bool(self.config.database_url),
                "conectada": self.gestor.tiene_persistencia,
            },
        }

    def registrar_registro(self, temperatura: float, personas: int, horas_uso: float,
                           consumo_anterior: float, consumo_real: float) -> Dict[str, Any]:
        with self._lock:
            return self.gestor.agregar_registro(
                temperatura, personas, horas_uso, consumo_anterior, consumo_real)

    def agregar_registros_masivo(self, filas: List[Dict[str, Any]]) -> int:
        with self._lock:
            return self.gestor.agregar_registros_masivo(filas)

    def cerrar(self) -> None:
        self.conexion.desconectar()
