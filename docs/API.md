# API de ElectroPredict

API REST (FastAPI) que expone **la misma logica de prediccion** que la
aplicacion de escritorio. Documentacion interactiva:

- Swagger UI: `/api/docs`
- ReDoc: `/api/redoc`
- OpenAPI JSON: `/api/openapi.json`

## Autenticacion

Las rutas de **escritura** (entrenar, registrar, importar, consumo real) se
protegen con una cabecera `X-API-Key` si la variable `ELECTROPREDICT_API_KEY`
esta definida:

```
X-API-Key: <tu-clave>
```

Si `ELECTROPREDICT_API_KEY` esta vacia (solo desarrollo), las rutas quedan
abiertas. Las rutas de **lectura** y prediccion no requieren clave.

## Limites de uso

Se aplica un limite por IP (`RATE_LIMIT`, por defecto `120/minute`). Al
excederlo se devuelve **429**.

## Codigos de estado

| Codigo | Significado |
|--------|-------------|
| 200 | OK |
| 422 | Datos de entrada invalidos (fuera de rango o formato incorrecto) |
| 401/403 | Falta `X-API-Key` o es incorrecta |
| 429 | Demasiadas solicitudes |
| 500 | Error interno (no se filtran detalles) |

## Endpoints

### Sistema

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/api/salud` | Estado del servicio (version, modelo entrenado, BD conectada) |
| GET | `/api/config-publica` | Configuracion no sensible (rangos, chat disponible) |

### Modelo

| Metodo | Ruta | Auth | Descripcion |
|--------|------|------|-------------|
| GET | `/api/modelo` | No | Estado e informacion del modelo actual |
| POST | `/api/modelo/entrenar` | Si | Entrena con los datos historicos |
| POST | `/api/modelo/comparar` | Si | Compara `lineal`, `ridge`, `random_forest` |

Cuerpo de `/entrenar` y `/comparar`:

```json
{ "algoritmo": "lineal", "imputar": false, "test_size": 0.2 }
```

### Prediccion

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | `/api/prediccion` | Prediccion individual |
| POST | `/api/prediccion/lotes` | Lotes desde archivo CSV (multipart) |
| POST | `/api/prediccion/lotes/json` | Lotes desde filas JSON |

Cuerpo de `/prediccion`:

```json
{
  "temperatura": 28.5,
  "personas": 4,
  "horas_uso": 6.5,
  "consumo_anterior": 210.0,
  "consumo_real": 218.0
}
```

Respuesta:

```json
{
  "exitoso": true,
  "consumo_estimado": 216.4,
  "consumo_real": 218.0,
  "error": -1.6,
  "error_absoluto": 1.6,
  "algoritmo": "lineal",
  "version": "1.1.0"
}
```

### Datos e historial

| Metodo | Ruta | Auth | Descripcion |
|--------|------|------|-------------|
| GET | `/api/registros` | No | Lista registros historicos |
| POST | `/api/registros` | Si | Registra un dato historico |
| POST | `/api/registros/importar` | Si | Importa registros desde CSV (multipart) |
| GET | `/api/estadisticas` | No | Estadisticas para el panel principal |
| GET | `/api/historial` | No | Historial de predicciones |
| POST | `/api/historial/consumo-real` | Si | Asocia el consumo real a una prediccion |

### Reportes

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/api/reportes/txt` | Reporte completo en texto |
| GET | `/api/reportes/csv` | Reporte tabular en CSV |
| GET | `/api/reportes/pdf` | Reporte en PDF |

### Chat IA (opcional)

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | `/api/chat` | Asistente de IA (desactivado si no hay `CHAT_API_KEY`) |

## Rangos validos (identicos al escritorio)

| Variable | Min | Max |
|----------|-----|-----|
| temperatura | -50 | 60 |
| personas | 1 | 50 |
| horas_uso | 0 | 24 |
| consumo_anterior | 0 | 1000 |
| consumo_real | 0 | 1000 |

## Ejemplos con curl

```bash
# Salud
curl http://localhost:8000/api/salud

# Prediccion
curl -X POST http://localhost:8000/api/prediccion \
  -H "Content-Type: application/json" \
  -d "{\"temperatura\":28.5,\"personas\":4,\"horas_uso\":6.5,\"consumo_anterior\":210}"

# Entrenar (protegido)
curl -X POST http://localhost:8000/api/modelo/entrenar \
  -H "Content-Type: application/json" \
  -H "X-API-Key: TU_CLAVE" \
  -d "{\"algoritmo\":\"lineal\",\"imputar\":false}"
```
