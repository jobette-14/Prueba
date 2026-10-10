"""Modulo de prediccion para ElectroPredict.

Proporciona funciones para predicciones individuales y por lotes utilizando
el modelo de regresion lineal multiple entrenado."""
import logging
from typing import List, Tuple, Optional, Dict, Any

from datos.carga_csv import leer_csv_prediccion
from modelo.entrenamiento import ModeloRegresionLineal

logger = logging.getLogger(__name__)


def predecir_individual(
    modelo: ModeloRegresionLineal,
    temperatura: float,
    personas: int,
    horas_uso: float,
    consumo_anterior: float,
) -> Tuple[Optional[float], Optional[str]]:
    """Realiza una prediccion individual de consumo electrico.

    Returns:
        Tupla (consumo_estimado_en_kWh, mensaje).
        Si hay error, el consumo_estimado es None y el mensaje describe el error.
    """
    if modelo is None:
        return None, "No se ha cargado un modelo"

    if not modelo.entrenado:
        return None, "El modelo aun no ha sido entrenado"

    consumo_estimado, info = modelo.predecir(
        [temperatura, personas, horas_uso, consumo_anterior]
    )

    if consumo_estimado is None:
        return None, "Error al realizar la prediccion (verifique los valores de entrada)"

    return consumo_estimado, f"Consumo estimado: {consumo_estimado:.2f} kWh"


def predecir_lotes(
    modelo: ModeloRegresionLineal,
    archivo_csv: str,
) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """Realiza predicciones por lotes a partir de un archivo CSV.

    El CSV puede incluir o no la columna 'consumo_real'. Si la incluye, se usa
    unicamente para comparar con la prediccion, nunca como entrada del modelo.

    Returns:
        Tupla (resultados, resumen). resultados es una lista de diccionarios.
    """
    if modelo is None:
        return None, "No se ha cargado un modelo"

    if not modelo.entrenado:
        return None, "El modelo aun no ha sido entrenado"

    datos, resumen_csv = leer_csv_prediccion(archivo_csv)

    if resumen_csv.get("errores"):
        errores_desc = "; ".join(
            e.get("mensaje", "Error desconocido") for e in resumen_csv["errores"]
        )
        return None, f"Errores en el CSV: {errores_desc}"

    if not datos:
        return None, "No hay datos validos en el archivo CSV para realizar predicciones"

    resultados: List[Dict[str, Any]] = []

    for i, fila in enumerate(datos):
        try:
            consumo_estimado, _ = modelo.predecir([
                fila["temperatura"],
                fila["personas"],
                fila["horas_uso"],
                fila["consumo_anterior"],
            ])

            registro = {
                "fila": i + 1,
                "temperatura": fila["temperatura"],
                "personas": fila["personas"],
                "horas_uso": fila["horas_uso"],
                "consumo_anterior": fila["consumo_anterior"],
                "consumo_estimado": consumo_estimado,
                "modelo": f"v{modelo.version}",
            }

            real = fila.get("consumo_real")
            if real is not None and consumo_estimado is not None:
                registro["consumo_real"] = real
                registro["error"] = round(real - consumo_estimado, 4)
                registro["error_absoluto"] = round(abs(real - consumo_estimado), 4)
            elif real is not None:
                registro["consumo_real"] = real

            resultados.append(registro)

        except Exception as e:
            logger.error(f"Error prediciendo fila {i + 1}: {e}")
            resultados.append({
                "fila": i + 1,
                "temperatura": fila.get("temperatura"),
                "personas": fila.get("personas"),
                "horas_uso": fila.get("horas_uso"),
                "consumo_anterior": fila.get("consumo_anterior"),
                "consumo_estimado": None,
                "error_prediccion": str(e),
                "modelo": f"v{modelo.version}",
            })

    if not resultados:
        return None, "No se pudieron generar predicciones para ninguna fila"

    exitosos = sum(1 for r in resultados if r.get("consumo_estimado") is not None)
    fallidos = len(resultados) - exitosos
    resumen = f"Procesadas: {len(resultados)} | Exitosas: {exitosos} | Fallidas: {fallidos}"

    return resultados, resumen
