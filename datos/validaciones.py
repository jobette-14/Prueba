"""Modulo de validaciones para ElectroPredict."""

from typing import Optional, Tuple


def validar_valor_numerico(
    valor: str,
    nombre: str,
    minimo: Optional[float] = None,
    maximo: Optional[float] = None,
    permitir_negativo: bool = False,
) -> Tuple[Optional[float], Optional[str]]:
    """Valida y convierte un valor numerico.

    Args:
        valor: Cadena de texto del valor.
        nombre: Nombre del parametro para mensajes de error.
        minimo: Valor minimo permitido.
        maximo: Valor maximo permitido.
        permitir_negativo: Si False, valores negativos son invalidos.

    Returns:
        Tupla (valor_convertido, mensaje_error). Si hay error, el valor es None.
    """
    if valor is None or str(valor).strip() == "":
        return None, f"{nombre} no puede estar vacio"

    try:
        float_valor = float(valor)
    except (ValueError, TypeError):
        return None, f"{nombre} debe ser un valor numerico"

    # Rechazar valores no finitos (inf, nan)
    if float_valor != float_valor or float_valor in (float("inf"), float("-inf")):
        return None, f"{nombre} contiene un valor no valido (infinito o indefinido)"

    if not permitir_negativo and float_valor < 0:
        return None, f"{nombre} no puede ser negativo"

    if minimo is not None and float_valor < minimo:
        return None, f"{nombre} debe ser mayor o igual a {minimo}"

    if maximo is not None and float_valor > maximo:
        return None, f"{nombre} debe ser menor o igual a {maximo}"

    return float_valor, None


def validar_entero(
    valor: str,
    nombre: str,
    minimo: Optional[int] = None,
    maximo: Optional[int] = None,
) -> Tuple[Optional[int], Optional[str]]:
    """Valida y convierte un valor entero."""
    if valor is None or str(valor).strip() == "":
        return None, f"{nombre} no puede estar vacio"

    try:
        int_valor = int(float(valor))
    except (ValueError, TypeError):
        return None, f"{nombre} debe ser un numero entero"

    if minimo is not None and int_valor < minimo:
        return None, f"{nombre} debe ser mayor o igual a {minimo}"

    if maximo is not None and int_valor > maximo:
        return None, f"{nombre} debe ser menor o igual a {maximo}"

    return int_valor, None


def validar_temperatura(valor: str) -> Tuple[Optional[float], Optional[str]]:
    """Valida un valor de temperatura. Rango tipico: -50C a 60C."""
    return validar_valor_numerico(valor, "Temperatura", minimo=-50, maximo=60, permitir_negativo=True)


def validar_personas(valor: str) -> Tuple[Optional[int], Optional[str]]:
    """Valida la cantidad de personas. Rango: 1 a 50 personas."""
    return validar_entero(valor, "Personas", minimo=1, maximo=50)


def validar_horas_uso(valor: str) -> Tuple[Optional[float], Optional[str]]:
    """Valida horas de uso. Rango: 0 a 24 horas."""
    return validar_valor_numerico(valor, "Horas de uso", minimo=0, maximo=24, permitir_negativo=False)


def validar_consumo(valor: str) -> Tuple[Optional[float], Optional[str]]:
    """Valida un valor de consumo en kWh. Rango: 0 a 1000 kWh."""
    return validar_valor_numerico(valor, "Consumo", minimo=0, maximo=1000)


def validar_consumo_anterior(valor: str) -> Tuple[Optional[float], Optional[str]]:
    """Valida el consumo anterior en kWh. Rango: 0 a 1000 kWh."""
    return validar_valor_numerico(valor, "Consumo anterior", minimo=0, maximo=1000)


def validar_csv_columnas(columnas, columnas_esperadas=None) -> Optional[str]:
    """Valida que las columnas de un CSV incluyan las esperadas.

    Returns:
        Mensaje de error si faltan columnas, None si son correctas.
    """
    if columnas_esperadas is None:
        columnas_esperadas = ["temperatura", "personas", "horas_uso", "consumo_anterior", "consumo_real"]

    columnas_normalizadas = [str(c).lower().strip() for c in (columnas or [])]
    faltantes = [c for c in columnas_esperadas if c not in columnas_normalizadas]
    if faltantes:
        return f"Columnas faltantes en el CSV: {', '.join(faltantes)}"
    return None
