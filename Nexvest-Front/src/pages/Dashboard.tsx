import { useEffect, useMemo, useState } from "react";
import {
  Database, Calendar, RefreshCw, Activity, Loader2, AlertCircle,
  TrendingUp, TrendingDown,
} from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";
import KPICard from "@/components/KPICard";
import RiskBadge from "@/components/RiskBadge";
import {
  fetchHistoricos, fetchMnemonicos, fetchRiesgoPortafolio, fetchPatrones,
  type RiesgoResponse, type CategoriaRiesgo, type PatronesResponse,
} from "@/lib/services";

interface PuntoChart {
  date: string;
  [ticker: string]: string | number;
}

interface EventoPatron {
  ticker: string;
  fecha: string;
  patron: string;
}

const TICKERS_CHART = [
  { ticker: "ECOPETROL", color: "hsl(166,100%,42%)" },
  { ticker: "ISA", color: "hsl(38,92%,50%)" },
  { ticker: "GEB", color: "hsl(0,72%,51%)" },
  { ticker: "VOO", color: "hsl(270,60%,60%)" },
  { ticker: "GLD", color: "hsl(200,80%,55%)" },
];

const RANGOS = ["1M", "3M", "6M", "1Y", "5Y"] as const;
type Rango = typeof RANGOS[number];
const DIAS_BURSATILES_POR_RANGO: Record<Rango, number> = {
  "1M": 22, "3M": 65, "6M": 130, "1Y": 252, "5Y": 1260,
};

function categoriaDisplay(cat: CategoriaRiesgo) {
  if (cat === "conservador") return "Conservative" as const;
  if (cat === "moderado") return "Moderate" as const;
  return "Aggressive" as const;
}

function nombreLegiblePatron(clave: string): string {
  if (clave === "dias_consecutivos_alza") return "dias consecutivos al alza";
  if (clave === "ruptura_maximo_ventana") return "ruptura de maximo";
  return clave;
}

export default function Dashboard() {
  const [rango, setRango] = useState<Rango>("1Y");

  const [mnemonicos, setMnemonicos] = useState<string[]>([]);
  const [riesgo, setRiesgo] = useState<RiesgoResponse | null>(null);
  const [series, setSeries] = useState<Record<string, { date: string; close: number }[]>>({});
  const [patrones, setPatrones] = useState<EventoPatron[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actualizado, setActualizado] = useState<Date | null>(null);

  useEffect(() => {
    let cancelado = false;
    setLoading(true);
    setError(null);

    // Cargar en paralelo lo necesario para el Dashboard.
    const peticiones = [
      fetchMnemonicos(),
      fetchRiesgoPortafolio(),
      Promise.all(
        TICKERS_CHART.map((t) =>
          fetchHistoricos(t.ticker, { limit: DIAS_BURSATILES_POR_RANGO["5Y"] }).then(
            (r) => ({
              ticker: t.ticker,
              data: r.data.map((e) => ({
                date: e.date,
                close: parseFloat(String(e.close)),
              })),
            })
          )
        )
      ),
      Promise.all([
        fetchPatrones({ mnemonic: "ECOPETROL", k: 3 }),
        fetchPatrones({ mnemonic: "ISA", k: 3 }),
      ]),
    ] as const;

    Promise.all(peticiones)
      .then(([mnem, ranking, historicos, patronesPorTicker]) => {
        if (cancelado) return;

        setMnemonicos(mnem);
        setRiesgo(ranking);

        const mapa: Record<string, { date: string; close: number }[]> = {};
        for (const h of historicos as { ticker: string; data: { date: string; close: number }[] }[]) {
          mapa[h.ticker] = h.data;
        }
        setSeries(mapa);

        const eventos: EventoPatron[] = [];
        for (const respuesta of patronesPorTicker as PatronesResponse[]) {
          for (const patronResultado of respuesta.patrones) {
            const fechas = patronResultado.fechas.slice(-5);
            for (const fecha of fechas) {
              eventos.push({
                ticker: respuesta.mnemonic,
                fecha,
                patron: nombreLegiblePatron(patronResultado.patron),
              });
            }
          }
        }
        eventos.sort((a, b) => (a.fecha < b.fecha ? 1 : -1));
        setPatrones(eventos.slice(0, 6));

        setActualizado(new Date());
      })
      .catch((e: Error) => {
        if (!cancelado) setError(e.message);
      })
      .finally(() => {
        if (!cancelado) setLoading(false);
      });

    return () => {
      cancelado = true;
    };
  }, []);

  // Construye la grafica de evolucion normalizada (base 100 al inicio del
  // rango). Cada ticker se alinea por fecha sobre el universo de fechas
  // observado en los datos cargados.
  const chartData = useMemo<PuntoChart[]>(() => {
    if (Object.keys(series).length === 0) return [];

    const tamano = DIAS_BURSATILES_POR_RANGO[rango];
    const fechasGlobales = new Set<string>();
    for (const ticker of Object.keys(series)) {
      const recorte = series[ticker].slice(-tamano);
      for (const punto of recorte) fechasGlobales.add(punto.date);
    }
    const fechasOrdenadas = Array.from(fechasGlobales).sort();

    const mapasPorTicker: Record<string, Map<string, number>> = {};
    for (const ticker of Object.keys(series)) {
      const recorte = series[ticker].slice(-tamano);
      const mapa = new Map<string, number>();
      for (const punto of recorte) mapa.set(punto.date, punto.close);
      mapasPorTicker[ticker] = mapa;
    }

    const baseInicial: Record<string, number> = {};
    for (const ticker of Object.keys(series)) {
      const mapa = mapasPorTicker[ticker];
      for (const fecha of fechasOrdenadas) {
        const v = mapa.get(fecha);
        if (v !== undefined && v > 0) {
          baseInicial[ticker] = v;
          break;
        }
      }
    }

    const puntos: PuntoChart[] = [];
    for (const fecha of fechasOrdenadas) {
      const punto: PuntoChart = { date: fecha };
      for (const ticker of Object.keys(series)) {
        const valor = mapasPorTicker[ticker].get(fecha);
        const base = baseInicial[ticker];
        if (valor !== undefined && base !== undefined && base > 0) {
          punto[ticker] = +((valor / base) * 100).toFixed(2);
        }
      }
      puntos.push(punto);
    }
    return puntos;
  }, [series, rango]);

  const topRiesgo = useMemo(() => {
    if (!riesgo) return [];
    return riesgo.ranking.slice(0, 5).map((p) => ({
      ticker: p.ticker,
      sigma: p.volatilidad_anualizada,
      categoria: categoriaDisplay(p.categoria),
    }));
  }, [riesgo]);

  const totalActivos = mnemonicos.length;

  // Rango temporal observado: primer y ultimo dato global.
  const rangoTemporal = useMemo(() => {
    let primer: string | null = null;
    let ultimo: string | null = null;
    for (const ticker of Object.keys(series)) {
      const datos = series[ticker];
      if (datos.length === 0) continue;
      if (primer === null || datos[0].date < primer) primer = datos[0].date;
      if (ultimo === null || datos[datos.length - 1].date > ultimo) ultimo = datos[datos.length - 1].date;
    }
    return { primer, ultimo };
  }, [series]);

  return (
    <div className="space-y-6">
      {/* Top bar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
          <p className="text-sm text-muted-foreground font-mono">
            {new Date().toLocaleDateString("es-CO", { year: "numeric", month: "long", day: "numeric" })}
          </p>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center gap-2 py-12 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span className="text-sm">Cargando datos del portafolio…</span>
        </div>
      )}
      {!loading && error && (
        <div className="flex items-center gap-2 rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {!loading && !error && (
        <>
          {/* KPI Row */}
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <KPICard
              label="Total activos"
              value={String(totalActivos)}
              icon={<Database className="h-4 w-4" />}
            />
            <KPICard
              label="Rango de datos"
              value={
                rangoTemporal.primer && rangoTemporal.ultimo
                  ? `${rangoTemporal.primer.slice(0, 7)} → ${rangoTemporal.ultimo.slice(0, 7)}`
                  : "—"
              }
              icon={<Calendar className="h-4 w-4" />}
            />
            <KPICard
              label="Actualizado"
              value={
                actualizado
                  ? actualizado.toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit" })
                  : "—"
              }
              icon={<RefreshCw className="h-4 w-4" />}
            />
            <KPICard
              label="Estado portafolio"
              value="Activo"
              icon={<Activity className="h-4 w-4" />}
              accent="teal"
            />
          </div>

          <div className="grid gap-6 lg:grid-cols-5">
            {/* Evolucion normalizada */}
            <div className="lg:col-span-3 rounded-lg border border-border bg-card p-4">
              <div className="mb-3 flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-semibold text-foreground">Evolucion normalizada</h2>
                  <p className="text-xs text-muted-foreground">Base 100 al inicio del rango.</p>
                </div>
                <div className="flex gap-1">
                  {RANGOS.map((r) => (
                    <button
                      key={r}
                      onClick={() => setRango(r)}
                      className={`rounded px-2 py-1 text-xs font-mono transition-colors ${
                        rango === r
                          ? "bg-primary/15 text-primary"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      {r}
                    </button>
                  ))}
                </div>
              </div>
              <ResponsiveContainer width="100%" height={288}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(220,20%,16%)" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 10, fill: "hsl(215,15%,55%)" }}
                    tickLine={false}
                    axisLine={false}
                    interval={Math.max(0, Math.floor(chartData.length / 6))}
                  />
                  <YAxis
                    tick={{ fontSize: 10, fill: "hsl(215,15%,55%)" }}
                    tickLine={false}
                    axisLine={false}
                    width={45}
                    tickFormatter={(v) => v.toFixed(0)}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "hsl(220,40%,8%)",
                      border: "1px solid hsl(220,20%,16%)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                    formatter={(v: number) => v.toFixed(2)}
                  />
                  {TICKERS_CHART.map((t) => (
                    <Line
                      key={t.ticker}
                      type="monotone"
                      dataKey={t.ticker}
                      stroke={t.color}
                      strokeWidth={1.5}
                      dot={false}
                      connectNulls
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
              <div className="mt-3 flex flex-wrap gap-4">
                {TICKERS_CHART.map((t) => (
                  <div key={t.ticker} className="flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full" style={{ background: t.color }} />
                    <span className="text-xs font-mono text-muted-foreground">{t.ticker}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Riesgo top-5 */}
            <div className="lg:col-span-2 rounded-lg border border-border bg-card p-4">
              <h2 className="mb-3 text-sm font-semibold text-foreground">
                Clasificacion de riesgo (5 menos volatiles)
              </h2>
              <div className="space-y-2">
                <div className="grid grid-cols-3 gap-2 text-xs text-muted-foreground uppercase tracking-wider pb-2 border-b border-border">
                  <span>Ticker</span>
                  <span className="text-right">Vol. anual</span>
                  <span className="text-right">Categoria</span>
                </div>
                {topRiesgo.map((asset) => (
                  <div key={asset.ticker} className="grid grid-cols-3 gap-2 items-center py-1.5">
                    <span className="text-sm font-mono text-foreground">{asset.ticker}</span>
                    <span className="text-right text-sm font-mono text-muted-foreground">
                      {(asset.sigma * 100).toFixed(2)}%
                    </span>
                    <div className="text-right">
                      <RiskBadge category={asset.categoria} />
                    </div>
                  </div>
                ))}
                {topRiesgo.length === 0 && (
                  <p className="text-xs text-muted-foreground py-3">Sin datos.</p>
                )}
              </div>
            </div>
          </div>

          {/* Patrones recientes (reales) */}
          <div className="rounded-lg border border-border bg-card p-4">
            <h2 className="mb-3 text-sm font-semibold text-foreground">
              Patrones recientes (ECOPETROL e ISA, k=3)
            </h2>
            <div className="space-y-3">
              {patrones.length === 0 && (
                <p className="text-xs text-muted-foreground">Sin patrones recientes.</p>
              )}
              {patrones.map((p, i) => (
                <div
                  key={`${p.ticker}-${p.fecha}-${i}`}
                  className="flex items-center justify-between rounded-md border border-border bg-muted/30 px-3 py-2"
                >
                  <div className="flex items-center gap-3">
                    {p.patron.includes("alza") ? (
                      <TrendingUp className="h-4 w-4 text-primary" />
                    ) : (
                      <TrendingDown className="h-4 w-4 text-warning" />
                    )}
                    <span className="text-sm text-foreground">{p.patron}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="rounded border border-border bg-secondary px-2 py-0.5 text-xs font-mono text-foreground">
                      {p.ticker}
                    </span>
                    <span className="text-xs font-mono text-muted-foreground">{p.fecha}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
