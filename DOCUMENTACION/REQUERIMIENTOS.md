# NexVest - Explicacion tecnica por requerimiento

Documento que mapea cada requerimiento del PDF de la asignatura a los archivos
y endpoints especificos del proyecto, con la justificacion de las decisiones
de implementacion.

---

## Requerimiento 1 - ETL automatizado

**Exigencia:** descargar al menos 5 anos de historial diario para >= 20
activos, unificar en un dataset, limpiar valores faltantes / anomalias, sin
usar `yfinance`, `pandas_datareader` o equivalentes.

### Implementacion

**Activos descargados (21):**

| Origen | Tickers |
|---|---|
| BVC (15 acciones colombianas) | ECOPETROL, ISA, GEB, PFBCOLOM, NUTRESA, GRUPOSURA, CELSIA, EXITO, CEMARGOS, CNEC, CORFICOLCF, PROMIGAS, MINEROS, CLH, PFDAVVNDA |
| Yahoo Finance (6 ETFs globales) | VOO, CSPX.L, SPY, QQQ, IVV, GLD |

**Archivos:**

- [`etl/finalInfoScript.py`](../Nexvest-Back-FASTAPI/etl/finalInfoScript.py): descarga por HTTP directo. La BVC se consulta con un token (sesion) que se refresca automaticamente; cada peticion devuelve el dia completo para todos los activos. Yahoo se consulta con la v8 (JSON) y fallback a v7 (CSV) usando `requests` puro.
- [`etl/storage.py`](../Nexvest-Back-FASTAPI/etl/storage.py): upsert idempotente a MongoDB. Una coleccion por activo (`historico_<mnemonic>`).
- [`etl/limpieza/`](../Nexvest-Back-FASTAPI/etl/limpieza): paquete de limpieza separado por roles.

**Limpieza (justificacion del impacto algoritmico):**

| Deteccion | Que detecta | Decision | Justificacion |
|---|---|---|---|
| `detectar_close_no_positivo` | Filas con `close <= 0` | Eliminar la fila | Son dias sin operacion real para activos de baja liquidez; el retorno calculado en esa transicion produce division por cero y -100%, contaminando volatilidad y similitud. |
| `detectar_fechas_duplicadas` | Fechas repetidas | Eliminar las duplicadas, conservar la primera | Inconsistencias del origen. Mantenerlas produciria retornos espurios cero. |
| `detectar_outliers_retorno_zscore` | `|z-score(retorno_t)| > 6` | Eliminar iterativamente | Captura saltos relativos a la propia serie. Es iterativo para mitigar el efecto de enmascaramiento del z-score (un outlier muy grande infla la desviacion estandar y esconde otros). |
| `detectar_retornos_extremos_absolutos` | `|retorno_t| > 50%` en un dia | Eliminar | Capa adicional para cambios de regimen (splits no ajustados). Un retorno diario > 50% en accion lider o ETF es astronomicamente improbable; suele ser error de datos. |

El reporte de la limpieza (`outliers_residuales`, `convergencia`) se expone via
`GET /analisis/limpieza/{mnemonic}` y se incluye en el apendice del PDF.

**Restricciones cumplidas:**

- Sin `yfinance`, `pandas_datareader`, ni equivalentes.
- Solo `requests` para HTTP, `json` para parsing, estructuras nativas de
  Python.
- Reproducible desde cero: `python etl/finalInfoScript.py && python etl/storage.py`.

---

## Requerimiento 2 - Algoritmos de similitud

**Exigencia:** al menos 4 algoritmos de similitud, implementados explicitamente.

### Implementacion

Todos en [`algorithms/similitud.py`](../Nexvest-Back-FASTAPI/algorithms/similitud.py).

| Algoritmo | Funcion | Formulacion |
|---|---|---|
| Distancia euclidiana | `distancia_euclidiana(a, b)` | `sqrt( sum( (a_i - b_i)^2 ) )` |
| Correlacion de Pearson | `correlacion_pearson(a, b)` | `cov(A,B) / (sigma_A * sigma_B)` |
| Dynamic Time Warping | `dynamic_time_warping(a, b, ventana)` | Programacion dinamica O(n*m) con banda Sakoe-Chiba opcional |
| Similitud coseno | `similitud_coseno(a, b)` | `dot(a,b) / (||a|| * ||b||)` |

**Helpers:**
- `alinear_por_fechas(serie_a, serie_b)`: interseccion de fechas comunes para evitar comparar dias que solo existen en uno de los mercados.
- `calcular_retornos(precios)`: `r_t = (p_t - p_{t-1}) / p_{t-1}`.

**API:** `GET /analisis/similitud?a=&b=&base=retorno|precio&ventana_dtw=`.
Devuelve los 4 valores en un solo response.

**Frontend:** [`SimilarityAnalysis.tsx`](../Nexvest-Front/src/pages/SimilarityAnalysis.tsx)
permite elegir dos activos, base y ventana, muestra los 4 valores y los
graficos comparativos (precio normalizado, precio absoluto, volumen).

El analisis formal de complejidad esta en
[COMPLEJIDAD.md](COMPLEJIDAD.md#requerimiento-2-similitud).

---

## Requerimiento 3 - Patrones (sliding window) y volatilidad

**Exigencia:** algoritmo de ventana deslizante para detectar patrones; al
menos uno predefinido (dias consecutivos al alza) y un segundo formalizado por
el equipo. Calculo de volatilidad y clasificacion de riesgo.

### 3.1 Patrones

Archivo: [`algorithms/patrones.py`](../Nexvest-Back-FASTAPI/algorithms/patrones.py).

**Patron 1 - Dias consecutivos al alza** (`dias_consecutivos_alza`):
```
Ocurre en t si  close[t-k+1] > close[t-k]  AND ... AND  close[t] > close[t-1]
```
Implementado con un contador `racha`. Cada vez que `racha >= k`, se reporta una aparicion. **O(n)** en una sola pasada.

**Patron 2 - Ruptura de maximo de k dias** (`ruptura_maximo_ventana`):
```
Ocurre en t si  close[t] > max( close[t-k..t-1] )
```
Es un breakout clasico del analisis tecnico. Implementacion **O(n*k)** con calculo directo del maximo en la ventana (didactica). Una version con deque monotona seria O(n) pero menos legible.

**API:** `GET /analisis/patrones/{mnemonic}?k={k}`.

### 3.2 Volatilidad y clasificacion de riesgo

Archivo: [`algorithms/volatilidad.py`](../Nexvest-Back-FASTAPI/algorithms/volatilidad.py).

**Definiciones:**

```
r_t = (close_t - close_{t-1}) / close_{t-1}      # retorno simple
mu = mean(r)
sigma_diaria = sqrt( sum( (r_i - mu)^2 ) / (n - 1) )      # muestral
sigma_anual = sigma_diaria * sqrt(252)                    # 252 dias bursatiles
```

**Umbrales de clasificacion:**

```
sigma_anual < 0.15    -> conservador
0.15 <= sigma_anual < 0.30 -> moderado
sigma_anual >= 0.30   -> agresivo
```

**Endpoints:**

| Endpoint | Devuelve |
|---|---|
| `GET /analisis/volatilidad/{mnemonic}` | sigma diario, sigma anual, categoria. |
| `GET /analisis/riesgo` | Ranking ascendente del portafolio + resumen por categoria. |

El ranking se ordena con un `ranking_por_riesgo` que ejecuta **insertion sort manual**, reutilizando una de las primitivas de [`algoritmos_ordenamiento.py`](../Nexvest-Back-FASTAPI/algorithms/algoritmos_ordenamiento.py).

**Frontend:** [`RiskDashboard.tsx`](../Nexvest-Front/src/pages/RiskDashboard.tsx)
+ widget del Dashboard.

---

## Requerimiento 4 - Dashboard visual + export PDF

**Exigencia:** matriz de correlacion (heatmap), candlestick con medias moviles,
exportacion de reporte tecnico en PDF.

### 4.1 Matriz de correlacion

- **Calculo:** [`routers/analisis.py:analisis_correlacion`](../Nexvest-Back-FASTAPI/routers/analisis.py) construye la matriz NxN llamando `correlacion_pearson` para cada par alineado por fechas comunes.
- **Endpoint:** `GET /analisis/correlacion?tickers&base`.
- **Frontend:** [`CorrelationHeatmap.tsx`](../Nexvest-Front/src/pages/CorrelationHeatmap.tsx) renderiza una grilla NxN coloreada (verde positiva, rojo negativa) + tabla de top 10 pares por magnitud.

### 4.2 Candlestick + medias moviles

- **Candlestick:** [`components/CandlestickChart.tsx`](../Nexvest-Front/src/components/CandlestickChart.tsx) en SVG puro. Cada vela = linea de low-high (mecha) + rectangulo de open-close (cuerpo). Color verde si alcista, rojo si bajista.
- **SMA:** calculada en cliente con [`lib/sma.ts`](../Nexvest-Front/src/lib/sma.ts) (suma corredera O(n)). Se superponen SMA20 y SMA50.
- **Pagina:** [`AssetExplorer.tsx`](../Nexvest-Front/src/pages/AssetExplorer.tsx).

### 4.3 Export PDF

- **Endpoint:** `GET /analisis/reporte/pdf?tickers&tickers_candle&base&desde&hasta`.
- **Backend:** paquete [`reportes/`](../Nexvest-Back-FASTAPI/reportes) con archivos separados por rol:

| Archivo | Rol |
|---|---|
| `medias_moviles.py` | SMA O(n) (mismo algoritmo que el frontend). |
| `graficos.py` | Heatmap + candlestick OHLC en `matplotlib` con backend `Agg`. |
| `tablas.py` | Tablas `reportlab` (riesgo, top pares, limpieza). |
| `pdf_builder.py` | Ensambla portada + 4 secciones. |
| `generador.py` | API publica, orquesta los anteriores. |

- **Contenido del PDF:**
  1. Portada (titulo, fecha, parametros, activos analizados).
  2. Heatmap de correlacion + top 10 pares.
  3. Tabla de ranking de riesgo con color por categoria.
  4. Una pagina con candlestick + SMA para cada ticker en `tickers_candle`.
  5. Apendice con el reporte de limpieza por activo.

- **Frontend:** boton "Exportar PDF" en [`CorrelationHeatmap.tsx`](../Nexvest-Front/src/pages/CorrelationHeatmap.tsx). Descarga via [`fetchReportePdf`](../Nexvest-Front/src/lib/services/reporte.ts) y guarda con `descargarBlob`.

---

## Requerimiento 5 - Despliegue web

**Exigencia:** el proyecto debe estar desplegado como aplicacion web funcional.

### Estado actual

- **Backend:** `vercel.json` presente. Recomendacion: usar Railway o Render
  porque el endpoint `/analisis/reporte/pdf` y el calculo de la matriz para
  todo el portafolio pueden tomar hasta 30 segundos (Vercel hobby limita a
  10s).
- **Frontend:** estatico, ideal para Vercel / Netlify / Cloudflare Pages.
- **Base de datos:** MongoDB Atlas (free tier 512 MB es suficiente para los 21
  activos por 5 anios = aprox 25 MB de documentos).

### Variables de entorno de produccion

```
# Backend (Render / Railway):
MONGO_URI=mongodb+srv://...
MONGO_DB_NAME=nexvest

# Frontend (Vercel):
VITE_API_URL=https://<host-del-backend>
```

### Reproducibilidad fuera de despliegue

Cualquier evaluador puede correr el sistema local:

```bash
# Backend
cd Nexvest-Back-FASTAPI && pip install -r requirements.txt
python -m uvicorn main:app --port 8000

# Frontend
cd Nexvest-Front && npm install && npm run dev
```

---

## Mapa rapido archivo -> requerimiento

| Archivo | Cubre |
|---|---|
| `etl/finalInfoScript.py` | R1 (descarga) |
| `etl/storage.py` | R1 (carga a Mongo) |
| `etl/limpieza/*` | R1 (limpieza con justificacion) |
| `algorithms/similitud.py` | R2 |
| `algorithms/patrones.py` | R3 (patrones) |
| `algorithms/volatilidad.py` | R3 (volatilidad + riesgo) |
| `algorithms/algoritmos_ordenamiento.py` | Apoyo a R3 (ranking) |
| `routers/analisis.py` | R2, R3, R4 (endpoints) |
| `reportes/*` | R4 (PDF) |
| `components/CandlestickChart.tsx` | R4 (visual) |
| Frontend completo | R4 (dashboard interactivo) |
| `vercel.json` (x2) | R5 (deploy) |
