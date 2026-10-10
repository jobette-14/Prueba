import { useState } from "react";
import { api } from "../api";

export default function Reportes() {
  const [texto, setTexto] = useState("");
  const [error, setError] = useState("");

  async function previsualizar() {
    setError("");
    try {
      const r = await fetch(api.urlReporteTxt());
      if (!r.ok) throw new Error("No se pudo generar el reporte.");
      setTexto(await r.text());
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <>
      <h2>Reportes</h2>
      {error && <div className="mensaje error" role="alert">{error}</div>}

      <div className="panel">
        <p className="pista">
          Descarga el reporte con resumen de datos, entrenamiento, metricas e
          historial de predicciones.
        </p>
        <div className="acciones">
          <button className="boton" onClick={previsualizar}>Ver reporte (texto)</button>
          <a className="boton secundario" href={api.urlReporteTxt()} download>Descargar TXT</a>
          <a className="boton secundario" href={api.urlReportePdf()} download>Descargar PDF</a>
          <a className="boton secundario" href={api.urlReporteCsv("predicciones")} download>
            Predicciones (CSV)
          </a>
          <a className="boton secundario" href={api.urlReporteCsv("historicos")} download>
            Historicos (CSV)
          </a>
        </div>
      </div>

      {texto && (
        <div className="panel">
          <h3>Previsualizacion</h3>
          <pre style={{ whiteSpace: "pre-wrap", fontSize: "0.82rem" }}>{texto}</pre>
        </div>
      )}
    </>
  );
}
