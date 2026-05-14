"""
Similitud por coseno entre dos vectores.

Implementacion manual usando solo estructuras basicas del lenguaje (listas,
bucles, condicionales y operaciones aritmeticas). No se usan funciones
especializadas de librerias externas como sklearn.metrics.pairwise.
"""

import math


def similitud_coseno(vector_a, vector_b):
    """
    Similitud por coseno entre dos vectores de igual longitud.

    Definicion matematica:

        cos(A, B) = ( sum_{i} a_i * b_i )
                    / ( sqrt(sum_{i} a_i^2) * sqrt(sum_{i} b_i^2) )

    Interpretacion:
        Es el coseno del angulo entre los dos vectores en R^n. No depende
        de la magnitud, solo de la 'direccion':
            - cos =  1  : misma direccion (vectores paralelos).
            - cos =  0  : ortogonales (no comparten direccion).
            - cos = -1  : direcciones opuestas.

        En el contexto financiero se suele aplicar sobre vectores de
        retornos diarios: indica si dos activos suben y bajan juntos o se
        mueven en sentidos opuestos, sin que importe la magnitud absoluta.

    Pasos:
        1. Acumular tres sumas: producto punto y las dos sumas de cuadrados.
        2. Si alguna norma es 0, no esta definida; devolver 0.0.
        3. Devolver producto punto dividido por el producto de las normas.

    Complejidad:
        Tiempo : O(n).
        Espacio: O(1).
    """
    if len(vector_a) != len(vector_b):
        raise ValueError(
            "Los vectores deben tener la misma longitud para la similitud "
            "por coseno."
        )
    if len(vector_a) == 0:
        return 0.0

    producto_punto = 0.0
    suma_cuad_a = 0.0
    suma_cuad_b = 0.0
    indice = 0
    while indice < len(vector_a):
        a = vector_a[indice]
        b = vector_b[indice]
        producto_punto = producto_punto + a * b
        suma_cuad_a = suma_cuad_a + a * a
        suma_cuad_b = suma_cuad_b + b * b
        indice = indice + 1

    if suma_cuad_a == 0.0 or suma_cuad_b == 0.0:
        return 0.0

    return producto_punto / (math.sqrt(suma_cuad_a) * math.sqrt(suma_cuad_b))
