import { useEffect, useState } from "react";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, Tooltip, Legend,
} from "chart.js";
import { api } from "../api";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend);

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [registros, setRegistros] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const [s, r] = await Promise.all([api.estadisticas(), api.registros()]);
        setStats(s);
        setRegistros(r.registros || []);
      } catch (e) {
        setError(e.message);
      }
    })();
  }, []);

  if (error) return <div className="mensaje error" role="alert">{error}</div>;
  if (!stats) return <p>Cargando estadisticas...</p>;

  const d = stats.datos || {};
  const p = stats.predicciones || {};
  const m = stats.modelo || {};

  const ultimos = registros.slice(-12);
  const datosGrafica = {
    labels: ultimos.map((r) => `#${r.id}`),
    datasets: [
      {
        label: "Consumo real (kWh)",
        data: ultimos.map((r) => r.consumo_real),
        backgroundColor: "#2563eb",
      },
    ],
  };
  const opciones = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: { y: { beginAtZero: true, title: { display: true, text: "kWh" } } },
  };

  return (
    <>
      <h2>Panel principal</h2>
      <div className="tarjetas">
        <Tarjeta titulo="Registros historicos" valor={d.cantidad ?? 0} />
        <Tarjeta titulo="Consumo promedio" valor={d.consumo_promedio ?? "--"} unidad="kWh" />
        <Tarjeta titulo="Predicciones" valor={p.cantidad ?? 0} />
        <Tarjeta
          titulo="Estado del modelo"
          valor={m.entrenado ? "Entrenado" : "No entrenado"}
          unidad={m.entrenado ? `R2 ${m.metricas?.r2?.toFixed(3)}` : ""}
        />
      </div>

      <div className="panel" style={{ marginTop: 18 }}>
        <h3>Consumo reciente</h3>
        {ultimos.length === 0 ? (
          <p className="pista">Aun no hay datos. Importa un CSV o registra datos.</p>
        ) : (
          <div className="grafica">
            <Bar data={datosGrafica} options={opciones} />
          </div>
        )}
      </div>

      <div className="panel">
        <h3>Base de datos</h3>
        <p className="pista">
          {stats.base_datos?.conectada
            ? "Conectada a PostgreSQL (Neon)."
            : "Sin base de datos: los datos viven en memoria durante la sesion."}
        </p>
        <p className="pista">
          Algoritmo del modelo: {m.algoritmo || "-"}
        </p>
      </div>
    </>
  );
}

function Tarjeta({ titulo, valor, unidad }) {
  return (
    <div className="tarjeta">
      <div className="titulo">{titulo}</div>
      <div className="valor">{valor}</div>
      {unidad ? <div className="unidad">{unidad}</div> : null}
    </div>
  );
}
