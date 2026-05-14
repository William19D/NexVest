# NexVest - Documento de arquitectura

Documento de diseno del proyecto NexVest, asignatura **Analisis de Algoritmos**
(Universidad del Quindio, 2026-1).

---

## 1. Vision general

NexVest es un sistema en tres capas:

```
                                       Internet
                                          |
                          BVC token API   |   Yahoo Finance API
                                  \       |       /
                                   \      |      /
                              +-----v-----v-----v------+
                              |  ETL (Python puro)     |
                              |  - Construye consultas |
                              |  - HTTP directo        |
                              |  - Parseo manual       |
                              +-----------+------------+
                                          | escribe JSON
                                          v
                              +-----------+------------+
                              |  etl/historicos/*.json |   (snapshot reproducible)
                              +-----------+------------+
                                          | upsert idempotente
                                          v
                              +-----------+------------+
                              |  MongoDB Atlas         |
                              |  21 colecciones        |
                              |  historico_<mnemonic>  |
                              +-----------+------------+
                                          ^
                                          | lectura
                                          |
                              +-----------+------------+
                              |  Backend FastAPI       |
                              |  /historicos/*         |
                              |  /analisis/*           |
                              |  - similitud (4)       |
                              |  - patrones (sliding)  |
                              |  - volatilidad         |
                              |  - correlacion NxN     |
                              |  - reporte PDF         |
                              +-----------+------------+
                                          |  JSON / PDF (HTTP)
                                          v
                              +-----------+------------+
                              |  Frontend React+Vite   |
                              |  TS + Tailwind         |
                              |  6 paginas + sidebar   |
                              +------------------------+
```

---

## 2. Stack tecnologico

| Capa | Tecnologia | Por que |
|---|---|---|
| ETL | Python 3.11, `requests`, `threading` | HTTP directo, control total sobre construccion de consultas, retries y parsing. Sin yfinance. |
| Almacenamiento | MongoDB Atlas (free tier) | Una coleccion por activo; documentos sin esquema rigido, lo que simplifica el ingest cuando BVC y Yahoo devuelven campos distintos. |
| Backend | FastAPI + Uvicorn | Tipado por Pydantic, generacion automatica de OpenAPI, latencia baja con `pymongo`. |
| Calculo | Python puro | Todos los algoritmos exigidos por la rubrica estan implementados manualmente. matplotlib y reportlab se usan unicamente para el render del reporte (no implementan algoritmos). |
| Frontend | React 18 + Vite + TypeScript | SPA tipada, hot reload rapido. |
| Estilos | Tailwind + shadcn-ui | Sistema de diseno con tokens, sin CSS custom disperso. |
| Visualizacion | Recharts + SVG puro | Recharts para graficos genericos (line/bar); SVG manual para el candlestick (Recharts no tiene primitiva OHLC). |

---

## 3. Modulos del backend (vista por roles)

```
algorithms/                       --- nucleo algoritmico (sin librerias)
├── algoritmos_ordenamiento.py    [12 sorts: TimSort, QuickSort, HeapSort, ...]
├── similitud.py                  [Euclidean, Pearson, DTW, Coseno]
├── patrones.py                   [dias_consec_alza, ruptura_maximo_ventana]
├── volatilidad.py                [std muestral, sigma anual, clasificacion]
└── desempeno.py                  [benchmark de los 12 sorts]

etl/                              --- adquisicion + limpieza
├── finalInfoScript.py            [descarga: BVC token + Yahoo v8/v7]
├── storage.py                    [upsert a Mongo, idempotente]
├── historicos/                   [21 archivos *_historico.json]
└── limpieza/
    ├── deteccion.py              [close<=0, z-score iterativo, retorno absoluto]
    ├── correccion.py             [eliminar / forward_fill]
    ├── pipeline.py               [orquesta detectar -> corregir]
    ├── reporte.py                [DTO ReporteLimpieza con convergencia]
    └── __init__.py               [fachada publica: limpiar_serie]

reportes/                         --- generacion de PDF
├── medias_moviles.py             [SMA O(n) con suma corredera]
├── graficos.py                   [heatmap + candlestick (matplotlib Agg)]
├── tablas.py                     [Table de reportlab para riesgo / pares]
├── pdf_builder.py                [armado del documento, secciones, paginas]
└── generador.py                  [API de alto nivel; orquesta los 3 anteriores]

routers/                          --- HTTP / FastAPI
├── _carga.py                     [cargar_serie / cargar_portafolio con normalizacion]
├── historicos.py                 [GET /historicos/*]
└── analisis.py                   [GET /analisis/*]
```

**Principio de diseno:** cada archivo tiene un rol unico (deteccion, correccion,
orquestacion, etc.). Ningun archivo supera 300 lineas. Los modulos de
algorithms/ son funciones puras sin dependencias externas, lo que facilita
testearlos en aislamiento.

---

## 4. Modulos del frontend (vista por roles)

```
src/
├── pages/                        --- vistas, una por ruta
├── components/                   --- piezas reutilizables (CandlestickChart, RiskBadge, ...)
├── lib/
│   ├── api.ts                    [http<T>() generico, construccion de URLs]
│   └── services/                 --- una capa por dominio
│       ├── historicos.ts
│       ├── similitud.ts
│       ├── correlacion.ts
│       ├── patrones.ts
│       ├── riesgo.ts
│       └── reporte.ts            [fetchReportePdf + descargarBlob]
├── data/                         --- constantes (tickers)
└── types/                        --- tipos compartidos
```

**Principio:** las paginas son delgadas. Toda la logica de red vive en
`lib/services/`, lo que permite cambiar el backend sin tocar las paginas.

---

## 5. Flujo de datos representativo: pagina Similarity Analysis

```
Usuario selecciona ECOPETROL y ISA
   |
   v
SimilarityAnalysis.tsx llama:
   - fetchHistoricos(ECOPETROL)        ---> GET /historicos/ECOPETROL
   - fetchHistoricos(ISA)              ---> GET /historicos/ISA
   - fetchSimilitud({a, b, base})      ---> GET /analisis/similitud?a&b&base
                                            |
                                            v
                                     routers/_carga.py
                                            | cargar_serie (con limpieza)
                                            v
                                     etl.limpieza.limpiar_serie
                                            | serie limpia
                                            v
                                     algorithms.similitud.comparar_activos
                                            | alinear_por_fechas + 4 metricas
                                            v
                                     JSON con 4 valores
   |
   v
La pagina renderiza KPIs + chart normalizado, sin recalcular en cliente.
```

Los calculos algoritmicos viven en el backend para cumplir la rubrica
("los algoritmos deberan ser implementados de forma explicita por los
estudiantes"); el frontend solo orquesta, visualiza y permite descarga.

---

## 6. Decisiones de diseno relevantes

### 6.1 Limpieza activa por defecto

`cargar_serie(..., limpiar=True)` se activa por defecto en todos los endpoints
de analisis. La limpieza:

1. Elimina filas con `close <= 0` (dias sin operacion artefactuales).
2. Elimina fechas duplicadas.
3. Itera hasta 5 pasadas removiendo outliers por z-score (`|z| > 6`) y por
   retorno absoluto (`|r| > 50%`).
4. Marca `convergencia=False` si despues de las pasadas siguen quedando
   retornos extremos (caso CNEC con split no ajustado).

Sin este paso, varias acciones colombianas mostraban volatilidades anualizadas
absurdas (200-500%) por filas espurias.

### 6.2 Candlestick custom

Recharts no tiene primitiva OHLC. Se implemento [`components/CandlestickChart.tsx`](../Nexvest-Front/src/components/CandlestickChart.tsx)
en SVG puro: una linea vertical para low-high y un rectangulo para open-close,
con SMA20/SMA50 superpuestas como polilineas. Evita anadir
`lightweight-charts` u otra dependencia pesada.

### 6.3 Generacion de PDF en backend

El reporte tecnico (correlacion + riesgo + candlestick + apendice de limpieza)
se construye en el servidor con `reportlab` y `matplotlib`. Razones:

- El backend ya tiene la matriz y las series limpias: evita transferir datos
  voluminosos al frontend solo para regenerarlos.
- `reportlab` permite resultados reproducibles, mientras que `jsPDF` en cliente
  depende del estado del DOM.
- Permite servir el endpoint a otras integraciones (por ejemplo, un script
  programado).

### 6.4 Reproducibilidad

El dataset NUNCA se distribuye como archivo plano. El flujo completo es:

```
finalInfoScript.py  ->  etl/historicos/*.json  ->  storage.py  ->  MongoDB
```

Cualquier evaluador con las credenciales de Mongo (o uno propio) puede
reconstruir el dataset desde cero en menos de 10 minutos.

---

## 7. Limites conocidos

| Limite | Mitigacion |
|---|---|
| `CNEC` muestra volatilidad ~200% por un evento corporativo no ajustado en los datos crudos | El reporte marca `convergencia=False` y se documenta en el apendice del PDF. |
| Endpoint `/analisis/reporte/pdf` puede tomar 10-30 segundos para portafolio completo | Para deploy en Vercel hobby (limite 10s) seria necesario un host con timeout extendido (Railway / Render / fly.io). |
| El BVC API no es publica oficial; depende del token de la pagina | El ETL refresca el token automaticamente cuando expira. |
