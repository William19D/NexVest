"""
Distancia euclidiana entre dos series de tiempo financieras.

Implementacion manual usando solo estructuras basicas del lenguaje (listas,
bucles, condicionales y operaciones aritmeticas). No se usan funciones
especializadas de librerias externas.
"""

import math


def distancia_euclidiana(serie_a, serie_b):
    """
    Distancia euclidiana entre dos series de igual longitud.

    Definicion matematica:

        d(A, B) = sqrt( sum_{i=0..n-1} (a_i - b_i)^2 )

    Interpretacion:
        Es la distancia 'en linea recta' entre los dos vectores en R^n. A
        menor valor, mas parecidas son las series punto a punto. La
        distancia es 0 si y solo si las dos series son identicas.

    Limitaciones:
        - Es muy sensible a la escala de los datos. Conviene normalizar o
          aplicarla sobre retornos en lugar de precios crudos.
        - Asume alineacion temporal perfecta: el dia i de A se compara con
          el dia i de B.

    Pasos:
        1. Verificar que las dos series tienen la misma longitud.
        2. Acumular la suma de cuadrados de las diferencias.
        3. Devolver la raiz cuadrada de la suma.

    Complejidad:
        Tiempo : O(n).
        Espacio: O(1).
    """
    if len(serie_a) != len(serie_b):
        raise ValueError(
            "Las series deben tener la misma longitud para la distancia "
            "euclidiana. Use alinear_por_fechas antes."
        )

    suma_cuadrados = 0.0
    indice = 0
    while indice < len(serie_a):
        diferencia = serie_a[indice] - serie_b[indice]
        suma_cuadrados = suma_cuadrados + diferencia * diferencia
        indice = indice + 1

    return math.sqrt(suma_cuadrados)
