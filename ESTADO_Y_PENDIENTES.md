# NexVest — Estado actual y pendientes por implementar

> Análisis del proyecto contra los **5 requerimientos** del PDF [`Proyecto Análisis de Algoritmos - 2026-1.pdf`](Proyecto%20An%C3%A1lisis%20de%20Algoritmos%20-%202026-1.pdf), revisando [`Nexvest-Back-FASTAPI/`](Nexvest-Back-FASTAPI/) y [`Nexvest-Front/`](Nexvest-Front/).

---

## 0. Resumen ejecutivo

| Requerimiento PDF | Backend | Frontend | Estado global |
|---|---|---|---|
| R1. ETL automatizado (HTTP directo, 5 años, 20+ activos) | ✅ Hecho | — | **Completo** |
| R2. 4 algoritmos de similitud (Euclidean, Pearson, DTW, Coseno) | ❌ Falta | ⚠️ Parcial (3/4 en cliente) | **Crítico mover al backend** |
| R3. Patrones (sliding window) + volatilidad + clasificación de riesgo | ❌ Falta | ⚠️ UI con mocks | **Crítico** |
| R4. Dashboard: heatmap correlación + candlestick + medias móviles + export PDF | ⚠️ Sin endpoints | ⚠️ Parcial | **Crítico** |
| R5. Despliegue web | ⚠️ `vercel.json` listo, sin deploy verificado | ⚠️ `vercel.json` listo, sin deploy verificado | **Pendiente verificar** |
| Documento final de diseño + complejidad algorítmica | ❌ Falta | ❌ Falta | **Pendiente** |

**Activos disponibles en el ETL (21):** ECOPETROL, ISA, GEB, PFBCOLOM, NUTRESA, GRUPOSURA, CELSIA, EXITO, CEMARGOS, CNEC, CORFICOLCF, PROMIGAS, MINEROS, CLH, PFDAVVNDA, VOO, CSPX.L, SPY, QQQ, IVV, GLD.

**Auditoría de librerías prohibidas:** ✅ Limpio — no se usa `yfinance`, `pandas_datareader`, `sklearn.metrics`, `scipy.spatial.distance`, ni `numpy.corrcoef` como implementación principal.

---

## 1. Backend ([`Nexvest-Back-FASTAPI/`](Nexvest-Back-FASTAPI/))

### ✅ Implementado

- [`main.py`](Nexvest-Back-FASTAPI/main.py) — app FastAPI, CORS, registro de routers.
- [`database.py`](Nexvest-Back-FASTAPI/database.py) — singleton MongoDB con pooling y optimización cold-start para Vercel.
- [`etl/finalInfoScript.py`](Nexvest-Back-FASTAPI/etl/finalInfoScript.py) — descarga BVC (token + 1 request por fecha) + Yahoo (v8 JSON con fallback v7 CSV), threading, retry, 5 años, 21 activos. Sin librerías prohibidas.
- [`etl/storage.py`](Nexvest-Back-FASTAPI/etl/storage.py) — bulk upsert idempotente a Mongo, una colección por activo.
- [`algorithms/algoritmos_ordenamiento.py`](Nexvest-Back-FASTAPI/algorithms/algoritmos_ordenamiento.py) — 12 algoritmos de ordenamiento implementados a mano (TimSort, QuickSort, HeapSort, RadixSort, …).
- [`algorithms/desempeno.py`](Nexvest-Back-FASTAPI/algorithms/desempeno.py) — benchmark de los algoritmos de ordenamiento con matplotlib.
- [`routers/historicos.py`](Nexvest-Back-FASTAPI/routers/historicos.py) — `GET /historicos/mnemonics`, `GET /historicos/{mnemonic}` (con `desde`, `hasta`, `limit`), `GET /historicos/{mnemonic}/{date}`.
- [`routers/analisis.py`](Nexvest-Back-FASTAPI/routers/analisis.py) — `GET /analisis/ordenamiento` (solo benchmark de sorting).

### ❌ Pendiente (en orden de ejecución sugerido)

#### 1.1 Algoritmos de similitud (R2) — **crítico**
Crear [`algorithms/similitud.py`](Nexvest-Back-FASTAPI/algorithms/similitud.py) con implementación **manual**:
- [ ] `euclidean_distance(s1, s2)` — sobre precios y sobre retornos. Complejidad O(n).
- [ ] `pearson_correlation(s1, s2)` — fórmula explícita (Σxy − nx̄ȳ) / (sₓsᵧ). O(n).
- [ ] `dynamic_time_warping(s1, s2, window=None)` — matriz DP, con banda de Sakoe-Chiba opcional. O(n·m) tiempo, O(n·m) espacio (versión optimizada O(min(n,m)) espacio).
- [ ] `cosine_similarity(v1, v2)` — sobre vectores de retornos diarios. O(n).
- [ ] Función de **alineación por fechas comunes** entre dos series (los precios vienen con calendarios distintos).
- [ ] Función de cálculo de **retornos logarítmicos / simples**.

Exponer en [`routers/analisis.py`](Nexvest-Back-FASTAPI/routers/analisis.py):
- [ ] `GET /analisis/similitud?a={ticker1}&b={ticker2}&metrica={euclidean|pearson|dtw|cosine|all}&base={precio|retorno}` → devuelve valor + serie alineada + tiempo de cómputo.

#### 1.2 Sliding window + volatilidad + clasificación de riesgo (R3) — **crítico**
Crear [`algorithms/patrones.py`](Nexvest-Back-FASTAPI/algorithms/patrones.py):
- [ ] `sliding_window_consecutive_up(prices, k)` — cuenta secuencias de k días consecutivos al alza. O(n).
- [ ] **Segundo patrón formalizado** (elegir uno y documentar):
  - Sugerencia A — *Bullish Engulfing*: día N tiene `open ≤ close[N-1]` y `close ≥ open[N-1]` (formalizar en el doc).
  - Sugerencia B — *Breakout de máximos de k días*: `close[t] > max(close[t-k..t-1])`.
- [ ] `pattern_frequency(prices, pattern_fn, window)` — devuelve frecuencia y posiciones.

Crear [`algorithms/volatilidad.py`](Nexvest-Back-FASTAPI/algorithms/volatilidad.py):
- [ ] `std_dev(returns)` — desviación estándar manual.
- [ ] `historical_volatility(returns, annualize=True)` — σ · √252.
- [ ] `classify_risk(vol)` con umbrales documentados (ej: <15% conservador, 15–30% moderado, >30% agresivo).

Endpoints en [`routers/analisis.py`](Nexvest-Back-FASTAPI/routers/analisis.py):
- [ ] `GET /analisis/patrones?ticker={t}&tipo={consecutive_up|engulfing|...}&ventana={k}`.
- [ ] `GET /analisis/volatilidad/{ticker}` → σ, σ anualizada, categoría.
- [ ] `GET /analisis/riesgo` → ranking de los 21 activos ordenados por riesgo (usando uno de los algoritmos de [`algoritmos_ordenamiento.py`](Nexvest-Back-FASTAPI/algorithms/algoritmos_ordenamiento.py) — ¡aprovechar!).

#### 1.3 Matriz de correlación (R4)
- [ ] `GET /analisis/correlacion?metrica=pearson&desde=&hasta=` → matriz N×N de todos los activos disponibles, usando la `pearson_correlation` del punto 1.1.

#### 1.4 Reporte PDF (R4)
- [ ] Añadir `reportlab` (o `fpdf2`) a [`requirements.txt`](Nexvest-Back-FASTAPI/requirements.txt).
- [ ] `GET /analisis/reporte/pdf?tickers=...` → genera PDF con: matriz de correlación, top correlaciones, ranking de riesgo, gráfico candlestick + SMA del o los activos seleccionados.

#### 1.5 Limpieza de datos (R1 — parte ETL)
El ETL descarga, pero el PDF exige **detectar valores faltantes, anomalías y justificar interpolación/eliminación**.
- [ ] Crear [`etl/limpieza.py`](Nexvest-Back-FASTAPI/etl/limpieza.py) con: detección de gaps por calendario bursátil, interpolación lineal de huecos cortos, eliminación de outliers (z-score), unificación de fechas entre activos colombianos y globales.
- [ ] Documentar en el informe el **impacto algorítmico** de cada decisión.

#### 1.6 Documentación de complejidad
- [ ] En cada función de similitud/patrón/volatilidad: docstring con **formulación matemática** + **complejidad temporal y espacial** + **breve análisis**.

---

## 2. Frontend ([`Nexvest-Front/`](Nexvest-Front/))

### ✅ Implementado

- Rutas y layout completos: [`src/App.tsx`](Nexvest-Front/src/App.tsx), [`src/components/Layout.tsx`](Nexvest-Front/src/components/Layout.tsx), [`src/components/AppSidebar.tsx`](Nexvest-Front/src/components/AppSidebar.tsx), [`src/components/SplashScreen.tsx`](Nexvest-Front/src/components/SplashScreen.tsx).
- [`src/pages/Dashboard.tsx`](Nexvest-Front/src/pages/Dashboard.tsx) — overview con KPIs y evolución de portafolio (parcialmente con mocks).
- [`src/pages/AssetExplorer.tsx`](Nexvest-Front/src/pages/AssetExplorer.tsx) — viewer real de los 21 activos vía API, SMA20/SMA50 incluidos.
- [`src/pages/SimilarityAnalysis.tsx`](Nexvest-Front/src/pages/SimilarityAnalysis.tsx) — Euclidean, Pearson, Cosine **calculados en el cliente**; DTW solo aparece en tabla de complejidad.
- [`src/pages/CorrelationHeatmap.tsx`](Nexvest-Front/src/pages/CorrelationHeatmap.tsx) — heatmap 8×8 con datos estáticos.
- [`src/pages/PatternDetection.tsx`](Nexvest-Front/src/pages/PatternDetection.tsx) — UI lista, sin cómputo real.
- [`src/pages/RiskDashboard.tsx`](Nexvest-Front/src/pages/RiskDashboard.tsx) — clasificación completa con [`src/data/mockData.ts`](Nexvest-Front/src/data/mockData.ts).
- [`src/lib/api.ts`](Nexvest-Front/src/lib/api.ts) — cliente con `fetchHistoricos()` y `fetchMnemonics()`.

### ❌ Pendiente (en orden de ejecución sugerido)

#### 2.1 Reconectar páginas a los endpoints reales del backend
Una vez existan los endpoints del punto 1, en [`src/lib/api.ts`](Nexvest-Front/src/lib/api.ts) añadir:
- [ ] `fetchSimilarity(a, b, metrica, base)`.
- [ ] `fetchCorrelationMatrix(tickers, desde, hasta)`.
- [ ] `fetchPattern(ticker, tipo, ventana)`.
- [ ] `fetchVolatility(ticker)`.
- [ ] `fetchRiskRanking()`.
- [ ] `fetchPdfReport(tickers)` (descarga blob).

Refactor de páginas para consumir esos endpoints en lugar de mocks:
- [ ] [`SimilarityAnalysis.tsx`](Nexvest-Front/src/pages/SimilarityAnalysis.tsx) — pedir el cálculo al backend (la rúbrica evalúa la **implementación algorítmica**, no debe quedar solo en el frontend); incluir **DTW**.
- [ ] [`CorrelationHeatmap.tsx`](Nexvest-Front/src/pages/CorrelationHeatmap.tsx) — reemplazar matriz hardcoded por respuesta del backend; activar selector de algoritmo y filtro de fechas.
- [ ] [`PatternDetection.tsx`](Nexvest-Front/src/pages/PatternDetection.tsx) — botón "Run Analysis" debe llamar a `/analisis/patrones`; mostrar resultados reales en timeline y tabla.
- [ ] [`RiskDashboard.tsx`](Nexvest-Front/src/pages/RiskDashboard.tsx) — reemplazar `RISK_DATA` por `/analisis/riesgo`.
- [ ] [`Dashboard.tsx`](Nexvest-Front/src/pages/Dashboard.tsx) — quitar mocks de "recent patterns".

#### 2.2 Candlestick real (R4) — **falta del todo**
- [ ] Añadir `lightweight-charts` (recomendado por TradingView) o `react-financial-charts` a [`package.json`](Nexvest-Front/package.json).
- [ ] En [`AssetExplorer.tsx`](Nexvest-Front/src/pages/AssetExplorer.tsx) reemplazar la combinación Bar+Line por velas OHLC reales con SMA20 y SMA50 superpuestas.

#### 2.3 Export PDF (R4)
- [ ] Botón actual en [`CorrelationHeatmap.tsx`](Nexvest-Front/src/pages/CorrelationHeatmap.tsx) no hace nada. Conectar a `fetchPdfReport` (que descarga el blob desde el backend), o bien instalar `jspdf` + `html2canvas` y generarlo en el cliente. **Recomendado:** backend (más controlable y reproducible).

#### 2.4 [`src/pages/Settings.tsx`](Nexvest-Front/src/pages/Settings.tsx)
- [ ] Decidir si se elimina del sidebar o se implementa (ej: rango de fechas global, refresh ETL).

---

## 3. Despliegue (R5)

- [ ] Verificar que [`Nexvest-Back-FASTAPI/vercel.json`](Nexvest-Back-FASTAPI/vercel.json) levanta correctamente FastAPI como serverless (cuidar el tiempo de cómputo de DTW para 5 años — puede pasar el timeout de 10s de Vercel hobby; considerar Railway / Render como alternativa para el backend).
- [ ] Configurar `VITE_API_URL` en [`Nexvest-Front/vercel.json`](Nexvest-Front/vercel.json) apuntando al backend desplegado.
- [ ] Variable de entorno `MONGODB_URI` en producción.
- [ ] README con instrucciones reproducibles (descarga ETL desde cero → carga a Mongo → arranque API → arranque front).

---

## 4. Documento final de diseño

Pendiente entregar:
- [ ] Arquitectura general (diagrama componentes: ETL ↔ Mongo ↔ FastAPI ↔ React).
- [ ] **Por cada requerimiento (R1–R5):** explicación técnica con detalles de implementación.
- [ ] **Por cada algoritmo de similitud y de patrón:** formulación matemática + pseudocódigo + análisis de complejidad temporal y espacial + comparación entre enfoques.
- [ ] Justificación de las decisiones de limpieza de datos (R1).
- [ ] Declaración explícita del uso de IA generativa.

---

## 5. Orden de ejecución recomendado

1. **Backend — algoritmos puros** (sin tocar HTTP todavía): crear [`algorithms/similitud.py`](Nexvest-Back-FASTAPI/algorithms/similitud.py), [`algorithms/patrones.py`](Nexvest-Back-FASTAPI/algorithms/patrones.py), [`algorithms/volatilidad.py`](Nexvest-Back-FASTAPI/algorithms/volatilidad.py) con tests rápidos sobre el JSON ya descargado en `etl/historicos/`.
2. **Backend — endpoints** en [`routers/analisis.py`](Nexvest-Back-FASTAPI/routers/analisis.py): similitud → correlación → volatilidad/riesgo → patrones → PDF.
3. **Limpieza ETL** [`etl/limpieza.py`](Nexvest-Back-FASTAPI/etl/limpieza.py) (puede ir en paralelo con el paso 1).
4. **Frontend — reconexión:** ampliar [`src/lib/api.ts`](Nexvest-Front/src/lib/api.ts) y refactor de páginas que hoy usan mocks.
5. **Candlestick** en [`AssetExplorer.tsx`](Nexvest-Front/src/pages/AssetExplorer.tsx).
6. **Botón de PDF** funcional.
7. **Despliegue + README reproducible.**
8. **Documento de diseño + análisis de complejidad.**
