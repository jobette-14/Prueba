"""Módulo de evaluación de modelos para ElectroPredict.

Cálculo y gestión de métricas de evaluación de regresión."""
import logging
import numpy as np
from typing import Optional, Dict, Any

from modelo.entrenamiento import ModeloRegresionLineal

logger = logging.getLogger(__name__)


def calcular_metrica_r2(y_real: np.ndarray, y_predicho: np.ndarray) -> float:
    """Calcula el coeficiente de determinación R².

    Args:
        y_real: Valores reales.
        y_predicho: Valores predichos.

    Returns:
        Valor de R² (puede ser negativo en modelos pobres).
    """
    if len(y_real) == 0 or len(y_predicho) == 0:
        return 0.0

    if len(y_real) != len(y_predicho):
        raise ValueError("Los arreglos deben tener la misma longitud")

    # Fórmula: 1 - (SS_res / SS_tot)
    ss_res = np.sum((y_real - y_predicho) ** 2)
    ss_tot = np.sum((y_real - np.mean(y_real)) ** 2)

    if ss_tot == 0:
        return 1.0 if ss_res == 0 else 0.0

    r2 = 1.0 - (ss_res / ss_tot)
    return float(r2)


def calcular_metrica_mae(y_real: np.ndarray, y_predicho: np.ndarray) -> float:
    """Calcula el Error Absoluto Medio (MAE).

    Args:
        y_real: Valores reales.
        y_predicho: Valores predichos.

    Returns:
        Valor de MAE (siempre no negativo).
    """
    if len(y_real) == 0:
        return 0.0

    mae = np.mean(np.abs(y_real - y_predicho))
    return float(mae)


def calcular_metrica_mse(y_real: np.ndarray, y_predicho: np.ndarray) -> float:
    """Calcula el Error Cuadrático Medio (MSE).

    Args:
        y_real: Valores reales.
        y_predicho: Valores predichos.

    Returns:
        Valor de MSE (siempre no negativo).
    """
    if len(y_real) == 0:
        return 0.0

    mse = np.mean((y_real - y_predicho) ** 2)
    return float(mse)


def calcular_metrica_rmse(y_real: np.ndarray, y_predicho: np.ndarray) -> float:
    """Calcula la Raíz del Error Cuadrático Medio (RMSE).

    Args:
        y_real: Valores reales.
        y_predicho: Valores predichos.

    Returns:
        Valor de RMSE (siempre no negativo).
    """
    mse = calcular_metrica_mse(y_real, y_predicho)
    if mse < 0:
        return 0.0
    rmse = np.sqrt(mse)
    return float(rmse)


def evaluar_modelo(
    modelo: ModeloRegresionLineal,
    X_test: np.ndarray,
    y_test: np.ndarray,
) -> Dict[str, Any]:
    """Evalúa un modelo entrenado con datos de prueba.

    Args:
        modelo: Modelo de regresión lineal múltiple entrenado.
        X_test: Características de prueba.
        y_test: Valores objetivo reales de prueba.

    Returns:
        Diccionario con todas las metricas calculadas.
    """
    if not modelo.entrenado:
        return {
            "exitoso": False,
            "error": "El modelo no ha sido entrenado",
            "metricas": None,
        }

    try:
        y_pred = modelo._modelo.predict(X_test)

        metricas = {
            "r2": calcular_metrica_r2(y_test, y_pred),
            "mae": calcular_metrica_mae(y_test, y_pred),
            "mse": calcular_metrica_mse(y_test, y_pred),
            "rmse": calcular_metrica_rmse(y_test, y_pred),
        }

        # Guardar en el modelo
        modelo._metricas = metricas

        logger.info(f"Evaluación completada: R²={metricas['r2']:.4f}, MAE={metricas['mae']:.4f}")

        return {
            "exitoso": True,
            "num_puntos_evaluacion": len(X_test),
            "metricas": metricas,
        }

    except Exception as e:
        logger.error(f"Error evaluando modelo: {e}")
        return {
            "exitoso": False,
            "error": str(e),
            "metricas": None,
        }