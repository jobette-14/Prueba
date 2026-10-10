export default function Ajustes({ accesibilidad = {}, setAccesibilidad }) {
  const toggle = (campo) => () =>
    setAccesibilidad({ ...accesibilidad, [campo]: !accesibilidad[campo] });

  return (
    <>
      <h2>Accesibilidad</h2>
      <div className="panel">
        <p className="pista">
          Ajustes de accesibilidad visual. Se guardan en este navegador.
        </p>
        <Opcion id="grande" etiqueta="Texto mas grande"
          activo={!!accesibilidad.grande} onToggle={toggle("grande")} />
        <Opcion id="contraste" etiqueta="Alto contraste"
          activo={!!accesibilidad.contraste} onToggle={toggle("contraste")} />
        <Opcion id="sinMovimiento" etiqueta="Reducir movimiento"
          activo={!!accesibilidad.sinMovimiento} onToggle={toggle("sinMovimiento")} />
      </div>

      <div className="panel">
        <h3>Ayuda de teclado y lector de pantalla</h3>
        <ul>
          <li>Use <strong>Tab</strong> y <strong>Shift+Tab</strong> para navegar entre controles.</li>
          <li>Todos los campos del formulario tienen etiquetas asociadas.</li>
          <li>Los mensajes de resultado usan regiones accesibles (aria-live).</li>
          <li>Los botones y enlaces son accesibles por teclado.</li>
        </ul>
      </div>
    </>
  );
}

function Opcion({ id, etiqueta, activo, onToggle }) {
  return (
    <div style={{ margin: "10px 0" }}>
      <input id={id} type="checkbox" checked={activo} onChange={onToggle}
        style={{ width: "auto", marginRight: 8 }} />
      <label htmlFor={id} style={{ display: "inline", color: "var(--texto)" }}>{etiqueta}</label>
    </div>
  );
}
