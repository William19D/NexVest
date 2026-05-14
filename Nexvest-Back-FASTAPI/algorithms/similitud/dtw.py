"""
Dynamic Time Warping (DTW) entre dos series de tiempo.

Implementacion manual usando programacion dinamica y solo estructuras basicas
del lenguaje (listas, bucles, condicionales y operaciones aritmeticas). No se
usan librerias externas como scipy o fastdtw.
"""

import math


def dynamic_time_warping(serie_a, serie_b, ventana=None):
    """
    Dynamic Time Warping (DTW).

    Idea:
        Mide la similitud entre dos secuencias temporales que pueden estar
        desfasadas o tener velocidades distintas. En vez de comparar el dia
        i de A con el dia i de B, busca el 'alineamiento' optimo entre las
        dos series usando programacion dinamica.

    Definicion matematica:
        Sea D una matriz (n+1) x (m+1) inicializada con infinito, salvo
        D[0][0] = 0. Para i = 1..n y j = 1..m:

            costo  = (a_{i-1} - b_{j-1})^2
            D[i][j] = costo + min( D[i-1][j],     # supresion en A
                                   D[i][j-1],     # supresion en B
                                   D[i-1][j-1] )  # paso diagonal

        El DTW final es sqrt(D[n][m]).

    Banda de Sakoe-Chiba (parametro 'ventana'):
        Para reducir tiempo y forzar un alineamiento razonable, solo se
        permiten celdas D[i][j] tales que |i - j| <= ventana. Si ventana es
        None, no se aplica restriccion (se calculan todas las celdas).

    Pasos:
        1. Crear la matriz D con dimensiones (n+1) x (m+1) llena de
           infinito y poner D[0][0] = 0.
        2. Para cada celda (i, j) dentro de la banda permitida:
              a. Calcular el costo local (diferencia al cuadrado).
              b. Tomar el minimo de las tres celdas vecinas.
              c. Sumar el costo local y guardarlo en D[i][j].
        3. Devolver sqrt(D[n][m]).

    Complejidad:
        Tiempo : O(n * m) sin banda; O(n * w) con banda de tamano w.
        Espacio: O(n * m). Se puede reducir a O(min(n, m)) si solo interesa
                 el valor final (no implementado aqui para que el codigo sea
                 facil de leer).

    Interpretacion:
        Un DTW pequeno indica que las dos series tienen una forma parecida
        aun si estan ligeramente desfasadas. DTW = 0 significa que existe
        un alineamiento perfecto sin diferencias.
    """
    n = len(serie_a)
    m = len(serie_b)

    if n == 0 or m == 0:
        return 0.0

    infinito = float("inf")

    # Construir matriz D de (n+1) x (m+1) con un bucle explicito.
    D = []
    fila = 0
    while fila <= n:
        nueva_fila = []
        columna = 0
        while columna <= m:
            nueva_fila.append(infinito)
            columna = columna + 1
        D.append(nueva_fila)
        fila = fila + 1

    D[0][0] = 0.0

    i = 1
    while i <= n:
        # Determinar las columnas validas segun la banda.
        if ventana is None:
            j_inicio = 1
            j_fin = m
        else:
            # Solo j tal que |i - j| <= ventana.
            j_inicio = i - ventana
            if j_inicio < 1:
                j_inicio = 1
            j_fin = i + ventana
            if j_fin > m:
                j_fin = m

        j = j_inicio
        while j <= j_fin:
            diferencia = serie_a[i - 1] - serie_b[j - 1]
            costo = diferencia * diferencia

            # Buscar el minimo de las tres celdas vecinas previas.
            mejor_vecino = D[i - 1][j]
            if D[i][j - 1] < mejor_vecino:
                mejor_vecino = D[i][j - 1]
            if D[i - 1][j - 1] < mejor_vecino:
                mejor_vecino = D[i - 1][j - 1]

            D[i][j] = costo + mejor_vecino
            j = j + 1
        i = i + 1

    if D[n][m] == infinito:
        # Puede ocurrir cuando la banda es demasiado estrecha.
        return infinito

    return math.sqrt(D[n][m])
