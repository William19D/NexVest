"""
routers/_carga.py
-----------------
Funciones de soporte para los endpoints de analisis. Cargan series
historicas desde MongoDB y las normalizan al formato que esperan los
modulos de algorithms/ (lista de dicts con 'fecha' como cadena
'AAAA-MM-DD' y 'close' como float).

Las colecciones en Mongo siguen la convencion 'historico_<mnemonic>'.
Los documentos pueden traer 'close' como cadena (BVC) o como float
(Yahoo), por eso cada lectura normaliza el tipo antes de devolverla.

Cargas con limpieza: las funciones cargar_serie y cargar_portafolio
aceptan un flag 'limpiar' (por defecto True) para descartar filas
inconsistentes (close <= 0, fechas duplicadas, retornos extremos) antes
de devolver la serie. La limpieza se delega al paquete etl.limpieza.
"""

from typing import Optional

from etl.limpieza import limpiar_serie as _limpiar_serie


def _close_a_float(valor):
    """Convierte el campo close a float aceptando cadenas o numeros."""
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return float(valor)
    if isinstance(valor, str):
        limpio = valor.strip().replace(",", "")
        if not limpio:
            return None
        try:
            return float(limpio)
        except ValueError:
            return None
    return None


def _ohlc_a_float(documento):
    """Convierte open/high/low/close a float si vienen como cadena."""
    salida = {}
    for clave_origen, clave_destino in [
        ("open", "open"),
        ("high", "high"),
        ("low", "low"),
        ("close", "close"),
    ]:
        salida[clave_destino] = _close_a_float(documento.get(clave_origen))
    return salida


def coleccion_de(mnemonic):
    """Convierte un mnemonico al nombre de coleccion de Mongo."""
    return f"historico_{mnemonic.lower()}"


def listar_mnemonicos(db):
    """Devuelve la lista de mnemonicos disponibles en mayusculas."""
    salida = []
    for nombre_coleccion in db.list_collection_names():
        if nombre_coleccion.startswith("historico_"):
            salida.append(nombre_coleccion.replace("historico_", "").upper())
    salida.sort()
    return salida


def cargar_serie(db, mnemonic, desde=None, hasta=None, limpiar=True):
    """
    Carga una serie historica para un mnemonico desde MongoDB y la
    normaliza al formato esperado por los algoritmos.

    Parametros:
        db       : base de datos MongoDB.
        mnemonic : ticker (insensible a mayusculas).
        desde    : fecha inclusiva 'AAAA-MM-DD' o None.
        hasta    : fecha inclusiva 'AAAA-MM-DD' o None.
        limpiar  : si True, se aplica etl.limpieza.limpiar_serie sobre la
                   serie antes de devolverla. Activado por defecto para
                   evitar que filas con close <= 0 o duplicadas afecten
                   los algoritmos posteriores.

    Devuelve una lista de dicts ordenada ascendentemente por fecha con
    las claves: fecha, open, high, low, close, volumen.

    Lanza ValueError si la coleccion no existe.
    """
    nombre_coleccion = coleccion_de(mnemonic)
    if nombre_coleccion not in db.list_collection_names():
        raise ValueError(
            f"No se encontro historico para '{mnemonic.upper()}'."
        )

    filtro = {}
    if desde is not None or hasta is not None:
        filtro["date"] = {}
        if desde is not None:
            filtro["date"]["$gte"] = desde
        if hasta is not None:
            filtro["date"]["$lte"] = hasta

    cursor = db[nombre_coleccion].find(filtro, {"_id": 0}).sort("date", 1)

    serie = []
    for documento in cursor:
        fecha = documento.get("date")
        precio_cierre = _close_a_float(documento.get("close"))
        if fecha is None or precio_cierre is None:
            continue

        ohlc = _ohlc_a_float(documento)
        volumen = documento.get("volume")
        if volumen is None:
            volumen = documento.get("volumen")

        fila = {
            "fecha": fecha,
            "open": ohlc["open"],
            "high": ohlc["high"],
            "low": ohlc["low"],
            "close": precio_cierre,
            "volumen": volumen,
        }
        serie.append(fila)

    if limpiar and len(serie) > 0:
        serie, _ = _limpiar_serie(serie, ticker=mnemonic.upper())

    return serie


def cargar_portafolio(db, mnemonicos=None, desde=None, hasta=None, limpiar=True):
    """
    Carga un grupo de series historicas y devuelve un diccionario
    { ticker: serie }. Si 'mnemonicos' es None, se cargan todos los
    disponibles en la base.

    El parametro 'limpiar' se propaga a cada cargar_serie.
    """
    if mnemonicos is None:
        mnemonicos = listar_mnemonicos(db)

    portafolio = {}
    for mnemonic in mnemonicos:
        try:
            serie = cargar_serie(
                db, mnemonic, desde=desde, hasta=hasta, limpiar=limpiar
            )
        except ValueError:
            continue
        if len(serie) > 0:
            portafolio[mnemonic.upper()] = serie
    return portafolio
