"""
etl/scheduled.py
----------------
Job incremental de actualizacion del dataset.

Diferencia con finalInfoScript.py:
    - finalInfoScript.py hace una descarga completa desde cero (5 anios).
      Sirve para el bootstrap inicial.
    - scheduled.py descarga UNICAMENTE los dias que faltan respecto al
      ultimo dia ya cargado en MongoDB. Sirve para correr a diario via
      systemd timer o cron.

Flujo:
    1. Conectarse a Mongo y leer la maxima fecha ya cargada por activo.
    2. Calcular el rango pendiente: desde min(maximas) + 1 hasta hoy.
    3. Si el rango esta vacio, salir 0 (no hay nada que hacer).
    4. Descargar BVC + Yahoo solo en ese rango.
    5. Upsert idempotente a Mongo (bulk_write con $set por fecha).
    6. Loggear resumen en stdout (lo recoge systemd journal).

Uso:
    python -m etl.scheduled

Codigos de salida:
    0  -> exito (con o sin nuevos datos)
    1  -> error fatal (conexion Mongo, etc.)
"""

from __future__ import annotations

import os
import sys
import time
import json
from datetime import date, datetime, timedelta
from pathlib import Path

# Carga del .env antes de importar otras cosas que usan os.environ.
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except ImportError:
    # python-dotenv puede no estar; .env siempre se puede sourcear desde la
    # unidad systemd con EnvironmentFile.
    pass

from pymongo import UpdateOne

# Hacemos el import de forma robusta cuando se llama con `python -m etl.scheduled`.
try:
    from etl.finalInfoScript import (
        BVC_ASSETS,
        YAHOO_ASSETS,
        descargar_bvc_rango,
        descargar_yahoo_rango,
    )
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from etl.finalInfoScript import (  # type: ignore  # noqa: E402
        BVC_ASSETS,
        YAHOO_ASSETS,
        descargar_bvc_rango,
        descargar_yahoo_rango,
    )

try:
    from database import get_client, MONGO_DB_NAME
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from database import get_client, MONGO_DB_NAME  # type: ignore  # noqa: E402


# ---------------------------------------------------------------------------
# Calculo del rango pendiente
# ---------------------------------------------------------------------------

def _nombre_coleccion(mnemonic: str) -> str:
    return f"historico_{mnemonic.lower()}"


def ultima_fecha_cargada(db, mnemonic: str):
    """
    Devuelve la fecha mas reciente cargada en la coleccion del activo, o
    None si la coleccion esta vacia. La fecha se devuelve como str
    'AAAA-MM-DD' (formato usado en los documentos).
    """
    coleccion = db[_nombre_coleccion(mnemonic)]
    documento = coleccion.find_one(
        {}, projection={"date": 1, "_id": 0}, sort=[("date", -1)]
    )
    if documento is None:
        return None
    return documento.get("date")


LOOKBACK_DIAS = 7  # ventana hacia atras del maximo para tolerar feriados


def calcular_rango_pendiente(db, mnemonicos, modo="max_lookback"):
    """
    Calcula el rango [inicio, fin] de dias que falta descargar.

    Parametros:
        modo:
            "max_lookback" (default, uso diario en cron):
                inicio = max(ultima_fecha_cargada) - LOOKBACK_DIAS.
                Cron rapido (~30s). Tolera feriados, no arrastra gaps
                de activos delistados.
            "catchup" (uso manual):
                inicio = min(ultima_fecha_cargada).
                Atrapa cualquier activo atrasado, incluso si lleva meses
                sin actualizarse. Activos delistados re-intentaran su
                rango muerto (fallan rapido, no corrompen datos) pero
                aumentan el tiempo de descarga proporcionalmente.

    fin siempre es la fecha de hoy.

    Si todos los activos ya tienen el dato de hoy y no hay vacios, devuelve None.
    """
    fechas_maximas = []
    activos_vacios = []
    for ticker in mnemonicos:
        ultima = ultima_fecha_cargada(db, ticker)
        if ultima is None:
            activos_vacios.append(ticker)
        else:
            fechas_maximas.append(ultima)

    hoy = date.today()

    if len(fechas_maximas) == 0:
        inicio = hoy - timedelta(days=5 * 365)
        return inicio, hoy, activos_vacios

    if modo == "catchup":
        referencia = min(fechas_maximas)
        inicio = datetime.strptime(referencia, "%Y-%m-%d").date() + timedelta(days=1)
        if inicio > hoy and len(activos_vacios) == 0:
            return None
        return inicio, hoy, activos_vacios

    # Default: max_lookback
    maxima = max(fechas_maximas)
    inicio_estimado = datetime.strptime(maxima, "%Y-%m-%d").date() + timedelta(days=1)
    inicio = inicio_estimado - timedelta(days=LOOKBACK_DIAS)
    if inicio > hoy:
        return None
    if inicio_estimado > hoy and len(activos_vacios) == 0:
        return None
    return inicio, hoy, activos_vacios


# ---------------------------------------------------------------------------
# Upsert a Mongo
# ---------------------------------------------------------------------------

def upsert_registros(coleccion, registros):
    """
    bulk_write idempotente por fecha. Devuelve (upserted, modified).
    """
    if not registros:
        return 0, 0
    operaciones = []
    for r in registros:
        fecha = r.get("date")
        if not fecha:
            continue
        operaciones.append(
            UpdateOne({"date": fecha}, {"$set": r}, upsert=True)
        )
    if not operaciones:
        return 0, 0
    resultado = coleccion.bulk_write(operaciones, ordered=False)
    return resultado.upserted_count, resultado.modified_count


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Actualizacion incremental de MongoDB.")
    parser.add_argument(
        "--catchup",
        action="store_true",
        help="Modo catch-up: descarga desde la fecha MINIMA por activo en lugar "
             "de un lookback fijo. Util para sincronizar activos muy atrasados.",
    )
    args = parser.parse_args()
    modo = "catchup" if args.catchup else "max_lookback"

    inicio_run = time.time()
    print(f"[{datetime.utcnow().isoformat()}Z] scheduled.py iniciado (modo={modo})")

    try:
        cliente = get_client()
        db = cliente[MONGO_DB_NAME]
    except Exception as exc:
        print(f"[ERROR] no se pudo conectar a MongoDB: {exc}", file=sys.stderr)
        return 1

    mnemonicos_bvc = [a["mnemonic"] for a in BVC_ASSETS]
    mnemonicos_todos = mnemonicos_bvc + list(YAHOO_ASSETS)

    rango = calcular_rango_pendiente(db, mnemonicos_todos, modo=modo)
    if rango is None:
        elapsed = time.time() - inicio_run
        print(f"Nada que descargar: todas las series estan al dia.  ({elapsed:.2f}s)")
        return 0

    inicio, fin, activos_vacios = rango
    print(f"Rango pendiente: {inicio} -> {fin}")
    if activos_vacios:
        print(f"Activos sin datos previos (cold start): {activos_vacios}")

    # Descarga BVC
    print(f"[BVC] descargando rango...")
    t0 = time.time()
    bvc_resultados = descargar_bvc_rango(inicio, fin)
    t_bvc = time.time() - t0
    print(f"[BVC] descarga lista en {t_bvc:.1f}s")

    # Descarga Yahoo
    print(f"[Yahoo] descargando rango...")
    t0 = time.time()
    yahoo_resultados = descargar_yahoo_rango(inicio, fin)
    t_yahoo = time.time() - t0
    print(f"[Yahoo] descarga lista en {t_yahoo:.1f}s")

    # Upsert
    total_upserted = 0
    total_modified = 0

    for mnemonic, registros in bvc_resultados.items():
        coleccion = db[_nombre_coleccion(mnemonic)]
        up, mod = upsert_registros(coleccion, registros)
        total_upserted += up
        total_modified += mod
        if up + mod > 0:
            print(f"  BVC   {mnemonic:<12} +{up} nuevos, ~{mod} actualizados")

    for ticker, registros in yahoo_resultados.items():
        coleccion = db[_nombre_coleccion(ticker)]
        up, mod = upsert_registros(coleccion, registros)
        total_upserted += up
        total_modified += mod
        if up + mod > 0:
            print(f"  Yahoo {ticker:<12} +{up} nuevos, ~{mod} actualizados")

    elapsed = time.time() - inicio_run

    resumen = {
        "fecha_run_utc": datetime.utcnow().isoformat() + "Z",
        "rango": {"inicio": inicio.isoformat(), "fin": fin.isoformat()},
        "activos_cold_start": activos_vacios,
        "upserted": total_upserted,
        "modified": total_modified,
        "duracion_segundos": round(elapsed, 2),
    }
    print(json.dumps(resumen, ensure_ascii=False, indent=2))
    print(f"OK en {elapsed:.2f}s")

    cliente.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
