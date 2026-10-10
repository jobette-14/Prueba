"""Panel de Reportes de ElectroPredict."""

import logging
import tkinter as tk
from tkinter import ttk, filedialog

from interfaz import tema
from reportes.generador import (
    generar_reporte_texto, exportar_reporte_csv, generar_reporte_pdf,
    reportlab_disponible,
)

logger = logging.getLogger(__name__)


class PanelReportes(ttk.Frame):
    """Generacion y exportacion de reportes de la aplicacion."""

    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, style="TFrame")
        self.app = app
        self._construir()
        self.refrescar()

    def _construir(self) -> None:
        barra = ttk.Frame(self, style="TFrame")
        barra.pack(fill="x", pady=(0, 10))

        ttk.Button(barra, text="Generar reporte", style="Primario.TButton",
                   command=self._generar).pack(side="left")
        ttk.Button(barra, text="Guardar reporte (TXT)",
                   command=self._guardar_txt).pack(side="left", padx=8)
        self._btn_pdf = ttk.Button(barra, text="Guardar reporte (PDF)",
                                   command=self._guardar_pdf)
        self._btn_pdf.pack(side="left", padx=8)
        if not reportlab_disponible():
            self._btn_pdf.configure(state="disabled")
        ttk.Button(barra, text="Exportar historial de predicciones (CSV)",
                   command=lambda: self._exportar_csv("predicciones")).pack(side="left", padx=8)
        ttk.Button(barra, text="Exportar datos historicos (CSV)",
                   command=lambda: self._exportar_csv("historicos")).pack(side="left", padx=8)

        contenedor = ttk.Frame(self, style="TFrame")
        contenedor.pack(fill="both", expand=True)

        self._texto = tk.Text(contenedor, wrap="word", font=("Consolas", 10),
                              bg="#ffffff", fg=tema.COLOR_TEXTO, relief="solid", bd=1)
        scroll = ttk.Scrollbar(contenedor, orient="vertical", command=self._texto.yview)
        self._texto.configure(yscrollcommand=scroll.set)
        self._texto.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def refrescar(self) -> None:
        self._generar()

    def _generar(self) -> None:
        reporte = generar_reporte_texto(
            self.app.gestor, self.app.modelo,
            self.app.metricas, self.app.info_entrenamiento,
        )
        self._texto.configure(state="normal")
        self._texto.delete("1.0", "end")
        self._texto.insert("1.0", reporte)
        self._texto.configure(state="disabled")

    def _guardar_txt(self) -> None:
        ruta = filedialog.asksaveasfilename(
            title="Guardar reporte", defaultextension=".txt",
            filetypes=[("Archivo de texto", "*.txt")])
        if not ruta:
            return
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(self._texto.get("1.0", "end"))
            self.app.mostrar_mensaje("Reporte guardado", f"Guardado en:\n{ruta}", "success")
        except OSError as e:
            self.app.mostrar_mensaje("Error", f"No se pudo guardar: {e}", "error")

    def _guardar_pdf(self) -> None:
        if not reportlab_disponible():
            self.app.mostrar_mensaje(
                "PDF no disponible",
                "Falta la libreria 'reportlab'. Instalela con:\n pip install reportlab",
                "warning")
            return
        ruta = filedialog.asksaveasfilename(
            title="Guardar reporte PDF", defaultextension=".pdf",
            filetypes=[("Documento PDF", "*.pdf")], parent=self.app.root)
        if not ruta:
            return
        ok = generar_reporte_pdf(
            self.app.gestor, self.app.modelo,
            self.app.metricas, self.app.info_entrenamiento, ruta)
        if ok:
            self.app.mostrar_mensaje("Reporte PDF guardado", f"Guardado en:\n{ruta}", "success")
        else:
            self.app.mostrar_mensaje("Error", "No se pudo generar el PDF.", "error")

    def _exportar_csv(self, tipo: str) -> None:
        if tipo == "predicciones" and self.app.gestor.cantidad_predicciones() == 0:
            self.app.mostrar_mensaje("Sin datos", "No hay predicciones para exportar.", "warning")
            return
        if tipo == "historicos" and self.app.gestor.cantidad_registros() == 0:
            self.app.mostrar_mensaje("Sin datos", "No hay datos historicos para exportar.", "warning")
            return

        ruta = filedialog.asksaveasfilename(
            title="Exportar reporte", defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")])
        if not ruta:
            return
        if exportar_reporte_csv(self.app.gestor, ruta, tipo):
            self.app.mostrar_mensaje("Exportacion exitosa", f"Archivo guardado en:\n{ruta}", "success")
        else:
            self.app.mostrar_mensaje("Error", "No se pudo exportar el reporte.", "error")
