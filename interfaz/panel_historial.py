"""Panel de Historial de predicciones de ElectroPredict."""

import logging
import tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime

from interfaz.componentes import crear_tabla, llenar_tabla
from interfaz import tema
from datos.carga_csv import exportar_a_csv
from datos.validaciones import validar_consumo

logger = logging.getLogger(__name__)


class PanelHistorial(ttk.Frame):
    """Historial de predicciones realizadas (individuales y por lotes)."""

    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, style="TFrame")
        self.app = app
        self._construir()
        self.refrescar()

    def _construir(self) -> None:
        ttk.Label(
            self, style="TLabel", wraplength=860, justify="left",
            text=("Historial de predicciones generadas por el modelo. Aqui puede registrar "
                  "el consumo real observado despues de una prediccion para calcular el error. "
                  "Las mediciones reales se administran en 'Datos historicos'."),
        ).pack(anchor="w", pady=(0, 12))

        filtros = ttk.Frame(self, style="TFrame")
        filtros.pack(fill="x", pady=(0, 10))

        ttk.Label(filtros, text="Desde (AAAA-MM-DD):", style="TLabel").pack(side="left")
        self._desde = ttk.Entry(filtros, width=14)
        self._desde.pack(side="left", padx=(6, 12))
        ttk.Label(filtros, text="Hasta:", style="TLabel").pack(side="left")
        self._hasta = ttk.Entry(filtros, width=14)
        self._hasta.pack(side="left", padx=(6, 12))

        ttk.Button(filtros, text="Filtrar", command=self._aplicar_filtro).pack(side="left")
        ttk.Button(filtros, text="Limpiar", command=self._limpiar_filtro).pack(side="left", padx=6)

        ttk.Button(filtros, text="Registrar consumo real",
                   command=self._registrar_real).pack(side="right")
        ttk.Button(filtros, text="Exportar", command=self._exportar).pack(side="right", padx=8)

        self._lbl_resumen = ttk.Label(self, text="", style="Suave.TLabel")
        self._lbl_resumen.pack(anchor="w", pady=(0, 8))

        columnas = ["id", "fecha", "tipo", "lote", "temperatura", "personas",
                    "horas_uso", "consumo_anterior", "consumo_estimado",
                    "consumo_real", "error", "modelo"]
        encabezados = ["ID", "Fecha", "Tipo", "Lote", "Temp", "Pers", "Horas",
                       "Cons. ant.", "Estimado", "Real", "Error", "Modelo"]
        anchos = [40, 130, 70, 70, 55, 45, 55, 75, 80, 75, 70, 70]

        self._tabla_frame, self._tabla = crear_tabla(self, columnas, encabezados, anchos, altura=16)
        self._tabla_frame.pack(fill="both", expand=True)

        self._registros_mostrados = []

    def refrescar(self) -> None:
        self._aplicar_filtro()

    def _filtrar(self):
        predicciones = self.app.gestor.predicciones()
        desde = self._desde.get().strip()
        hasta = self._hasta.get().strip()

        resultado = []
        for p in predicciones:
            fecha = str(p.get("fecha", ""))
            dia = fecha[:10]
            if desde and dia < desde:
                continue
            if hasta and dia > hasta:
                continue
            resultado.append(p)
        return resultado

    def _aplicar_filtro(self) -> None:
        filas = self._filtrar()
        self._registros_mostrados = filas
        datos = []
        for p in filas:
            datos.append((
                p["id"], p.get("fecha", ""), p.get("tipo", ""), p.get("lote") or "-",
                f"{p['temperatura']:.1f}", p["personas"], f"{p['horas_uso']:.1f}",
                f"{p['consumo_anterior']:.2f}", f"{p['consumo_estimado']:.2f}",
                f"{p['consumo_real']:.2f}" if p.get("consumo_real") is not None else "--",
                f"{p['error']:.2f}" if p.get("error") is not None else "--",
                p.get("modelo", ""),
            ))
        llenar_tabla(self._tabla, datos)
        self._lbl_resumen.configure(text=f"Predicciones mostradas: {len(datos)}")

    def _limpiar_filtro(self) -> None:
        self._desde.delete(0, "end")
        self._hasta.delete(0, "end")
        self._aplicar_filtro()

    def _registrar_real(self) -> None:
        seleccion = self._tabla.selection()
        if not seleccion:
            self.app.mostrar_mensaje("Seleccione una fila",
                                     "Seleccione una prediccion de la tabla.", "warning")
            return
        indice = int(seleccion[0])
        if indice >= len(self._registros_mostrados):
            return
        prediccion = self._registros_mostrados[indice]

        dialogo = tk.Toplevel(self.app.root)
        dialogo.title("Registrar consumo real")
        dialogo.geometry("360x190")
        dialogo.transient(self.app.root)
        dialogo.grab_set()

        ttk.Label(dialogo, text=f"Prediccion #{prediccion['id']}",
                  style="Subtitulo.TLabel").pack(anchor="w", padx=20, pady=(16, 4))
        ttk.Label(dialogo, text=f"Consumo estimado: {prediccion['consumo_estimado']:.2f} kWh",
                  style="TLabel").pack(anchor="w", padx=20)
        ttk.Label(dialogo, text="Consumo real observado (kWh):", style="TLabel").pack(
            anchor="w", padx=20, pady=(12, 4))
        entrada = ttk.Entry(dialogo, width=18)
        entrada.pack(anchor="w", padx=20)
        lbl_error = ttk.Label(dialogo, text="", style="Error.TLabel")
        lbl_error.pack(anchor="w", padx=20)

        def guardar():
            valor, err = validar_consumo(entrada.get())
            if err:
                lbl_error.configure(text=err)
                return
            self.app.gestor.registrar_consumo_real(prediccion["id"], valor)
            dialogo.destroy()
            self._aplicar_filtro()
            self.app.actualizar_todo()
            self.app.mostrar_mensaje(
                "Consumo registrado",
                f"Error calculado: {valor - prediccion['consumo_estimado']:.2f} kWh", "success")

        botones = ttk.Frame(dialogo, style="TFrame")
        botones.pack(fill="x", padx=20, pady=14)
        ttk.Button(botones, text="Guardar", style="Primario.TButton",
                   command=guardar).pack(side="right")
        ttk.Button(botones, text="Cancelar", command=dialogo.destroy).pack(side="right", padx=8)

    def _exportar(self) -> None:
        if not self._registros_mostrados:
            self.app.mostrar_mensaje("Sin datos", "No hay predicciones para exportar.", "warning")
            return
        ruta = filedialog.asksaveasfilename(
            title="Exportar historial", defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")])
        if not ruta:
            return
        columnas = ["id", "fecha", "tipo", "lote", "temperatura", "personas",
                    "horas_uso", "consumo_anterior", "consumo_estimado",
                    "consumo_real", "error", "modelo"]
        datos = [{k: p.get(k) for k in columnas} for p in self._registros_mostrados]
        if exportar_a_csv(datos, ruta, columnas=columnas):
            self.app.mostrar_mensaje("Exportacion exitosa", f"Historial exportado a:\n{ruta}",
                                     "success")
        else:
            self.app.mostrar_mensaje("Error", "No se pudo exportar.", "error")
