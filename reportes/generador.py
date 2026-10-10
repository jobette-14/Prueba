"""Generador de reportes de ElectroPredict.

Produce resumenes de datos historicos, entrenamientos, metricas e historial
de predicciones, en texto y CSV. Solo utiliza datos realmente calculados.
"""

import csv
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    )
    REPORTLAB_DISPONIBLE = True
except ImportError:  # pragma: no cover - depende del entorno
    REPORTLAB_DISPONIBLE = False


def resumen_datos_historicos(gestor) -> Dict[str, Any]:
    """Calcula un resumen de los datos historicos."""
    registros = gestor.registros()
    if not registros:
        return {"cantidad": 0}

    consumos = [r["consumo_real"] for r in registros]
    return {
        "cantidad": len(registros),
        "consumo_promedio": round(sum(consumos) / len(consumos), 3),
        "consumo_minimo": round(min(consumos), 3),
        "consumo_maximo": round(max(consumos), 3),
        "temperatura_promedio": round(sum(r["temperatura"] for r in registros) / len(registros), 3),
        "personas_promedio": round(sum(r["personas"] for r in registros) / len(registros), 3),
        "horas_promedio": round(sum(r["horas_uso"] for r in registros) / len(registros), 3),
    }


def resumen_predicciones(gestor) -> Dict[str, Any]:
    """Calcula un resumen de las predicciones realizadas."""
    predicciones = gestor.predicciones()
    if not predicciones:
        return {"cantidad": 0}

    con_real = [p for p in predicciones if p.get("consumo_real") is not None]
    errores = [abs(p["error"]) for p in con_real if p.get("error") is not None]

    resumen = {
        "cantidad": len(predicciones),
        "individuales": sum(1 for p in predicciones if p.get("tipo") == "individual"),
        "lotes": sum(1 for p in predicciones if p.get("tipo") == "lote"),
        "con_consumo_real": len(con_real),
    }
    if errores:
        resumen["error_absoluto_promedio"] = round(sum(errores) / len(errores), 3)
        resumen["error_absoluto_maximo"] = round(max(errores), 3)
    return resumen


def generar_reporte_texto(gestor, modelo, metricas: Optional[Dict[str, float]],
                          info_entrenamiento: Optional[Dict[str, Any]]) -> str:
    """Genera un reporte completo en texto plano."""
    lineas: List[str] = []
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lineas.append("=" * 60)
    lineas.append("REPORTE ELECTROPREDICT")
    lineas.append(f"Generado: {ahora}")
    lineas.append("=" * 60)

    lineas.append("\n1. RESUMEN DE DATOS HISTORICOS")
    lineas.append("-" * 60)
    resumen_datos = resumen_datos_historicos(gestor)
    if resumen_datos.get("cantidad", 0) == 0:
        lineas.append("No hay registros historicos.")
    else:
        lineas.append(f"Cantidad de registros: {resumen_datos['cantidad']}")
        lineas.append(f"Consumo promedio: {resumen_datos['consumo_promedio']} kWh")
        lineas.append(f"Consumo minimo: {resumen_datos['consumo_minimo']} kWh")
        lineas.append(f"Consumo maximo: {resumen_datos['consumo_maximo']} kWh")
        lineas.append(f"Temperatura promedio: {resumen_datos['temperatura_promedio']} C")

    lineas.append("\n2. INFORMACION DEL ENTRENAMIENTO")
    lineas.append("-" * 60)
    if modelo is not None and modelo.entrenado:
        lineas.append(f"Algoritmo: {modelo.algoritmo_nombre} (scikit-learn)")
        lineas.append(f"Version del modelo: {modelo.version}")
        lineas.append(f"Imputacion de faltantes: {'activada' if modelo.imputar else 'desactivada'}")
        if info_entrenamiento:
            lineas.append(f"Registros usados: {info_entrenamiento.get('num_registros', '-')}")
            lineas.append(f"Registros de entrenamiento: {info_entrenamiento.get('registros_entrenamiento', '-')}")
            lineas.append(f"Registros de prueba: {info_entrenamiento.get('registros_prueba', '-')}")
        lineas.append(f"Ecuacion: {modelo.obtener_formula()}")
    else:
        lineas.append("El modelo no ha sido entrenado.")

    lineas.append("\n3. METRICAS DE EVALUACION")
    lineas.append("-" * 60)
    if metricas:
        lineas.append(f"R2:  {metricas.get('r2', 'N/D')}")
        lineas.append(f"MAE: {metricas.get('mae', 'N/D')} kWh")
        lineas.append(f"MSE: {metricas.get('mse', 'N/D')}")
        lineas.append(f"RMSE:{metricas.get('rmse', 'N/D')} kWh")
    else:
        lineas.append("No hay metricas calculadas.")

    lineas.append("\n4. HISTORIAL DE PREDICCIONES")
    lineas.append("-" * 60)
    resumen_pred = resumen_predicciones(gestor)
    if resumen_pred.get("cantidad", 0) == 0:
        lineas.append("No hay predicciones registradas.")
    else:
        lineas.append(f"Total de predicciones: {resumen_pred['cantidad']}")
        lineas.append(f"  Individuales: {resumen_pred['individuales']}")
        lineas.append(f"  Por lotes: {resumen_pred['lotes']}")
        lineas.append(f"  Con consumo real disponible: {resumen_pred['con_consumo_real']}")
        if "error_absoluto_promedio" in resumen_pred:
            lineas.append(f"Error absoluto promedio: {resumen_pred['error_absoluto_promedio']} kWh")
            lineas.append(f"Error absoluto maximo: {resumen_pred['error_absoluto_maximo']} kWh")

    lineas.append("\nNota: los errores se calculan solo cuando existe un consumo real")
    lineas.append("registrado despues de la prediccion.")
    lineas.append("=" * 60)
    return "\n".join(lineas)


def exportar_reporte_csv(gestor, ruta: str, tipo: str = "predicciones") -> bool:
    """Exporta un reporte tabular a CSV.

    Args:
        gestor: Gestor de datos.
        ruta: Ruta destino.
        tipo: 'predicciones' o 'historicos'.
    """
    try:
        if tipo == "predicciones":
            datos = gestor.predicciones()
            columnas = ["id", "fecha", "tipo", "lote", "temperatura", "personas",
                        "horas_uso", "consumo_anterior", "consumo_estimado",
                        "consumo_real", "error", "modelo"]
        else:
            datos = gestor.registros()
            columnas = ["id", "fecha_registro", "temperatura", "personas",
                        "horas_uso", "consumo_anterior", "consumo_real"]

        with open(ruta, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=columnas, extrasaction="ignore")
            writer.writeheader()
            for fila in datos:
                writer.writerow(fila)
        return True
    except OSError as e:
        logger.error(f"Error exportando reporte CSV: {e}")
        return False


def reportlab_disponible() -> bool:
    """Indica si reportlab esta instalado (necesario para PDF)."""
    return REPORTLAB_DISPONIBLE


def generar_reporte_pdf(
    gestor, modelo, metricas: Optional[Dict[str, float]],
    info_entrenamiento: Optional[Dict[str, Any]], ruta: str,
) -> bool:
    """Genera un reporte PDF con resumen, entrenamiento, metricas y predicciones.

    Returns:
        True si el PDF se genero correctamente; False si reportlab no esta
        disponible o hubo un error.
    """
    if not REPORTLAB_DISPONIBLE:
        logger.error("reportlab no esta instalado; no se puede generar PDF")
        return False

    try:
        doc = SimpleDocTemplate(
            ruta, pagesize=A4,
            leftMargin=2 * cm, rightMargin=2 * cm,
            topMargin=2 * cm, bottomMargin=2 * cm,
            title="Reporte ElectroPredict",
        )
        estilos = getSampleStyleSheet()
        estilo_titulo = ParagraphStyle(
            "TituloEP", parent=estilos["Title"], fontSize=20, spaceAfter=6)
        estilo_h = ParagraphStyle(
            "H2EP", parent=estilos["Heading2"], textColor=colors.HexColor("#2563eb"),
            spaceBefore=12, spaceAfter=6)
        estilo_normal = estilos["BodyText"]

        elementos: List[Any] = []
        elementos.append(Paragraph("ElectroPredict", estilo_titulo))
        elementos.append(Paragraph("Reporte de consumo electrico", estilo_normal))
        elementos.append(Paragraph(
            f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", estilo_normal))
        elementos.append(Spacer(1, 10))

        # 1. Datos historicos
        elementos.append(Paragraph("1. Resumen de datos historicos", estilo_h))
        rd = resumen_datos_historicos(gestor)
        if rd.get("cantidad", 0) == 0:
            elementos.append(Paragraph("No hay registros historicos.", estilo_normal))
        else:
            filas = [
                ["Metrica", "Valor"],
                ["Registros", str(rd["cantidad"])],
                ["Consumo promedio", f"{rd['consumo_promedio']} kWh"],
                ["Consumo minimo", f"{rd['consumo_minimo']} kWh"],
                ["Consumo maximo", f"{rd['consumo_maximo']} kWh"],
                ["Temperatura promedio", f"{rd['temperatura_promedio']} C"],
            ]
            elementos.append(_tabla_pdf(filas))

        # 2. Entrenamiento
        elementos.append(Paragraph("2. Informacion del entrenamiento", estilo_h))
        if modelo is not None and modelo.entrenado:
            info = info_entrenamiento or {}
            filas = [
                ["Campo", "Valor"],
                ["Algoritmo", modelo.algoritmo_nombre],
                ["Version del modelo", modelo.version],
                ["Imputacion", "activada" if modelo.imputar else "desactivada"],
                ["Registros usados", str(info.get("num_registros", "-"))],
                ["Registros de prueba", str(info.get("registros_prueba", "-"))],
            ]
            elementos.append(_tabla_pdf(filas))
            elementos.append(Spacer(1, 6))
            elementos.append(Paragraph(
                f"Ecuacion: {modelo.obtener_formula()}", estilo_normal))
        else:
            elementos.append(Paragraph("El modelo no ha sido entrenado.", estilo_normal))

        # 3. Metricas
        elementos.append(Paragraph("3. Metricas de evaluacion", estilo_h))
        if metricas:
            filas = [
                ["Metrica", "Valor"],
                ["R2", str(metricas.get("r2"))],
                ["MAE", f"{metricas.get('mae')} kWh"],
                ["MSE", str(metricas.get("mse"))],
                ["RMSE", f"{metricas.get('rmse')} kWh"],
            ]
            elementos.append(_tabla_pdf(filas))
        else:
            elementos.append(Paragraph("No hay metricas calculadas.", estilo_normal))

        # 4. Predicciones
        elementos.append(Paragraph("4. Historial de predicciones", estilo_h))
        rp = resumen_predicciones(gestor)
        if rp.get("cantidad", 0) == 0:
            elementos.append(Paragraph("No hay predicciones registradas.", estilo_normal))
        else:
            filas = [
                ["Concepto", "Valor"],
                ["Total de predicciones", str(rp["cantidad"])],
                ["Individuales", str(rp["individuales"])],
                ["Por lotes", str(rp["lotes"])],
                ["Con consumo real", str(rp["con_consumo_real"])],
            ]
            if "error_absoluto_promedio" in rp:
                filas.append(["Error absoluto promedio",
                              f"{rp['error_absoluto_promedio']} kWh"])
                filas.append(["Error absoluto maximo",
                              f"{rp['error_absoluto_maximo']} kWh"])
            elementos.append(_tabla_pdf(filas))

        elementos.append(Spacer(1, 12))
        elementos.append(Paragraph(
            "Nota: los errores se calculan solo cuando existe un consumo real "
            "registrado despues de la prediccion.", estilo_normal))

        doc.build(elementos)
        logger.info(f"Reporte PDF generado en {ruta}")
        return True

    except Exception as e:
        logger.error(f"Error generando PDF: {e}")
        return False


def _tabla_pdf(filas: List[List[str]]):
    """Construye una tabla de reportlab con estilo uniforme."""
    tabla = Table(filas, hAlign="LEFT", colWidths=[7 * cm, 8 * cm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f1f5f9")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return tabla
