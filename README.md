# NexVest

> Algorithmic financial analytics for the Colombian Stock Exchange and global ETFs.
> Built from scratch as a university project for the *Analisis de Algoritmos* course
> (Universidad del Quindio, 2026-1).

![status](https://img.shields.io/badge/status-deployed-success)
![python](https://img.shields.io/badge/python-3.11-blue)
![fastapi](https://img.shields.io/badge/fastapi-0.109-009688)
![react](https://img.shields.io/badge/react-18-61dafb)
![docker](https://img.shields.io/badge/docker-compose-2496ED)

NexVest pulls daily prices from the **Bolsa de Valores de Colombia (BVC)** and
**Yahoo Finance**, runs every required algorithm by hand (no high-level
shortcuts), and surfaces the results in an interactive dashboard plus a
downloadable PDF report.

The Spanish version of this document lives at [README.es.md](README.es.md).

---

## Table of contents

- [Highlights](#highlights)
- [Live architecture](#live-architecture)
- [Tech stack](#tech-stack)
- [Quick start with Docker](#quick-start-with-docker)
- [Quick start without Docker](#quick-start-without-docker-local-dev)
- [Repository layout](#repository-layout)
- [Algorithms implemented from scratch](#algorithms-implemented-from-scratch)
- [API reference](#api-reference)
- [Daily incremental ETL](#daily-incremental-etl)
- [Documentation index](#documentation-index)
- [License](#license)

---

## Highlights

- **21 assets, 5+ years of daily history**: 15 Colombian stocks (ECOPETROL,
  ISA, GEB, ...) and 6 global ETFs (VOO, SPY, QQQ, IVV, CSPX.L, GLD).
- **No black-box libraries**: every similarity, sorting, pattern detection,
  volatility and cleaning routine is written explicitly in pure Python (no
  `yfinance`, no `pandas_datareader`, no `sklearn.metrics`, no
  `scipy.spatial.distance`, no `numpy.corrcoef`). All algorithms ship with a
  step-by-step docstring and a formal time/space complexity analysis.
- **Reproducible ETL**: the full 5-year dataset for the 21 assets can be
  rebuilt from zero with two commands. A daily incremental job keeps Mongo in
  sync via a cron-friendly scheduler.
- **Interactive dashboard**: 6 pages (Dashboard, Asset Explorer, Similarity,
  Correlation, Patterns, Risk) consuming live endpoints.
- **PDF technical report**: a single endpoint generates a multi-page PDF with
  correlation heatmap, top correlated pairs, risk ranking, candlestick + SMA
  charts and a data-cleaning appendix.
- **Single-command deploy**: `docker compose up -d` brings up the entire
  stack (API + cron + Caddy with automatic HTTPS).

---

## Live architecture

```
                        Internet
                            |
       +--------------------+--------------------+
       |  Caddy v2 (reverse proxy + Let's Encrypt) |
       |  - /          -> SPA static (Vite build)  |
       |  - /api/*     -> reverse_proxy api:8000   |
       +--------------------+--------------------+
                            |
                   internal docker network
                            |
            +---------------+----------------+
            |                                |
   +--------+--------+              +--------+---------+
   |   FastAPI api   |              |  etl-cron        |
   |  - /historicos  |              |  supercronic +   |
   |  - /analisis/*  |              |  python -m etl.. |
   |  - /reporte/pdf |              |  Mon-Fri 22 UTC  |
   +--------+--------+              +--------+---------+
            |                                |
            +-------------+------------------+
                          |
                          v
               MongoDB Atlas (free tier)
              21 collections: historico_<ticker>
```

Three containers, one external dependency (MongoDB Atlas). Caddy is the only
service with public ports (80/443). The API talks to MongoDB Atlas over TLS.

A deep architecture write-up lives at
[DOCUMENTACION/ARQUITECTURA.md](DOCUMENTACION/ARQUITECTURA.md).

---

## Tech stack

| Layer | Stack |
|---|---|
| ETL | Python 3.11, `requests`, `threading` |
| Backend | FastAPI, Uvicorn, Pydantic, PyMongo |
| Data store | MongoDB Atlas |
| Algorithms | Pure Python (no numerical libraries for required algorithms) |
| Reports | matplotlib (PNG generation only), reportlab (PDF composition) |
| Frontend | React 18, Vite, TypeScript, Tailwind CSS, shadcn-ui |
| Charts | Recharts (line/bar), hand-rolled SVG candlestick |
| Reverse proxy | Caddy 2 (automatic HTTPS) |
| Scheduling | supercronic (cron in containers) |
| Container runtime | Docker + Docker Compose |

---

## Quick start with Docker

The fastest path to a running instance. Three containers come up: `api`,
`etl-cron`, `web`.

```bash
# 1. Clone
git clone https://github.com/<owner>/NexVest.git
cd NexVest

# 2. Configure the two .env files
cp .env.example .env
cp Nexvest-Back-FASTAPI/.env.example Nexvest-Back-FASTAPI/.env

# Edit .env                          --> DOMAIN=nexvest.example.com (or <ip>.nip.io)
# Edit Nexvest-Back-FASTAPI/.env     --> MONGO_URI=mongodb+srv://...

# 3. Build and start
docker compose up -d --build

# 4. Verify
curl -I https://<your-domain>
curl https://<your-domain>/api/

# 5. (Cold start) Trigger an immediate ETL run
docker compose exec api python -m etl.scheduled --catchup
```

For a production deploy on a fresh VPS (Hetzner, DigitalOcean, etc.) follow
the step-by-step guide in
[deploy/DEPLOY-DOCKER.md](deploy/DEPLOY-DOCKER.md).

---

## Quick start without Docker (local dev)

Useful for working on the code locally.

```bash
# Backend (terminal 1)
cd Nexvest-Back-FASTAPI
python -m venv .venv && .venv\Scripts\activate          # Windows
# source .venv/bin/activate                              # macOS / Linux
pip install -r requirements.txt
cp .env.example .env                                    # then edit MONGO_URI
python -m uvicorn main:app --reload --port 8000

# Frontend (terminal 2)
cd Nexvest-Front
npm install
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev
```

Browse to <http://localhost:5173>.

---

## Repository layout

```
NexVest/
├── README.md                       # this file
├── README.es.md                    # Spanish overview
├── docker-compose.yml              # 3-service stack: api + etl-cron + web
├── .env.example                    # DOMAIN for the stack
│
├── Nexvest-Back-FASTAPI/           # Python backend
│   ├── Dockerfile                  # base image used by api + etl-cron
│   ├── main.py                     # FastAPI entrypoint
│   ├── database.py                 # MongoDB singleton
│   ├── algorithms/                 # hand-written algorithms (R2, R3)
│   │   ├── similitud.py            # Euclidean, Pearson, DTW, Cosine
│   │   ├── patrones.py             # sliding-window pattern detectors
│   │   ├── volatilidad.py          # std, annualized vol, risk buckets
│   │   ├── algoritmos_ordenamiento.py   # 12 sort implementations
│   │   └── desempeno.py            # sorting benchmark harness
│   ├── etl/                        # data acquisition + cleaning (R1)
│   │   ├── finalInfoScript.py      # full 5-year download (HTTP only)
│   │   ├── scheduled.py            # incremental ETL with --catchup mode
│   │   ├── storage.py              # idempotent upsert to MongoDB
│   │   └── limpieza/               # detection + correction + reporting
│   ├── reportes/                   # PDF generation (R4)
│   │   ├── graficos.py             # heatmap + candlestick PNGs
│   │   ├── tablas.py               # reportlab tables
│   │   ├── pdf_builder.py          # document assembly
│   │   └── generador.py            # high-level orchestrator
│   └── routers/                    # FastAPI routers
│       ├── historicos.py
│       └── analisis.py
│
├── Nexvest-Front/                  # React + Vite + TypeScript SPA
│   ├── Dockerfile                  # multi-stage Node build + Caddy serve
│   └── src/
│       ├── pages/                  # Dashboard, AssetExplorer, ...
│       ├── components/             # CandlestickChart, RiskBadge, ...
│       ├── lib/services/           # one file per backend domain
│       └── lib/sma.ts              # client-side SMA helper
│
├── deploy/                         # production artifacts
│   ├── DEPLOY-DOCKER.md            # step-by-step deploy guide
│   ├── Caddyfile                   # reverse proxy + HTTPS
│   ├── crontab                     # supercronic schedule
│   └── systemd/                    # bare-metal alternative (not used by default)
│
└── DOCUMENTACION/                  # course deliverables (in Spanish)
    ├── ARQUITECTURA.md             # design document
    ├── REQUERIMIENTOS.md           # technical explanation per R1-R5
    ├── COMPLEJIDAD.md              # formal complexity analysis
    └── USO_IA.md                   # AI usage declaration
```

---

## Algorithms implemented from scratch

### Similarity (R2)

| Algorithm | File | Time | Space |
|---|---|---|---|
| Euclidean distance | [`similitud.py`](Nexvest-Back-FASTAPI/algorithms/similitud.py) | O(n) | O(1) |
| Pearson correlation | [`similitud.py`](Nexvest-Back-FASTAPI/algorithms/similitud.py) | O(n) | O(1) |
| Dynamic Time Warping | [`similitud.py`](Nexvest-Back-FASTAPI/algorithms/similitud.py) | O(n*m) | O(n*m) |
| Cosine similarity | [`similitud.py`](Nexvest-Back-FASTAPI/algorithms/similitud.py) | O(n) | O(1) |

Includes helpers for date alignment and simple-return computation. DTW
supports an optional Sakoe-Chiba band to reduce search complexity.

### Patterns (R3)

| Pattern | File | Time | Notes |
|---|---|---|---|
| `k` consecutive up days | [`patrones.py`](Nexvest-Back-FASTAPI/algorithms/patrones.py) | O(n) | Sliding-window counter |
| `k`-day high breakout | [`patrones.py`](Nexvest-Back-FASTAPI/algorithms/patrones.py) | O(n*k) | Custom-formalized pattern |

### Risk (R3)

Hand-implemented sample standard deviation (n-1 divisor), annualised
volatility (sqrt(252) factor), and three-bucket classifier
(`conservador / moderado / agresivo`) with documented thresholds.

### Sorting (auxiliary)

12 sorts in [`algoritmos_ordenamiento.py`](Nexvest-Back-FASTAPI/algorithms/algoritmos_ordenamiento.py):
TimSort (run-detection hybrid), Comb, Selection, Tree, Pigeonhole, Bucket,
Quick (3-way), Heap, Bitonic, Gnome, Binary Insertion, Radix (LSD with stable
pre-pass).

A consolidated formal complexity analysis lives at
[DOCUMENTACION/COMPLEJIDAD.md](DOCUMENTACION/COMPLEJIDAD.md).

---

## API reference

The API is fully documented via OpenAPI at `<host>/docs` (when running).
The most useful endpoints:

### Historical data (`/historicos`)

| Method | Path | Notes |
|---|---|---|
| GET | `/historicos/mnemonics` | List available tickers. |
| GET | `/historicos/{ticker}?desde&hasta&limit` | OHLCV by ticker, filterable. |
| GET | `/historicos/{ticker}/{date}` | Single-day record. |

### Algorithmic analysis (`/analisis`)

| Method | Path | Algorithm invoked |
|---|---|---|
| GET | `/analisis/mnemonicos` | catalogue |
| GET | `/analisis/similitud?a&b&base&ventana_dtw` | Euclidean + Pearson + DTW + Cosine in one shot |
| GET | `/analisis/correlacion?tickers&base` | NxN Pearson matrix |
| GET | `/analisis/patrones/{ticker}?k` | Both sliding-window patterns |
| GET | `/analisis/volatilidad/{ticker}` | sigma diario, sigma anual, categoria |
| GET | `/analisis/riesgo?tickers` | Full portfolio ranking |
| GET | `/analisis/ordenamiento` | Benchmark of the 12 sorts |
| GET | `/analisis/limpieza/{ticker}` | Per-ticker cleaning report |
| GET | `/analisis/reporte/pdf?tickers&tickers_candle&base&desde&hasta` | Multi-page PDF report |

The PDF endpoint streams `application/pdf` with `Content-Disposition: attachment`.

---

## Daily incremental ETL

The full 5-year download takes about 2 minutes. The incremental scheduler is
much smaller: it queries Mongo for the most recent loaded date and only
fetches the gap.

```bash
# Daily mode (max - 7 days lookback, ~30 seconds)
docker compose exec api python -m etl.scheduled

# Catch-up mode (uses min across tickers, brings stale tickers to today)
docker compose exec api python -m etl.scheduled --catchup
```

In the deployed stack this runs automatically Monday-Friday at **22:00 UTC**
(17:00 Colombia time, two hours after the BVC close) via supercronic inside
the `etl-cron` container. The schedule lives at
[deploy/crontab](deploy/crontab).

All writes are idempotent: `bulk_write` upserts keyed by the `date` field
guarantee no duplicates regardless of how many times the job runs.

---

## Documentation index

| Document | Description |
|---|---|
| [README.es.md](README.es.md) | Spanish project overview. |
| [DOCUMENTACION/ARQUITECTURA.md](DOCUMENTACION/ARQUITECTURA.md) | Full architecture write-up (Spanish). |
| [DOCUMENTACION/REQUERIMIENTOS.md](DOCUMENTACION/REQUERIMIENTOS.md) | Per-requirement implementation breakdown (Spanish). |
| [DOCUMENTACION/COMPLEJIDAD.md](DOCUMENTACION/COMPLEJIDAD.md) | Formal time & space complexity analysis. |
| [DOCUMENTACION/USO_IA.md](DOCUMENTACION/USO_IA.md) | Declaration of AI tooling usage during development. |
| [deploy/DEPLOY-DOCKER.md](deploy/DEPLOY-DOCKER.md) | Step-by-step Docker deployment guide. |
| [Nexvest-Back-FASTAPI/README.md](Nexvest-Back-FASTAPI/README.md) | Backend setup and module map. |
| [Nexvest-Front/README.md](Nexvest-Front/README.md) | Frontend setup and page map. |

---

## License

This project was developed as an academic deliverable. Source code is
released under the MIT License (see `LICENSE`). The project PDF and any
brand assets remain property of their respective owners.
