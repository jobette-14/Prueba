import { useState } from "react";
import { api } from "../api";

export default function PrediccionLotes({ seleccionar }) {
  const [archivo, setArchivo] = useState(null);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);

  async function procesar(e) {
    e.preventDefault();
    if (!archivo) {
      setError("Selecciona un archivo CSV.");
      return;
    }
    setError("");
    setResultado(null);
    setCargando(true);
    try {
      const r = await api.predecirLotesArchivo(archivo);
      setResultado(r);
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  }

  function descargarCsv() {
    if (!resultado) return;
    const filas = resultado.resultados;
    const columnas = ["fila", "temperatura", "personas", "horas_uso",
      "consumo_anterior", "consumo_estimado", "consumo_real", "error"];
    const lineas = [columnas.join(",")];
    filas.forEach((f) =>
      lineas.push(columnas.map((c) => (f[c] ?? "")).join(",")));
    const blob = new Blob([lineas.join("\n")], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "predicciones_lote.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <>
      <h2>Prediccion por lotes</h2>
      <form className="panel" onSubmit={procesar}>
        <p className="pista">
          Sube un CSV con las columnas: temperatura, personas, horas_uso y
          consumo_anterior. La columna consumo_real es opcional (solo para comparar).
        </p>
        <div>
          <label htmlFor="archivo">Archivo CSV</label>
          <input id="archivo" type="file" accept=".csv"
            onChange={(e) => setArchivo(e.target.files?.[0] || null)} />
        </div>
        <div className="acciones">
          <button className="boton" type="submit" disabled={cargando}>
            {cargando ? "Procesando..." : "Predecir lote"}
          </button>
        </div>
      </form>

      {error && (
        <div className="mensaje error" role="alert">
          {error}
          {error.toLowerCase().includes("no esta entrenado") && (
            <> <button className="boton secundario"
              onClick={() => seleccionar?.("entrenamiento")}>Ir a Entrenamiento</button></>
          )}
        </div>
      )}

      {resultado && (
        <div className="panel">
          <h3>Resultados</h3>
          <p className="pista">{resultado.resumen}</p>
          <div className="acciones">
            <button className="boton secundario" onClick={descargarCsv}>
              Descargar resultados (CSV)
            </button>
          </div>
          <div className="tabla-envoltura">
            <table>
              <thead>
                <tr>
                  <th>#</th><th>Temperatura</th><th>Personas</th><th>Horas</th>
                  <th>Ant.</th><th>Estimado (kWh)</th><th>Real</th><th>Error</th>
                </tr>
              </thead>
              <tbody>
                {resultado.resultados.map((f) => (
                  <tr key={f.fila}>
                    <td>{f.fila}</td>
                    <td>{f.temperatura}</td>
                    <td>{f.personas}</td>
                    <td>{f.horas_uso}</td>
                    <td>{f.consumo_anterior}</td>
                    <td>{f.consumo_estimado != null ? f.consumo_estimado.toFixed(2) : "-"}</td>
                    <td>{f.consumo_real ?? "-"}</td>
                    <td>{f.error != null ? f.error.toFixed(2) : "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
