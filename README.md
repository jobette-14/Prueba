# ElectroPredict — Predictor de Consumo Eléctrico

Aplicación para predecir consumo eléctrico a partir de datos históricos,
entrenando un modelo de **regresión lineal múltiple** con Scikit-learn.

El proyecto ofrece **dos modalidades que comparten la misma lógica de cálculo**:

- **Aplicación de escritorio (Windows)** — interfaz Tkinter, distribuida como
  instalador `.exe` (se puede descargar e instalar sin Python).
- **Versión web** — API **FastAPI** + frontend **React/Vite**, accesible desde el
  navegador y desplegable en la nube.

> Este README documenta la implementación **real** del proyecto. Al final se
> indican con honestidad las funcionalidades pendientes y las limitaciones.

**Documentación detallada:** [API](docs/API.md) ·
[Despliegue](docs/DESPLIEGUE.md) · [Instalación](docs/INSTALACION.md) ·
[Mantenimiento](docs/MANTENIMIENTO.md).

---

## 1. Descripción del proyecto

ElectroPredict es una aplicación de escritorio con interfaz gráfica (Tkinter/`ttk`)
que permite:

- Importar y registrar datos históricos de consumo eléctrico.
- Entrenar un modelo de regresión lineal múltiple.
- Evaluar el modelo con métricas estadísticas (R², MAE, MSE, RMSE).
- Realizar predicciones individuales y por lotes.
- Visualizar los resultados con gráficas de Matplotlib.
- Consultar el historial de predicciones y registrar consumos reales posteriores.
- Generar y exportar reportes.
- Persistir la información en PostgreSQL (Neon) de forma opcional.

La aplicación es **funcional sin base de datos**: en ese caso los datos viven
en memoria durante la sesión. Al configurar `DATABASE_URL`, los datos se
persisten en PostgreSQL.

---

## 2. Objetivo general y específicos

**Objetivo general:** construir un sistema de escritorio funcional que permita
predecir el consumo eléctrico mediante aprendizaje automático supervisado y
gestionar toda la información asociada.

**Objetivos específicos:**

1. Gestionar datos históricos (CSV y registro manual) con validación.
2. Entrenar un modelo de regresión lineal múltiple reproducible.
3. Evaluar el modelo con datos no usados en el entrenamiento.
4. Predecir consumos individuales y por lotes.
5. Visualizar resultados con gráficas basadas en datos reales.
6. Mantener un historial consultable de predicciones y mediciones.
7. Generar reportes exportables.
8. Integrar PostgreSQL/Neon con configuración por variables de entorno.
9. Aplicar buenas prácticas de seguridad y validación.

---

## 3. Funcionalidades

| Sección | Función | Estado |
|---|---|---|
| Dashboard | Tarjetas estadísticas y gráficas resumidas | Implementado |
| Datos históricos | Importar CSV, registro manual, exportar CSV | Implementado |
| Entrenamiento | Entrenar (Lineal, Ridge, Random Forest), comparar algoritmos, imputación opcional | Implementado |
| Predicción individual | Formulario de 4 variables y botón *Predecir consumo* | Implementado |
| Predicción por lotes | Importar CSV, predecir, exportar, guardar | Implementado |
| Historial | Consultar, filtrar, registrar consumo real, exportar | Implementado |
| Evaluación | 7 gráficas estadísticas | Implementado |
| Reportes | Reporte en TXT, **PDF** y exportación CSV | Implementado |
| Configuración | Conexión a Neon, probar conexión, inicializar tablas | Implementado |
| Persistencia en disco del modelo | Guardar/cargar `.pkl` con metadatos JSON | Implementado |
| Versión web | API REST + SPA React con las mismas funciones | Implementado |
| Instalador de escritorio | `.exe` (PyInstaller) + instalador (Inno Setup) | Implementado |

---

## 4. Arquitectura y estructura real

```text
ElectroPredict/
├── main.py                      # Punto de entrada
├── interfaz/
│   ├── ventana_principal.py     # Ventana, menú lateral, navegación
│   ├── tema.py                  # Colores y estilos centralizados
│   ├── componentes.py           # Tarjetas, tablas, formularios, mensajes
│   ├── panel_inicio.py          # Dashboard
│   ├── panel_datos.py           # Datos históricos
│   ├── panel_entrenamiento.py   # Entrenamiento
│   ├── panel_prediccion.py      # Predicción individual
│   ├── panel_lotes.py           # Predicción por lotes
│   ├── panel_historial.py       # Historial
│   ├── panel_evaluacion.py      # Evaluación con gráficas
│   ├── panel_reportes.py        # Reportes
│   └── panel_configuracion.py   # Configuración de BD
├── modelo/
│   ├── entrenamiento.py         # Regresión lineal múltiple
│   ├── prediccion.py            # Predicción individual y por lotes
│   └── evaluacion.py            # Métricas R², MAE, MSE, RMSE
├── datos/
│   ├── carga_csv.py             # Lectura/validación/exportación CSV
│   ├── validaciones.py          # Validación de campos y rangos
│   └── gestor.py                # Estado en memoria + persistencia
├── base_datos/
│   ├── conexion.py              # Conexión psycopg2 + SSL (Neon)
│   └── repositorio.py           # Consultas parametrizadas y esquema
├── graficas/
│   └── visualizaciones.py       # Figuras de Matplotlib
├── reportes/
│   └── generador.py             # Reportes de texto/CSV
├── web/
│   ├── api/                     # API FastAPI (reutiliza el núcleo)
│   │   ├── config.py            # Configuración por variables de entorno
│   │   ├── estado.py            # Servicio compartido (modelo + datos + BD)
│   │   ├── seguridad.py         # X-API-Key + límite de peticiones
│   │   ├── schemas.py           # Esquemas Pydantic (rangos idénticos)
│   │   ├── routers/             # Endpoints REST
│   │   └── main.py              # App + sirve el frontend compilado
│   └── frontend/                # SPA React/Vite (Dashboard, Predicción, …)
├── empaquetado/
│   ├── electropredict.spec      # PyInstaller (.exe)
│   ├── build_exe.ps1            # Compila el .exe
│   └── instalador.iss           # Inno Setup (instalador Windows)
├── docs/                        # API, DESPLIEGUE, INSTALACION, MANTENIMIENTO
├── .github/workflows/           # CI (pruebas) + build de Windows
├── ejemplos/
│   ├── datos_ejemplo.csv        # Datos históricos de ejemplo
│   └── lote_ejemplo.csv         # Entradas para predicción por lotes
├── tests/                       # Pruebas con pytest (núcleo + API)
├── Dockerfile / render.yaml / fly.toml   # Despliegue web
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

La interfaz, la lógica del modelo, el acceso a PostgreSQL y las visualizaciones
están **separadas por responsabilidades**. El **núcleo** (`modelo/`, `datos/`,
`base_datos/`) es compartido por el escritorio y la web; **no se duplica lógica
de predicción**.

---

## 5. Tecnologías utilizadas

- **Python 3** (probado con 3.14).
- **Tkinter / ttk** — interfaz gráfica de escritorio.
- **NumPy** — operaciones numéricas.
- **Scikit-learn** — `LinearRegression`, `Ridge`, `RandomForestRegressor`, `SimpleImputer`, métricas y división de datos.
- **Matplotlib** — visualizaciones integradas en Tkinter.
- **psycopg2-binary** — conexión a PostgreSQL/Neon.
- **joblib** — persistencia del modelo en disco (`.pkl`).
- **reportlab** — generación de reportes en PDF.
- **python-dotenv** — carga de variables de entorno desde `.env`.
- **pytest** — pruebas automatizadas.

Versión web:

- **FastAPI** + **Uvicorn** — API REST (reutiliza el mismo núcleo).
- **Pydantic** — validación de datos de entrada.
- **slowapi** — límite de peticiones (rate limiting).
- **httpx** — cliente para el chat de IA opcional.
- **React + Vite** — frontend SPA (Node.js).
- **Docker** — empaquetado y despliegue.

Empaquetado de escritorio: **PyInstaller** (`.exe`) e **Inno Setup** (instalador).

---

## 6. Explicación de la regresión lineal múltiple

El modelo estima el consumo eléctrico como una combinación lineal de cuatro
variables de entrada:

```text
consumo_estimado =
    b0
    + b1 * temperatura
    + b2 * personas
    + b3 * horas_uso
    + b4 * consumo_anterior
```

Los coeficientes `b0..b4` los **aprende** Scikit-learn durante el entrenamiento
(no están fijados en el código). El modelo se entrena con `LinearRegression` de
`sklearn.linear_model`. Los datos se dividen en entrenamiento y prueba con
`train_test_split(..., random_state=42)` para que la evaluación sea reproducible
y sin fuga de información.

### Algoritmos disponibles

Puede elegir el algoritmo desde la sección *Entrenamiento* y compararlos con el
botón **Comparar algoritmos** (mismos datos, mismas métricas):

| Clave | Algoritmo | Notas |
|---|---|---|
| `lineal` | Regresión Lineal Múltiple | Expone coeficientes e intercepto |
| `ridge` | Regresión Ridge (L2) | Regularización, útil con colinealidad |
| `random_forest` | Random Forest | No lineal; no expone coeficientes |

### Imputación de valores faltantes

Si se activa **Imputar faltantes**, las entradas vacías o inválidas se rellenan
con la **media**, y el imputador (`SimpleImputer`) se ajusta **únicamente con el
conjunto de entrenamiento**; luego se aplica al conjunto de prueba y a las
predicciones. Así se evita la fuga de información. El objetivo (`consumo_real`)
nunca se imputa: las filas sin objetivo se descartan.

### Persistencia del modelo

El modelo entrenado puede guardarse y cargarse desde *Entrenamiento*:

- **Guardar modelo (.pkl)**: usa `joblib` y crea además un `.json` con
  metadatos (versión, algoritmo, imputación, métricas y fecha). Los archivos se
  guardan en `modelos/` (excluido de Git).
- **Cargar modelo (.pkl)**: valida que el archivo contenga un modelo de
  ElectroPredict entrenado antes de usarlo.

---

## 7. Variables del modelo

| Variable | Nombre lógico | Unidad | Rol |
|---|---|---|---|
| Temperatura | `temperatura` | °C | Entrada |
| Cantidad de personas | `personas` | Personas | Entrada |
| Horas de uso | `horas_uso` | Horas | Entrada |
| Consumo anterior | `consumo_anterior` | kWh | Entrada |
| Consumo real | `consumo_real` | kWh | Objetivo |

Las cuatro primeras son las entradas; `consumo_real` es la variable objetivo.

**Rangos de validación (documentados en `datos/validaciones.py`):**

| Variable | Rango | Justificación |
|---|---|---|
| Temperatura | −50 °C a 60 °C | Rango ambiental razonable |
| Personas | 1 a 50 | Ocupantes de una vivienda |
| Horas de uso | 0 a 24 | No puede exceder un día |
| Consumo anterior | 0 a 1000 kWh | Consumo doméstico plausible |
| Consumo real | 0 a 1000 kWh | Consumo doméstico plausible |

---

## 8. Formato del CSV

### Datos históricos (entrenamiento)

Cabecera obligatoria:

```csv
temperatura,personas,horas_uso,consumo_anterior,consumo_real
25,3,6,10.5,22.3
30,5,8,12.1,28.7
20,2,4,8.0,15.2
```

### Predicción por lotes

La columna `consumo_real` es **opcional**. Si está presente, se usa únicamente
para comparar con la predicción, nunca como entrada del modelo.

```csv
temperatura,personas,horas_uso,consumo_anterior
29,4,6,10.2
31,5,8,12.1
28,3,5,9.4
```

Se incluyen archivos de ejemplo en `ejemplos/`.

---

## 9. Configuración de PostgreSQL y Neon

1. Cree una cuenta y un proyecto en [Neon](https://neon.tech).
2. Copie la cadena de conexión (incluye `sslmode=require`).
3. Defina la variable de entorno `DATABASE_URL` (ver sección 12).
4. En la aplicación, abra **Configuración** y pulse *Aplicar y conectar*.
   También puede inicializar el esquema con *Inicializar tablas*.

La conexión usa **psycopg2** con un contexto SSL creado con
`ssl.create_default_context()`, como requiere Neon.

### Tablas creadas

La aplicación crea el esquema de forma **controlada** (no elimina tablas):

- **`registros_historicos`**: `id`, `temperatura`, `personas`, `horas_uso`,
  `consumo_anterior`, `consumo_real`, `fecha_registro`, `fecha_creacion`.
- **`entrenamientos`**: `id`, `fecha_training`, `algoritmo`, `num_registros`,
  `r2_score`, `mae`, `mse`, `rmse`, `version`, `estado`.
- **`predicciones`**: `id`, `fecha_prediccion`, `temperatura`, `personas`,
  `horas_uso`, `consumo_anterior`, `consumo_estimado`, `modelo`,
  `lote_identificador`, `consumo_real_posterior`, `error_calculado`.

Todas las consultas son **parametrizadas** (`%s`).

---

## 10. Instalación y dependencias

Compatible con Windows. Desde la carpeta del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`requirements.txt`:

```text
numpy
pandas
scikit-learn
psycopg2-binary
matplotlib
python-dotenv
joblib
reportlab
pytest
```

> `tkinter` viene incluido con la instalación estándar de Python en Windows.
> `pandas` se declara como dependencia, aunque el núcleo actual usa NumPy de
> forma directa; puede retirarse si no se necesita.

---

## 11. Configuración del entorno virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Para desactivar: `deactivate`.

---

## 12. Variables de entorno

Copie `.env.example` a `.env` y complete la URL:

```env
DATABASE_URL=postgresql://usuario:password@ep-xxxx.neon.tech/neondb?sslmode=require
```

- `.env` está excluido de Git (ver `.gitignore`).
- `.env.example` no contiene secretos.
- Nunca escriba credenciales directamente en el código.

---

## 13. Inicialización de la base de datos

Opción A — desde la aplicación: **Configuración → Inicializar tablas**.

Opción B — automática: al iniciar, si `DATABASE_URL` está configurada, la
aplicación intenta conectar e inicializar el esquema en segundo plano.

---

## 14. Ejecución de la aplicación

### 14.1 Escritorio

```powershell
python main.py
```

Se abre la ventana principal. Si no hay `DATABASE_URL`, aparecerá
"Base de datos: no configurada (modo memoria)".

**Instalador de Windows:** `powershell -ExecutionPolicy Bypass -File empaquetado\build_exe.ps1`
genera `dist\ElectroPredict.exe`; luego `ISCC.exe empaquetado\instalador.iss`
crea el instalador. El `.exe` **no requiere Python instalado**. Ver
[INSTALACION.md](docs/INSTALACION.md).

### 14.2 Web

```powershell
# Backend
pip install -r requirements.txt -r web/requirements.txt
python -m uvicorn web.api.main:app --reload --port 8000
```

```powershell
# Frontend (otra terminal)
cd web\frontend
npm install
npm run dev        # http://localhost:5173, proxy /api -> 8000
```

En producción compila el frontend (`npm run build`) y sirve todo con FastAPI
(`http://localhost:8000`), o usa Docker: `docker build -t electropredict .`.
Documentación de la API en `/api/docs`. Ver [DESPLIEGUE.md](docs/DESPLIEGUE.md).

---

## 15. Uso de las funciones

1. **Datos históricos** → *Importar CSV* (ejemplo: `ejemplos/datos_ejemplo.csv`)
   o *Registrar manualmente*.
2. **Entrenamiento** → ajuste la proporción de prueba y pulse *Entrenar modelo*.
3. **Predicción individual** → complete las 4 variables y pulse *Predecir consumo*.
4. **Predicción por lotes** → *Cargar CSV* (ejemplo: `ejemplos/lote_ejemplo.csv`),
   luego *Predecir lote*.
5. **Historial** → consulte, filtre por fecha y registre consumo real.
6. **Evaluación** → revise las 7 gráficas.
7. **Reportes** → genere y exporte el reporte.

---

## 16. Entrenamiento y evaluación

- Se requieren **al menos 3 registros válidos**.
- División entrenamiento/prueba configurable (10 %–40 %, por defecto 20 %).
- Métricas calculadas con los datos de prueba:
  - **R²**: proporción de varianza explicada (puede ser negativo; **no** es un
    porcentaje de precisión garantizado).
  - **MAE**: error absoluto medio (kWh).
  - **MSE**: error cuadrático medio.
  - **RMSE**: raíz del error cuadrático medio (kWh).

---

## 17. Predicciones individuales y por lotes

- **Individual:** formulario con las 4 variables; resultado con el formato
  `Consumo estimado: XX.XX kWh`. Permite guardar la predicción en el historial y,
  opcionalmente, registrar el consumo real para calcular el error.
- **Por lotes:** procesa todas las filas válidas de un CSV, muestra una tabla de
  resultados, resumen de filas procesadas/rechazadas y permite exportar a CSV o
  guardar en el historial identificando el lote y el modelo.

---

## 18. Gráficas y reportes

Gráficas (Matplotlib integrado en Tkinter), solo cuando hay datos suficientes:

1. Consumo real vs predicho.
2. Dispersión de valores reales y predichos.
3. Errores de predicción.
4. Distribución de errores.
5. Evolución del consumo histórico.
6. Historial de predicciones.
7. Resultados por lotes.

Fórmulas usadas:

```text
Error = Consumo real − Consumo predicho
Error absoluto = |Consumo real − Consumo predicho|
```

No se calculan errores cuando no se conoce el consumo real.

Reportes: texto completo (exportable a **TXT** o **PDF**) y exportación tabular a
**CSV**. El PDF se genera con `reportlab` incluyendo resumen de datos,
entrenamiento, métricas e historial de predicciones.

---

## 19. Pruebas

```powershell
python -m pytest tests -v
```

Resultado actual verificado: **119 pruebas, 119 passed**.

Cubren el **núcleo**: validaciones, carga/exportación CSV, entrenamiento (incluida
la recuperación de coeficientes), los tres algoritmos (Lineal, Ridge, Random
Forest), la comparación entre algoritmos, la imputación ajustada solo con datos
de entrenamiento, la persistencia del modelo (guardar/cargar/listar), la
generación de reportes TXT/CSV/PDF, predicción individual y por lotes, cálculo de
métricas, gestor de datos (con repositorio simulado), conexión segura y consultas
parametrizadas. Y la **API web** (`tests/test_api.py`): salud, config pública,
predicción, lotes, registros, historial, reportes, protección con `X-API-Key` y
`tests/test_consistencia_web.py`, que verifica que web y escritorio producen
**las mismas predicciones y métricas**.

**Las pruebas no requieren una cuenta real de Neon ni conexión externa**: usan
dobles/mocks y un repositorio en memoria. La carpeta `tests/` incluye
`conftest.py` con datos deterministas.

---

## 20. Validaciones

Se validan: campos vacíos, valores no numéricos, valores infinitos/indefinidos,
cantidades negativas, horas fuera de rango, fechas, archivos inexistentes o
vacíos, columnas incorrectas, datos insuficientes para entrenar y ausencia de
modelo. Los rangos permitidos están justificados en la sección 7.

---

## 21. Limitaciones

- La conexión a Neon **no se pudo probar contra una cuenta real** en el entorno de
  desarrollo (no había credenciales). Las pruebas de base de datos usan mocks;
  la prueba de integración real queda como opcional/manual.
- Los modelos guardados usan `pickle` (vía `joblib`): no cargue archivos `.pkl`
  de procedencia desconocida (la aplicación valida el tipo del objeto cargado).
- El instalador `.exe` se compila correctamente; **generar el `Setup.exe` final
  requiere Inno Setup** (no instalado en el entorno de desarrollo, sin permisos
  de administrador). Puede generarse con `ISCC.exe` o vía el workflow de GitHub
  Actions (`Build Windows`).
- Para la modalidad web, el **chat de IA es opcional** y queda desactivado si no
  se configura `CHAT_API_KEY`.
- La aplicación de escritorio es monousuario.

---

## 22. Mejoras futuras

- Sincronización y autenticación multiusuario.
- Exportación de gráficas a imagen.
- Ajuste de hiperparámetros y validación cruzada.
- Registro histórico de métricas por versión de modelo.

---

## 23. Autor

Proyecto **ElectroPredict** — desarrollado como aplicación de escritorio de
predicción de consumo eléctrico con aprendizaje automático.

---

## 24. Licencia

Uso educativo. Puede adaptarse libremente indicando la fuente original.
