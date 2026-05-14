"""
reportes/generador.py
---------------------
Punto de entrada de alto nivel para construir el reporte PDF.

Responsabilidades:
    1. Cargar los datos crudos y limpios desde la base.
    2. Pedirle al modulo de algoritmos los calculos (matriz de
       correlacion, ranking de riesgo).
    3. Pedirle al modulo de graficos las imagenes PNG.
    4. Pedirle al modulo pdf_builder que ensamble el documento.

No contiene logica de calculo; solo orquesta.
"""

from algorithms import similitud as alg_similitud
from algorithms import volatilidad as alg_volatilidad
from etl.limpieza import limpiar_serie

from reportes.graficos import (
    grafico_candlestick,
    grafico_heatmap_correlacion,
)
from reportes.pdf_builder import construir_pdf
from routers._carga import cargar_portafolio, cargar_serie


def _matriz_correlacion(portafolio, base="retorno"):
    """
    Calcula la matriz de correlacion de Pearson entre todos los activos
    del portafolio.

    Devuelve (activos_ordenados, matriz_valores).
    """
    activos = sorted(portafolio.keys())
    n = len(activos)
    matriz = []
    i = 0
    while i < n:
        fila = []
        j = 0
        while j < n:
            if i == j:
                fila.append(1.0)
            else:
                _, valores_i, valores_j = alg_similitud.alinear_por_fechas(
                    portafolio[activos[i]],
                    portafolio[activos[j]],
                )
                if base == "retorno":
                    valores_i = alg_similitud.calcular_retornos(valores_i)
                    valores_j = alg_similitud.calcular_retornos(valores_j)
                if len(valores_i) < 2:
                    fila.append(0.0)
                else:
                    fila.append(
                        alg_similitud.correlacion_pearson(
                            valores_i, valores_j
                        )
                    )
            j = j + 1
        matriz.append(fila)
        i = i + 1
    return activos, matriz


def _candlesticks(db, tickers_candle, desde, hasta):
    """
    Para cada ticker en 'tickers_candle' carga la serie con OHLC y
    genera el PNG del candlestick + SMA. Devuelve una lista de pares
    (ticker, bytes_png).
    """
    resultado = []
    for ticker in tickers_candle:
        try:
            serie = cargar_serie(db, ticker, desde=desde, hasta=hasta)
        except ValueError:
            continue
        if len(serie) == 0:
            continue
        png = grafico_candlestick(serie, ticker)
        resultado.append((ticker, png))
    return resultado


def _reportes_limpieza(db, mnemonicos):
    """
    Carga cada activo sin limpiar y obtiene un reporte de cuantas filas
    habrian sido descartadas. Sirve solo para el apendice del PDF.
    """
    reportes = []
    for ticker in mnemonicos:
        try:
            serie_cruda = cargar_serie(db, ticker, limpiar=False)
        except ValueError:
            continue
        _, reporte = limpiar_serie(serie_cruda, ticker=ticker)
        reportes.append(reporte.to_dict())
    return reportes


def generar_reporte_portafolio(
    db,
    tickers=None,
    tickers_candle=None,
    desde=None,
    hasta=None,
    base_correlacion="retorno",
):
    """
    Genera el PDF y devuelve sus bytes.

    Parametros:
        db              : base de datos MongoDB.
        tickers         : lista de mnemonicos a incluir; None para todos.
        tickers_candle  : subconjunto a graficar como candlestick.
                          Por defecto, los primeros 3 del portafolio.
        desde, hasta    : filtros de fecha 'AAAA-MM-DD' o None.
        base_correlacion: 'precio' o 'retorno' (recomendado).
    """
    portafolio = cargar_portafolio(
        db, mnemonicos=tickers, desde=desde, hasta=hasta
    )
    if len(portafolio) < 2:
        raise ValueError(
            "Se requieren al menos dos activos con datos para generar "
            "el reporte."
        )

    # Calculo de matriz de correlacion.
    activos_corr, matriz = _matriz_correlacion(
        portafolio, base=base_correlacion
    )
    heatmap_png = grafico_heatmap_correlacion(
        activos_corr, matriz, titulo="Matriz de Correlacion (Pearson)"
    )

    # Ranking de riesgo.
    clasificacion = alg_volatilidad.clasificar_portafolio(portafolio)

    # Candlesticks: por defecto los 3 primeros del portafolio ordenado.
    if tickers_candle is None:
        tickers_candle = activos_corr[:3]
    candlesticks = _candlesticks(db, tickers_candle, desde, hasta)

    # Apendice de limpieza.
    reportes_limp = _reportes_limpieza(db, activos_corr)

    parametros = {
        "Base correlacion": base_correlacion,
        "Desde": desde or "(toda la historia)",
        "Hasta": hasta or "(toda la historia)",
        "Total activos": str(len(activos_corr)),
        "Candlesticks": ", ".join(tickers_candle) if tickers_candle else "(ninguno)",
    }

    pdf_bytes = construir_pdf(
        titulo="NexVest - Reporte Tecnico de Portafolio",
        parametros=parametros,
        activos_portafolio=activos_corr,
        matriz_correlacion_png=heatmap_png,
        activos_correlacion=activos_corr,
        matriz_valores=matriz,
        ranking_riesgo=clasificacion["ranking"],
        candlesticks_png=candlesticks,
        reportes_limpieza=reportes_limp,
    )
    return pdf_bytes
