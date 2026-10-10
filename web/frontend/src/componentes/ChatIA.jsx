import { useState } from "react";
import { api } from "../api";

export default function ChatIA({ disponible }) {
  const [abierto, setAbierto] = useState(false);
  const [mensajes, setMensajes] = useState([
    { rol: "bot", texto: "Hola. Soy el asistente de ElectroPredict. Puedo ayudarte a interpretar las predicciones." },
  ]);
  const [texto, setTexto] = useState("");
  const [cargando, setCargando] = useState(false);

  async function enviar(e) {
    e.preventDefault();
    const mensaje = texto.trim();
    if (!mensaje) return;
    setMensajes((m) => [...m, { rol: "user", texto: mensaje }]);
    setTexto("");
    setCargando(true);
    try {
      const historial = mensajes.map((m) => ({
        rol: m.rol === "user" ? "user" : "assistant", texto: m.texto,
      }));
      const r = await api.chat(mensaje, historial);
      setMensajes((m) => [...m, { rol: "bot", texto: r.respuesta }]);
    } catch (err) {
      setMensajes((m) => [...m, { rol: "bot", texto: err.message }]);
    } finally {
      setCargando(false);
    }
  }

  return (
    <>
      <div className="chat-flotante">
        <button className="boton" onClick={() => setAbierto(!abierto)}
          aria-expanded={abierto} aria-label="Abrir asistente de IA">
          {abierto ? "Cerrar asistente" : "Asistente IA"}
        </button>
      </div>

      {abierto && (
        <section className="chat-panel" aria-label="Asistente de IA">
          <header>Asistente de ElectroPredict</header>
          {!disponible && (
            <div className="mensaje info" style={{ margin: 10 }}>
              El asistente de IA no esta configurado en este servidor. Puedes usar
              la app sin problema.
            </div>
          )}
          <div className="chat-cuerpo">
            {mensajes.map((m, i) => (
              <div key={i} className={"chat-burbuja " + (m.rol === "user" ? "user" : "bot")}>
                {m.texto}
              </div>
            ))}
            {cargando && <div className="chat-burbuja bot">Escribiendo...</div>}
          </div>
          <form className="chat-pie" onSubmit={enviar}>
            <input value={texto} onChange={(e) => setTexto(e.target.value)}
              placeholder="Escribe tu pregunta" aria-label="Mensaje para el asistente"
              disabled={!disponible} />
            <button className="boton" type="submit" disabled={!disponible || cargando}>Enviar</button>
          </form>
        </section>
      )}
    </>
  );
}
