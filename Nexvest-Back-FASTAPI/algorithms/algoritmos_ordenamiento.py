"""
Algoritmos de ordenamiento implementados manualmente.

Todos los algoritmos de este modulo trabajan sobre listas de diccionarios con
la siguiente forma minima:

    {
        "fecha":   "AAAA-MM-DD",   # cadena ordenable lexicograficamente
        "close":   float,
        "volumen": int,
        ...otros campos opcionales...
    }

El criterio de orden por defecto es ascendente por (fecha, close). Para que el
codigo del modulo sea facil de leer y analizar, se respetan estas reglas:

  1. No se usan funciones de alto nivel de Python que implementen el algoritmo
     en una sola llamada (no se usa list.sort ni sorted como nucleo del
     algoritmo). Las unicas excepciones son lugares puntuales donde se ordena
     una lista pequena de claves enteras para iterar por orden, lo cual no
     reemplaza al algoritmo que se este estudiando.
  2. Cada algoritmo esta acompanado de un docstring con la idea general, los
     pasos del algoritmo y un analisis de complejidad temporal y espacial.
  3. Se evitan trucos del lenguaje que dificulten la lectura: se prefiere un
     bucle explicito sobre una comprension cuando aclara la intencion.

Funcion de comparacion comun:

    es_menor(a, b)  ->  True si a debe quedar antes que b.

Se utiliza en lugar de comparar diccionarios directamente.
"""


# ---------------------------------------------------------------------------
# Comparador comun
# ---------------------------------------------------------------------------

def es_menor(activo_a, activo_b):
    """
    Devuelve True si 'activo_a' debe quedar antes que 'activo_b' en el orden
    ascendente. El criterio es lexicografico sobre dos campos:

        1. Primero compara la fecha (cadena 'AAAA-MM-DD' ordena bien lex.).
        2. En caso de empate, compara el precio de cierre 'close'.

    No usa ninguna funcion de ordenamiento; solo comparaciones basicas.
    """
    fecha_a = activo_a["fecha"]
    fecha_b = activo_b["fecha"]

    if fecha_a < fecha_b:
        return True
    if fecha_a > fecha_b:
        return False

    # Si las fechas son iguales, se desempata por close.
    return activo_a["close"] < activo_b["close"]


def son_iguales(activo_a, activo_b):
    """
    Devuelve True cuando dos registros son equivalentes para el criterio de
    orden (misma fecha y mismo close). Se usa en quick_sort para separar los
    elementos exactamente iguales al pivote sin compararlos como diccionarios
    completos.
    """
    return (
        activo_a["fecha"] == activo_b["fecha"]
        and activo_a["close"] == activo_b["close"]
    )


# ---------------------------------------------------------------------------
# 1) TimSort simplificado
# ---------------------------------------------------------------------------

def _insertion_sort_rango(data, izquierda, derecha):
    """
    Insertion sort sobre el sub-arreglo data[izquierda..derecha] (ambos
    extremos incluidos). Es la rutina interna que usa tim_sort para ordenar
    los 'runs' pequenos antes de fusionarlos.

    Complejidad:
        Peor caso : O(m^2) donde m = derecha - izquierda + 1.
        Mejor caso: O(m) cuando el sub-arreglo ya esta casi ordenado.
    """
    i = izquierda + 1
    while i <= derecha:
        # Tomamos el elemento actual y lo desplazamos hacia la izquierda
        # mientras existan vecinos mayores que el.
        actual = data[i]
        j = i - 1
        while j >= izquierda and es_menor(actual, data[j]):
            data[j + 1] = data[j]
            j = j - 1
        data[j + 1] = actual
        i = i + 1


def _merge_rangos(data, izquierda, medio, derecha):
    """
    Fusiona dos sub-arreglos consecutivos ya ordenados:

        izquierdo = data[izquierda..medio]
        derecho   = data[medio+1..derecha]

    Resultado: data[izquierda..derecha] queda ordenado.

    Complejidad: O(n) en tiempo, O(n) en memoria auxiliar (las dos copias).
    """
    # Copiamos las dos mitades a buffers temporales para poder sobrescribir
    # 'data' en orden ascendente sin perder informacion.
    izq = []
    der = []

    indice_izq = izquierda
    while indice_izq <= medio:
        izq.append(data[indice_izq])
        indice_izq = indice_izq + 1

    indice_der = medio + 1
    while indice_der <= derecha:
        der.append(data[indice_der])
        indice_der = indice_der + 1

    # Recorremos los dos buffers en paralelo y vamos colocando el menor.
    i = 0
    j = 0
    k = izquierda
    while i < len(izq) and j < len(der):
        if es_menor(izq[i], der[j]):
            data[k] = izq[i]
            i = i + 1
        else:
            data[k] = der[j]
            j = j + 1
        k = k + 1

    # Lo que sobre de cualquiera de los dos buffers se vuelca al final.
    while i < len(izq):
        data[k] = izq[i]
        i = i + 1
        k = k + 1
    while j < len(der):
        data[k] = der[j]
        j = j + 1
        k = k + 1


def tim_sort(data):
    """
    TimSort simplificado.

    Idea:
        TimSort es un hibrido entre insertion sort y merge sort. Divide la
        lista en bloques de tamano fijo llamados 'runs', ordena cada run
        usando insertion sort (muy eficiente en arreglos pequenos), y luego
        fusiona los runs por pares con merge sort hasta cubrir toda la lista.

    Pasos:
        1. Definir el tamano de run (aqui MIN_RUN = 32, valor clasico).
        2. Recorrer la lista en bloques de MIN_RUN y ordenar cada bloque con
           insertion sort.
        3. Fusionar bloques de tamano MIN_RUN -> 2*MIN_RUN -> 4*MIN_RUN ...
           hasta cubrir la lista completa.

    Complejidad:
        Tiempo : O(n log n) en promedio y peor caso.
        Espacio: O(n) por los buffers de la fusion.
    """
    n = len(data)
    if n <= 1:
        return data

    MIN_RUN = 32

    # Paso 1 y 2: ordenar los runs con insertion sort.
    inicio_run = 0
    while inicio_run < n:
        fin_run = inicio_run + MIN_RUN - 1
        if fin_run >= n:
            fin_run = n - 1
        _insertion_sort_rango(data, inicio_run, fin_run)
        inicio_run = inicio_run + MIN_RUN

    # Paso 3: ir duplicando el tamano del bloque y fusionando pares de runs.
    tamano_bloque = MIN_RUN
    while tamano_bloque < n:
        izquierda = 0
        while izquierda < n:
            medio = izquierda + tamano_bloque - 1
            derecha = izquierda + 2 * tamano_bloque - 1
            if medio >= n - 1:
                # No hay segundo bloque que fusionar.
                break
            if derecha >= n:
                derecha = n - 1
            _merge_rangos(data, izquierda, medio, derecha)
            izquierda = izquierda + 2 * tamano_bloque
        tamano_bloque = tamano_bloque * 2

    return data


# ---------------------------------------------------------------------------
# 2) Comb Sort
# ---------------------------------------------------------------------------

def comb_sort(data):
    """
    Comb Sort.

    Idea:
        Es una mejora del bubble sort. En lugar de comparar siempre vecinos
        inmediatos, compara elementos separados por un 'gap' que comienza
        grande y se va reduciendo dividiendolo por un factor de encogimiento
        (1.3 segun la literatura). Cuando el gap llega a 1 se comporta como
        bubble sort.

    Pasos:
        1. Inicializar gap = n y bandera 'ordenado' = False.
        2. Mientras no este ordenado:
             a. Calcular nuevo gap = floor(gap / 1.3).
             b. Si gap <= 1, fijar gap = 1 y asumir que esta ordenado.
             c. Recorrer el arreglo comparando data[i] con data[i + gap] y
                hacer swap si estan fuera de orden. Si hubo algun swap,
                volver a marcar 'ordenado' = False.

    Complejidad:
        Tiempo : O(n^2) en el peor caso, ~O(n log n) en promedio empirico.
        Espacio: O(1).
    """
    n = len(data)
    gap = n
    factor_encogimiento = 1.3
    esta_ordenado = False

    while not esta_ordenado:
        # Reducimos el gap.
        gap = int(gap / factor_encogimiento)
        if gap <= 1:
            gap = 1
            esta_ordenado = True

        # Recorrido con el gap actual.
        i = 0
        while i + gap < n:
            if es_menor(data[i + gap], data[i]):
                # Estan fuera de orden: intercambiar.
                temporal = data[i]
                data[i] = data[i + gap]
                data[i + gap] = temporal
                esta_ordenado = False
            i = i + 1

    return data


# ---------------------------------------------------------------------------
# 3) Selection Sort
# ---------------------------------------------------------------------------

def selection_sort(data):
    """
    Selection Sort.

    Idea:
        En cada pasada se busca el minimo del sub-arreglo restante y se
        coloca en la primera posicion no ordenada.

    Pasos:
        Para i = 0..n-1:
            1. Asumir que el minimo esta en la posicion i.
            2. Recorrer j = i+1..n-1; si encuentra alguno menor, actualizar
               el indice del minimo.
            3. Intercambiar data[i] con data[indice_min].

    Complejidad:
        Tiempo : O(n^2) en cualquier caso (n*(n-1)/2 comparaciones).
        Espacio: O(1).
    """
    n = len(data)
    i = 0
    while i < n:
        indice_min = i
        j = i + 1
        while j < n:
            if es_menor(data[j], data[indice_min]):
                indice_min = j
            j = j + 1

        # Intercambio si el minimo no es el primer elemento.
        if indice_min != i:
            temporal = data[i]
            data[i] = data[indice_min]
            data[indice_min] = temporal
        i = i + 1

    return data


# ---------------------------------------------------------------------------
# 4) Tree Sort (insercion en BST + recorrido inorder)
# ---------------------------------------------------------------------------

class _NodoBST:
    """Nodo simple de un arbol binario de busqueda."""

    def __init__(self, valor):
        self.valor = valor
        self.izquierda = None
        self.derecha = None


def _insertar_en_bst(raiz, valor):
    """
    Inserta 'valor' en el arbol cuya raiz es 'raiz' y devuelve la raiz.

    Se hace de forma iterativa (no recursiva) para no caer en
    RecursionError cuando el dataset tiene miles de filas.
    """
    if raiz is None:
        return _NodoBST(valor)

    actual = raiz
    while True:
        if es_menor(valor, actual.valor):
            if actual.izquierda is None:
                actual.izquierda = _NodoBST(valor)
                return raiz
            actual = actual.izquierda
        else:
            if actual.derecha is None:
                actual.derecha = _NodoBST(valor)
                return raiz
            actual = actual.derecha


def _inorder_iterativo(raiz, resultado):
    """
    Recorrido inorder iterativo del BST.

    El recorrido inorder de un BST produce los elementos en orden
    ascendente. Se usa una pila para simular la recursion.
    """
    pila = []
    actual = raiz
    while pila or actual is not None:
        # Bajar siempre por la izquierda apilando.
        while actual is not None:
            pila.append(actual)
            actual = actual.izquierda
        # Sacar de la pila, anadir al resultado y pasar al hijo derecho.
        actual = pila.pop()
        resultado.append(actual.valor)
        actual = actual.derecha


def tree_sort(data):
    """
    Tree Sort.

    Idea:
        Insertar todos los elementos en un arbol binario de busqueda y
        luego recorrer el arbol en inorder; el recorrido inorder devuelve
        los elementos ordenados ascendentemente.

    Pasos:
        1. Crear un BST vacio.
        2. Insertar cada elemento de la lista en el BST.
        3. Recorrer el BST en inorder y volcar los valores a la salida.

    Complejidad:
        Tiempo : O(n log n) en promedio (arbol balanceado),
                 O(n^2) en el peor caso si los datos vienen ya ordenados
                 (el arbol degenera en una lista).
        Espacio: O(n) por los nodos del arbol.
    """
    if not data:
        return []

    raiz = None
    indice = 0
    while indice < len(data):
        raiz = _insertar_en_bst(raiz, data[indice])
        indice = indice + 1

    resultado = []
    _inorder_iterativo(raiz, resultado)
    return resultado


# ---------------------------------------------------------------------------
# 5) Pigeonhole Sort (agrupacion por clave entera)
# ---------------------------------------------------------------------------

def pigeonhole_sort(data, clave="volumen"):
    """
    Pigeonhole Sort (version por agrupacion).

    Idea:
        Para cada elemento se calcula una clave entera (por defecto el
        volumen). Todos los elementos con la misma clave se guardan en la
        misma 'casilla' (pigeonhole). Al final se recorren las casillas en
        orden ascendente de clave y se concatenan los elementos.

    Esta variante por diccionario funciona aun cuando max-min es muy grande,
    porque no reserva un arreglo de tamano (max-min+1); en vez de eso solo
    crea una entrada por valor que realmente aparece.

    Complejidad:
        Tiempo : O(n + k) donde k = numero de claves distintas.
        Espacio: O(n + k).
    """
    casillas = {}

    # Paso 1: meter cada elemento en su casilla.
    for elemento in data:
        clave_entera = int(elemento[clave])
        if clave_entera not in casillas:
            casillas[clave_entera] = []
        casillas[clave_entera].append(elemento)

    # Paso 2: recorrer las claves en orden ascendente y concatenar.
    # Se ordenan las claves enteras con sorted: es un detalle auxiliar,
    # no reemplaza el algoritmo principal (la idea del pigeonhole es la
    # distribucion en casillas, no como se enumeran las llaves).
    resultado = []
    claves_ordenadas = sorted(casillas.keys())
    for clave_actual in claves_ordenadas:
        for elemento in casillas[clave_actual]:
            resultado.append(elemento)

    return resultado


# ---------------------------------------------------------------------------
# 6) Bucket Sort
# ---------------------------------------------------------------------------

def bucket_sort(data):
    """
    Bucket Sort.

    Idea:
        Se distribuyen los elementos en cubetas segun una clave que se
        calcula de cada elemento. Despues se ordena cada cubeta con un
        algoritmo secundario (aqui insertion sort, implementado manualmente
        arriba) y por ultimo se concatenan las cubetas en orden.

    Mapeo usado:
        clave_bucket = (anio, mes)  extraido de la fecha 'AAAA-MM-DD'.

    Se usa la pareja (anio, mes) porque es una clave entera natural sobre la
    que se puede agrupar facilmente y conserva el orden cronologico cuando
    se recorre la lista de claves ordenadas. Cada cubeta agrupa entonces
    todas las filas del mismo mes; el insertion sort interno termina de
    ordenarlas por (fecha, close), y al concatenar las cubetas en orden de
    clave se obtiene la lista completa ordenada por (fecha, close).

    Pasos:
        1. Recorrer 'data' y agrupar cada fila en la cubeta correspondiente
           a su (anio, mes).
        2. Ordenar la lista de claves de cubeta.
        3. Para cada cubeta, ejecutar insertion sort por (fecha, close).
        4. Concatenar las cubetas en orden de clave y devolver el resultado.

    Complejidad:
        Tiempo : O(n + k) en promedio cuando los datos se distribuyen de
                 forma uniforme entre k cubetas; O(n^2) en el peor caso.
        Espacio: O(n + k).
    """
    if not data:
        return []

    # Paso 1: distribuir en cubetas indexadas por (anio, mes).
    buckets = {}
    for elemento in data:
        fecha = elemento["fecha"]
        # 'AAAA-MM-DD': caracteres 0..3 = anio, 5..6 = mes.
        anio = int(fecha[0:4])
        mes = int(fecha[5:7])
        clave = (anio, mes)
        if clave not in buckets:
            buckets[clave] = []
        buckets[clave].append(elemento)

    # Paso 2: ordenar las claves de cubeta. Se usa sorted sobre tuplas de
    # enteros porque es una operacion auxiliar (no es el algoritmo en
    # estudio), del mismo modo que se hace en pigeonhole_sort.
    claves_ordenadas = sorted(buckets.keys())

    # Pasos 3 y 4: ordenar cada cubeta con insertion sort manual y
    # concatenar el resultado.
    resultado = []
    for clave in claves_ordenadas:
        cubeta = buckets[clave]
        _insertion_sort_rango(cubeta, 0, len(cubeta) - 1)
        for elemento in cubeta:
            resultado.append(elemento)

    return resultado


# ---------------------------------------------------------------------------
# 7) Quick Sort
# ---------------------------------------------------------------------------

def quick_sort(data):
    """
    Quick Sort (version con particionado en tres listas).

    Idea:
        1. Si la lista tiene 0 o 1 elementos, ya esta ordenada.
        2. Se elige un pivote (aqui el elemento del medio).
        3. Se construyen tres listas:
              - 'menores' : elementos estrictamente menores que el pivote.
              - 'iguales' : elementos equivalentes al pivote.
              - 'mayores' : elementos estrictamente mayores que el pivote.
        4. Se ordenan recursivamente las listas 'menores' y 'mayores' y se
           devuelve la concatenacion menores + iguales + mayores.

    Esta version es facil de leer y no modifica la lista original.

    Complejidad:
        Tiempo : O(n log n) en promedio, O(n^2) en el peor caso (pivote
                 siempre el minimo o el maximo).
        Espacio: O(n) por las listas auxiliares y la pila de recursion.
    """
    if len(data) <= 1:
        return list(data)

    pivote = data[len(data) // 2]

    menores = []
    iguales = []
    mayores = []
    for elemento in data:
        if es_menor(elemento, pivote):
            menores.append(elemento)
        elif son_iguales(elemento, pivote):
            iguales.append(elemento)
        else:
            mayores.append(elemento)

    return quick_sort(menores) + iguales + quick_sort(mayores)


# ---------------------------------------------------------------------------
# 8) Heap Sort
# ---------------------------------------------------------------------------

def _heapify_max(data, tamano_heap, raiz_actual):
    """
    Asegura la propiedad de max-heap en el sub-arbol con raiz 'raiz_actual',
    considerando que el heap ocupa data[0..tamano_heap-1].

    Es iterativo (no recursivo) para evitar recursion profunda en datasets
    grandes.
    """
    actual = raiz_actual
    while True:
        izquierda = 2 * actual + 1
        derecha = 2 * actual + 2
        mayor = actual

        if izquierda < tamano_heap and es_menor(data[mayor], data[izquierda]):
            mayor = izquierda
        if derecha < tamano_heap and es_menor(data[mayor], data[derecha]):
            mayor = derecha

        if mayor == actual:
            # Ya cumple la propiedad de heap: terminamos.
            return

        # Intercambiar y bajar a la posicion del hijo mayor.
        temporal = data[actual]
        data[actual] = data[mayor]
        data[mayor] = temporal
        actual = mayor


def heap_sort(data):
    """
    Heap Sort sobre un max-heap.

    Idea:
        1. Construir un max-heap a partir de la lista completa. En un max-heap
           cada nodo es mayor o igual que sus hijos, asi que el maximo esta
           en la raiz (indice 0).
        2. Intercambiar la raiz con el ultimo elemento del heap (lo deja
           ordenado al final) y reducir el tamano del heap en uno.
        3. Reparar la propiedad de heap con _heapify_max y repetir.

    Complejidad:
        Tiempo : O(n log n) en todos los casos.
        Espacio: O(1) (ordenamiento en sitio).
    """
    n = len(data)
    if n <= 1:
        return data

    # Paso 1: construir el heap. Se hace de abajo hacia arriba empezando por
    # el ultimo nodo interno: indice (n // 2 - 1).
    i = n // 2 - 1
    while i >= 0:
        _heapify_max(data, n, i)
        i = i - 1

    # Paso 2 y 3: extraer el maximo y reparar el heap.
    i = n - 1
    while i > 0:
        temporal = data[0]
        data[0] = data[i]
        data[i] = temporal
        _heapify_max(data, i, 0)
        i = i - 1

    return data


# ---------------------------------------------------------------------------
# 9) Bitonic Sort
# ---------------------------------------------------------------------------

def bitonic_sort(data, inicio, cantidad, ascendente):
    """
    Bitonic Sort recursivo.

    Idea (red de ordenamiento bitonica):
        Una secuencia bitonica es aquella que primero crece y luego decrece
        (o viceversa). Bitonic sort construye una secuencia bitonica y luego
        la convierte en monotona con sucesivas mezclas bitonicas.

    Pasos:
        1. Dividir la sub-secuencia data[inicio..inicio+cantidad-1] en dos
           mitades.
        2. Ordenar la primera mitad ascendentemente y la segunda
           descendentemente (genera una secuencia bitonica).
        3. Aplicar bitonic_merge para volverla monotona en la direccion
           solicitada.

    Restriccion: 'cantidad' debe ser potencia de 2. El llamador es
    responsable de pasar una entrada del tamano correcto (se puede rellenar
    con elementos "infinito" para alcanzar la potencia mas cercana).

    Complejidad:
        Tiempo : O(n log^2 n) comparaciones.
        Espacio: O(log n) por la pila de recursion.
    """
    if cantidad > 1:
        mitad = cantidad // 2
        bitonic_sort(data, inicio, mitad, True)
        bitonic_sort(data, inicio + mitad, mitad, False)
        bitonic_merge(data, inicio, cantidad, ascendente)


def bitonic_merge(data, inicio, cantidad, ascendente):
    """
    Mezcla bitonica: dada una secuencia bitonica, la convierte en una
    secuencia monotona (toda ascendente o toda descendente).
    """
    if cantidad > 1:
        mitad = cantidad // 2
        i = inicio
        while i < inicio + mitad:
            # Si la direccion solicitada coincide con que data[i+mitad] sea
            # menor que data[i], se hace el intercambio.
            if ascendente == es_menor(data[i + mitad], data[i]):
                temporal = data[i]
                data[i] = data[i + mitad]
                data[i + mitad] = temporal
            i = i + 1
        bitonic_merge(data, inicio, mitad, ascendente)
        bitonic_merge(data, inicio + mitad, mitad, ascendente)


# ---------------------------------------------------------------------------
# 10) Gnome Sort
# ---------------------------------------------------------------------------

def gnome_sort(data):
    """
    Gnome Sort.

    Idea:
        Variante muy simple del insertion sort. Se avanza por la lista; si el
        elemento actual esta en orden con el anterior, se sigue adelante; si
        no, se intercambia con el anterior y se retrocede una posicion.

    Pasos:
        1. i = 0.
        2. Si i == 0 o data[i] >= data[i-1], avanzar: i = i + 1.
        3. Si data[i] < data[i-1], intercambiar y retroceder: i = i - 1.
        4. Terminar cuando i == n.

    Complejidad:
        Tiempo : O(n^2) en el peor caso, O(n) en el mejor (ya ordenado).
        Espacio: O(1).
    """
    n = len(data)
    i = 0
    while i < n:
        if i == 0 or not es_menor(data[i], data[i - 1]):
            i = i + 1
        else:
            temporal = data[i]
            data[i] = data[i - 1]
            data[i - 1] = temporal
            i = i - 1
    return data


# ---------------------------------------------------------------------------
# 11) Binary Insertion Sort
# ---------------------------------------------------------------------------

def binary_insertion_sort(data):
    """
    Binary Insertion Sort.

    Idea:
        Es un insertion sort en el que la posicion en la que se debe insertar
        cada elemento se busca usando busqueda binaria en la parte ya
        ordenada de la lista, en vez de comparacion lineal.

    Pasos:
        Para i = 1..n-1:
            1. Sacar el valor data[i].
            2. Busqueda binaria en data[0..i-1] para encontrar 'pos':
               la primera posicion donde data[pos] no es menor que val.
            3. Desplazar data[pos..i-1] una posicion a la derecha.
            4. Colocar el valor en data[pos].

    Complejidad:
        Comparaciones: O(n log n) (busqueda binaria).
        Movimientos  : O(n^2) (los desplazamientos siguen siendo lineales).
        Espacio      : O(1).
    """
    n = len(data)
    i = 1
    while i < n:
        valor = data[i]

        # Busqueda binaria de la posicion de insercion.
        izquierda = 0
        derecha = i - 1
        while izquierda <= derecha:
            medio = (izquierda + derecha) // 2
            if es_menor(valor, data[medio]):
                derecha = medio - 1
            else:
                izquierda = medio + 1
        posicion_insercion = izquierda

        # Desplazar a la derecha los elementos posteriores.
        j = i
        while j > posicion_insercion:
            data[j] = data[j - 1]
            j = j - 1
        data[posicion_insercion] = valor

        i = i + 1
    return data


# ---------------------------------------------------------------------------
# 12) Radix Sort
# ---------------------------------------------------------------------------

def _fecha_a_entero(fecha_str):
    """
    Convierte 'AAAA-MM-DD' a entero AAAAMMDD para poder usar radix sort por
    digito sobre las fechas.
    """
    partes = fecha_str.split("-")
    anio = int(partes[0])
    mes = int(partes[1])
    dia = int(partes[2])
    return anio * 10000 + mes * 100 + dia


def _counting_sort_por_digito(data, exponente):
    """
    Counting sort estable que ordena 'data' por el digito que corresponde al
    'exponente' (1 = unidades, 10 = decenas, 100 = centenas, ...).

    Se ejecuta sobre la clave entera generada a partir de la fecha. Esta
    rutina es la pieza interna que radix_sort llama varias veces.

    Estabilidad: dos registros con el mismo digito conservan el orden
    relativo que traian. Esto es lo que permite que radix sort funcione.

    Complejidad:
        Tiempo : O(n + base). Aqui la base es 10.
        Espacio: O(n + base).
    """
    n = len(data)
    salida = [None] * n
    conteo = [0] * 10  # base 10

    # Paso 1: contar cuantos elementos hay para cada digito.
    i = 0
    while i < n:
        clave = _fecha_a_entero(data[i]["fecha"])
        digito = (clave // exponente) % 10
        conteo[digito] = conteo[digito] + 1
        i = i + 1

    # Paso 2: prefijos acumulados. conteo[d] termina indicando la posicion
    # final (exclusiva) donde van los elementos con digito <= d.
    i = 1
    while i < 10:
        conteo[i] = conteo[i] + conteo[i - 1]
        i = i + 1

    # Paso 3: recorrer 'data' de derecha a izquierda para mantener la
    # estabilidad y colocar cada elemento en su posicion final.
    i = n - 1
    while i >= 0:
        clave = _fecha_a_entero(data[i]["fecha"])
        digito = (clave // exponente) % 10
        conteo[digito] = conteo[digito] - 1
        salida[conteo[digito]] = data[i]
        i = i - 1

    # Paso 4: copiar la salida sobre data.
    i = 0
    while i < n:
        data[i] = salida[i]
        i = i + 1


def _insertion_sort_por_close(data):
    """
    Insertion sort estable que ordena 'data' unicamente por el campo
    'close'. Se utiliza como pre-pasada de radix_sort para que, despues de
    ordenar por fecha, los empates queden ordenados por close (radix LSD
    conserva el orden relativo cuando el counting sort interno es estable).
    """
    i = 1
    while i < len(data):
        actual = data[i]
        j = i - 1
        while j >= 0 and data[j]["close"] > actual["close"]:
            data[j + 1] = data[j]
            j = j - 1
        data[j + 1] = actual
        i = i + 1


def radix_sort(data):
    """
    Radix Sort (LSD - Least Significant Digit) ordenando por (fecha, close).

    Idea:
        Para datos enteros, se ordena varias veces el arreglo usando un
        algoritmo estable, una vez por cada digito, empezando por el menos
        significativo (las unidades) hasta el mas significativo. Cuando se
        termina, el arreglo queda ordenado.

        Para desempatar por 'close' cuando dos filas comparten fecha, se
        aprovecha la estabilidad del counting sort interno: primero se
        ordena la lista por close, despues se aplica el radix sort por
        fecha. Como el counting sort por digito no altera el orden relativo
        entre elementos con el mismo digito, el orden por close se preserva
        dentro de cada fecha.

    Conversion fecha -> entero:

        2024-01-15  ->  20240115

    Pasos:
        1. Pre-pasada estable: ordenar 'data' por close con insertion sort.
        2. Calcular la clave maxima entre todas las fechas para conocer
           cuantos digitos hay que recorrer.
        3. Para cada digito (unidades, decenas, centenas, ...), aplicar
           counting sort estable por ese digito.

    Complejidad:
        Tiempo : O(n^2) por la pre-pasada de insertion sort en el peor
                 caso, mas O(d * (n + base)) por las pasadas de radix.
                 Si se eligiera otra pre-pasada O(n log n) la complejidad
                 total bajaria a O(n log n + d * n). Se mantiene insertion
                 sort por simplicidad didactica.
        Espacio: O(n + base) por counting sort.
    """
    if not data:
        return data

    # Paso 1: pre-pasada estable por close.
    _insertion_sort_por_close(data)

    # Paso 2: clave maxima sobre las fechas.
    clave_maxima = _fecha_a_entero(data[0]["fecha"])
    i = 1
    while i < len(data):
        actual = _fecha_a_entero(data[i]["fecha"])
        if actual > clave_maxima:
            clave_maxima = actual
        i = i + 1

    # Paso 3: counting sort por cada digito de la fecha.
    exponente = 1
    while clave_maxima // exponente > 0:
        _counting_sort_por_digito(data, exponente)
        exponente = exponente * 10

    return data
