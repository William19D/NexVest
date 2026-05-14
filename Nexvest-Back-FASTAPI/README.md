# NexVest - Backend

API y modulo de analisis algoritmico del proyecto NexVest. Construido en
**Python 3.11 + FastAPI + MongoDB**, sin librerias de alto nivel prohibidas por
la rubrica de la asignatura.

Para una vista global del proyecto, ver [../README.md](../README.md).

---

## Estructura del proyecto

```
Nexvest-Back-FASTAPI/
├── main.py                         # punto de entrada FastAPI (CORS + routers)
├── database.py                     # singleton MongoDB
├── requirements.txt                # dependencias permitidas
├── algorithms/                     # algoritmos implementados a mano
│   ├── algoritmos_ordenamiento.py  # 12 sorts (TimSort, QuickSort, ...)
│   ├── similitud.py                # Euclidean, Pearson, DTW, Coseno
│   ├── patrones.py                 # sliding window: dias consec alza + breakout
│   ├── volatilidad.py              # std muestral, sigma anualizada, riesgo
│   └── desempeno.py                # benchmark de los 12 sorts
├── etl/                            # extraccion, limpieza, carga
│   ├── finalInfoScript.py          # descarga BVC (token) + Yahoo (HTTP directo)
│   ├── storage.py                  # upsert idempotente a MongoDB
│   ├── historicos/                 # JSONs crudos por ticker
│   └── limpieza/                   # paquete de limpieza (5 modulos)
│       ├── deteccion.py            # detectores: close<=0, z-score, retorno abs
│       ├── correccion.py           # eliminar / forward-fill
│       ├── pipeline.py             # orquestador iterativo
│       ├── reporte.py              # DTO ReporteLimpieza
│       └── __init__.py             # fachada publica
├── reportes/                       # generacion de PDF
│   ├── medias_moviles.py           # SMA O(n) manual
│   ├── graficos.py                 # heatmap + candlestick (matplotlib)
│   ├── tablas.py                   # tablas reportlab
│   ├── pdf_builder.py              # ensamblador del documento
│   └── generador.py                # API de alto nivel
└── routers/                        # endpoints FastAPI
    ├── _carga.py                   # helper de carga + normalizacion
    ├── historicos.py               # /historicos/* (series crudas)
    └── analisis.py                 # /analisis/* (algoritmos + reporte)
```

---

## Setup

### 1. Entorno virtual

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux/Mac
pip install -r requirements.txt
```

### 2. Variables de entorno

Crear un archivo `.env` (o copiar `.env.example`):

```env
MONGO_URI=mongodb+srv://<usuario>:<password>@<cluster>/?appName=NexVest
MONGO_DB_NAME=nexvest
```

### 3. Construir el dataset (solo la primera vez)

```bash
python etl/finalInfoScript.py    # descarga 21 historicos por HTTP
python etl/storage.py            # carga a MongoDB
```

### 4. Levantar la API

```bash
python -m uvicorn main:app --reload --port 8000
```

Documentacion OpenAPI interactiva: <http://localhost:8000/docs>.

---

## Endpoints

### Datos crudos (`/historicos`)

| Endpoint | Descripcion |
|---|---|
| `GET /historicos/mnemonics` | Lista de mnemonicos disponibles en Mongo. |
| `GET /historicos/{mnemonic}` | Historico filtrable por `desde`, `hasta`, `limit`. |
| `GET /historicos/{mnemonic}/{date}` | Registro de un dia especifico. |

### Analisis algoritmico (`/analisis`)

| Endpoint | Algoritmo invocado |
|---|---|
| `GET /analisis/mnemonicos` | Lista de mnemonicos. |
| `GET /analisis/similitud?a&b&base&ventana_dtw` | Euclidean, Pearson, DTW, Coseno. |
| `GET /analisis/correlacion?tickers&base` | Matriz NxN de Pearson. |
| `GET /analisis/patrones/{mnemonic}?k` | Dias consec al alza + ruptura de maximo. |
| `GET /analisis/volatilidad/{mnemonic}` | sigma diario, sigma anual, categoria de riesgo. |
| `GET /analisis/riesgo?tickers` | Ranking completo del portafolio. |
| `GET /analisis/ordenamiento` | Benchmark de los 12 algoritmos de ordenamiento. |
| `GET /analisis/limpieza/{mnemonic}` | Reporte de filas descartadas por la limpieza. |
| `GET /analisis/reporte/pdf?tickers&tickers_candle&base` | PDF tecnico consolidado. |

---

## Dependencias

```
fastapi              # framework HTTP
uvicorn[standard]    # servidor ASGI
pymongo[srv]         # cliente Mongo
dnspython            # SRV para Atlas
python-dotenv        # .env loader
pydantic + pydantic-settings
requests             # HTTP directo en el ETL
matplotlib           # graficos del PDF
reportlab            # composicion del PDF
```

**Librerias prohibidas que NO se usan:** `yfinance`, `pandas_datareader`,
`sklearn.metrics`, `scipy.spatial.distance`, `numpy.corrcoef`. Todos los
algoritmos exigidos por la rubrica estan implementados a mano (ver el archivo
[../DOCUMENTACION/COMPLEJIDAD.md](../DOCUMENTACION/COMPLEJIDAD.md)).

---

## Tests

Hay tres suites principales (no automatizadas, se ejecutan como scripts):

```bash
# Unitarios algorithms/ (sorting, similitud, patrones, volatilidad)
# y etl/limpieza
python -m py_compile algorithms/*.py etl/limpieza/*.py reportes/*.py routers/*.py

# Suites de smoke + integracion estan en C:\temp/ durante el desarrollo;
# verifican que cada endpoint produce respuestas validas contra MongoDB.
```

---

## Restricciones de la asignatura respetadas

- Adquisicion de datos por HTTP directo (no yfinance, no pandas_datareader).
- Todos los algoritmos de similitud, sliding window, volatilidad y
  ordenamiento estan escritos a mano.
- Sin librerias de ML que encapsulen los algoritmos en una sola llamada.
- ETL reproducible: el dataset se reconstruye desde cero ejecutando
  `etl/finalInfoScript.py` + `etl/storage.py`.
