"""Persistencia de modelos entrenados en disco.

Guarda y carga el modelo (estimador + metadatos) usando joblib/pickle, con un
archivo JSON de metadatos legible. Controla la version y valida que el objeto
cargado sea un modelo de ElectroPredict para no cargar archivos desconocidos.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

import joblib

from modelo.entrenamiento import ModeloRegresionLineal

logger = logging.getLogger(__name__)

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
DIRECTORIO_MODELOS = RAIZ_PROYECTO / "modelos"


def directorio_modelos() -> Path:
    """Devuelve (y crea si hace falta) el directorio de modelos."""
    DIRECTORIO_MODELOS.mkdir(parents=True, exist_ok=True)
    return DIRECTORIO_MODELOS


def _ruta_metadata(ruta_pkl: Path) -> Path:
    return ruta_pkl.with_suffix(".json")


def guardar_modelo(
    modelo: ModeloRegresionLineal,
    ruta: Optional[str] = None,
    nombre: Optional[str] = None,
    directorio: Optional[str] = None,
) -> Optional[str]:
    """Guarda el modelo entrenado y sus metadatos.

    Args:
        modelo: Modelo ya entrenado.
        ruta: Ruta destino del .pkl. Si es None, se genera con nombre/version.
        nombre: Nombre base opcional para el archivo.
        directorio: Directorio alternativo (por defecto `modelos/`).

    Returns:
        La ruta del archivo .pkl guardado, o None si fallo.
    """
    if modelo is None or not modelo.entrenado:
        logger.error("No se puede guardar un modelo sin entrenar")
        return None

    try:
        if ruta is None:
            base = nombre or f"modelo_{modelo.algoritmo}"
            marca = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_dir = Path(directorio) if directorio else directorio_modelos()
            base_dir.mkdir(parents=True, exist_ok=True)
            ruta_path = base_dir / f"{base}_v{modelo.version}_{marca}.pkl"
        else:
            ruta_path = Path(ruta)
            ruta_path.parent.mkdir(parents=True, exist_ok=True)

        joblib.dump(modelo, ruta_path)

        metadata = {
            "version_modelo": modelo.version,
            "algoritmo": modelo.algoritmo,
            "algoritmo_nombre": modelo.algoritmo_nombre,
            "imputacion": modelo.imputar,
            "feature_names": modelo.feature_names,
            "metricas": modelo.metricas,
            "fecha_guardado": datetime.now().isoformat(timespec="seconds"),
            "archivo": ruta_path.name,
        }
        with open(_ruta_metadata(ruta_path), "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        logger.info(f"Modelo guardado en {ruta_path}")
        return str(ruta_path)

    except Exception as e:
        logger.error(f"Error guardando modelo: {e}")
        return None


def cargar_modelo(ruta: str) -> Optional[ModeloRegresionLineal]:
    """Carga un modelo desde disco validando su tipo.

    Returns:
        El modelo cargado, o None si el archivo es invalido o de otro tipo.
    """
    ruta_path = Path(ruta)
    if not ruta_path.exists():
        logger.error(f"El archivo no existe: {ruta}")
        return None

    try:
        objeto = joblib.load(ruta_path)
    except Exception as e:
        logger.error(f"No se pudo cargar el archivo (posiblemente corrupto): {e}")
        return None

    if not isinstance(objeto, ModeloRegresionLineal):
        logger.error("El archivo no contiene un modelo valido de ElectroPredict")
        return None

    if not objeto.entrenado:
        logger.error("El modelo cargado no esta entrenado")
        return None

    logger.info(f"Modelo cargado desde {ruta} ({objeto.algoritmo_nombre})")
    return objeto


def listar_modelos(directorio: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lista los modelos guardados leyendo sus metadatos JSON.

    Returns:
        Lista de diccionarios con los metadatos y la ruta del modelo.
    """
    base = Path(directorio) if directorio else directorio_modelos()
    if not base.exists():
        return []

    modelos: List[Dict[str, Any]] = []
    for pkl in sorted(base.glob("*.pkl"), key=lambda p: p.stat().st_mtime, reverse=True):
        meta_path = _ruta_metadata(pkl)
        meta: Dict[str, Any] = {"archivo": pkl.name, "ruta": str(pkl)}
        if meta_path.exists():
            try:
                with open(meta_path, encoding="utf-8") as f:
                    meta.update(json.load(f))
            except (OSError, json.JSONDecodeError):
                pass
        modelos.append(meta)
    return modelos
