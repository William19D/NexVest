"""
Deteccion de patrones en series de tiempo financieras mediante ventanas
deslizantes (sliding window).

Este modulo cubre el Requerimiento 3 del proyecto en su primera parte:
recorrer el historial de precios y contar la frecuencia con la que aparecen
patrones formalmente definidos.

Se implementan dos patrones:

    1. dias_consecutivos_alza
       Secuencia de k dias consecutivos en los que el precio de cierre sube
       respecto al dia anterior.

    2. ruptura_maximo_ventana
       (segundo patron formalizado): el precio de cierre del dia t supera
       estrictamente el maximo de los k dias previos.

Ambos patrones se evaluan con una sola pasada sobre la serie (sliding
window). Para cada patron se devuelve:

    {
        "total_apariciones": int,
        "indices": [i1, i2, ...],       # indices donde termina el patron
        "fechas":  [f1, f2, ...],       # fechas correspondientes
    }
"""


# ---------------------------------------------------------------------------
# Utilidad de extraccion de series
# ---------------------------------------------------------------------------

def extraer_cierres(historico):
    """
    Devuelve dos listas paralelas (fechas, cierres) a partir de un historico
    de un activo. Se asume que 'historico' es una lista de dicts ordenada
    ascendentemente por fecha; si no lo esta, conviene ordenarla antes
    usando algoritmos_ordenamiento.tim_sort.

    Complejidad: O(n) en tiempo y espacio.
    """
    fechas = []
    cierres = []
    for fila in historico:
        fechas.append(fila["fecha"])
        cierres.append(fila["close"])
    return fechas, cierres


# ---------------------------------------------------------------------------
# Patron 1: k dias consecutivos al alza
# ---------------------------------------------------------------------------

def dias_consecutivos_alza(historico, k):
    """
    Cuenta cuantas veces aparece el patron de 'k dias consecutivos al alza'
    en el historico de un activo.

    Definicion formal del patron:
        El patron ocurre en el indice t (con t >= k) si y solo si:

            close[t - k + 1] > close[t - k]
            close[t - k + 2] > close[t - k + 1]
            ...
            close[t]         > close[t - 1]

        Es decir, hubo k subidas estrictas consecutivas justo antes y
        hasta el dia t.

    Idea algoritmica (ventana deslizante de tamano k):
        En vez de recontar las subidas para cada ventana, mantenemos un
        contador 'racha' con la cantidad de subidas estrictas consecutivas
        que llevamos hasta el dia actual:

            - Si close[t] > close[t-1], racha = racha + 1.
            - Si no, racha = 0.

        Cada vez que racha alcance el valor k, se reporta una aparicion en
        el indice t.

    Pasos:
        1. Validar que k >= 1 y que la serie tenga al menos k+1 puntos.
        2. Inicializar racha = 0.
        3. Para t = 1..n-1:
             a. Si close[t] > close[t-1], incrementar racha; si no,
                reiniciar racha a 0.
             b. Si racha >= k, registrar t como aparicion.
        4. Devolver el conteo y la lista de apariciones.

    Complejidad:
        Tiempo : O(n) (una sola pasada).
        Espacio: O(p) donde p es el numero de apariciones reportadas.
    """
    if k < 1:
        raise ValueError("El tamano de ventana k debe ser >= 1.")

    fechas, cierres = extraer_cierres(historico)
    n = len(cierres)

    indices = []
    fechas_evento = []

    if n < k + 1:
        return {
            "patron": "dias_consecutivos_alza",
            "k": k,
            "total_apariciones": 0,
            "indices": indices,
            "fechas": fechas_evento,
        }

    racha = 0
    t = 1
    while t < n:
        if cierres[t] > cierres[t - 1]:
            racha = racha + 1
        else:
            racha = 0

        if racha >= k:
            indices.append(t)
            fechas_evento.append(fechas[t])
        t = t + 1

    return {
        "patron": "dias_consecutivos_alza",
        "k": k,
        "total_apariciones": len(indices),
        "indices": indices,
        "fechas": fechas_evento,
    }


# ---------------------------------------------------------------------------
# Patron 2: ruptura del maximo de la ventana de k dias previos
# ---------------------------------------------------------------------------

def ruptura_maximo_ventana(historico, k):
    """
    Detecta dias en los que el precio de cierre rompe (supera estrictamente)
    el maximo de los k dias previos. Es un patron tecnico clasico llamado
    'breakout de k dias'.

    Definicion formal del patron:
        El patron ocurre en el indice t (con t >= k) si y solo si:

            close[t] > max( close[t - k],
                             close[t - k + 1],
                             ...,
                             close[t - 1] )

    Idea algoritmica:
        Se mantiene una ventana deslizante de tamano k con los cierres de
        los k dias previos al dia t. Para cada t se calcula el maximo de la
        ventana y se compara con close[t].

        Para mantener el codigo simple y facil de explicar, se calcula el
        maximo recorriendo la ventana con un bucle. El costo es O(k) por
        cada t y O(n*k) en total. Una version mas eficiente usaria una
        deque monotona y bajaria el costo a O(n), pero el codigo se vuelve
        mas dificil de leer, asi que se prefiere esta version clara.

    Pasos:
        1. Validar que k >= 1 y que la serie tenga al menos k+1 puntos.
        2. Para t = k..n-1:
             a. Recorrer close[t-k..t-1] y obtener max_previo.
             b. Si close[t] > max_previo, registrar t.
        3. Devolver el conteo y la lista de apariciones.

    Complejidad:
        Tiempo : O(n * k).
        Espacio: O(p) donde p es el numero de apariciones reportadas.
    """
    if k < 1:
        raise ValueError("El tamano de ventana k debe ser >= 1.")

    fechas, cierres = extraer_cierres(historico)
    n = len(cierres)

    indices = []
    fechas_evento = []

    if n < k + 1:
        return {
            "patron": "ruptura_maximo_ventana",
            "k": k,
            "total_apariciones": 0,
            "indices": indices,
            "fechas": fechas_evento,
        }

    t = k
    while t < n:
        # Buscar el maximo de los k dias previos: close[t-k..t-1].
        inicio_ventana = t - k
        max_previo = cierres[inicio_ventana]
        i = inicio_ventana + 1
        while i < t:
            if cierres[i] > max_previo:
                max_previo = cierres[i]
            i = i + 1

        if cierres[t] > max_previo:
            indices.append(t)
            fechas_evento.append(fechas[t])

        t = t + 1

    return {
        "patron": "ruptura_maximo_ventana",
        "k": k,
        "total_apariciones": len(indices),
        "indices": indices,
        "fechas": fechas_evento,
    }


# ---------------------------------------------------------------------------
# Funcion de alto nivel: ejecuta los dos patrones sobre un activo.
# ---------------------------------------------------------------------------

def frecuencia_de_patrones(historico, k):
    """
    Ejecuta los dos patrones soportados sobre el historico de un activo y
    devuelve un resumen consolidado.

    Parametros:
        historico: lista de dicts con 'fecha' y 'close', ordenada
                   ascendentemente por fecha.
        k: tamano de la ventana (numero de dias).

    Devuelve:
        {
            "k": k,
            "total_dias": n,
            "patrones": [
                <resultado de dias_consecutivos_alza>,
                <resultado de ruptura_maximo_ventana>
            ]
        }
    """
    return {
        "k": k,
        "total_dias": len(historico),
        "patrones": [
            dias_consecutivos_alza(historico, k),
            ruptura_maximo_ventana(historico, k),
        ],
    }
