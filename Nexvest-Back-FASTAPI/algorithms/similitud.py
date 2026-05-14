"""
Algoritmos de similitud entre series de tiempo financieras.

Este modulo implementa los cuatro algoritmos exigidos por el proyecto:

    1. Distancia euclidiana.
    2. Correlacion de Pearson.
    3. Dynamic Time Warping (DTW).
    4. Similitud por coseno.

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

import math


# ---------------------------------------------------------------------------
# Utilidades de preparacion
# ---------------------------------------------------------------------------

def alinear_por_fechas(serie_a, serie_b):
    """
    Alinea dos series financieras por sus fechas comunes.

    Parametros:
        serie_a, serie_b: listas de diccionarios con al menos las claves
                          'fecha' y 'close'.

    Devuelve una tupla (fechas, valores_a, valores_b) donde:
        - fechas    : lista de fechas comunes ordenadas ascendentemente.
        - valores_a : lista de close de serie_a en esas fechas.
        - valores_b : lista de close de serie_b en esas fechas.

    Pasos:
        1. Construir un diccionario fecha -> close para cada serie.
        2. Calcular la interseccion de fechas como conjunto.
        3. Ordenar las fechas comunes.
        4. Recolectar los valores correspondientes en el mismo orden.

    Complejidad:
        Tiempo: O(n + m) para construir los diccionarios, mas O(k log k)
                para ordenar las k fechas comunes.
        Espacio: O(n + m).
    """
    mapa_a = {}
    for fila in serie_a:
        mapa_a[fila["fecha"]] = fila["close"]

    mapa_b = {}
    for fila in serie_b:
        mapa_b[fila["fecha"]] = fila["close"]

    # Interseccion manual: recorremos las claves del mas chico.
    if len(mapa_a) <= len(mapa_b):
        fechas_pequeno = mapa_a.keys()
        mapa_grande = mapa_b
    else:
        fechas_pequeno = mapa_b.keys()
        mapa_grande = mapa_a

    fechas_comunes = []
    for fecha in fechas_pequeno:
        if fecha in mapa_grande:
            fechas_comunes.append(fecha)

    fechas_comunes.sort()

    valores_a = []
    valores_b = []
    for fecha in fechas_comunes:
        valores_a.append(mapa_a[fecha])
        valores_b.append(mapa_b[fecha])

    return fechas_comunes, valores_a, valores_b


def calcular_retornos(precios):
    """
    Calcula los retornos simples diarios de una serie de precios.

    Definicion (retorno simple):

        r_t = (p_t - p_{t-1}) / p_{t-1}

    El primer dia no tiene retorno (no hay p_{t-1}), por lo que la lista de
    retornos tiene longitud n - 1.

    Complejidad:
        Tiempo: O(n).
        Espacio: O(n).
    """
    retornos = []
    indice = 1
    while indice < len(precios):
        precio_anterior = precios[indice - 1]
        precio_actual = precios[indice]
        if precio_anterior == 0:
            # Evitar division por cero: se asume retorno cero ese dia.
            retornos.append(0.0)
        else:
            retornos.append((precio_actual - precio_anterior) / precio_anterior)
        indice = indice + 1
    return retornos


# ---------------------------------------------------------------------------
# 1) Distancia euclidiana
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# 2) Correlacion de Pearson
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# 3) Dynamic Time Warping (DTW)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# 4) Similitud por coseno
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Funcion de alto nivel: comparar dos activos con los cuatro algoritmos.
# ---------------------------------------------------------------------------

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
