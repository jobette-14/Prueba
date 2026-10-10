"""Panel de Prediccion por lotes de ElectroPredict."""

import logging
import tkinter as tk
from tkinter import ttk, filedialog

from datos.carga_csv import leer_csv_prediccion, exportar_a_csv
from modelo.prediccion import predecir_lotes
from interfaz.componentes import crear_tabla, llenar_tabla, limpiar_frame
from interfaz import tema

logger = logging.getLogger(__name__)


class PanelLotes(ttk.Frame):
    """Prediccion de multiples filas desde un archivo CSV."""

    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, style="TFrame")
        self.app = app
        self._resultados = None
        self._ruta = None
        self._construir()
        self.refrescar()

    def _construir(self) -> None:
        ttk.Label(
            self, style="TLabel", wraplength=860, justify="left",
            text=("Cargue un CSV con las columnas: temperatura, personas, horas_uso, "
                  "consumo_anterior. La columna consumo_real es opcional y solo se usa "
                  "para comparar, nunca como entrada del modelo."),
        ).pack(anchor="w", pady=(0, 12))

        barra = ttk.Frame(self, style="TFrame")
        barra.pack(fill="x", pady=(0, 10))

        ttk.Button(barra, text="Cargar CSV", style="Primario.TButton",
                   command=self._cargar).pack(side="left")
        self._btn_predecir = ttk.Button(barra, text="Predecir lote",
                                        command=self._predecir, state="disabled")
        self._btn_predecir.pack(side="left", padx=8)
        self._btn_exportar = ttk.Button(barra, text="Exportar resultados",
                                        command=self._exportar, state="disabled")
        self._btn_exportar.pack(side="left", padx=8)
        self._btn_guardar = ttk.Button(barra, text="Guardar en historial",
                                       command=self._guardar, state="disabled")
        self._btn_guardar.pack(side="left", padx=8)

        self._lbl_archivo = ttk.Label(self, text="Ningun archivo cargado", style="Suave.TLabel")
        self._lbl_archivo.pack(anchor="w", pady=(0, 8))

        self._lbl_resumen = ttk.Label(self, text="", style="TLabel")
        self._lbl_resumen.pack(anchor="w", pady=(0, 8))

        columnas = ["fila", "temperatura", "personas", "horas_uso",
                    "consumo_anterior", "consumo_estimado", "consumo_real", "error"]
        encabezados = ["Fila", "Temp (C)", "Personas", "Horas",
                       "Consumo ant.", "Estimado (kWh)", "Real (kWh)", "Error (kWh)"]
        anchos = [50, 80, 80, 70, 100, 120, 100, 100]
        self._tabla_frame, self._tabla = crear_tabla(self, columnas, encabezados, anchos, altura=14)
        self._tabla_frame.pack(fill="both", expand=True)

    def refrescar(self) -> None:
        if self.app.modelo.entrenado:
            self._lbl_resumen.configure(text="Modelo listo. Cargue un CSV para predecir.",
                                        foreground=tema.COLOR_EXITO)
        else:
            self._lbl_resumen.configure(
                text="El modelo no esta entrenado. Entrene antes de predecir por lotes.",
                foreground=tema.COLOR_ADVERTENCIA)

    def _cargar(self) -> None:
        ruta = filedialog.askopenfilename(
            title="Seleccionar CSV para prediccion por lotes",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos", "*.*")],
        )
        if not ruta:
            return

        datos, resumen = leer_csv_prediccion(ruta)
        if resumen.get("errores"):
            mensajes = "\n".join(e.get("mensaje", "") for e in resumen["errores"])
            self.app.mostrar_mensaje("Columnas invalidas", mensajes, "error")
            return
        if not datos:
            self.app.mostrar_mensaje("Sin datos validos",
                                     "El archivo no contiene filas validas.", "warning")
            return

        self._ruta = ruta
        self._lbl_archivo.configure(
            text=f"Archivo: {ruta}  |  Filas validas: {len(datos)}  |  "
                 f"Invalidas: {resumen['invalidos']}  |  "
                 f"Consumo real incluido: {'si' if resumen.get('tiene_consumo_real') else 'no'}")
        self._btn_predecir.configure(state="normal")
        self._resultados = None
        self._btn_exportar.configure(state="disabled")
        self._btn_guardar.configure(state="disabled")

    def _predecir(self) -> None:
        if not self.app.modelo.entrenado:
            self.app.mostrar_mensaje("Sin modelo",
                                     "Debe entrenar el modelo antes de predecir.", "warning")
            return
        if not self._ruta:
            return

        resultados, resumen = predecir_lotes(self.app.modelo, self._ruta)
        if resultados is None:
            self.app.mostrar_mensaje("Error", resumen or "No se pudo procesar el lote.", "error")
            return

        self._resultados = resultados
        self._lote_id = f"lote-{self.app.gestor.cantidad_predicciones() + 1}"

        filas = []
        for r in resultados:
            filas.append((
                r.get("fila"), r.get("temperatura"), r.get("personas"),
                r.get("horas_uso"), r.get("consumo_anterior"),
                f"{r['consumo_estimado']:.2f}" if r.get("consumo_estimado") is not None else "--",
                f"{r['consumo_real']:.2f}" if r.get("consumo_real") is not None else "--",
                f"{r['error']:.2f}" if r.get("error") is not None else "--",
            ))
        llenar_tabla(self._tabla, filas)

        self._lbl_resumen.configure(text=resumen, foreground=tema.COLOR_TEXTO)
        self._btn_exportar.configure(state="normal")
        self._btn_guardar.configure(state="normal")

    def _exportar(self) -> None:
        if not self._resultados:
            return
        ruta = filedialog.asksaveasfilename(
            title="Exportar resultados del lote",
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")],
        )
        if not ruta:
            return
        columnas = ["fila", "temperatura", "personas", "horas_uso",
                    "consumo_anterior", "consumo_estimado", "consumo_real", "error", "modelo"]
        if exportar_a_csv([{k: r.get(k) for k in columnas} for r in self._resultados], ruta,
                          columnas=columnas):
            self.app.mostrar_mensaje("Exportacion exitosa",
                                     f"Resultados exportados a:\n{ruta}", "success")
        else:
            self.app.mostrar_mensaje("Error", "No se pudo exportar.", "error")

    def _guardar(self) -> None:
        if not self._resultados:
            return
        guardados = 0
        for r in self._resultados:
            if r.get("consumo_estimado") is None:
                continue
            self.app.gestor.agregar_prediccion(
                r["temperatura"], r["personas"], r["horas_uso"], r["consumo_anterior"],
                r["consumo_estimado"], modelo=f"v{self.app.modelo.version}",
                tipo="lote", lote=getattr(self, "_lote_id", None),
                consumo_real=r.get("consumo_real"),
            )
            guardados += 1
        self.app.actualizar_todo()
        self.app.mostrar_mensaje("Lote guardado",
                                 f"Se guardaron {guardados} predicciones en el historial.", "success")
