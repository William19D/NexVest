"""
Utilidades de preparacion de series financieras para los algoritmos de
similitud: alineacion por fechas y calculo de retornos simples.
"""


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
