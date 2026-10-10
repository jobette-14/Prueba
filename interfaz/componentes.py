"""Componentes reutilizables de la interfaz de ElectroPredict."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Tuple, Optional, Callable

from interfaz import tema


def limpiar_frame(frame: tk.Widget) -> None:
    """Elimina todos los widgets hijos de un frame."""
    for hijo in frame.winfo_children():
        hijo.destroy()


def crear_tarjeta(
    parent: tk.Widget,
    titulo: str,
    valor_inicial: str = "--",
    descripcion: str = "",
) -> Tuple[ttk.Frame, ttk.Label]:
    """Crea una tarjeta estadistica y devuelve (frame, label_del_valor)."""
    tarjeta = ttk.Frame(parent, style="Tarjeta.TFrame", padding=16)
    tarjeta.configure(borderwidth=1, relief="solid")

    lbl_titulo = ttk.Label(tarjeta, text=titulo.upper(), style="TarjetaTitulo.TLabel")
    lbl_titulo.pack(anchor="w")

    lbl_valor = ttk.Label(tarjeta, text=valor_inicial, style="TarjetaValor.TLabel")
    lbl_valor.pack(anchor="w", pady=(6, 0))

    if descripcion:
        lbl_desc = ttk.Label(tarjeta, text=descripcion, style="TarjetaTitulo.TLabel")
        lbl_desc.pack(anchor="w", pady=(2, 0))

    return tarjeta, lbl_valor


def crear_tabla(
    parent: tk.Widget,
    columnas: List[str],
    encabezados: Optional[List[str]] = None,
    anchos: Optional[List[int]] = None,
    altura: int = 12,
) -> Tuple[ttk.Frame, ttk.Treeview]:
    """Crea una tabla Treeview con scrollbar y devuelve (frame, treeview)."""
    frame = ttk.Frame(parent, style="TFrame")
    if encabezados is None:
        encabezados = columnas
    if anchos is None:
        anchos = [120] * len(columnas)

    tree = ttk.Treeview(frame, columns=columnas, show="headings", height=altura)
    for col, enc, ancho in zip(columnas, encabezados, anchos):
        tree.heading(col, text=enc)
        tree.column(col, width=ancho, anchor="center")

    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")

    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    return frame, tree


def llenar_tabla(tree: ttk.Treeview, filas: List[Tuple], formato: Optional[dict] = None) -> None:
    """Limpia y llena una tabla con filas."""
    for item in tree.get_children():
        tree.delete(item)

    for i, fila in enumerate(filas):
        valores = fila
        if formato:
            valores = tuple(formato.get(j, (lambda x: x))(v) for j, v in enumerate(fila))
        tree.insert("", "end", iid=str(i), values=valores)


def mostrar_mensaje(parent: tk.Widget, titulo: str, mensaje: str, tipo: str = "info") -> None:
    """Muestra un messagebox segun el tipo."""
    if tipo == "error":
        messagebox.showerror(titulo, mensaje, parent=parent)
    elif tipo == "warning":
        messagebox.showwarning(titulo, mensaje, parent=parent)
    elif tipo == "success":
        messagebox.showinfo(titulo, mensaje, parent=parent)
    else:
        messagebox.showinfo(titulo, mensaje, parent=parent)


def crear_formulario_campo(
    parent: tk.Widget,
    fila: int,
    etiqueta: str,
    ayuda: str = "",
) -> Tuple[ttk.Entry, ttk.Label]:
    """Crea una fila de formulario con etiqueta y entrada.

    Returns:
        (entry, label_error)
    """
    ttk.Label(parent, text=etiqueta, style="TLabel").grid(
        row=fila, column=0, sticky="w", padx=(0, 10), pady=6
    )
    entry = ttk.Entry(parent, width=28)
    entry.grid(row=fila, column=1, sticky="ew", pady=6)

    lbl_error = ttk.Label(parent, text="", style="Error.TLabel")
    lbl_error.grid(row=fila, column=2, sticky="w", padx=(10, 0), pady=6)
    return entry, lbl_error


class BarraEstado(ttk.Frame):
    """Barra inferior con estado del modelo y la base de datos."""

    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent, style="TFrame", padding=(12, 6))
        self._lbl_bd = ttk.Label(self, text="Base de datos: --", style="Suave.TLabel")
        self._lbl_bd.pack(side="left")

        self._lbl_modelo = ttk.Label(self, text="Modelo: no entrenado", style="Suave.TLabel")
        self._lbl_modelo.pack(side="right")

    def set_estado_bd(self, conectada: bool, bd_configurada: bool) -> None:
        if conectada:
            self._lbl_bd.configure(text="Base de datos: conectada", foreground=tema.COLOR_EXITO)
        elif bd_configurada:
            self._lbl_bd.configure(text="Base de datos: error de conexion",
                                   foreground=tema.COLOR_ERROR)
        else:
            self._lbl_bd.configure(text="Base de datos: no configurada (modo memoria)",
                                   foreground=tema.COLOR_ADVERTENCIA)

    def set_estado_modelo(self, entrenado: bool, r2: Optional[float] = None) -> None:
        if entrenado:
            extra = f" (R2={r2:.3f})" if r2 is not None else ""
            self._lbl_modelo.configure(text=f"Modelo: entrenado{extra}",
                                       foreground=tema.COLOR_EXITO)
        else:
            self._lbl_modelo.configure(text="Modelo: no entrenado",
                                       foreground=tema.COLOR_ADVERTENCIA)
