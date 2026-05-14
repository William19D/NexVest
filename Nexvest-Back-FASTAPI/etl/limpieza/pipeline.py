"""
etl/limpieza/pipeline.py
------------------------
Orquesta el flujo de limpieza:
    1. Detectar problemas con etl/limpieza/deteccion.py.
    2. Aplicar la estrategia elegida usando etl/limpieza/correccion.py.
    3. Devolver la serie limpia + un ReporteLimpieza.

La idea es mantener este archivo corto: aqui solo se decide el orden y la
politica; el calculo real esta en los modulos especializados.
"""

from etl.limpieza.correccion import eliminar_indices, forward_fill_close
from etl.limpieza.deteccion import (
    detectar_close_no_positivo,
    detectar_fechas_duplicadas,
    detectar_outliers_retorno_zscore,
    detectar_retornos_extremos_absolutos,
)
from etl.limpieza.reporte import ReporteLimpieza


ESTRATEGIAS_VALIDAS = ("eliminar", "forward_fill")


def _eliminar_outliers_iterativo(serie, umbral_z, umbral_abs, max_pasadas):
    """
    Elimina outliers de retorno aplicando dos detectores complementarios:

        1. detectar_outliers_retorno_zscore : detecta dias anomalos
           relativos al comportamiento tipico de la propia serie.
        2. detectar_retornos_extremos_absolutos : detecta dias con saltos
           que en valor absoluto son irreales (cambios de regimen,
           splits no ajustados).

    En cada pasada se acumulan los indices marcados por cualquiera de los
    dos detectores y se eliminan. El proceso se repite hasta que ya no
    haya filas marcadas (o hasta agotar 'max_pasadas'). El bucle es
    necesario por el efecto de enmascaramiento del z-score: al quitar un
    outlier la desviacion estandar baja y aparecen otros que antes
    quedaban escondidos.

    Devuelve (serie_sin_outliers, total_outliers_eliminados, pasadas).
    """
    actual = serie
    total = 0
    pasadas = 0
    while pasadas < max_pasadas:
        indices_z = detectar_outliers_retorno_zscore(actual, umbral=umbral_z)
        indices_abs = detectar_retornos_extremos_absolutos(
            actual, umbral_absoluto=umbral_abs
        )
        # Union de indices (sin duplicar).
        indices = list(set(indices_z) | set(indices_abs))
        if len(indices) == 0:
            break
        actual = eliminar_indices(actual, indices)
        total = total + len(indices)
        pasadas = pasadas + 1
    return actual, total, pasadas


def limpiar_serie(
    serie,
    ticker=None,
    estrategia="eliminar",
    umbral_zscore=6.0,
    umbral_retorno_absoluto=0.5,
    detectar_outliers=True,
    max_pasadas_outliers=5,
):
    """
    Limpia una serie historica y devuelve (serie_limpia, reporte).

    Parametros:
        serie               : lista de dicts con 'fecha' y 'close' (float).
        ticker              : identificador para el reporte (opcional).
        estrategia          : 'eliminar' (descarta filas problematicas) o
                              'forward_fill' (mantiene la fila pero copia el
                              close del dia anterior valido).
        umbral_zscore       : umbral del z-score para outliers de retorno.
        detectar_outliers   : si False, no se aplica deteccion por z-score
                              (util para inspeccion previa o pruebas).
        max_pasadas_outliers: numero maximo de pasadas iterativas de
                              eliminacion de outliers. Limita el caso
                              extremo en que la serie completa colapsara.

    Pasos:
        1. Detectar y eliminar (o rellenar) filas con close <= 0.
        2. Detectar y eliminar fechas duplicadas (se eliminan SIEMPRE,
           sin importar la estrategia).
        3. Si detectar_outliers, ejecutar deteccion iterativa por z-score
           hasta que ya no haya outliers (o hasta max_pasadas_outliers).
        4. Devolver la serie resultante y el reporte.
    """
    if estrategia not in ESTRATEGIAS_VALIDAS:
        raise ValueError(
            f"Estrategia desconocida '{estrategia}'. "
            f"Validas: {ESTRATEGIAS_VALIDAS}."
        )

    indices_cero = detectar_close_no_positivo(serie)
    indices_duplicados = detectar_fechas_duplicadas(serie)

    if estrategia == "eliminar":
        a_eliminar_iniciales = list(indices_cero)
        a_eliminar_iniciales.extend(indices_duplicados)
        serie_paso1 = eliminar_indices(serie, a_eliminar_iniciales)
    else:  # forward_fill
        # Primero rellenamos los close <= 0 con el cierre anterior valido,
        # luego eliminamos duplicados (que son inconsistencias).
        serie_rellena = forward_fill_close(serie, indices_cero)
        serie_paso1 = eliminar_indices(serie_rellena, indices_duplicados)

    if detectar_outliers:
        serie_limpia, total_outliers, _ = _eliminar_outliers_iterativo(
            serie_paso1,
            umbral_z=umbral_zscore,
            umbral_abs=umbral_retorno_absoluto,
            max_pasadas=max_pasadas_outliers,
        )
        # Verificar si quedaron retornos extremos despues del corte.
        residuales = detectar_retornos_extremos_absolutos(
            serie_limpia, umbral_absoluto=umbral_retorno_absoluto
        )
        outliers_residuales = len(residuales)
        convergencia = outliers_residuales == 0
    else:
        serie_limpia = serie_paso1
        total_outliers = 0
        outliers_residuales = 0
        convergencia = True

    reporte = ReporteLimpieza(
        ticker=ticker,
        filas_entrada=len(serie),
        filas_salida=len(serie_limpia),
        close_no_positivo=len(indices_cero),
        outliers_zscore=total_outliers,
        fechas_duplicadas=len(indices_duplicados),
        estrategia=estrategia,
        umbral_zscore=umbral_zscore,
        outliers_residuales=outliers_residuales,
        convergencia=convergencia,
    )
    return serie_limpia, reporte


def limpiar_portafolio(
    portafolio,
    estrategia="eliminar",
    umbral_zscore=6.0,
    detectar_outliers=True,
):
    """
    Aplica limpiar_serie a cada activo del portafolio.

    Parametros:
        portafolio: dict { ticker: serie }.

    Devuelve:
        (portafolio_limpio, reportes) donde 'reportes' es una lista de
        diccionarios con la informacion devuelta por cada limpieza.
    """
    portafolio_limpio = {}
    reportes = []
    for ticker in portafolio:
        serie_limpia, reporte = limpiar_serie(
            portafolio[ticker],
            ticker=ticker,
            estrategia=estrategia,
            umbral_zscore=umbral_zscore,
            detectar_outliers=detectar_outliers,
        )
        portafolio_limpio[ticker] = serie_limpia
        reportes.append(reporte.to_dict())
    return portafolio_limpio, reportes
