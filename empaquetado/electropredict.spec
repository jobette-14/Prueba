# -*- mode: python ; coding: utf-8 -*-
"""Especificacion de PyInstaller para ElectroPredict (aplicacion de escritorio).

Genera un unico ejecutable ElectroPredict.exe que incluye Python y todas las
dependencias, de modo que el usuario NO necesita instalar Python manualmente.

Compilar con:
    python -m PyInstaller --clean --noconfirm empaquetado/electropredict.spec
(o ejecutar empaquetado/build_exe.ps1)
"""

import os

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))

a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    binaries=[],
    datas=[
        (os.path.join(ROOT, "ejemplos"), "ejemplos"),
        (os.path.join(ROOT, "README.md"), "."),
    ],
    hiddenimports=[
        "matplotlib.backends.backend_tkagg",
        "psycopg2",
        "sklearn.utils._typedefs",
        "sklearn.utils._heap",
        "sklearn.utils._sorting",
        "sklearn.utils._vector_sentinel",
    ],
    hookspath=[],
    runtime_hooks=[],
    # La version de escritorio no incluye la web ni sus dependencias.
    excludes=[
        "web", "fastapi", "uvicorn", "starlette", "slowapi", "httpx",
        "pydantic", "reportlab", "tests",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="ElectroPredict",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # aplicacion grafica (Tkinter), sin consola
    disable_windowed_traceback=False,
    version=os.path.join(SPECPATH, "version_info.txt"),
)
