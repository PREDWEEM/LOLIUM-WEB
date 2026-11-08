"""Mantiene despiertas las apps Streamlit enlazadas en el mapa de index.html.

Uso:
  python scripts/despertar_apps.py --listar        -> JSON con [{"nombre", "url"}] (para la matriz del workflow)
  python scripts/despertar_apps.py URL [NOMBRE]    -> abre la app, la despierta si hiberna y espera a que cargue

La lista de apps se lee del arreglo `locations` de index.html: si se agrega o cambia una
localidad en el mapa, el despertador la incluye sin más cambios.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

INDEX = Path(__file__).resolve().parent.parent / "index.html"
MAX_ESPERA_S = 300
BOTON_DESPERTAR = re.compile(r"(get this app back up|wake up)", re.IGNORECASE)


def listar_apps() -> list[dict[str, str]]:
    html = INDEX.read_text(encoding="utf-8")
    patron = re.compile(r"name:\s*'([^']+)'\s*,\s*url:\s*'(https://[^']+)'")
    apps = [{"nombre": n, "url": u} for n, u in patron.findall(html)]
    if not apps:
        raise SystemExit("No se encontraron apps en index.html.")
    return apps


def app_cargada(frame) -> bool:
    """La interfaz de Streamlit está montada y muestra contenido propio de la app."""
    contenedor = frame.locator('[data-testid="stAppViewContainer"]')
    if not contenedor.count() or not contenedor.first.is_visible():
        return False
    contenido = frame.locator(
        '[data-testid="stMarkdownContainer"], [data-testid="stPlotlyChart"], '
        '[data-testid="stMetric"], h1, h2'
    )
    return contenido.count() > 0 and contenido.first.is_visible()


def visitar(url: str, nombre: str) -> str:
    from playwright.sync_api import Error, TimeoutError, sync_playwright

    with sync_playwright() as pw:
        navegador = pw.chromium.launch()
        try:
            pagina = navegador.new_page()
            pagina.set_default_timeout(5000)
            inicio = time.monotonic()
            desperto = False
            lista_desde = None
            try:
                pagina.goto(url, wait_until="domcontentloaded", timeout=60000)
            except TimeoutError:
                print("La apertura inicial sigue en curso.", flush=True)

            while time.monotonic() - inicio < MAX_ESPERA_S:
                lista = False
                for frame in pagina.frames:  # Community Cloud sirve la app dentro de un iframe
                    try:
                        boton = frame.get_by_role("button", name=BOTON_DESPERTAR)
                        if not desperto and boton.count() and boton.first.is_visible():
                            boton.first.click()
                            desperto = True
                            print(f"{nombre}: estaba hibernando, se pidió despertarla.", flush=True)
                        lista = app_cargada(frame) or lista
                    except Error:
                        continue  # el iframe puede cambiar mientras Streamlit arranca
                if lista:
                    lista_desde = lista_desde or time.monotonic()
                    if time.monotonic() - lista_desde >= 5:
                        s = round(time.monotonic() - inicio)
                        estado = "despertada" if desperto else "ya estaba activa"
                        return f"OK {nombre}: {estado}, cargó en {s} s."
                else:
                    lista_desde = None
                pagina.wait_for_timeout(5000)
            raise RuntimeError(f"{nombre}: no terminó de cargar en {MAX_ESPERA_S // 60} minutos.")
        finally:
            navegador.close()


def informar(mensaje: str, url: str) -> None:
    print(mensaje, flush=True)
    if resumen := os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(resumen).open("a", encoding="utf-8") as f:
            f.write(f"{mensaje}  \n{url}\n\n")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--listar":
        print(json.dumps(listar_apps(), ensure_ascii=False))
        raise SystemExit(0)
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    url = sys.argv[1]
    nombre = sys.argv[2] if len(sys.argv) > 2 else url
    try:
        informar(visitar(url, nombre), url)
    except Exception as error:  # noqa: BLE001
        informar(f"FALLO {nombre}: {error}", url)
        raise SystemExit(1)
