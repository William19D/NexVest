# NexVest - Frontend

Aplicacion web del proyecto NexVest. **React 18 + Vite + TypeScript + Tailwind**.
Consume los endpoints expuestos por el backend FastAPI.

Para una vista global del proyecto, ver [../README.md](../README.md).

---

## Estructura del proyecto

```
Nexvest-Front/
├── index.html
├── package.json
├── vite.config.ts
├── tailwind.config.ts
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── components/
    │   ├── AppSidebar.tsx
    │   ├── CandlestickChart.tsx     # velas OHLC en SVG puro + SMA
    │   ├── KPICard.tsx
    │   ├── RiskBadge.tsx
    │   └── ...
    ├── pages/
    │   ├── Dashboard.tsx            # KPIs + evolucion + riesgo + patrones
    │   ├── AssetExplorer.tsx        # candlestick + SMA + datos historicos
    │   ├── SimilarityAnalysis.tsx   # los 4 algoritmos de similitud
    │   ├── CorrelationHeatmap.tsx   # matriz NxN + export PDF
    │   ├── PatternDetection.tsx     # sliding window de patrones
    │   └── RiskDashboard.tsx        # ranking de riesgo del portafolio
    ├── lib/
    │   ├── api.ts                   # cliente HTTP base
    │   ├── sma.ts                   # SMA O(n) en cliente
    │   └── services/                # un archivo por dominio
    │       ├── historicos.ts
    │       ├── similitud.ts
    │       ├── correlacion.ts
    │       ├── patrones.ts
    │       ├── riesgo.ts
    │       └── reporte.ts           # descarga del PDF
    ├── data/
    │   └── tickers.ts               # catalogo compartido de tickers
    └── types/
        └── risk.ts                  # tipo RiskCategory
```

---

## Setup

### 1. Dependencias

```bash
npm install
```

### 2. Variables de entorno

Crear `.env`:

```env
VITE_API_URL=http://localhost:8000
```

### 3. Modo desarrollo

```bash
npm run dev
```

Vite arranca en <http://localhost:5173>.

### 4. Build de produccion

```bash
npm run build
npm run preview
```

Los archivos quedan en `dist/` listos para subir a Vercel, Netlify, Cloudflare
Pages, etc.

---

## Paginas

| Ruta | Pagina | Endpoints consumidos |
|---|---|---|
| `/` | Dashboard | `/analisis/mnemonicos`, `/analisis/riesgo`, `/historicos/*`, `/analisis/patrones/*` |
| `/asset-explorer` | Asset Explorer | `/historicos/{ticker}` |
| `/similarity` | Similarity Analysis | `/analisis/similitud`, `/historicos/{ticker}` |
| `/correlation` | Correlation Heatmap | `/analisis/correlacion`, `/analisis/reporte/pdf` |
| `/patterns` | Pattern Detection | `/analisis/patrones/{ticker}`, `/historicos/{ticker}` |
| `/risk` | Risk Dashboard | `/analisis/riesgo` |

---

## Stack

| Tecnologia | Uso |
|---|---|
| React 18 | UI |
| Vite | bundler + dev server |
| TypeScript | tipos estrictos |
| Tailwind CSS | estilos |
| shadcn-ui | componentes base |
| Recharts | line/bar charts |
| lucide-react | iconos |
| SVG nativo | candlestick custom (sin libreria de finanzas) |
