// Guardia de las páginas de la web: si el ingreso está activo y no hay sesión, lleva a ingreso.html y vuelve acá
// después de ingresar. Con el ingreso inactivo (acceso-config.js) no hace nada.
// Uso, en el <head>:  <script src="acceso-config.js"></script>  <script type="module" src="acceso-guardia.js"></script>
import { configurado, usuarioActual, salir } from "./acceso.js?v=20261119c";

if (configurado()) {
  const raiz = document.documentElement;
  raiz.style.visibility = "hidden"; // no mostrar la página hasta saber si hay sesión
  try {
    const u = await usuarioActual();
    if (!u) {
      location.replace("ingreso.html?volver=" + encodeURIComponent(location.pathname + location.search + location.hash));
    } else {
      raiz.style.visibility = "";
      const chip = document.createElement("div");
      chip.className = "predweem-sesion";
      chip.innerHTML = '<span></span><button type="button">Cerrar sesión</button>';
      chip.querySelector("span").textContent = u.email || u.displayName || "Sesión iniciada";
      chip.querySelector("button").addEventListener("click", async () => { await salir(); location.replace("ingreso.html"); });
      const estilo = document.createElement("style");
      estilo.textContent = ".predweem-sesion{position:fixed;left:12px;bottom:12px;z-index:2000;display:flex;gap:.5rem;align-items:center;"
        + "background:#fff;border:1px solid rgba(26,95,63,.2);border-radius:999px;padding:.3rem .4rem .3rem .8rem;font:500 13px Inter,system-ui,sans-serif;"
        + "color:#1a5f3f;box-shadow:0 4px 14px rgba(0,0,0,.08)}.predweem-sesion button{border:0;background:#1a5f3f;color:#fff;border-radius:999px;"
        + "padding:.25rem .7rem;font:inherit;cursor:pointer}.predweem-sesion span{max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}";
      document.head.appendChild(estilo);
      (document.body ? Promise.resolve() : new Promise((r) => addEventListener("DOMContentLoaded", r))).then(() => document.body.appendChild(chip));
    }
  } catch (e) {
    // si Firebase no responde, no se deja la página en blanco: se manda a ingresar
    location.replace("ingreso.html?volver=" + encodeURIComponent(location.pathname));
  }
}
