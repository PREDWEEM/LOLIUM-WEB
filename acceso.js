// Ingreso a la web PREDWEEM con Firebase Authentication (Microsoft, Google y email/contraseña).
// Lo usan ingreso.html (pantalla de ingreso) y acceso-guardia.js (páginas que exigen haber ingresado).
const FB = "https://www.gstatic.com/firebasejs/10.12.2/";

export const cfg = window.PREDWEEM_ACCESO || { activo: false };

// Modo de prueba: ingreso.html?prueba=1 usa Firebase aunque el ingreso no esté activo (el resto de la web no lo exige).
export const enPrueba = /ingreso\.html$/.test(location.pathname) && new URLSearchParams(location.search).has("prueba");

export function configurado() {
  const f = cfg.firebase || {};
  return Boolean((cfg.activo || enPrueba) && f.apiKey && f.authDomain && f.projectId);
}

let _auth = null;
let _m = null;

export async function conectar() {
  if (_auth) return { auth: _auth, m: _m };
  const app = await import(FB + "firebase-app.js");
  _m = await import(FB + "firebase-auth.js");
  const fb = app.initializeApp(cfg.firebase);
  _auth = _m.getAuth(fb);
  _auth.languageCode = "es";
  await _m.setPersistence(_auth, _m.browserLocalPersistence);
  return { auth: _auth, m: _m };
}

export async function usuarioActual() {
  const { auth, m } = await conectar();
  return new Promise((resolver) => {
    const fin = m.onAuthStateChanged(auth, (u) => { fin(); resolver(u); });
  });
}

function proveedor(m, id) {
  if (id === "google") {
    const p = new m.GoogleAuthProvider();
    p.setCustomParameters({ prompt: "select_account" });
    return p;
  }
  const p = new m.OAuthProvider("microsoft.com");
  p.setCustomParameters({ prompt: "select_account", ...(cfg.microsoftInquilino ? { tenant: cfg.microsoftInquilino } : {}) });
  return p;
}

export async function ingresarCon(id) {
  const { auth, m } = await conectar();
  try {
    return await m.signInWithPopup(auth, proveedor(m, id));
  } catch (e) {
    // ventana emergente bloqueada (frecuente en celulares): mismo ingreso redirigiendo la página
    if (e && (e.code === "auth/popup-blocked" || e.code === "auth/operation-not-supported-in-this-environment")) {
      return m.signInWithRedirect(auth, proveedor(m, id));
    }
    throw e;
  }
}

export async function ingresarConEmail(email, clave) {
  const { auth, m } = await conectar();
  return m.signInWithEmailAndPassword(auth, email.trim(), clave);
}

export async function recuperarClave(email) {
  const { auth, m } = await conectar();
  return m.sendPasswordResetEmail(auth, email.trim());
}

export async function salir() {
  const { auth, m } = await conectar();
  await m.signOut(auth);
}

// Destino después de ingresar: el de ?volver= si es una página de este mismo sitio; si no, cfg.destino.
export function destino() {
  const v = new URLSearchParams(location.search).get("volver");
  if (v && v.startsWith("/") && !v.startsWith("//")) return v;
  return cfg.destino || "./";
}

const MENSAJES = {
  "auth/invalid-credential": "Email o contraseña incorrectos.",
  "auth/wrong-password": "Email o contraseña incorrectos.",
  "auth/user-not-found": "Email o contraseña incorrectos.",
  "auth/invalid-email": "El email no es válido.",
  "auth/user-disabled": "Esta cuenta está deshabilitada. Pedí acceso al administrador.",
  "auth/too-many-requests": "Demasiados intentos. Esperá unos minutos y probá de nuevo.",
  "auth/popup-closed-by-user": "Se cerró la ventana de ingreso antes de terminar.",
  "auth/cancelled-popup-request": "Se cerró la ventana de ingreso antes de terminar.",
  "auth/network-request-failed": "No hay conexión. Revisá internet y probá de nuevo.",
  "auth/account-exists-with-different-credential": "Ese email ya ingresa con otro método. Usá el botón con el que entraste antes.",
  "auth/unauthorized-domain": "Este sitio no está autorizado en Firebase (falta agregar el dominio).",
  "auth/operation-not-allowed": "Esta forma de ingreso no está habilitada.",
};

export function mensajeError(e) {
  return MENSAJES[e && e.code] || "No se pudo ingresar. Probá de nuevo en unos minutos.";
}
