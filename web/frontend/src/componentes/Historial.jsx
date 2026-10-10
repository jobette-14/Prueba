import { useEffect, useState } from "react";
import { api } from "../api";

export default function Historial() {
  const [predicciones, setPredicciones] = useState([]);
  const [filtro, setFiltro] = useState("todas");
  const [editando, setEditando] = useState(null);
  const [valorReal, setValorReal] = useState("");
  const [error, setError] = useState("");

  async function cargar() {
    try {
      const r = await api.historial();
      setPredicciones(r.predicciones || []);
    } catch (e) {
      setError(e.message);
    }
  }
  useEffect(() => { cargar(); }, []);

  const visibles = predicciones.filter((p) =>
    filtro === "todas" ? true : p.tipo === filtro);

  async function guardarReal(p) {
    try {
      await api.consumoReal(p.id, Number(valorReal));
      setEditando(null);
      setValorReal("");
      cargar();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <>
      <h2>Historial de predicciones</h2>
      {error && <div className="mensaje error" role="alert">{error}</div>}

      <div className="panel">
        <label htmlFor="filtro">Filtrar</label>
        <select id="filtro" value={filtro} onChange={(e) => setFiltro(e.target.value)}
          style={{ maxWidth: 220 }}>
          <option value="todas">Todas</option>
          <option value="individual">Individuales</option>
          <option value="lote">Por lotes</option>
        </select>
      </div>

      <div className="panel">
        <div className="tabla-envoltura">
          <table>
            <thead>
              <tr>
                <th>#</th><th>Fecha</th><th>Tipo</th><th>Est. (kWh)</th>
                <th>Real (kWh)</th><th>Error</th><th>Accion</th>
              </tr>
            </thead>
            <tbody>
              {visibles.map((p) => (
                <tr key={p.id}>
                  <td>{p.id}</td>
                  <td>{p.fecha}</td>
                  <td>{p.tipo}</td>
                  <td>{p.consumo_estimado?.toFixed(2)}</td>
                  <td>{p.consumo_real != null ? p.consumo_real.toFixed(2) : "-"}</td>
                  <td>{p.error != null ? p.error.toFixed(2) : "-"}</td>
                  <td>
                    {editando === p.id ? (
                      <span style={{ display: "inline-flex", gap: 6 }}>
                        <input type="number" step="0.1" min="0" max="1000" value={valorReal}
                          onChange={(e) => setValorReal(e.target.value)}
                          style={{ width: 90 }} aria-label={`Consumo real para prediccion ${p.id}`} />
                        <button className="boton" onClick={() => guardarReal(p)}>Guardar</button>
                      </span>
                    ) : (
                      <button className="boton secundario"
                        onClick={() => { setEditando(p.id); setValorReal(""); }}>
                        Registrar real
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {visibles.length === 0 && <p className="pista">No hay predicciones.</p>}
      </div>
    </>
  );
}
