import { useState } from "react";
import { api } from "../api";

const INICIAL = { temperatura: "", personas: "", horas_uso: "", consumo_anterior: "", consumo_real: "" };

export default function PrediccionIndividual({ seleccionar }) {
  const [valores, setValores] = useState(INICIAL);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);

  const cambiar = (campo) => (e) => setValores({ ...valores, [campo]: e.target.value });

  async function predecir(e) {
    e.preventDefault();
    setError("");
    setResultado(null);
    setCargando(true);
    try {
      const cuerpo = {
        temperatura: Number(valores.temperatura),
        personas: Number(valores.personas),
        horas_uso: Number(valores.horas_uso),
        consumo_anterior: Number(valores.consumo_anterior),
      };
      if (valores.consumo_real !== "") cuerpo.consumo_real = Number(valores.consumo_real);
      const r = await api.predecir(cuerpo);
      setResultado(r);
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  }

  return (
    <>
      <h2>Prediccion individual</h2>
      <form className="panel" onSubmit={predecir}>
        <div className="campos">
          <Campo etiqueta="Temperatura (C)" id="temp" tipo="number" valor={valores.temperatura}
            onChange={cambiar("temperatura")} min={-50} max={60} step="0.1" />
          <Campo etiqueta="Personas" id="pers" tipo="number" valor={valores.personas}
            onChange={cambiar("personas")} min={1} max={50} step="1" />
          <Campo etiqueta="Horas de uso" id="horas" tipo="number" valor={valores.horas_uso}
            onChange={cambiar("horas_uso")} min={0} max={24} step="0.5" />
          <Campo etiqueta="Consumo anterior (kWh)" id="ant" tipo="number"
            valor={valores.consumo_anterior} onChange={cambiar("consumo_anterior")}
            min={0} max={1000} step="0.1" />
          <Campo etiqueta="Consumo real (opcional)" id="real" tipo="number"
            valor={valores.consumo_real} onChange={cambiar("consumo_real")}
            min={0} max={1000} step="0.1" />
        </div>
        <div className="acciones">
          <button className="boton" type="submit" disabled={cargando}>
            {cargando ? "Calculando..." : "Predecir consumo"}
          </button>
        </div>
      </form>

      {error && (
        <div className="mensaje error" role="alert">
          {error}
          {error.toLowerCase().includes("no esta entrenado") && (
            <>
              {" "}
              <button className="boton secundario" onClick={() => seleccionar?.("entrenamiento")}>
                Ir a Entrenamiento
              </button>
            </>
          )}
        </div>
      )}

      {resultado && (
        <div className="panel" aria-live="polite">
          <div className="resultado">Consumo estimado: {resultado.consumo_estimado?.toFixed(2)} kWh</div>
          {resultado.error != null && (
            <p className="pista">
              Consumo real: {resultado.consumo_real?.toFixed(2)} kWh | Error:{" "}
              {resultado.error.toFixed(2)} kWh | Error absoluto:{" "}
              {resultado.error_absoluto?.toFixed(2)} kWh
            </p>
          )}
          <p className="pista">Algoritmo: {resultado.algoritmo} (v{resultado.version})</p>
        </div>
      )}
    </>
  );
}

function Campo({ etiqueta, id, ...resto }) {
  return (
    <div>
      <label htmlFor={id}>{etiqueta}</label>
      <input id={id} required={!etiqueta.includes("opcional")} {...resto} />
    </div>
  );
}
