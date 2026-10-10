import { useEffect, useState } from "react";
import { api } from "../api";

const INICIAL = { temperatura: "", personas: "", horas_uso: "", consumo_anterior: "", consumo_real: "" };

export default function Datos() {
  const [registros, setRegistros] = useState([]);
  const [valores, setValores] = useState(INICIAL);
  const [mensaje, setMensaje] = useState(null);
  const [error, setError] = useState("");

  async function cargar() {
    try {
      const r = await api.registros();
      setRegistros(r.registros || []);
    } catch (e) {
      setError(e.message);
    }
  }

  useEffect(() => { cargar(); }, []);

  const cambiar = (c) => (e) => setValores({ ...valores, [c]: e.target.value });

  async function registrar(e) {
    e.preventDefault();
    setMensaje(null);
    setError("");
    try {
      await api.registrar({
        temperatura: Number(valores.temperatura),
        personas: Number(valores.personas),
        horas_uso: Number(valores.horas_uso),
        consumo_anterior: Number(valores.consumo_anterior),
        consumo_real: Number(valores.consumo_real),
      });
      setValores(INICIAL);
      setMensaje({ tipo: "ok", texto: "Registro agregado correctamente." });
      cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  async function importar(e) {
    const archivo = e.target.files?.[0];
    if (!archivo) return;
    setMensaje(null);
    setError("");
    try {
      const r = await api.importarRegistros(archivo);
      setMensaje({ tipo: "ok", texto: `Importados ${r.agregados} registros.` });
      cargar();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <>
      <h2>Datos historicos</h2>

      <div className="panel">
        <h3>Importar desde CSV</h3>
        <p className="pista">
          Columnas: temperatura, personas, horas_uso, consumo_anterior, consumo_real.
        </p>
        <input type="file" accept=".csv" onChange={importar}
          aria-label="Importar registros desde CSV" />
      </div>

      <form className="panel" onSubmit={registrar}>
        <h3>Registrar dato manualmente</h3>
        <div className="campos">
          <Campo id="t" etiqueta="Temperatura (C)" value={valores.temperatura} onChange={cambiar("temperatura")} min={-50} max={60} />
          <Campo id="p" etiqueta="Personas" value={valores.personas} onChange={cambiar("personas")} min={1} max={50} />
          <Campo id="h" etiqueta="Horas de uso" value={valores.horas_uso} onChange={cambiar("horas_uso")} min={0} max={24} />
          <Campo id="a" etiqueta="Consumo anterior (kWh)" value={valores.consumo_anterior} onChange={cambiar("consumo_anterior")} min={0} max={1000} />
          <Campo id="r" etiqueta="Consumo real (kWh)" value={valores.consumo_real} onChange={cambiar("consumo_real")} min={0} max={1000} />
        </div>
        <div className="acciones">
          <button className="boton" type="submit">Registrar</button>
        </div>
      </form>

      {mensaje && <div className={"mensaje " + mensaje.tipo}>{mensaje.texto}</div>}
      {error && <div className="mensaje error" role="alert">{error}</div>}

      <div className="panel">
        <h3>Registros ({registros.length})</h3>
        <div className="tabla-envoltura">
          <table>
            <thead>
              <tr>
                <th>#</th><th>Temp.</th><th>Personas</th><th>Horas</th>
                <th>Ant.</th><th>Real</th><th>Fecha</th>
              </tr>
            </thead>
            <tbody>
              {registros.map((r) => (
                <tr key={r.id}>
                  <td>{r.id}</td><td>{r.temperatura}</td><td>{r.personas}</td>
                  <td>{r.horas_uso}</td><td>{r.consumo_anterior}</td>
                  <td>{r.consumo_real}</td><td>{r.fecha_registro}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

function Campo({ id, etiqueta, ...resto }) {
  return (
    <div>
      <label htmlFor={id}>{etiqueta}</label>
      <input id={id} type="number" step="0.1" required {...resto} />
    </div>
  );
}
