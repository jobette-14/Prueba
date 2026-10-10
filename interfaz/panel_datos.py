"""Panel de Datos historicos de ElectroPredict.

Permite importar CSV, registrar datos manualmente y exportar el historico.
"""

import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Dict, Any

from interfaz import tema
from interfaz.componentes import crear_tabla, llenar_tabla, limpiar_frame
from datos.carga_csv import leer_csv, exportar_a_csv, detectar_duplicados
from datos.validaciones import (
    validar_temperatura, validar_personas, validar_horas_uso,
    validar_consumo, validar_consumo_anterior,
)

logger = logging.getLogger(__name__)


class PanelDatos(ttk.Frame):
    """Gestion de registros historicos (mediciones reales)."""

    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, style="TFrame")
        self.app = app
        self._construir()
        self.refrescar()

    def _construir(self) -> None:
        barra = ttk.Frame(self, style="TFrame")
        barra.pack(fill="x", pady=(0, 12))

        ttk.Button(barra, text="Importar CSV", style="Primario.TButton",
                   command=self._importar_csv).pack(side="left")
        ttk.Button(barra, text="Registrar manualmente",
                   command=self._abrir_registro_manual).pack(side="left", padx=8)
        ttk.Button(barra, text="Exportar CSV",
                   command=self._exportar_csv).pack(side="left", padx=8)

        self._lbl_resumen = ttk.Label(barra, text="", style="Suave.TLabel")
        self._lbl_resumen.pack(side="right")

        columnas = ["id", "fecha", "temperatura", "personas", "horas_uso",
                    "consumo_anterior", "consumo_real"]
        encabezados = ["ID", "Fecha", "Temp (C)", "Personas", "Horas",
                       "Consumo ant. (kWh)", "Consumo real (kWh)"]
        anchos = [50, 140, 90, 80, 80, 140, 140]

        self._tabla_frame, self._tabla = crear_tabla(self, columnas, encabezados, anchos, altura=16)
        self._tabla_frame.pack(fill="both", expand=True)

        ttk.Label(
            self, style="Suave.TLabel",
            text="Los datos historicos contienen el consumo real medido (variable objetivo)."
        ).pack(anchor="w", pady=(8, 0))

    def refrescar(self) -> None:
        registros = self.app.gestor.registros()
        filas = []
        for r in registros:
            filas.append((
                r["id"], r.get("fecha_registro", ""),
                f"{r['temperatura']:.1f}", r["personas"], f"{r['horas_uso']:.1f}",
                f"{r['consumo_anterior']:.2f}", f"{r['consumo_real']:.2f}",
            ))
        llenar_tabla(self._tabla, filas)
        self._lbl_resumen.configure(text=f"Total: {len(registros)} registros")

    # ------------------------------------------------------------------
    # Importacion CSV
    # ------------------------------------------------------------------
    def _importar_csv(self) -> None:
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo CSV",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos", "*.*")],
        )
        if not ruta:
            return

        try:
            datos, resumen = leer_csv(ruta)
        except Exception as e:
            self.app.mostrar_mensaje("Error de importacion",
                                     f"No se pudo leer el archivo:\n{e}", "error")
            return

        if resumen.get("errores"):
            mensajes = "\n".join(e.get("mensaje", "") for e in resumen["errores"])
            self.app.mostrar_mensaje("Columnas invalidas", mensajes, "error")
            return

        if not datos:
            self.app.mostrar_mensaje("Sin datos",
                                     "El archivo no contiene filas validas.", "warning")
            return

        duplicados = detectar_duplicados(datos)
        confirmado = self._dialogo_preview(datos, resumen, duplicados)
        if not confirmado:
            return

        cantidad = self.app.gestor.agregar_registros_masivo(datos)
        self.refrescar()
        self.app.actualizar_todo()
        self.app.mostrar_mensaje(
            "Importacion completada",
            f"Se importaron {cantidad} registros validos.\n"
            f"Se rechazaron {resumen['invalidos']} filas invalidas.",
            "success",
        )

    def _dialogo_preview(self, datos, resumen, duplicados) -> bool:
        dialogo = tk.Toplevel(self.app.root)
        dialogo.title("Vista previa de importacion")
        dialogo.geometry("720x540")
        dialogo.transient(self.app.root)
        dialogo.grab_set()

        ttk.Label(dialogo, text="Vista previa de datos a importar",
                  style="Subtitulo.TLabel").pack(anchor="w", padx=16, pady=(16, 4))

        info = (
            f"Filas totales: {resumen['total']}    "
            f"Validas: {resumen['validos']}    "
            f"Invalidas: {resumen['invalidos']}    "
            f"Duplicados detectados: {len(duplicados)}"
        )
        ttk.Label(dialogo, text=info, style="TLabel").pack(anchor="w", padx=16)

        contenedor = ttk.Frame(dialogo, style="TFrame")
        contenedor.pack(fill="both", expand=True, padx=16, pady=10)

        columnas = ["temperatura", "personas", "horas_uso", "consumo_anterior", "consumo_real"]
        frame_tabla, tabla = crear_tabla(contenedor, columnas, altura=8)
        frame_tabla.pack(fill="both", expand=True)
        for i, d in enumerate(datos[:50]):
            tabla.insert("", "end", values=(
                f"{d['temperatura']:.1f}", d["personas"], f"{d['horas_uso']:.1f}",
                f"{d['consumo_anterior']:.2f}", f"{d['consumo_real']:.2f}",
            ))
        if len(datos) > 50:
            ttk.Label(contenedor, text=f"... y {len(datos) - 50} filas mas",
                      style="Suave.TLabel").pack(anchor="w")

        if resumen.get("filas_invalidas"):
            ttk.Label(dialogo, text="Filas invalidas (no se importaran):",
                      style="Error.TLabel").pack(anchor="w", padx=16)
            texto = tk.Text(dialogo, height=4, font=tema.FUENTE_PEQUENA)
            texto.pack(fill="x", padx=16, pady=(0, 6))
            for f in resumen["filas_invalidas"][:20]:
                texto.insert("end", f"  Fila {f['fila']}: {'; '.join(f['errores'])}\n")
            texto.configure(state="disabled")

        resultado = {"ok": False}
        botones = ttk.Frame(dialogo, style="TFrame")
        botones.pack(fill="x", padx=16, pady=12)

        def confirmar():
            resultado["ok"] = True
            dialogo.destroy()

        ttk.Button(botones, text="Confirmar importacion", style="Primario.TButton",
                   command=confirmar).pack(side="right")
        ttk.Button(botones, text="Cancelar", command=dialogo.destroy).pack(side="right", padx=8)

        self.app.root.wait_window(dialogo)
        return resultado["ok"]

    # ------------------------------------------------------------------
    # Registro manual
    # ------------------------------------------------------------------
    def _abrir_registro_manual(self) -> None:
        dialogo = tk.Toplevel(self.app.root)
        dialogo.title("Registrar medicion historica")
        dialogo.geometry("420x400")
        dialogo.transient(self.app.root)
        dialogo.grab_set()

        ttk.Label(dialogo, text="Nueva medicion real", style="Subtitulo.TLabel").pack(
            anchor="w", padx=20, pady=(18, 10))

        formulario = ttk.Frame(dialogo, style="TFrame")
        formulario.pack(fill="x", padx=20)
        formulario.columnconfigure(1, weight=1)

        campos = {}
        definiciones = [
            ("temperatura", "Temperatura (C):", "-50 a 60"),
            ("personas", "Cantidad de personas:", "1 a 50"),
            ("horas_uso", "Horas de uso:", "0 a 24"),
            ("consumo_anterior", "Consumo anterior (kWh):", "0 a 1000"),
            ("consumo_real", "Consumo real (kWh):", "0 a 1000"),
        ]
        for i, (clave, etiqueta, ayuda) in enumerate(definiciones):
            ttk.Label(formulario, text=etiqueta, style="TLabel").grid(
                row=i, column=0, sticky="w", pady=6)
            entry = ttk.Entry(formulario, width=18)
            entry.grid(row=i, column=1, sticky="ew", padx=(10, 6), pady=6)
            ttk.Label(formulario, text=ayuda, style="Suave.TLabel").grid(
                row=i, column=2, sticky="w", pady=6)
            campos[clave] = entry

        lbl_error = ttk.Label(dialogo, text="", style="Error.TLabel", wraplength=360)
        lbl_error.pack(anchor="w", padx=20, pady=(6, 0))

        def guardar():
            valores = {}
            validadores = {
                "temperatura": validar_temperatura,
                "personas": validar_personas,
                "horas_uso": validar_horas_uso,
                "consumo_anterior": validar_consumo_anterior,
                "consumo_real": validar_consumo,
            }
            for clave, entry in campos.items():
                val, err = validadores[clave](entry.get())
                if err:
                    lbl_error.configure(text=err)
                    return
                valores[clave] = val

            self.app.gestor.agregar_registro(
                valores["temperatura"], valores["personas"], valores["horas_uso"],
                valores["consumo_anterior"], valores["consumo_real"],
            )
            dialogo.destroy()
            self.refrescar()
            self.app.actualizar_todo()
            self.app.mostrar_mensaje("Registro guardado",
                                     "La medicion se ha registrado correctamente.", "success")

        botones = ttk.Frame(dialogo, style="TFrame")
        botones.pack(fill="x", padx=20, pady=16)
        ttk.Button(botones, text="Guardar", style="Primario.TButton",
                   command=guardar).pack(side="right")
        ttk.Button(botones, text="Cancelar", command=dialogo.destroy).pack(side="right", padx=8)

    # ------------------------------------------------------------------
    def _exportar_csv(self) -> None:
        registros = self.app.gestor.registros()
        if not registros:
            self.app.mostrar_mensaje("Sin datos", "No hay registros para exportar.", "warning")
            return

        ruta = filedialog.asksaveasfilename(
            title="Exportar datos historicos",
            defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")],
        )
        if not ruta:
            return

        datos = [{
            "temperatura": r["temperatura"], "personas": r["personas"],
            "horas_uso": r["horas_uso"], "consumo_anterior": r["consumo_anterior"],
            "consumo_real": r["consumo_real"], "fecha_registro": r.get("fecha_registro", ""),
        } for r in registros]

        if exportar_a_csv(datos, ruta):
            self.app.mostrar_mensaje("Exportacion exitosa",
                                     f"Se exportaron {len(datos)} registros a:\n{ruta}", "success")
        else:
            self.app.mostrar_mensaje("Error", "No se pudo exportar el archivo.", "error")
