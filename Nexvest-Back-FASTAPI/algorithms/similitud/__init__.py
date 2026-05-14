"""
Algoritmos de similitud entre series de tiempo financieras.

Este paquete implementa los cuatro algoritmos exigidos por el proyecto,
cada uno en su propio modulo:

    1. Distancia euclidiana       -> euclidiana.py
    2. Correlacion de Pearson     -> pearson.py
    3. Dynamic Time Warping (DTW) -> dtw.py
    4. Similitud por coseno       -> coseno.py

Ademas:
    - utilidades.py : alineacion por fechas y calculo de retornos.
    - comparar.py   : funcion de alto nivel que aplica los cuatro algoritmos.

Todos los algoritmos estan implementados de forma manual usando solo
estructuras basicas del lenguaje (listas, bucles, condicionales y operaciones
aritmeticas). No se usan funciones especializadas de librerias externas como
numpy.corrcoef, scipy.spatial.distance, sklearn.metrics o similares.

Convenciones:
    - Las series de entrada son listas de numeros reales (floats).
    - Cuando se trabaja sobre precios, la serie es la sucesion de precios de
      cierre. Cuando se trabaja sobre retornos, se calculan los retornos
      simples a partir de los precios usando la funcion calcular_retornos.
    - Antes de comparar dos series, conviene alinearlas por fechas comunes
      con alinear_por_fechas, para evitar comparar dias que solo existen en
      uno de los mercados (festivos diferentes, suspensiones, etc.).
"""

from .utilidades import alinear_por_fechas, calcular_retornos
from .euclidiana import distancia_euclidiana
from .pearson import correlacion_pearson
from .dtw import dynamic_time_warping
from .coseno import similitud_coseno
from .comparar import comparar_activos

__all__ = [
    "alinear_por_fechas",
    "calcular_retornos",
    "distancia_euclidiana",
    "correlacion_pearson",
    "dynamic_time_warping",
    "similitud_coseno",
    "comparar_activos",
]
