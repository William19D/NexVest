"""
etl/limpieza/deteccion.py
-------------------------
Funciones puras de DETECCION de filas problematicas dentro de una serie
historica. Ninguna de estas funciones modifica la serie de entrada; todas
devuelven listas de indices que despues consume el modulo de correccion.

Convenciones:
    - Una serie es una lista de dicts con al menos las claves 'fecha' y
      'close' (este ultimo como float).
    - Los indices devueltos son posiciones (0-based) en la serie de entrada.
"""

import math


def detectar_close_no_positivo(serie):
    """
    Devuelve la lista de indices donde 'close' es None, cero o negativo.

    Un close de cero o negativo indica un dia sin operacion real para el
    activo (artefacto del proveedor de datos). Estos registros rompen el
    calculo de retornos porque generan division por cero o saltos
    irreales del -100%.

    Complejidad: O(n).
    """
    indices = []
    indice = 0
    while indice < len(serie):
        close = serie[indice].get("close")
        if close is None or close <= 0:
            indices.append(indice)
        indice = indice + 1
    return indices


def detectar_outliers_retorno_zscore(serie, umbral=6.0):
    """
    Detecta indices con retornos diarios anomalos usando el z-score.

    Definicion:
        r_t = (close_t - close_{t-1}) / close_{t-1}
        z_t = (r_t - media(r)) / desviacion_estandar(r)

    Si |z_t| supera el umbral, el dia t es marcado como outlier.

    El umbral por defecto es 6.0, un valor conservador. Para una
    distribucion aproximadamente normal, |z| > 6 corresponde a una
    probabilidad de ~2e-9, asi que solo se marcan dias verdaderamente
    extremos.

    No se marcan filas con close anterior <= 0 (esas las captura
    detectar_close_no_positivo).

    Complejidad: O(n) (dos pasadas).
    """
    if len(serie) < 3:
        return []

    # Paso 1: construir lista (indice_en_serie, retorno) solo para filas
    # con base valida (close anterior positivo y close actual positivo).
    pares = []
    indice = 1
    while indice < len(serie):
        anterior = serie[indice - 1].get("close")
        actual = serie[indice].get("close")
        if anterior is not None and anterior > 0 and actual is not None and actual > 0:
            retorno = (actual - anterior) / anterior
            pares.append((indice, retorno))
        indice = indice + 1

    if len(pares) < 2:
        return []

    # Paso 2: calcular media y desviacion estandar muestral manualmente.
    suma = 0.0
    for _, retorno in pares:
        suma = suma + retorno
    media = suma / len(pares)

    suma_cuadrados = 0.0
    for _, retorno in pares:
        diferencia = retorno - media
        suma_cuadrados = suma_cuadrados + diferencia * diferencia
    if len(pares) < 2:
        return []
    desviacion = math.sqrt(suma_cuadrados / (len(pares) - 1))
    if desviacion == 0:
        return []

    # Paso 3: marcar los indices cuyo z-score supera el umbral.
    indices_outliers = []
    for indice_original, retorno in pares:
        z = (retorno - media) / desviacion
        if z > umbral or z < -umbral:
            indices_outliers.append(indice_original)
    return indices_outliers


def detectar_retornos_extremos_absolutos(serie, umbral_absoluto=0.5):
    """
    Devuelve los indices con retorno diario cuyo valor absoluto supera
    'umbral_absoluto'. Por defecto 0.5 = 50% en un solo dia.

    Justificacion:
        Un retorno diario de mas del 50% en una accion lider o ETF es
        excepcionalmente raro y suele indicar un evento corporativo no
        ajustado (split, dividendo extraordinario, cambio de moneda) o un
        error del proveedor de datos. Este filtro absoluto complementa al
        z-score: el z-score se vuelve poco efectivo cuando hay un cambio
        de regimen sostenido (varios dias en un nivel muy distinto), pero
        el umbral absoluto siempre captura saltos individuales irreales.

    Pasos:
        1. Recorrer la serie generando retornos r_t = (c_t - c_{t-1}) / c_{t-1}
           solo cuando ambos cierres son positivos.
        2. Marcar el indice t si |r_t| > umbral_absoluto.

    Complejidad: O(n).
    """
    indices = []
    indice = 1
    while indice < len(serie):
        anterior = serie[indice - 1].get("close")
        actual = serie[indice].get("close")
        if anterior is not None and anterior > 0 and actual is not None and actual > 0:
            retorno = (actual - anterior) / anterior
            if retorno > umbral_absoluto or retorno < -umbral_absoluto:
                indices.append(indice)
        indice = indice + 1
    return indices


def detectar_fechas_duplicadas(serie):
    """
    Devuelve los indices de filas cuya fecha aparece mas de una vez.

    Se conserva la primera aparicion y se marcan las repetidas para que el
    modulo de correccion las elimine. Esto evita falsos retornos cero o
    saltos artificiales producidos por filas duplicadas en el origen.

    Complejidad: O(n).
    """
    vistas = set()
    duplicados = []
    indice = 0
    while indice < len(serie):
        fecha = serie[indice].get("fecha")
        if fecha in vistas:
            duplicados.append(indice)
        else:
            vistas.add(fecha)
        indice = indice + 1
    return duplicados
