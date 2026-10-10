"""Módulo de carga y validación de datos CSV para ElectroPredict."""

import csv
import io
import os
from typing import List, Dict, Any, Optional, Tuple


COLUMNAS_ESPERADAS = [
    "temperatura",
    "personas",
    "horas_uso",
    "consumo_anterior",
    "consumo_real",
]

COLUMNAS_PREDICCION = [
    "temperatura",
    "personas",
    "horas_uso",
    "consumo_anterior",
]


def leer_csv(archivo_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Lee un archivo CSV y devuelve los datos validos y un resumen.

    Args:
        archivo_path: Ruta al archivo CSV.

    Returns:
        Tupla con (lista de diccionarios de datos, resumen de validacion).
    """
    resumen_vacio = {"total": 0, "validos": 0, "invalidos": 0, "errores": []}

    if not archivo_path or not str(archivo_path).strip():
        return [], resumen_vacio

    if not os.path.exists(archivo_path):
        return [], {
            "total": 0,
            "validos": 0,
            "invalidos": 0,
            "errores": [{"fila": 0, "mensaje": "El archivo no existe", "tipo": "archivo"}],
        }

    try:
        with open(archivo_path, "r", encoding="utf-8-sig") as f:
            contenido = f.read()
    except OSError as e:
        return [], {
            "total": 0,
            "validos": 0,
            "invalidos": 0,
            "errores": [{"fila": 0, "mensaje": f"No se pudo leer el archivo: {e}", "tipo": "archivo"}],
        }

    if not contenido.strip():
        return [], resumen_vacio

    reader = csv.DictReader(io.StringIO(contenido))
    filas = list(reader)
    columnas = reader.fieldnames or []

    errores: List[Dict[str, Any]] = []
    columnas_normalizadas = [c.strip().lower() for c in columnas]
    columnas_faltantes = [c for c in COLUMNAS_ESPERADAS if c not in columnas_normalizadas]

    if columnas_faltantes:
        errores.append({
            "fila": 0,
            "mensaje": f"Columnas faltantes: {', '.join(columnas_faltantes)}",
            "tipo": "columnas",
        })

    datos_validos: List[Dict[str, Any]] = []
    datos_invalidos: List[Dict[str, Any]] = []

    for i, fila in enumerate(filas, start=1):
        fila_errores: List[str] = []
        fila_normalizada = {(k.strip().lower() if k else k): v for k, v in fila.items()}

        valores_numericos: Dict[str, Any] = {}
        for col in COLUMNAS_ESPERADAS:
            valor_raw = fila_normalizada.get(col, "")
            valor = (valor_raw or "").strip()

            if valor == "":
                fila_errores.append(f"Campo vacio en '{col}'")
                continue

            try:
                if col == "personas":
                    valores_numericos[col] = int(float(valor))
                else:
                    valores_numericos[col] = float(valor)
            except (ValueError, TypeError):
                fila_errores.append(f"Valor no numerico en '{col}': '{valor}'")

        if fila_errores:
            datos_invalidos.append({
                "fila": i,
                "errores": fila_errores,
                "datos_originales": dict(fila),
            })
        else:
            datos_validos.append(valores_numericos)

    resumen = {
        "total": len(filas),
        "validos": len(datos_validos),
        "invalidos": len(datos_invalidos),
        "errores": errores,
        "filas_invalidas": datos_invalidos,
    }

    return datos_validos, resumen


def leer_csv_prediccion(archivo_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Lee un CSV de prediccion por lotes (puede o no incluir consumo_real).

    Args:
        archivo_path: Ruta al archivo CSV.

    Returns:
        Tupla (datos validos, resumen). Los datos incluyen 'consumo_real' si existe.
    """
    resumen_vacio = {"total": 0, "validos": 0, "invalidos": 0, "errores": []}

    if not archivo_path or not os.path.exists(archivo_path):
        return [], {
            "total": 0, "validos": 0, "invalidos": 0,
            "errores": [{"fila": 0, "mensaje": "El archivo no existe", "tipo": "archivo"}],
        }

    with open(archivo_path, "r", encoding="utf-8-sig") as f:
        contenido = f.read()

    if not contenido.strip():
        return [], resumen_vacio

    reader = csv.DictReader(io.StringIO(contenido))
    filas = list(reader)
    columnas = [c.strip().lower() for c in (reader.fieldnames or [])]

    errores: List[Dict[str, Any]] = []
    faltantes = [c for c in COLUMNAS_PREDICCION if c not in columnas]
    if faltantes:
        errores.append({
            "fila": 0,
            "mensaje": f"Columnas faltantes: {', '.join(faltantes)}",
            "tipo": "columnas",
        })

    tiene_real = "consumo_real" in columnas
    datos_validos: List[Dict[str, Any]] = []
    datos_invalidos: List[Dict[str, Any]] = []

    for i, fila in enumerate(filas, start=1):
        fila_errores: List[str] = []
        fila_normalizada = {(k.strip().lower() if k else k): v for k, v in fila.items()}
        registro: Dict[str, Any] = {"consumo_real": None}

        for col in COLUMNAS_PREDICCION:
            valor = (fila_normalizada.get(col, "") or "").strip()
            if valor == "":
                fila_errores.append(f"Campo vacio en '{col}'")
                continue
            try:
                if col == "personas":
                    registro[col] = int(float(valor))
                else:
                    registro[col] = float(valor)
            except (ValueError, TypeError):
                fila_errores.append(f"Valor no numerico en '{col}': '{valor}'")

        if tiene_real:
            valor_real = (fila_normalizada.get("consumo_real", "") or "").strip()
            if valor_real != "":
                try:
                    registro["consumo_real"] = float(valor_real)
                except (ValueError, TypeError):
                    fila_errores.append(f"Valor no numerico en 'consumo_real': '{valor_real}'")

        if fila_errores:
            datos_invalidos.append({"fila": i, "errores": fila_errores, "datos_originales": dict(fila)})
        else:
            datos_validos.append(registro)

    return datos_validos, {
        "total": len(filas),
        "validos": len(datos_validos),
        "invalidos": len(datos_invalidos),
        "errores": errores,
        "filas_invalidas": datos_invalidos,
        "tiene_consumo_real": tiene_real,
    }


def obtener_columnas_csv(archivo_path: str) -> Optional[List[str]]:
    """Obtiene las columnas de un archivo CSV."""
    try:
        with open(archivo_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header:
                return [h.strip() for h in header]
    except (FileNotFoundError, StopIteration, OSError):
        pass
    return None


def detectar_duplicados(datos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detecta filas duplicadas en los datos.

    Args:
        datos: Lista de diccionarios de datos.

    Returns:
        Lista de grupos de filas duplicadas.
    """
    vistos: Dict[tuple, int] = {}
    duplicados: List[Dict[str, Any]] = []

    for i, fila in enumerate(datos):
        clave = tuple(fila.get(c) for c in COLUMNAS_ESPERADAS)
        if clave in vistos:
            duplicados.append({
                "fila_original": vistos[clave],
                "fila_actual": i,
            })
        else:
            vistos[clave] = i

    return duplicados


def exportar_a_csv(datos: List[Dict[str, Any]], archivo_destino: str,
                   columnas: Optional[List[str]] = None) -> bool:
    """Exporta datos a un archivo CSV.

    Args:
        datos: Lista de diccionarios.
        archivo_destino: Ruta de destino.
        columnas: Columnas a exportar (si None, usa las claves de la primera fila).

    Returns:
        True si se exporto correctamente.
    """
    if not datos:
        return False

    if columnas is None:
        columnas = list(datos[0].keys())

    try:
        with open(archivo_destino, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columnas, extrasaction="ignore")
            writer.writeheader()
            for fila in datos:
                writer.writerow(fila)
        return True
    except OSError:
        return False
