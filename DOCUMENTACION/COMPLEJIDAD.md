# NexVest - Analisis de complejidad algoritmica

Documento que consolida la formulacion matematica y el analisis formal de
complejidad temporal y espacial de cada algoritmo implementado en el proyecto.
La rubrica de la asignatura exige este analisis "destacando las diferencias
entre los enfoques implementados".

Notacion: `n` = numero de observaciones de una serie; `m` = longitud de la
segunda serie; `k` = tamano de ventana; `d` = numero de digitos de la clave
maxima; `K` = numero de activos del portafolio.

---

## Tabla resumen

| Categoria | Algoritmo | Tiempo | Espacio | Archivo |
|---|---|---|---|---|
| Sort | TimSort (insertion + merge sobre runs) | O(n log n) | O(n) | `algoritmos_ordenamiento.py` |
| Sort | Comb Sort | O(n^2) peor, ~O(n log n) promedio | O(1) | `algoritmos_ordenamiento.py` |
| Sort | Selection Sort | O(n^2) | O(1) | `algoritmos_ordenamiento.py` |
| Sort | Tree Sort (BST inorder) | O(n log n) prom., O(n^2) peor | O(n) | `algoritmos_ordenamiento.py` |
| Sort | Pigeonhole Sort (por agrupacion) | O(n + K_claves) | O(n + K_claves) | `algoritmos_ordenamiento.py` |
| Sort | Bucket Sort (por anio-mes) | O(n + b) promedio, O(n^2) peor | O(n + b) | `algoritmos_ordenamiento.py` |
| Sort | Quick Sort (3-way) | O(n log n) prom., O(n^2) peor | O(n) | `algoritmos_ordenamiento.py` |
| Sort | Heap Sort | O(n log n) | O(1) | `algoritmos_ordenamiento.py` |
| Sort | Bitonic Sort | O(n log^2 n) | O(log n) | `algoritmos_ordenamiento.py` |
| Sort | Gnome Sort | O(n^2) peor, O(n) mejor | O(1) | `algoritmos_ordenamiento.py` |
| Sort | Binary Insertion Sort | O(n log n) compar., O(n^2) mov. | O(1) | `algoritmos_ordenamiento.py` |
| Sort | Radix Sort (LSD por fecha) | O(d * (n + base)) | O(n + base) | `algoritmos_ordenamiento.py` |
| Similitud | Distancia euclidiana | O(n) | O(1) | `similitud.py` |
| Similitud | Correlacion de Pearson | O(n) | O(1) | `similitud.py` |
| Similitud | Dynamic Time Warping | O(n * m) | O(n * m) | `similitud.py` |
| Similitud | Similitud coseno | O(n) | O(1) | `similitud.py` |
| Patrones | Dias consecutivos al alza | O(n) | O(p) p apariciones | `patrones.py` |
| Patrones | Ruptura de maximo de k dias | O(n * k) | O(p) | `patrones.py` |
| Volatilidad | Desviacion estandar muestral | O(n) | O(1) | `volatilidad.py` |
| Volatilidad | Volatilidad anualizada | O(n) | O(1) | `volatilidad.py` |
| Volatilidad | Ranking por riesgo (insertion sort) | O(K^2) | O(K) | `volatilidad.py` |
| Correlacion | Matriz NxN del portafolio | O(K^2 * n) | O(K^2) | `routers/analisis.py` |
| Limpieza | Deteccion close<=0 | O(n) | O(p) | `etl/limpieza/deteccion.py` |
| Limpieza | Deteccion outliers z-score | O(n) | O(p) | `etl/limpieza/deteccion.py` |
| Limpieza | Deteccion retorno absoluto | O(n) | O(p) | `etl/limpieza/deteccion.py` |
| Limpieza | Pipeline iterativo (max 5 pasadas) | O(n) por pasada | O(n) | `etl/limpieza/pipeline.py` |
| PDF | SMA (suma corredera) | O(n) | O(n) | `reportes/medias_moviles.py` |

---

## 1. Similitud (Requerimiento 2)

### 1.1 Distancia euclidiana

```
d(A, B) = sqrt( sum_{i=0..n-1} (a_i - b_i)^2 )
```

- **Tiempo:** O(n). Una sola suma acumulada sobre las n posiciones alineadas.
- **Espacio:** O(1). Solo un acumulador.
- **Sensibilidad:** la escala importa. En el proyecto se aplica sobre retornos diarios para evitar que magnitudes distintas dominen.

### 1.2 Correlacion de Pearson

```
r = sum( (a_i - mu_a)(b_i - mu_b) )
    / ( sqrt( sum (a_i - mu_a)^2 ) * sqrt( sum (b_i - mu_b)^2 ) )
```

- **Tiempo:** O(n). Dos pasadas (medias + numerador y denominadores).
- **Espacio:** O(1).
- **Interpretacion:** r en [-1, 1]. Solo mide relacion lineal. Insensible a la escala. Indefinido si una serie es constante (se devuelve 0).

### 1.3 Dynamic Time Warping (DTW)

Se construye una matriz D de (n+1) x (m+1) con D[0][0] = 0 y el resto inf.
Para cada celda valida (i, j):

```
costo = (a_{i-1} - b_{j-1})^2
D[i][j] = costo + min( D[i-1][j], D[i][j-1], D[i-1][j-1] )
```

Resultado final: `sqrt(D[n][m])`.

- **Tiempo:** O(n * m) sin banda. Con banda Sakoe-Chiba de ancho w: O(n * w).
- **Espacio:** O(n * m) en la version explicita (la usada aqui por claridad). Se puede reducir a O(min(n, m)) si solo interesa el costo final.
- **Para que sirve:** permite alinear dos series que pueden ir desfasadas o tener velocidades distintas; util para detectar movimientos similares aunque ocurran en dias diferentes.

### 1.4 Similitud coseno

```
cos(A, B) = sum(a_i * b_i) / ( sqrt(sum a_i^2) * sqrt(sum b_i^2) )
```

- **Tiempo:** O(n).
- **Espacio:** O(1).
- **Interpretacion:** coseno del angulo entre los vectores. Insensible a magnitud absoluta; relevante para vectores de retornos donde solo interesa la "direccion" del movimiento.

### 1.5 Comparativa entre las cuatro

| Aspecto | Euclidiana | Pearson | DTW | Coseno |
|---|---|---|---|---|
| Sensible a la escala | Si | No | Si | No |
| Sensible a desfases temporales | Si | Si | **No** | Si |
| Captura relacion no lineal | No | No | Indirectamente | No |
| Costo | O(n) | O(n) | O(n*m) | O(n) |
| Uso recomendado en el proyecto | Magnitud del desvio entre series alineadas | Relacion lineal | Series con posibles retrasos | Direccion de retornos diarios |

---

## 2. Patrones (Requerimiento 3)

### 2.1 Dias consecutivos al alza

**Definicion formal del patron:**
```
Ocurre en t (con t >= k) sii:
  close[t-k+1] > close[t-k] AND close[t-k+2] > close[t-k+1] AND ... AND close[t] > close[t-1]
```

**Idea algoritmica (ventana deslizante con contador):**
Mantenemos `racha` = numero de subidas estrictas consecutivas hasta el dia
actual. En cada t: si `close[t] > close[t-1]`, incrementamos `racha`; si no,
`racha = 0`. Cada vez que `racha >= k`, reportamos t como aparicion.

- **Tiempo:** O(n). Una sola pasada.
- **Espacio:** O(p) donde p es la cantidad de apariciones.

### 2.2 Ruptura de maximo de k dias (patron formalizado adicional)

**Definicion formal del patron:**
```
Ocurre en t (con t >= k) sii:
  close[t] > max( close[t-k], close[t-k+1], ..., close[t-1] )
```

Es un "breakout" clasico del analisis tecnico.

**Idea algoritmica:**
Para cada t recorremos la ventana de k dias previos buscando el maximo y
comparamos contra `close[t]`.

- **Tiempo:** O(n * k). La implementacion didactica calcula el maximo
  directamente.
- **Espacio:** O(p).
- **Optimizacion posible (no aplicada):** una deque monotona decreciente
  permite mantener el maximo de la ventana en O(1) amortizado, reduciendo a
  O(n). Se prefiere la version explicita por legibilidad.

---

## 3. Volatilidad y riesgo (Requerimiento 3)

### 3.1 Media aritmetica

```
mu = ( sum_{i=0..n-1} x_i ) / n
```
O(n) tiempo, O(1) espacio.

### 3.2 Desviacion estandar muestral

```
sigma = sqrt( ( sum_{i} (x_i - mu)^2 ) / (n - 1) )
```

Se usa el divisor `(n - 1)` (estimador muestral, **no** poblacional) porque las
observaciones son una muestra del comportamiento del activo.

O(n) tiempo (dos pasadas), O(1) espacio. Indefinida si `n < 2` (devuelve 0).

### 3.3 Volatilidad anualizada

```
sigma_anual = sigma_diaria * sqrt(252)
```

`252` corresponde a la cantidad aproximada de dias bursatiles por anio. Si se
usaran datos semanales seria `sqrt(52)`; mensuales, `sqrt(12)`.

### 3.4 Clasificacion de riesgo

```
sigma_anual < 0.15           -> conservador
0.15 <= sigma_anual < 0.30   -> moderado
sigma_anual >= 0.30          -> agresivo
```

Tiempo O(1). Los umbrales son convencion documentada en
[`algorithms/volatilidad.py`](../Nexvest-Back-FASTAPI/algorithms/volatilidad.py).

### 3.5 Ranking por riesgo (insertion sort)

Tiempo O(K^2) en el peor caso (K = numero de activos, tipicamente 21 en el
proyecto -> a lo sumo ~441 comparaciones, despreciable). Se eligio insertion
sort por:

1. Es eficiente para listas pequenas como las del portafolio.
2. Es estable (preserva el orden relativo de empates).
3. Es facil de leer y de explicar paso a paso.

---

## 4. Matriz de correlacion (Requerimiento 4)

Para un portafolio de K activos con series de longitud n cada uno:

```
para cada par (i, j) con i < j:
    alinear series i y j por fechas comunes  -> O(n)
    calcular pearson sobre la alineacion     -> O(n)
```

- **Pares:** K * (K - 1) / 2 = O(K^2).
- **Tiempo total:** O(K^2 * n).
- **Espacio:** O(K^2) para la matriz.

Para K = 21 y n = 1244 dias bursatiles, son ~250 mil operaciones aritmeticas, que se ejecutan en pocos cientos de milisegundos.

---

## 5. Limpieza de datos (Requerimiento 1)

### 5.1 Detectores individuales

| Detector | Tiempo | Espacio |
|---|---|---|
| `detectar_close_no_positivo` | O(n) | O(p) |
| `detectar_fechas_duplicadas` | O(n) | O(n) (set de vistas) |
| `detectar_outliers_retorno_zscore` | O(n) (dos pasadas: media y umbral) | O(n) (lista de retornos) |
| `detectar_retornos_extremos_absolutos` | O(n) | O(p) |

### 5.2 Pipeline iterativo

```
maxPasadas = 5
while pasadas < maxPasadas:
    indices = z-score U retorno_absoluto sobre la serie actual
    si indices = {}: terminar
    serie = eliminar(serie, indices)
```

En cada pasada el detector recibe la serie ya reducida, por lo que el numero de
elementos baja monotonamente. En el peor caso teorico es O(n^2 * maxPasadas)
pero en la practica con `maxPasadas = 5` y series de 1244 puntos es lineal.

**Justificacion del enfoque iterativo:** el z-score sufre del efecto de
enmascaramiento (un outlier muy grande infla la desviacion estandar y oculta
outliers de magnitud media). Iterar resuelve ese efecto.

---

## 6. Ordenamiento (Requerimiento general)

La asignatura pide tambien medir el desempeno de varios algoritmos de
ordenamiento sobre el dataset unificado. Estan implementados a mano en
[`algorithms/algoritmos_ordenamiento.py`](../Nexvest-Back-FASTAPI/algorithms/algoritmos_ordenamiento.py) y se ejecutan via
`GET /analisis/ordenamiento`.

| Algoritmo | Tiempo peor | Tiempo promedio | Espacio | Nota |
|---|---|---|---|---|
| TimSort | O(n log n) | O(n log n) | O(n) | Hibrido: insertion sort sobre runs de 32 + merge bottom-up. |
| Comb Sort | O(n^2) | ~O(n log n) | O(1) | Mejora del bubble sort con gap decreciente (factor 1.3). |
| Selection Sort | O(n^2) | O(n^2) | O(1) | Selecciona el minimo en cada pasada. |
| Tree Sort | O(n^2) | O(n log n) | O(n) | Insertar en BST iterativo + inorder. |
| Pigeonhole | O(n + K) | O(n + K) | O(n + K) | Bucket por valor exacto del campo entero (volumen). |
| Bucket Sort | O(n^2) | O(n + b) | O(n + b) | Bucket por `(anio, mes)`; cada cubeta se ordena con insertion sort manual. |
| Quick Sort | O(n^2) | O(n log n) | O(n) | Particionado en tres listas (menores / iguales / mayores). |
| Heap Sort | O(n log n) | O(n log n) | O(1) | Heapify iterativo + extract-max. |
| Bitonic Sort | O(n log^2 n) | O(n log^2 n) | O(log n) | Requiere tamano potencia de 2 (padding). |
| Gnome Sort | O(n^2) | O(n^2) | O(1) | Insertion sort de "un gnomo". |
| Binary Insertion Sort | O(n log n) compar. + O(n^2) mov. | igual | O(1) | Insercion con busqueda binaria. |
| Radix Sort | O(d (n + base)) | igual | O(n + base) | LSD por fecha AAAAMMDD con pre-pasada por close para desempate. |

---

## 7. Operaciones del lado del frontend

El frontend no implementa algoritmos exigidos por la rubrica (todos viven en
el backend). Solo realiza:

- **SMA**: [`lib/sma.ts`](../Nexvest-Front/src/lib/sma.ts), suma corredera O(n).
- **Render del candlestick**: [`components/CandlestickChart.tsx`](../Nexvest-Front/src/components/CandlestickChart.tsx) escala lineal -> coordenadas SVG; O(n) en numero de velas.
- **Top pares en heatmap**: ordena los K*(K-1)/2 pares por |valor| descendente; O(K^2 log K).
