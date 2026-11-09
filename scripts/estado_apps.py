"""Calcula el estado de cada app del mapa y lo guarda en estado_apps.json (lo lee index.html).

Uso:
  python scripts/estado_apps.py [CARPETA_RESULTADOS]

CARPETA_RESULTADOS contiene los resultado*.json que escribe despertar_apps.py (si la app respondió).
Sin carpeta, se toma como que todas las apps respondieron.

Estados:
  ok              app responde y datos de estación (≥ 80 % observados) al día
  estimada        app responde y datos al día, pero mayormente estimados (reanálisis o pronósticos)
  desactualizada  app responde, pero los datos no llegan a la fecha esperada
  caida           la app no respondió en la última verificación
"""

from __future__ import annotations

import csv
import io
import json
import re
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
INDEX = RAIZ / "index.html"
SALIDA = RAIZ / "estado_apps.json"
TOLERANCIA_DIAS = 3          # durante la campaña, los datos pueden venir hasta 3 días atrasados
MIN_OBSERVADOS = 0.80        # proporción mínima de días observados para considerarlos "de estación"
FIN_CAMPANIA = (10, 1)       # 1 de octubre
HOY = datetime.now(timezone(timedelta(hours=-3))).date()


def apps_del_mapa() -> list[dict]:
    html = INDEX.read_text(encoding="utf-8")
    patron = re.compile(r"name:\s*'([^']+)'\s*,\s*url:\s*'([^']+)'\s*,\s*repo:\s*'([^']+)'")
    return [{"nombre": n, "url": u, "repo": r} for n, u, r in patron.findall(html)]


def leer_resultados(carpeta: Path | None) -> dict[str, bool]:
    if carpeta is None:
        return {}
    res = {}
    for f in carpeta.rglob("resultado*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        res[d["nombre"]] = bool(d["ok"])
    return res


def descargar(url: str) -> str:
    with urllib.request.urlopen(url, timeout=30) as r:  # noqa: S310
        return r.read().decode("utf-8", errors="replace")


def analizar_datos(repo: str) -> dict:
    texto = descargar(f"https://raw.githubusercontent.com/{repo}/HEAD/meteo_daily.csv")
    filas = list(csv.DictReader(io.StringIO(texto)))
    claves = {k.lower(): k for k in (filas[0].keys() if filas else [])}
    col_tipo = claves.get("tipodato") or claves.get("tipo")
    col_fuente = claves.get("fuente")
    fechas, observados, fuentes = [], 0, {}
    for f in filas:
        try:
            dia = date.fromisoformat(str(f.get("Fecha", "")).strip()[:10])
        except ValueError:
            continue
        tipo = str(f.get(col_tipo, "")).strip().lower() if col_tipo else ""
        if tipo.startswith("pron") and dia > HOY:
            continue  # días de pronóstico futuro: no cuentan como carga
        fechas.append(dia)
        fuente = str(f.get(col_fuente, "")).strip() if col_fuente else ""
        fuentes[fuente] = fuentes.get(fuente, 0) + 1
        if tipo == "observado" or fuente.upper().startswith("SIGA"):
            observados += 1
    if not fechas:
        raise ValueError("meteo_daily.csv sin fechas válidas")
    principal = max(fuentes, key=fuentes.get) if fuentes else ""
    return {
        "ultima_fecha": max(fechas).isoformat(),
        "dias": len(fechas),
        "pct_observado": round(100 * observados / len(fechas)),
        "fuente_principal": principal,
    }


def fecha_esperada() -> date:
    fin = date(HOY.year, *FIN_CAMPANIA)
    if HOY >= fin:
        return fin                                   # campaña cerrada: datos completos hasta el 1/10
    return HOY - timedelta(days=TOLERANCIA_DIAS)     # campaña en curso: casi al día


def describir_fuente(fuente: str) -> str:
    f = fuente.upper()
    if f.startswith("SIGA"):
        return "estación SIGA–INTA"
    if "ERA5" in f:
        return "reanálisis ERA5"
    if "METEOBAHIA" in f:
        return "pronósticos MeteoBahía archivados"
    if "ECMWF" in f:
        return "modelo ECMWF"
    return fuente or "sin dato"


def main() -> None:
    carpeta = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    respondio = leer_resultados(carpeta)
    esperada = fecha_esperada()
    salida = {
        "generado": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fecha_esperada": esperada.isoformat(),
        "apps": {},
    }
    for app in apps_del_mapa():
        info: dict = {"repo": app["repo"], "app_responde": respondio.get(app["nombre"], True)}
        try:
            info.update(analizar_datos(app["repo"]))
            info["fuente"] = describir_fuente(info.pop("fuente_principal"))
            al_dia = date.fromisoformat(info["ultima_fecha"]) >= esperada
            if not info["app_responde"]:
                info["estado"] = "caida"
            elif not al_dia:
                info["estado"] = "desactualizada"
            elif info["pct_observado"] < MIN_OBSERVADOS * 100:
                info["estado"] = "estimada"
            else:
                info["estado"] = "ok"
        except Exception as error:  # noqa: BLE001
            info["estado"] = "caida" if not info["app_responde"] else "desactualizada"
            info["error"] = f"{type(error).__name__}: {error}"[:200]
        salida["apps"][app["nombre"]] = info
        print(f"{app['nombre']}: {info['estado']} {info.get('ultima_fecha', '')} {info.get('pct_observado', '')}%")
    SALIDA.write_text(json.dumps(salida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
