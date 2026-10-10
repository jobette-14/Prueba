// Cliente de la API de ElectroPredict.
// La clave de escritura (X-API-Key) se guarda solo en el navegador del usuario
// y se envia al backend; nunca se incrusta en el bundle.

const BASE = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

export function getApiKey() {
  return localStorage.getItem("electropredict_api_key") || "";
}

export function setApiKey(clave) {
  if (clave) localStorage.setItem("electropredict_api_key", clave);
  else localStorage.removeItem("electropredict_api_key");
}

async function peticion(ruta, opciones = {}) {
  const cabeceras = { ...(opciones.headers || {}) };
  const clave = getApiKey();
  if (clave) cabeceras["X-API-Key"] = clave;
  if (opciones.body && !(opciones.body instanceof FormData)) {
    cabeceras["Content-Type"] = "application/json";
  }

  let respuesta;
  try {
    respuesta = await fetch(`${BASE}${ruta}`, { ...opciones, headers: cabeceras });
  } catch (e) {
    throw new Error(
      "No se pudo conectar con el servidor. Revisa tu conexion e intentalo de nuevo.");
  }

  const tipo = respuesta.headers.get("content-type") || "";
  let cuerpo = null;
  if (tipo.includes("application/json")) {
    cuerpo = await respuesta.json();
  } else {
    cuerpo = await respuesta.text();
  }

  if (!respuesta.ok) {
    let detalle = "Error del servidor.";
    if (cuerpo && typeof cuerpo === "object") {
      detalle = cuerpo.detail || cuerpo.mensaje || JSON.stringify(cuerpo);
    } else if (typeof cuerpo === "string" && cuerpo) {
      detalle = cuerpo;
    }
    const err = new Error(detalle);
    err.status = respuesta.status;
    throw err;
  }
  return cuerpo;
}

export const api = {
  salud: () => peticion("/api/salud"),
  configPublica: () => peticion("/api/config-publica"),
  estadisticas: () => peticion("/api/estadisticas"),
  estadoModelo: () => peticion("/api/modelo"),
  entrenar: (datos) =>
    peticion("/api/modelo/entrenar", { method: "POST", body: JSON.stringify(datos) }),
  comparar: (datos) =>
    peticion("/api/modelo/comparar", { method: "POST", body: JSON.stringify(datos) }),
  predecir: (datos) =>
    peticion("/api/prediccion", { method: "POST", body: JSON.stringify(datos) }),
  predecirLotesJson: (datos) =>
    peticion("/api/prediccion/lotes/json", { method: "POST", body: JSON.stringify(datos) }),
  predecirLotesArchivo: (archivo) => {
    const fd = new FormData();
    fd.append("archivo", archivo);
    return peticion("/api/prediccion/lotes", { method: "POST", body: fd });
  },
  registros: () => peticion("/api/registros"),
  registrar: (datos) =>
    peticion("/api/registros", { method: "POST", body: JSON.stringify(datos) }),
  importarRegistros: (archivo) => {
    const fd = new FormData();
    fd.append("archivo", archivo);
    return peticion("/api/registros/importar", { method: "POST", body: fd });
  },
  historial: () => peticion("/api/historial"),
  consumoReal: (id_prediccion, consumo_real) =>
    peticion("/api/historial/consumo-real", {
      method: "POST",
      body: JSON.stringify({ id_prediccion, consumo_real }),
    }),
  chat: (mensaje, historial) =>
    peticion("/api/chat", {
      method: "POST",
      body: JSON.stringify({ mensaje, historial }),
    }),
  urlReporteTxt: () => `${BASE}/api/reportes/txt`,
  urlReporteCsv: (tipo) => `${BASE}/api/reportes/csv?tipo=${tipo}`,
  urlReportePdf: () => `${BASE}/api/reportes/pdf`,
};
