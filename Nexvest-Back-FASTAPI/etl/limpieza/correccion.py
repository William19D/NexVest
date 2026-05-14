"""
etl/limpieza/correccion.py
--------------------------
Estrategias de CORRECCION sobre una serie historica. Cada funcion devuelve
una NUEVA serie sin alterar la original.
"""


def eliminar_indices(serie, indices_a_eliminar):
    """
    Devuelve una copia de 'serie' sin los indices indicados.

    Pasos:
        1. Convertir 'indices_a_eliminar' a un set para busqueda O(1).
        2. Recorrer la serie y copiar solo las filas cuyo indice no este
           en el set.

    Complejidad:
        Tiempo : O(n).
        Espacio: O(n).
    """
    a_eliminar = set(indices_a_eliminar)
    resultado = []
    indice = 0
    while indice < len(serie):
        if indice not in a_eliminar:
            resultado.append(serie[indice])
        indice = indice + 1
    return resultado


def forward_fill_close(serie, indices_a_rellenar):
    """
    Devuelve una copia de la serie en la que cada fila marcada se rellena
    con el close de la fila anterior valida (forward-fill clasico).

    Si el primer registro esta marcado, no hay valor anterior; se omite la
    correccion para esa fila y queda como estaba.

    Esta estrategia es util cuando se quiere conservar la fila (por
    ejemplo para mantener el calendario continuo) pero evitando que el
    close cero contamine el calculo de retornos.

    Complejidad: O(n).
    """
    a_rellenar = set(indices_a_rellenar)
    resultado = []
    ultimo_close_valido = None

    indice = 0
    while indice < len(serie):
        fila = serie[indice]
        if indice in a_rellenar and ultimo_close_valido is not None:
            # Copia superficial de la fila y reescritura del close.
            nueva_fila = dict(fila)
            nueva_fila["close"] = ultimo_close_valido
            resultado.append(nueva_fila)
        else:
            resultado.append(fila)
            close_actual = fila.get("close")
            if close_actual is not None and close_actual > 0:
                ultimo_close_valido = close_actual
        indice = indice + 1

    return resultado
