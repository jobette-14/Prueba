"""Gestor de datos de ElectroPredict.

Coordina el estado en memoria (registros historicos, predicciones y
entrenamientos) y su persistencia opcional en PostgreSQL/Neon.

La aplicacion es funcional sin base de datos; en ese caso los datos viven
unicamente en memoria durante la sesion.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class GestorDatos:
    """Gestiona los registros historicos, predicciones y entrenamientos."""

    def __init__(self, repositorio=None) -> None:
        self._repositorio = repositorio
        self._registros: List[Dict[str, Any]] = []
        self._predicciones: List[Dict[str, Any]] = []
        self._entrenamientos: List[Dict[str, Any]] = []
        self._siguiente_id_registro = 1
        self._siguiente_id_prediccion = 1

    # --- Configuracion ---
    def usar_repositorio(self, repositorio) -> None:
        """Asigna o actualiza el repositorio de persistencia."""
        self._repositorio = repositorio

    @property
    def tiene_persistencia(self) -> bool:
        """Indica si hay un repositorio con conexion activa."""
        if self._repositorio is None:
            return False
        conexion = getattr(self._repositorio, "_conexion", None)
        return bool(conexion and getattr(conexion, "esta_conectado", False))

    # --- Registros historicos ---
    def agregar_registro(
        self,
        temperatura: float,
        personas: int,
        horas_uso: float,
        consumo_anterior: float,
        consumo_real: float,
        fecha: Optional[str] = None,
        persistir: bool = True,
    ) -> Dict[str, Any]:
        """Agrega un registro historico en memoria y opcionalmente en la BD."""
        registro = {
            "id": self._siguiente_id_registro,
            "temperatura": float(temperatura),
            "personas": int(personas),
            "horas_uso": float(horas_uso),
            "consumo_anterior": float(consumo_anterior),
            "consumo_real": float(consumo_real),
            "fecha_registro": fecha or datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        self._registros.append(registro)
        self._siguiente_id_registro += 1

        if persistir and self.tiene_persistencia:
            id_bd = self._repositorio.insertar_registro_historico(
                temperatura, personas, horas_uso, consumo_anterior, consumo_real
            )
            if id_bd is not None:
                registro["id_bd"] = id_bd

        return registro

    def agregar_registros_masivo(self, registros: List[Dict[str, Any]],
                                 persistir: bool = True) -> int:
        """Agrega varios registros. Devuelve la cantidad agregada."""
        contador = 0
        for reg in registros:
            self.agregar_registro(
                reg["temperatura"], reg["personas"], reg["horas_uso"],
                reg["consumo_anterior"], reg["consumo_real"],
                fecha=reg.get("fecha_registro"), persistir=persistir,
            )
            contador += 1
        return contador

    def registros(self) -> List[Dict[str, Any]]:
        """Devuelve una copia de los registros historicos en memoria."""
        return list(self._registros)

    def cantidad_registros(self) -> int:
        return len(self._registros)

    def vaciar_registros(self) -> None:
        """Vacía los registros solo en memoria (no elimina datos de la BD)."""
        self._registros = []

    def cargar_desde_bd(self) -> int:
        """Carga registros historicos desde la base de datos a memoria."""
        if not self.tiene_persistencia:
            return 0
        try:
            filas = self._repositorio.obtener_todos_registros()
        except Exception as e:
            logger.error(f"Error cargando registros desde BD: {e}")
            return 0

        cargados = 0
        ids_existentes = {r.get("id_bd") for r in self._registros}
        for fila in filas:
            if fila.get("id") in ids_existentes:
                continue
            self._registros.append({
                "id": self._siguiente_id_registro,
                "id_bd": fila.get("id"),
                "temperatura": float(fila["temperatura"]),
                "personas": int(fila["personas"]),
                "horas_uso": float(fila["horas_uso"]),
                "consumo_anterior": float(fila["consumo_anterior"]),
                "consumo_real": float(fila["consumo_real"]),
                "fecha_registro": str(fila.get("fecha_registro", "")),
            })
            self._siguiente_id_registro += 1
            cargados += 1
        return cargados

    # --- Predicciones ---
    def agregar_prediccion(
        self,
        temperatura: float,
        personas: int,
        horas_uso: float,
        consumo_anterior: float,
        consumo_estimado: float,
        modelo: str,
        tipo: str = "individual",
        lote: Optional[str] = None,
        consumo_real: Optional[float] = None,
        persistir: bool = True,
    ) -> Dict[str, Any]:
        """Agrega una prediccion en memoria y opcionalmente en la BD."""
        error = None
        if consumo_real is not None:
            error = round(float(consumo_real) - float(consumo_estimado), 4)

        prediccion = {
            "id": self._siguiente_id_prediccion,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "temperatura": float(temperatura),
            "personas": int(personas),
            "horas_uso": float(horas_uso),
            "consumo_anterior": float(consumo_anterior),
            "consumo_estimado": float(consumo_estimado),
            "modelo": modelo,
            "tipo": tipo,
            "lote": lote,
            "consumo_real": consumo_real,
            "error": error,
        }
        self._predicciones.append(prediccion)
        self._siguiente_id_prediccion += 1

        if persistir and self.tiene_persistencia:
            id_bd = self._repositorio.insertar_prediccion(
                temperatura, personas, horas_uso, consumo_anterior,
                consumo_estimado, modelo, lote, consumo_real, error,
            )
            if id_bd is not None:
                prediccion["id_bd"] = id_bd

        return prediccion

    def predicciones(self) -> List[Dict[str, Any]]:
        return list(self._predicciones)

    def cantidad_predicciones(self) -> int:
        return len(self._predicciones)

    def registrar_consumo_real(self, id_prediccion: int,
                               consumo_real: float) -> Optional[Dict[str, Any]]:
        """Registra el consumo real posterior de una prediccion."""
        for pred in self._predicciones:
            if pred["id"] == id_prediccion:
                pred["consumo_real"] = float(consumo_real)
                pred["error"] = round(float(consumo_real) - pred["consumo_estimado"], 4)
                if self.tiene_persistencia and pred.get("id_bd"):
                    try:
                        self._repositorio.actualizar_consumo_real_prediccion(
                            pred["id_bd"], consumo_real,
                            round(float(consumo_real) - pred["consumo_estimado"], 4)
                        )
                    except Exception as e:
                        logger.error(f"No se pudo persistir consumo real: {e}")
                return pred
        return None

    # --- Entrenamientos ---
    def registrar_entrenamiento(self, info: Dict[str, Any], persistir: bool = True) -> Dict[str, Any]:
        """Registra la informacion de un entrenamiento."""
        metricas = info.get("metricas") or {}
        registro = {
            "id": len(self._entrenamientos) + 1,
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "algoritmo": info.get("algoritmo_nombre", "Regresion Lineal Multiple"),
            "num_registros": info.get("num_registros", 0),
            "r2": metricas.get("r2"),
            "mae": metricas.get("mae"),
            "mse": metricas.get("mse"),
            "rmse": metricas.get("rmse"),
            "version": info.get("version", "1.0.0"),
            "estado": "activo" if info.get("exitoso") else "fallido",
        }
        self._entrenamientos.append(registro)

        if persistir and self.tiene_persistencia and info.get("exitoso"):
            try:
                self._repositorio.insertar_entrenamiento(
                    registro["algoritmo"], registro["num_registros"],
                    registro["r2"], registro["mse"], registro["rmse"],
                    registro["version"], registro["estado"],
                )
            except Exception as e:
                logger.error(f"No se pudo persistir entrenamiento: {e}")

        return registro

    def entrenamientos(self) -> List[Dict[str, Any]]:
        return list(self._entrenamientos)

    def ultimo_entrenamiento(self) -> Optional[Dict[str, Any]]:
        return self._entrenamientos[-1] if self._entrenamientos else None

    # --- Utilidades ---
    def datos_para_entrenamiento(self) -> List[Dict[str, Any]]:
        """Registros con las 5 columnas requeridas para el modelo."""
        return [
            {
                "temperatura": r["temperatura"],
                "personas": r["personas"],
                "horas_uso": r["horas_uso"],
                "consumo_anterior": r["consumo_anterior"],
                "consumo_real": r["consumo_real"],
            }
            for r in self._registros
        ]

    def ultimo_consumo(self) -> Optional[Dict[str, Any]]:
        """Devuelve el registro mas reciente por fecha (o el ultimo agregado)."""
        if not self._registros:
            return None
        return max(self._registros, key=lambda r: r.get("fecha_registro", ""))
