# NexVest

Plataforma de analisis financiero algoritmico desarrollada como proyecto de la
asignatura **Analisis de Algoritmos** (Programa de Ingenieria de Sistemas y
Computacion, Universidad del Quindio, periodo 2026-1).

El sistema descarga, limpia y analiza series historicas de la **Bolsa de Valores
de Colombia (BVC)** y de ETFs internacionales relevantes. Todos los algoritmos
exigidos por la rubrica (similitud, deteccion de patrones, volatilidad, riesgo)
estan implementados a mano, sin librerias de alto nivel.

---

## Tabla de contenidos

1. [Arquitectura general](#arquitectura-general)
2. [Activos analizados](#activos-analizados)
3. [Requisitos previos](#requisitos-previos)
4. [Reproducibilidad: ejecutar el proyecto desde cero](#reproducibilidad-ejecutar-el-proyecto-desde-cero)
5. [Documentacion adicional](#documentacion-adicional)

---

## Arquitectura general

```
+----------------------+        +-------------------+        +----------------+
|  ETL (Python puro)   |  -->   |    MongoDB        |  <--   |  FastAPI       |
|  - BVC token + API   |        |  21 colecciones   |        |  /historicos   |
|  - Yahoo Finance     |        |  historico_<tk>   |        |  /analisis/*   |
|  - HTTP directo      |        +-------------------+        +-------+--------+
|  - sin yfinance      |                                              |
+----------------------+                                              | JSON / PDF
                                                                      v
                                                          +-----------+-----------+
                                                          |  Frontend React+Vite  |
                                                          |  Dashboard, Asset     |
                                                          |  Explorer, Similitud, |
                                                          |  Correlacion, Riesgo, |
                                                          |  Patrones, PDF        |
                                                          +-----------------------+
```

Mas detalle en [DOCUMENTACION/ARQUITECTURA.md](DOCUMENTACION/ARQUITECTURA.md).

---

## Activos analizados

**Acciones colombianas (15):** ECOPETROL, ISA, GEB, PFBCOLOM, NUTRESA,
GRUPOSURA, CELSIA, EXITO, CEMARGOS, CNEC, CORFICOLCF, PROMIGAS, MINEROS, CLH,
PFDAVVNDA.

**ETFs globales (6):** VOO, CSPX.L, SPY, QQQ, IVV, GLD.

**Total: 21 activos**, con horizonte historico aproximado de 5 anios (2021 - 2026).

---

## Requisitos previos

| Herramienta | Version probada | Notas |
|---|---|---|
| Python | 3.11 | Versiones >= 3.10 deberian funcionar |
| Node.js | 20.x | Cualquier LTS reciente |
| MongoDB | 6.x | Local o Atlas. Se usa Atlas en `MONGO_URI`. |
| Git | cualquier | Para clonar el repo |

---

## Reproducibilidad: ejecutar el proyecto desde cero

> El PDF de la asignatura exige que un evaluador pueda ejecutar el proyecto y
> obtener resultados equivalentes sin ajustes manuales. Esta seccion documenta
> el procedimiento completo.

### 1. Backend (FastAPI + ETL)

```bash
cd Nexvest-Back-FASTAPI
python -m venv .venv
.venv\Scripts\activate                # Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt

# Configurar credenciales de MongoDB.
copy .env.example .env                # Linux/Mac: cp .env.example .env
# Editar .env y poner el MONGO_URI propio
```

#### 1.a Descarga y carga del dataset desde cero

El sistema reconstruye los 21 historicos por HTTP directo. **No se usan
librerias de alto nivel prohibidas** (yfinance, pandas_datareader).

```bash
python etl/finalInfoScript.py         # descarga BVC + Yahoo a etl/historicos/
python etl/storage.py                 # upsert idempotente a MongoDB
```

La descarga toma aproximadamente 5-10 minutos dependiendo de la conexion.
Genera 21 archivos `*_historico.json` y luego los sube a la base.

#### 1.b Arrancar la API

```bash
python -m uvicorn main:app --reload --port 8000
```

La API queda disponible en <http://localhost:8000>. La documentacion
interactiva esta en <http://localhost:8000/docs>.

### 2. Frontend (React + Vite)

En otra terminal:

```bash
cd Nexvest-Front
npm install
copy .env.example .env                # o crear .env con VITE_API_URL=http://localhost:8000
npm run dev
```

El frontend queda en <http://localhost:5173>.

### 3. Verificacion rapida

```bash
# El backend debe responder
curl http://localhost:8000/

# Lista de activos disponibles
curl http://localhost:8000/analisis/mnemonicos

# Generar un PDF de ejemplo (lo guarda en reporte.pdf)
curl -o reporte.pdf "http://localhost:8000/analisis/reporte/pdf?tickers=ECOPETROL&tickers=ISA&tickers=VOO"
```

---

## Documentacion adicional

| Documento | Contenido |
|---|---|
| [DOCUMENTACION/ARQUITECTURA.md](DOCUMENTACION/ARQUITECTURA.md) | Diagrama detallado, stack tecnologico, flujo de datos. |
| [DOCUMENTACION/REQUERIMIENTOS.md](DOCUMENTACION/REQUERIMIENTOS.md) | Explicacion tecnica de R1 a R5 con archivos y endpoints involucrados. |
| [DOCUMENTACION/COMPLEJIDAD.md](DOCUMENTACION/COMPLEJIDAD.md) | Analisis formal de complejidad temporal y espacial por algoritmo. |
| [DOCUMENTACION/USO_IA.md](DOCUMENTACION/USO_IA.md) | Declaracion explicita del uso de IA generativa en el desarrollo. |
| [deploy/DEPLOY.md](deploy/DEPLOY.md) | Guia paso a paso de despliegue en un VPS Hetzner (R5). |
| [Nexvest-Back-FASTAPI/README.md](Nexvest-Back-FASTAPI/README.md) | Setup detallado del backend. |
| [Nexvest-Front/README.md](Nexvest-Front/README.md) | Setup detallado del frontend. |
| [ESTADO_Y_PENDIENTES.md](ESTADO_Y_PENDIENTES.md) | Bitacora del avance del proyecto y trabajo pendiente. |

### Actualizacion incremental del dataset

Una vez desplegado, hay dos modos de cargar datos:

- **`python -m etl.finalInfoScript`** — descarga full de 5 anios, sobreescribe los JSON. Solo para el primer arranque.
- **`python -m etl.scheduled`** — descarga incremental: lee la maxima fecha por activo en Mongo y solo trae lo que falta. Idempotente. Es lo que ejecuta el timer `nexvest-etl.timer` cada dia habil a las 22:00 UTC en produccion.
