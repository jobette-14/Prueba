"""Panel de Entrenamiento del modelo de ElectroPredict."""

import logging
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog

from interfaz.componentes import limpiar_frame, crear_tarjeta
from modelo.entrenamiento import ALGORITMOS, comparar_algoritmos
from modelo.persistencia import (
    guardar_modelo, cargar_modelo, listar_modelos, directorio_modelos,
)

logger = logging.getLogger(__name__)

# Mapa nombre legible -> clave interna
_NOMBRE_A_CLAVE = {nombre: clave for clave, nombre in ALGORITMOS.items()}


class PanelEntrenamiento(ttk.Frame):
    """Seccion para entrenar el modelo de regresion de consumo electrico."""

    def __init__(self, parent: tk.Widget, app) -> None:
        super().__init__(parent, style="TFrame")
        self.app = app
        self._construir()
        self.refrescar()

    def _construir(self) -> None:
        ttk.Label(
            self, style="TLabel", wraplength=860, justify="left",
            text=(
                "El modelo estima el consumo real (kWh) a partir de cuatro variables de "
                "entrada: temperatura, personas, horas de uso y consumo anterior. Puede "
                "elegir el algoritmo. Los datos se dividen en entrenamiento y prueba para "
                "evaluar con datos no vistos. La imputacion, si se activa, rellena valores "
                "faltantes con la media calculada SOLO del conjunto de entrenamiento."
            ),
        ).pack(anchor="w", pady=(0, 14))

        controles = ttk.Frame(self, style="TFrame")
        controles.pack(fill="x", pady=(0, 8))

        ttk.Label(controles, text="Algoritmo:", style="TLabel").pack(side="left")
        self._algoritmo = tk.StringVar(value=ALGORITMOS["lineal"])
        self._combo_algo = ttk.Combobox(
            controles, textvariable=self._algoritmo, state="readonly", width=26,
            values=list(ALGORITMOS.values()))
        self._combo_algo.pack(side="left", padx=(6, 16))

        ttk.Label(controles, text="Proporcion de prueba:", style="TLabel").pack(side="left")
        self._test_size = tk.DoubleVar(value=20)
        ttk.Spinbox(controles, from_=10, to=40, increment=5, width=5,
                    textvariable=self._test_size).pack(side="left", padx=(6, 4))
        ttk.Label(controles, text="%", style="TLabel").pack(side="left", padx=(0, 16))

        self._imputar = tk.BooleanVar(value=False)
        ttk.Checkbutton(controles, text="Imputar faltantes",
                        variable=self._imputar).pack(side="left", padx=(0, 16))

        self._lbl_disponibles = ttk.Label(controles, text="", style="Suave.TLabel")
        self._lbl_disponibles.pack(side="right")

        botones = ttk.Frame(self, style="TFrame")
        botones.pack(fill="x", pady=(0, 14))

        self._btn_entrenar = ttk.Button(
            botones, text="Entrenar modelo", style="Primario.TButton",
            command=self._entrenar)
        self._btn_entrenar.pack(side="left")

        ttk.Button(botones, text="Comparar algoritmos",
                   command=self._comparar).pack(side="left", padx=(8, 0))

        self._btn_guardar = ttk.Button(
            botones, text="Guardar modelo (.pkl)", command=self._guardar,
            state="disabled")
        self._btn_guardar.pack(side="left", padx=(8, 0))

        ttk.Button(botones, text="Cargar modelo (.pkl)",
                   command=self._cargar).pack(side="left", padx=(8, 0))

        self._resultado = ttk.Frame(self, style="TFrame")
        self._resultado.pack(fill="both", expand=True)

    def refrescar(self) -> None:
        disponibles = self.app.gestor.cantidad_registros()
        self._lbl_disponibles.configure(
            text=f"Registros disponibles: {disponibles} (minimo 3)")
        self._btn_guardar.configure(
            state="normal" if self.app.modelo.entrenado else "disabled")
        self._mostrar_resultados()

    # ------------------------------------------------------------------
    def _entrenar(self) -> None:
        datos = self.app.gestor.datos_para_entrenamiento()
        if len(datos) < 3:
            self.app.mostrar_mensaje(
                "Datos insuficientes",
                "Se requieren al menos 3 registros historicos validos para entrenar.\n"
                f"Actualmente hay {len(datos)}.",
                "warning",
            )
            return

        algoritmo = _NOMBRE_A_CLAVE.get(self._algoritmo.get(), "lineal")
        imputar = bool(self._imputar.get())
        self.app.crear_modelo(algoritmo=algoritmo, imputar=imputar)

        X, y = self.app.modelo.preparar_datos(datos)
        if X is None or y is None:
            self.app.mostrar_mensaje(
                "Datos invalidos",
                "Algunos registros no cumplen con los rangos validos. Revise los datos "
                "o active la imputacion de faltantes.",
                "error",
            )
            return

        test_size = max(0.1, min(0.4, self._test_size.get() / 100.0))
        resultado = self.app.modelo.entrenar(X, y, test_size=test_size)

        if not resultado.get("exitoso"):
            self.app.mostrar_mensaje("Error de entrenamiento",
                                     resultado.get("error", "Error desconocido"), "error")
            return

        self.app.registrar_entrenamiento(resultado)
        self._mostrar_resultados()
        self.app.actualizar_todo()
        self.app.mostrar_mensaje(
            "Entrenamiento completado",
            f"El modelo '{self.app.modelo.algoritmo_nombre}' se entreno correctamente. "
            "Ya puede realizar predicciones.",
            "success",
        )

    def _comparar(self) -> None:
        datos = self.app.gestor.datos_para_entrenamiento()
        if len(datos) < 3:
            self.app.mostrar_mensaje(
                "Datos insuficientes",
                "Se requieren al menos 3 registros para comparar algoritmos.", "warning")
            return

        test_size = max(0.1, min(0.4, self._test_size.get() / 100.0))
        resultados = comparar_algoritmos(
            datos, test_size=test_size, imputar=bool(self._imputar.get()))
        _VentanaComparacion(self.app.root, resultados)

    def _guardar(self) -> None:
        if not self.app.modelo.entrenado:
            self.app.mostrar_mensaje("Sin modelo", "Entrene un modelo antes de guardarlo.",
                                     "warning")
            return
        nombre = simpledialog.askstring(
            "Guardar modelo",
            "Nombre del archivo (opcional; se agrega version y fecha):",
            parent=self.app.root)
        if nombre is None:
            return
        ruta = guardar_modelo(self.app.modelo, nombre=nombre.strip() or None)
        if ruta:
            self.app.mostrar_mensaje(
                "Modelo guardado", f"El modelo se guardo en:\n{ruta}", "success")
        else:
            self.app.mostrar_mensaje("Error", "No se pudo guardar el modelo.", "error")

    def _cargar(self) -> None:
        disponibles = listar_modelos()
        ruta = filedialog.askopenfilename(
            title="Cargar modelo entrenado",
            initialdir=str(directorio_modelos()),
            filetypes=[("Modelo ElectroPredict", "*.pkl"), ("Todos", "*.*")],
            parent=self.app.root)
        if not ruta:
            if not disponibles:
                self.app.mostrar_mensaje(
                    "Sin modelos", "No hay modelos guardados todavia.", "info")
            return
        modelo = cargar_modelo(ruta)
        if modelo is None:
            self.app.mostrar_mensaje(
                "Error al cargar",
                "El archivo no contiene un modelo valido de ElectroPredict.", "error")
            return
        self.app.cargar_modelo_en_app(modelo)
        self._algoritmo.set(modelo.algoritmo_nombre)
        self._imputar.set(modelo.imputar)
        self._mostrar_resultados()
        self.app.actualizar_todo()
        self.app.mostrar_mensaje(
            "Modelo cargado",
            f"Se cargo el modelo '{modelo.algoritmo_nombre}' desde disco.", "success")

    # ------------------------------------------------------------------
    def _mostrar_resultados(self) -> None:
        limpiar_frame(self._resultado)

        if not self.app.modelo.entrenado:
            ttk.Label(self._resultado, style="Suave.TLabel",
                      text="El modelo aun no ha sido entrenado.").pack(anchor="w")
            return

        info = self.app.info_entrenamiento or {}
        metricas = self.app.metricas or {}
        coeficientes = info.get("coeficientes", {})

        encabezado = ttk.Label(
            self._resultado, style="Subtitulo.TLabel",
            text=(f"Modelo actual: {self.app.modelo.algoritmo_nombre}  |  "
                  f"Imputacion: {'activada' if self.app.modelo.imputar else 'desactivada'}"))
        encabezado.pack(anchor="w", pady=(0, 8))

        tarjetas = ttk.Frame(self._resultado, style="TFrame")
        tarjetas.pack(fill="x", pady=(0, 14))
        definiciones = [
            ("R2 (coef. determinacion)", metricas.get("r2")),
            ("MAE (error abs. medio)", metricas.get("mae")),
            ("MSE (error cuadratico)", metricas.get("mse")),
            ("RMSE (raiz error cuad.)", metricas.get("rmse")),
        ]
        for i, (titulo, valor) in enumerate(definiciones):
            texto = f"{valor:.4f}" if valor is not None else "--"
            tarjeta, lbl = crear_tarjeta(tarjetas, titulo, texto)
            tarjeta.grid(row=0, column=i, sticky="nsew",
                         padx=(0 if i == 0 else 8, 0), pady=4)
            tarjetas.columnconfigure(i, weight=1)

        detalle = ttk.Frame(self._resultado, style="TFrame")
        detalle.pack(fill="both", expand=True)

        ttk.Label(detalle, text="Ecuacion del modelo", style="Subtitulo.TLabel").pack(
            anchor="w", pady=(6, 4))
        ttk.Label(detalle, text=self.app.modelo.obtener_formula(), style="TLabel",
                  wraplength=860, justify="left").pack(anchor="w")

        ttk.Label(detalle, text="Coeficientes aprendidos", style="Subtitulo.TLabel").pack(
            anchor="w", pady=(14, 4))
        if coeficientes:
            inter = info.get("intercepto")
            texto_coef = f"b0 (intercepto) = {inter:.4f}\n" if inter is not None else ""
            for nombre, valor in coeficientes.items():
                texto_coef += f"{nombre} = {valor:.4f}\n"
        else:
            texto_coef = ("Este algoritmo no expone coeficientes lineales "
                          "(los arboles no son interpretables de forma directa).")
        ttk.Label(detalle, text=texto_coef, style="TLabel",
                  justify="left").pack(anchor="w")

        ttk.Label(
            detalle, style="Suave.TLabel", wraplength=860, justify="left",
            text=(
                "\nInterpretacion: R2 indica la proporcion de la varianza del consumo real "
                "explicada por el modelo (1.0 = ajuste perfecto; valores negativos indican "
                "un ajuste peor que la media). MAE y RMSE estan en kWh."
            ),
        ).pack(anchor="w", pady=(10, 0))


class _VentanaComparacion(tk.Toplevel):
    """Ventana con la comparacion de metricas entre algoritmos."""

    def __init__(self, parent: tk.Widget, resultados) -> None:
        super().__init__(parent)
        self.title("Comparacion de algoritmos")
        self.geometry("640x260")
        self.transient(parent)

        ttk.Label(
            self, style="Subtitulo.TLabel",
            text="Comparacion de algoritmos con los mismos datos").pack(
            anchor="w", padx=16, pady=(14, 8))

        columnas = ("algoritmo", "r2", "mae", "rmse")
        tabla = ttk.Treeview(self, columns=columnas, show="headings", height=4)
        for col, texto, ancho in (
                ("algoritmo", "Algoritmo", 240), ("r2", "R2", 110),
                ("mae", "MAE (kWh)", 110), ("rmse", "RMSE (kWh)", 110)):
            tabla.heading(col, text=texto)
            tabla.column(col, width=ancho, anchor="center")
        tabla.pack(fill="both", expand=True, padx=16)

        for r in resultados:
            m = r.get("metricas") or {}
            if r.get("exitoso") and m:
                tabla.insert("", "end", values=(
                    r["nombre"], f"{m.get('r2', 0):.4f}",
                    f"{m.get('mae', 0):.4f}", f"{m.get('rmse', 0):.4f}"))
            else:
                tabla.insert("", "end", values=(r["nombre"], "N/D", "N/D", "N/D"))

        ttk.Label(
            self, style="Suave.TLabel", wraplength=600,
            text="R2 mas alto y MAE/RMSE mas bajos indican mejor ajuste. "
                 "Compare y elija el algoritmo mas conveniente.").pack(
            anchor="w", padx=16, pady=(8, 4))

        ttk.Button(self, text="Cerrar", command=self.destroy).pack(pady=(0, 14))
