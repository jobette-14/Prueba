import { useEffect, useState } from "react";
import { api, getApiKey, setApiKey } from "../api";

export default function Entrenamiento({ config }) {
  const [algoritmo, setAlgoritmo] = useState("lineal");
  const [imputar, setImputar] = useState(false);
  const [testSize, setTestSize] = useState(0.2);
  const [clave, setClave] = useState(getApiKey());
  const [estado, setEstado] = useState(null);
  const [comparacion, setComparacion] = useState(null);
  const [mensaje, setMensaje] = useState(null);
  const [cargando, setCargando] = useState(false);

  async function cargarEstado() {
    try { setEstado(await api.estadoModelo()); } catch { /* ignore */ }
  }
  useEffect(() => { cargarEstado(); }, []);

  function guardarClave(v) {
    setClave(v);
    setApiKey(v.trim());
  }

  async function entrenar() {
    setMensaje(null);
    setCargando(true);
    try {
      const r = await api.entrenar({ algoritmo, imputar, test_size: Number(testSize) });
      setMensaje({ tipo: "ok", texto:
        `Entrenado. R2=${r.metricas.r2.toFixed(4)} | MAE=${r.metricas.mae.toFixed(4)} kWh` });
      cargarEstado();
    } catch (e) {
      setMensaje({ tipo: "error", texto: e.message });
    } finally {
      setCargando(false);
    }
  }

  async function comparar() {
    setMensaje(null);
    setComparacion(null);
    try {
      const r = await api.comparar({ algoritmo, imputar, test_size: Number(testSize) });
      setComparacion(r.resultados);
    } catch (e) {
      setMensaje({ tipo: "error", texto: e.message });
    }
  }

  return (
    <>
      <h2>Entrenamiento del modelo</h2>
      {config?.escritura_protegida && (
        <div className="panel">
          <label htmlFor="apikey">Clave de API (necesaria para entrenar)</label>
          <input id="apikey" type="password" value={clave}
            onChange={(e) => guardarClave(e.target.value)}
            placeholder="X-API-Key" autoComplete="off" />
          <p className="pista">Se guarda solo en este navegador.</p>
        </div>
      )}

      <div className="panel">
        <div className="campos">
          <div>
            <label htmlFor="algo">Algoritmo</label>
            <select id="algo" value={algoritmo} onChange={(e) => setAlgoritmo(e.target.value)}>
              <option value="lineal">Regresion Lineal Multiple</option>
              <option value="ridge">Regresion Ridge (L2)</option>
              <option value="random_forest">Random Forest</option>
            </select>
          </div>
          <div>
            <label htmlFor="test">Proporcion de prueba</label>
            <select id="test" value={testSize} onChange={(e) => setTestSize(e.target.value)}>
              <option value="0.1">10%</option><option value="0.2">20%</option>
              <option value="0.3">30%</option><option value="0.4">40%</option>
            </select>
          </div>
          <div>
            <label htmlFor="imp">Imputar faltantes</label>
            <input id="imp" type="checkbox" checked={imputar}
              onChange={(e) => setImputar(e.target.checked)} style={{ width: "auto" }} />
          </div>
        </div>
        <div className="acciones">
          <button className="boton" onClick={entrenar} disabled={cargando}>
            {cargando ? "Entrenando..." : "Entrenar modelo"}
          </button>
          <button className="boton secundario" onClick={comparar}>Comparar algoritmos</button>
        </div>
        {mensaje && <div className={"mensaje " + mensaje.tipo}>{mensaje.texto}</div>}
      </div>

      {estado?.entrenado && (
        <div className="panel">
          <h3>Modelo actual: {estado.algoritmo_nombre}</h3>
          <div className="tarjetas">
            <Tarjeta titulo="R2" valor={estado.metricas?.r2?.toFixed(4)} />
            <Tarjeta titulo="MAE" valor={estado.metricas?.mae?.toFixed(4)} unidad="kWh" />
            <Tarjeta titulo="RMSE" valor={estado.metricas?.rmse?.toFixed(4)} unidad="kWh" />
            <Tarjeta titulo="Imputacion" valor={estado.imputacion ? "Si" : "No"} />
          </div>
          {estado.formula && (
            <pre style={{ whiteSpace: "pre-wrap", marginTop: 12, fontSize: "0.82rem" }}>
              {estado.formula}
            </pre>
          )}
        </div>
      )}

      {comparacion && (
        <div className="panel">
          <h3>Comparacion de algoritmos</h3>
          <table>
            <thead><tr><th>Algoritmo</th><th>R2</th><th>MAE</th><th>RMSE</th></tr></thead>
            <tbody>
              {comparacion.map((r) => (
                <tr key={r.algoritmo}>
                  <td>{r.nombre}</td>
                  <td>{r.metricas ? r.metricas.r2.toFixed(4) : "N/D"}</td>
                  <td>{r.metricas ? r.metricas.mae.toFixed(4) : "N/D"}</td>
                  <td>{r.metricas ? r.metricas.rmse.toFixed(4) : "N/D"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

function Tarjeta({ titulo, valor, unidad }) {
  return (
    <div className="tarjeta">
      <div className="titulo">{titulo}</div>
      <div className="valor">{valor ?? "--"}</div>
      {unidad ? <div className="unidad">{unidad}</div> : null}
    </div>
  );
}
