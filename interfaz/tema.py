"""Tema y estilos centralizados de ElectroPredict.

Define colores, tipografias y estilos ttk para mantener una apariencia
moderna y consistente en toda la aplicacion.
"""
import tkinter as tk
from tkinter import ttk


# --- Paleta de colores ---
COLOR_FONDO = "#f4f6fb"
COLOR_SIDEBAR = "#1f2a44"
COLOR_SIDEBAR_HOVER = "#2c3a5e"
COLOR_SIDEBAR_ACTIVO = "#3b82f6"
COLOR_PRIMARIO = "#2563eb"
COLOR_PRIMARIO_HOVER = "#1d4ed8"
COLOR_ENCABEZADO = "#ffffff"
COLOR_TARJETA = "#ffffff"
COLOR_TEXTO = "#1f2937"
COLOR_TEXTO_CLARO = "#ffffff"
COLOR_TEXTO_SUAVE = "#6b7280"
COLOR_BORDE = "#e5e7eb"
COLOR_EXITO = "#16a34a"
COLOR_ERROR = "#dc2626"
COLOR_ADVERTENCIA = "#d97706"
COLOR_INFO = "#2563eb"

# --- Tipografias ---
FUENTE_TITULO = ("Segoe UI", 20, "bold")
FUENTE_SUBTITULO = ("Segoe UI", 14, "bold")
FUENTE_ENCABEZADO = ("Segoe UI", 12, "bold")
FUENTE_NORMAL = ("Segoe UI", 10)
FUENTE_PEQUENA = ("Segoe UI", 9)
FUENTE_MENU = ("Segoe UI", 11)
FUENTE_MENU_ACTIVO = ("Segoe UI", 11, "bold")
FUENTE_VALOR_TARJETA = ("Segoe UI", 22, "bold")


class Tema:
    """Aplica y expone el tema visual de la aplicacion."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root

    def aplicar(self) -> None:
        """Configura los estilos ttk globales."""
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        self.root.configure(bg=COLOR_FONDO)

        # Frames
        style.configure("TFrame", background=COLOR_FONDO)
        style.configure("Tarjeta.TFrame", background=COLOR_TARJETA, relief="flat")
        style.configure("Sidebar.TFrame", background=COLOR_SIDEBAR)
        style.configure("Encabezado.TFrame", background=COLOR_ENCABEZADO)

        # Labels
        style.configure("TLabel", background=COLOR_FONDO, foreground=COLOR_TEXTO,
                        font=FUENTE_NORMAL)
        style.configure("Titulo.TLabel", background=COLOR_FONDO, foreground=COLOR_TEXTO,
                        font=FUENTE_TITULO)
        style.configure("Subtitulo.TLabel", background=COLOR_FONDO, foreground=COLOR_TEXTO,
                        font=FUENTE_SUBTITULO)
        style.configure("Encabezado.TLabel", background=COLOR_ENCABEZADO,
                        foreground=COLOR_TEXTO, font=FUENTE_TITULO)
        style.configure("TarjetaTitulo.TLabel", background=COLOR_TARJETA,
                        foreground=COLOR_TEXTO_SUAVE, font=FUENTE_PEQUENA)
        style.configure("TarjetaValor.TLabel", background=COLOR_TARJETA,
                        foreground=COLOR_TEXTO, font=FUENTE_VALOR_TARJETA)
        style.configure("Tarjeta.TLabel", background=COLOR_TARJETA,
                        foreground=COLOR_TEXTO, font=FUENTE_NORMAL)
        style.configure("Suave.TLabel", background=COLOR_FONDO,
                        foreground=COLOR_TEXTO_SUAVE, font=FUENTE_PEQUENA)
        style.configure("Exito.TLabel", background=COLOR_FONDO,
                        foreground=COLOR_EXITO, font=FUENTE_NORMAL)
        style.configure("Error.TLabel", background=COLOR_FONDO,
                        foreground=COLOR_ERROR, font=FUENTE_NORMAL)

        # Botones
        style.configure("TButton", font=FUENTE_NORMAL, padding=6)
        style.configure("Primario.TButton", font=FUENTE_ENCABEZADO, padding=(14, 8),
                        background=COLOR_PRIMARIO, foreground=COLOR_TEXTO_CLARO,
                        borderwidth=0)
        style.map("Primario.TButton",
                  background=[("active", COLOR_PRIMARIO_HOVER), ("disabled", "#9ca3af")],
                  foreground=[("disabled", "#f3f4f6")])
        style.configure("Secundario.TButton", font=FUENTE_NORMAL, padding=(12, 7))

        # Entry y Combobox
        style.configure("TEntry", padding=4, font=FUENTE_NORMAL)
        style.configure("TCombobox", padding=4, font=FUENTE_NORMAL)

        # Treeview
        style.configure("Treeview", font=FUENTE_NORMAL, rowheight=26,
                        background=COLOR_TARJETA, fieldbackground=COLOR_TARJETA)
        style.configure("Treeview.Heading", font=FUENTE_ENCABEZADO, padding=6,
                        background="#e8edf7", foreground=COLOR_TEXTO)
        style.map("Treeview", background=[("selected", COLOR_PRIMARIO)],
                  foreground=[("selected", COLOR_TEXTO_CLARO)])

        # Notebook
        style.configure("TNotebook", background=COLOR_FONDO, borderwidth=0)
        style.configure("TNotebook.Tab", font=FUENTE_NORMAL, padding=(12, 6))
