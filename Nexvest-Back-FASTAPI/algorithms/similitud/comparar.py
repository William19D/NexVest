"""
Funcion de alto nivel que aplica los cuatro algoritmos de similitud sobre
los historicos de dos activos.
"""

from .utilidades import alinear_por_fechas, calcular_retornos
from .euclidiana import distancia_euclidiana
from .pearson import correlacion_pearson
from .dtw import dynamic_time_warping
from .coseno import similitud_coseno


def comparar_activos(historico_a, historico_b, base="precio", ventana_dtw=None):
    """
    Aplica los cuatro algoritmos de similitud sobre dos historicos.

    Parametros:
        historico_a, historico_b: listas de dicts con 'fecha' y 'close'.
        base: 'precio' para comparar precios de cierre,
              'retorno' para comparar retornos diarios simples.
        ventana_dtw: tamano de banda Sakoe-Chiba para DTW (None = sin banda).

    Devuelve un diccionario con los cuatro valores y la cantidad de puntos
    comunes despues de la alineacion por fechas.

    Pasos:
        1. Alinear las dos series por fechas comunes.
        2. Si base == 'retorno', convertir precios a retornos.
        3. Calcular las cuatro metricas y devolverlas.
    """
    fechas, valores_a, valores_b = alinear_por_fechas(historico_a, historico_b)

    if base == "retorno":
        valores_a = calcular_retornos(valores_a)
        valores_b = calcular_retornos(valores_b)

    return {
        "puntos_comunes": len(valores_a),
        "base": base,
        "euclidiana": distancia_euclidiana(valores_a, valores_b),
        "pearson": correlacion_pearson(valores_a, valores_b),
        "dtw": dynamic_time_warping(valores_a, valores_b, ventana=ventana_dtw),
        "coseno": similitud_coseno(valores_a, valores_b),
    }
