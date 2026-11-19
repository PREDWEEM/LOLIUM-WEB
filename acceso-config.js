// Configuración del ingreso a la web PREDWEEM (página ingreso.html y guardia de las demás páginas).
//
// Mientras `activo` sea false, el ingreso no se exige: ingreso.html muestra un botón «Continuar» y las páginas se ven
// como siempre. Para activarlo:
//   1. Crear un proyecto en Firebase (console.firebase.google.com) → Authentication → habilitar los proveedores:
//      Google, Microsoft y/o Correo electrónico/contraseña. En Settings → Authorized domains agregar predweem.github.io.
//   2. Copiar acá la configuración web del proyecto (Project settings → Your apps → Web app → firebaseConfig).
//   3. Para Microsoft (cuenta de la empresa): registrar la app en Microsoft Entra ID con la URL de retorno que indica
//      Firebase (https://<proyecto>.firebaseapp.com/__/auth/handler) y poner el id de inquilino en `microsoftInquilino`.
//   4. Usuarios con email y contraseña: crearlos en Firebase → Authentication → Users (la página no permite registrarse
//      sola; la recuperación de contraseña la manda Firebase por email).
//   5. Poner `activo: true`.
//
// Esta configuración es pública por diseño (la de Firebase no es un secreto). La protección de las apps sigue estando
// en cada app; esta página ordena el ingreso a la web.
window.PREDWEEM_ACCESO = {
  activo: false,
  firebase: {
    apiKey: "",
    authDomain: "",
    projectId: "",
    appId: "",
  },
  // Botones, en este orden: "microsoft", "google", "email"
  proveedores: ["microsoft", "google", "email"],
  textos: {
    microsoft: "Cuenta de la empresa (Microsoft)",
    google: "Cuenta de Google",
  },
  microsoftInquilino: "",            // id de inquilino de Microsoft Entra de la empresa ("" = cualquier cuenta Microsoft)
  destino: "./",                     // a dónde se va después de ingresar (la página principal)
  contacto: "",                      // email para pedir acceso (se muestra al pie)
};
