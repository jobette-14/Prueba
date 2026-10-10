import { useEffect, useState } from "react";
import { api } from "./api";
import Dashboard from "./componentes/Dashboard.jsx";
import Entrenamiento from "./componentes/Entrenamiento.jsx";
import PrediccionIndividual from "./componentes/PrediccionIndividual.jsx";
import PrediccionLotes from "./componentes/PrediccionLotes.jsx";
import Datos from "./componentes/Datos.jsx";
import Historial from "./componentes/Historial.jsx";
import Reportes from "./componentes/Reportes.jsx";
import Ajustes from "./componentes/Ajustes.jsx";
import ChatIA from "./componentes/ChatIA.jsx";

const SECCIONES = [
  { id: "inicio", nombre: "Inicio", Componente: Dashboard },
  { id: "prediccion", nombre: "Prediccion", Componente: PrediccionIndividual },
  { id: "lotes", nombre: "Por lotes", Componente: PrediccionLotes },
  { id: "datos", nombre: "Datos historicos", Componente: Datos },
  { id: "entrenamiento", nombre: "Entrenamiento", Componente: Entrenamiento },
  { id: "historial", nombre: "Historial", Componente: Historial },
  { id: "reportes", nombre: "Reportes", Componente: Reportes },
  { id: "ajustes", nombre: "Accesibilidad", Componente: Ajustes },
];

function cargarAccesibilidad() {
  try {
    return JSON.parse(localStorage.getItem("electropredict_accesibilidad")) || {};
  } catch {
    return {};
  }
}

export default function App() {
  const [seccion, setSeccion] = useState("inicio");
  const [config, setConfig] = useState(null);
  const [servicioOk, setServicioOk] = useState(null);
  const [accesibilidad, setAccesibilidad] = useState(cargarAccesibilidad);

  useEffect(() => {
    const b = document.body;
    b.classList.toggle("accesible-grande", !!accesibilidad.grande);
    b.classList.toggle("accesible-contraste", !!accesibilidad.contraste);
    b.classList.toggle("accesible-sin-movimiento", !!accesibilidad.sinMovimiento);
    localStorage.setItem("electropredict_accesibilidad", JSON.stringify(accesibilidad));
  }, [accesibilidad]);

  useEffect(() => {
    (async () => {
      try {
        const cfg = await api.configPublica();
        setConfig(cfg);
        setServicioOk(true);
      } catch {
        setServicioOk(false);
      }
    })();
  }, []);

  const actual = SECCIONES.find((s) => s.id === seccion) || SECCIONES[0];
  const Seccion = actual.Componente;

  return (
    <div className="app">
      <aside className="barra">
        <div>
          <h1>ElectroPredict</h1>
          <p className="lema">Prediccion de consumo electrico</p>
        </div>
        <nav aria-label="Navegacion principal">
          {SECCIONES.map((s) => (
            <button
              key={s.id}
              onClick={() => setSeccion(s.id)}
              aria-current={seccion === s.id ? "page" : undefined}
            >
              {s.nombre}
            </button>
          ))}
        </nav>
        <div style={{ marginTop: "auto" }}>
          <span className={"estado-servicio " + (servicioOk === false ? "error" : "ok")}>
            {servicioOk === false ? "Sin conexion con la API" : "API conectada"}
          </span>
        </div>
      </aside>

      <main className="contenido" id="contenido" tabIndex={-1}>
        {servicioOk === false && (
          <div className="mensaje error" role="alert">
            No se pudo conectar con el servicio. Revisa tu conexion o intenta mas
            tarde. Algunas funciones pueden no estar disponibles.
          </div>
        )}
        <Seccion
          config={config}
          seleccionar={setSeccion}
          accesibilidad={accesibilidad}
          setAccesibilidad={setAccesibilidad}
        />
      </main>

      <ChatIA disponible={config?.chat_disponible} />
    </div>
  );
}
