"""
Coeficiente de correlacion de Pearson entre dos series de tiempo.

Implementacion manual usando solo estructuras basicas del lenguaje (listas,
bucles, condicionales y operaciones aritmeticas). No se usan funciones
especializadas de librerias externas como numpy.corrcoef.
"""

import math


def _media(valores):
    """Media aritmetica manual de una lista de numeros."""
    if len(valores) == 0:
        return 0.0
    suma = 0.0
    for v in valores:
        suma = suma + v
    return suma / len(valores)


def correlacion_pearson(serie_a, serie_b):
    """
    Coeficiente de correlacion de Pearson entre dos series.

    Definicion matematica:

        r = sum( (a_i - media_a) * (b_i - media_b) )
            / ( sqrt( sum( (a_i - media_a)^2 ) ) * sqrt( sum( (b_i - media_b)^2 ) ) )

    Interpretacion:
        - r =  1  : correlacion lineal positiva perfecta.
        - r =  0  : no hay relacion lineal.
        - r = -1  : correlacion lineal negativa perfecta.

    Asume alineacion temporal perfecta entre las dos series.

    Pasos:
        1. Calcular la media de cada serie.
        2. Acumular tres sumas:
              - numerador: sum( (a_i - mu_a) * (b_i - mu_b) )
              - sumcuad_a: sum( (a_i - mu_a)^2 )
              - sumcuad_b: sum( (b_i - mu_b)^2 )
        3. Devolver numerador / (sqrt(sumcuad_a) * sqrt(sumcuad_b)).

    Complejidad:
        Tiempo : O(n) (dos pasadas: una para la media, otra para las sumas).
        Espacio: O(1).

    Casos especiales:
        Si la varianza de alguna de las dos series es 0 (todos los valores
        iguales), la correlacion no esta definida; se devuelve 0.0.
    """
    if len(serie_a) != len(serie_b):
        raise ValueError(
            "Las series deben tener la misma longitud para Pearson."
        )
    if len(serie_a) == 0:
        return 0.0

    media_a = _media(serie_a)
    media_b = _media(serie_b)

    numerador = 0.0
    sumcuad_a = 0.0
    sumcuad_b = 0.0
    indice = 0
    while indice < len(serie_a):
        diferencia_a = serie_a[indice] - media_a
        diferencia_b = serie_b[indice] - media_b
        numerador = numerador + diferencia_a * diferencia_b
        sumcuad_a = sumcuad_a + diferencia_a * diferencia_a
        sumcuad_b = sumcuad_b + diferencia_b * diferencia_b
        indice = indice + 1

    if sumcuad_a == 0.0 or sumcuad_b == 0.0:
        return 0.0

    return numerador / (math.sqrt(sumcuad_a) * math.sqrt(sumcuad_b))
