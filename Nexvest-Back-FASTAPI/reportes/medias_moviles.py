"""
reportes/medias_moviles.py
--------------------------
Calculo manual de medias moviles simples (SMA), implementadas con un
bucle explicito. No se usan funciones de alto nivel ni operaciones
vectorizadas de numpy/pandas.
"""


def sma(valores, ventana):
    """
    Media movil simple (SMA) sobre una lista de numeros.

    Definicion matematica:

        SMA_t = (v_{t-ventana+1} + v_{t-ventana+2} + ... + v_t) / ventana

    Para los primeros 'ventana - 1' indices no hay suficiente historia
    para calcular la SMA; en esos puntos se devuelve None. Esto facilita
    despues alinear el resultado con el eje temporal.

    Pasos:
        1. Validar que la ventana es >= 1.
        2. Crear una lista 'resultado' del mismo largo que 'valores',
           inicializada con None.
        3. Mantener una suma corredera 'suma_actual' con los ultimos
           'ventana' valores. En cada iteracion:
              - Sumar el valor entrante.
              - Si ya entraron 'ventana' valores, restar el que sale.
              - Si la ventana esta completa, escribir la SMA en el
                resultado.

    Complejidad:
        Tiempo : O(n) (una sola pasada, sin recalcular toda la suma).
        Espacio: O(n) por la lista de resultados.
    """
    if ventana < 1:
        raise ValueError("La ventana de la SMA debe ser >= 1.")

    n = len(valores)
    resultado = [None] * n
    if n == 0:
        return resultado

    suma_actual = 0.0
    indice = 0
    while indice < n:
        suma_actual = suma_actual + valores[indice]
        if indice >= ventana:
            # Sale el valor que ya quedo fuera de la ventana.
            suma_actual = suma_actual - valores[indice - ventana]
        if indice >= ventana - 1:
            resultado[indice] = suma_actual / ventana
        indice = indice + 1

    return resultado
