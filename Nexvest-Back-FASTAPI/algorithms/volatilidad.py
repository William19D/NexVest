"""
Calculo de metricas de dispersion y clasificacion de riesgo para activos
financieros (Requerimiento 3 del proyecto, segunda parte).

Este modulo implementa de forma manual:

    1. Media aritmetica.
    2. Desviacion estandar muestral.
    3. Volatilidad historica anualizada.
    4. Clasificacion de un activo en categorias de riesgo
       (conservador, moderado, agresivo).
    5. Ranking de activos por nivel de riesgo (reutilizando los algoritmos
       de ordenamiento del modulo algoritmos_ordenamiento).

No se usan funciones de numpy, statistics o pandas. Todas las operaciones
son bucles explicitos sobre listas de numeros.

Notas matematicas:

    - Retornos simples diarios:  r_t = (p_t - p_{t-1}) / p_{t-1}.
    - La desviacion estandar mide cuanto se aleja en promedio cada retorno
      respecto a la media.
    - La volatilidad historica anualizada estandar para datos diarios usa
      el factor sqrt(252), ya que se asume que un anio tiene
      aproximadamente 252 dias habiles de mercado.
"""

import math


# ---------------------------------------------------------------------------
# 1) Media aritmetica
# ---------------------------------------------------------------------------

def media(valores):
    """
    Media aritmetica de una lista de numeros.

    Definicion:
        mu = ( sum_{i} x_i ) / n

    Complejidad:
        Tiempo : O(n).
        Espacio: O(1).
    """
    if len(valores) == 0:
        return 0.0
    suma = 0.0
    for x in valores:
        suma = suma + x
    return suma / len(valores)


# ---------------------------------------------------------------------------
# 2) Desviacion estandar (muestral)
# ---------------------------------------------------------------------------

def desviacion_estandar(valores):
    """
    Desviacion estandar muestral.

    Definicion:
        sigma = sqrt( ( sum_{i} (x_i - mu)^2 ) / (n - 1) )

    Se usa el denominador (n - 1) (estimador muestral, no poblacional),
    porque los retornos historicos son una muestra del comportamiento del
    activo y no la poblacion completa.

    Pasos:
        1. Calcular la media mu.
        2. Acumular la suma de cuadrados de las desviaciones respecto a mu.
        3. Dividir entre (n - 1) y tomar raiz cuadrada.

    Casos especiales:
        - n < 2: la desviacion no esta definida; se devuelve 0.0.

    Complejidad:
        Tiempo : O(n).
        Espacio: O(1).
    """
    n = len(valores)
    if n < 2:
        return 0.0

    mu = media(valores)
    suma_cuadrados = 0.0
    for x in valores:
        diferencia = x - mu
        suma_cuadrados = suma_cuadrados + diferencia * diferencia

    return math.sqrt(suma_cuadrados / (n - 1))


# ---------------------------------------------------------------------------
# 3) Retornos y volatilidad historica anualizada
# ---------------------------------------------------------------------------

def calcular_retornos_simples(precios):
    """
    Calcula los retornos simples diarios a partir de una lista de precios.

    Definicion:
        r_t = (p_t - p_{t-1}) / p_{t-1}

    Devuelve una lista de longitud n - 1. El primer dia no genera retorno.

    Complejidad: O(n).
    """
    retornos = []
    i = 1
    while i < len(precios):
        anterior = precios[i - 1]
        actual = precios[i]
        if anterior == 0:
            retornos.append(0.0)
        else:
            retornos.append((actual - anterior) / anterior)
        i = i + 1
    return retornos


def volatilidad_historica(precios, anualizar=True, dias_habiles=252):
    """
    Volatilidad historica de una serie de precios.

    Definicion:
        sigma_diaria = desviacion_estandar( retornos_diarios )
        sigma_anual  = sigma_diaria * sqrt(dias_habiles)

    El parametro dias_habiles vale 252 por convencion para mercados de
    acciones (numero aproximado de jornadas habiles en un anio). Si se
    estuviera trabajando con datos semanales o mensuales habria que ajustarlo.

    Pasos:
        1. Construir la serie de retornos simples diarios.
        2. Calcular su desviacion estandar muestral.
        3. Si anualizar es True, multiplicar por sqrt(252).

    Complejidad: O(n).
    """
    retornos = calcular_retornos_simples(precios)
    sigma_diaria = desviacion_estandar(retornos)
    if anualizar:
        return sigma_diaria * math.sqrt(dias_habiles)
    return sigma_diaria


# ---------------------------------------------------------------------------
# 4) Clasificacion de riesgo
# ---------------------------------------------------------------------------

# Umbrales (en terminos de volatilidad anualizada) para clasificar un activo.
# Estos valores son convenciones razonables para acciones y ETFs y deben
# documentarse explicitamente en el informe.
UMBRAL_CONSERVADOR = 0.15  # < 15% anualizado -> conservador
UMBRAL_MODERADO = 0.30     # entre 15% y 30%   -> moderado
                            # > 30%             -> agresivo


def clasificar_riesgo(volatilidad_anualizada):
    """
    Clasifica un activo en una categoria de riesgo segun su volatilidad
    historica anualizada.

    Reglas:
        - vol <  0.15  -> 'conservador'
        - 0.15 <= vol < 0.30 -> 'moderado'
        - vol >= 0.30 -> 'agresivo'

    Complejidad: O(1).
    """
    if volatilidad_anualizada < UMBRAL_CONSERVADOR:
        return "conservador"
    if volatilidad_anualizada < UMBRAL_MODERADO:
        return "moderado"
    return "agresivo"


def perfil_riesgo_activo(ticker, historico):
    """
    Calcula la volatilidad historica anualizada de un activo y su categoria
    de riesgo asociada.

    Parametros:
        ticker   : identificador del activo (cadena).
        historico: lista de dicts con 'fecha' y 'close', ordenada
                   ascendentemente por fecha.

    Devuelve un diccionario con:
        ticker, observaciones, desviacion_diaria, volatilidad_anualizada,
        categoria.
    """
    # Extraer la lista de precios respetando el orden recibido.
    precios = []
    for fila in historico:
        precios.append(fila["close"])

    retornos = calcular_retornos_simples(precios)
    sigma_diaria = desviacion_estandar(retornos)
    sigma_anual = sigma_diaria * math.sqrt(252)
    categoria = clasificar_riesgo(sigma_anual)

    return {
        "ticker": ticker,
        "observaciones": len(precios),
        "desviacion_diaria": sigma_diaria,
        "volatilidad_anualizada": sigma_anual,
        "categoria": categoria,
    }


# ---------------------------------------------------------------------------
# 5) Ranking de activos por riesgo
# ---------------------------------------------------------------------------

def ranking_por_riesgo(perfiles, ascendente=True):
    """
    Ordena una lista de perfiles de riesgo (los devueltos por
    perfil_riesgo_activo) por volatilidad anualizada.

    Se implementa un insertion sort manual sobre el campo
    'volatilidad_anualizada' para no depender de list.sort. Insertion sort
    es eficiente cuando la lista es chica (en el proyecto seran del orden
    de 20 a 50 activos), y su codigo es lineal y facil de leer.

    Pasos (insertion sort):
        Para i = 1..n-1:
            1. Tomar val = perfiles[i].
            2. Comparar val con perfiles[i-1], perfiles[i-2], ...
               y desplazarlos hacia la derecha mientras tengan una
               volatilidad mayor (o menor, si ascendente=False) que val.
            3. Insertar val en la posicion encontrada.

    Complejidad:
        Tiempo : O(n^2) en el peor caso. Para 20-50 activos es despreciable.
        Espacio: O(1).
    """
    # Trabajamos sobre una copia para no mutar la lista original.
    copia = []
    for p in perfiles:
        copia.append(p)

    n = len(copia)

    i = 1
    while i < n:
        actual = copia[i]
        j = i - 1
        while j >= 0:
            if ascendente:
                fuera_de_orden = (
                    copia[j]["volatilidad_anualizada"]
                    > actual["volatilidad_anualizada"]
                )
            else:
                fuera_de_orden = (
                    copia[j]["volatilidad_anualizada"]
                    < actual["volatilidad_anualizada"]
                )
            if not fuera_de_orden:
                break
            copia[j + 1] = copia[j]
            j = j - 1
        copia[j + 1] = actual
        i = i + 1

    return copia


# ---------------------------------------------------------------------------
# Funcion de alto nivel: clasifica un portafolio completo.
# ---------------------------------------------------------------------------

def clasificar_portafolio(portafolio):
    """
    Calcula el perfil de riesgo de cada activo de un portafolio y devuelve
    el ranking ordenado de menor a mayor volatilidad.

    Parametros:
        portafolio: diccionario { ticker: historico } donde 'historico' es
                    una lista de dicts con 'fecha' y 'close' ordenada
                    ascendentemente por fecha.

    Devuelve:
        {
            "total_activos": int,
            "ranking": [ perfil_riesgo_activo, ... ],   # ordenado asc
            "resumen": {
                "conservador": int,
                "moderado":    int,
                "agresivo":    int
            }
        }
    """
    perfiles = []
    for ticker in portafolio:
        historico = portafolio[ticker]
        perfiles.append(perfil_riesgo_activo(ticker, historico))

    ranking = ranking_por_riesgo(perfiles, ascendente=True)

    resumen = {"conservador": 0, "moderado": 0, "agresivo": 0}
    for perfil in ranking:
        resumen[perfil["categoria"]] = resumen[perfil["categoria"]] + 1

    return {
        "total_activos": len(ranking),
        "ranking": ranking,
        "resumen": resumen,
    }
