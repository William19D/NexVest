import { useState, useEffect, useMemo } from "react";
import {
  Ruler, Activity, Waypoints, CircleDot, Loader2, AlertCircle, GitMerge,
} from "lucide-react";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, Legend,
} from "recharts";
import {
  fetchHistoricos, type HistoricoEntry,
  fetchSimilitud, type SimilitudResponse, type BaseSimilitud,
} from "@/lib/services";
import { API_TICKERS } from "@/data/tickers";

const LIMIT_OPTIONS = [100, 250, 500, 1000];
const BASE_OPTIONS: { base: BaseSimilitud; label: string }[] = [
  { base: "retorno", label: "Retornos" },
  { base: "precio", label: "Precios" },
];

const complexityTable = [
  { algo: "Distancia Euclidiana", time: "O(n)", space: "O(1)", bestFor: "Comparacion punto a punto" },
  { algo: "Correlacion de Pearson", time: "O(n)", space: "O(1)", bestFor: "Relacion lineal entre series" },
  { algo: "Dynamic Time Warping", time: "O(n*m)", space: "O(n*m)", bestFor: "Series desfasadas en el tiempo" },
  { algo: "Similitud Coseno", time: "O(n)", space: "O(1)", bestFor: "Similitud direccional" },
];

function normalize(arr: number[]): number[] {
  if (arr.length === 0) return arr;
  const min = Math.min(...arr);
  const max = Math.max(...arr);
  if (max === min) return arr.map(() => 0.5);
  return arr.map((v) => (v - min) / (max - min));
}

function alignByDate(a: HistoricoEntry[], b: HistoricoEntry[]) {
  const mapB = new Map(b.map((e) => [e.date, e]));
  return a
    .filter((e) => mapB.has(e.date))
    .map((e) => {
      const otro = mapB.get(e.date)!;
      return {
        date: e.date,
        a: parseFloat(String(e.close)),
        b: parseFloat(String(otro.close)),
        volA: e.volume,
        volB: otro.volume,
      };
    });
}

function fmt4(n: number) {
  return n.toFixed(4);
}

export default function SimilarityAnalysis() {
  const [assetA, setAssetA] = useState("ECOPETROL");
  const [assetB, setAssetB] = useState("PFBCOLOM");
  const [limit, setLimit] = useState(500);
  const [base, setBase] = useState<BaseSimilitud>("retorno");

  const [dataA, setDataA] = useState<HistoricoEntry[]>([]);
  const [dataB, setDataB] = useState<HistoricoEntry[]>([]);
  const [similitud, setSimilitud] = useState<SimilitudResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelado = false;
    setLoading(true);
    setError(null);
    Promise.all([
      fetchHistoricos(assetA, { limit }),
      fetchHistoricos(assetB, { limit }),
      fetchSimilitud({ a: assetA, b: assetB, base }),
    ])
      .then(([respuestaA, respuestaB, respuestaSim]) => {
        if (cancelado) return;
        setDataA(respuestaA.data);
        setDataB(respuestaB.data);
        setSimilitud(respuestaSim);
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
  }, [assetA, assetB, limit, base]);

  const aligned = useMemo(() => alignByDate(dataA, dataB), [dataA, dataB]);
  const closesA = useMemo(() => aligned.map((d) => d.a), [aligned]);
  const closesB = useMemo(() => aligned.map((d) => d.b), [aligned]);
  const normA = useMemo(() => normalize(closesA), [closesA]);
  const normB = useMemo(() => normalize(closesB), [closesB]);

  const normalizedChart = useMemo(
    () =>
      aligned.map((d, i) => ({
        date: d.date,
        [assetA]: +normA[i].toFixed(4),
        [assetB]: +normB[i].toFixed(4),
      })),
    [aligned, normA, normB, assetA, assetB]
  );

  const priceChart = useMemo(
    () =>
      aligned.map((d) => ({
        date: d.date,
        [assetA]: d.a,
        [assetB]: d.b,
      })),
    [aligned, assetA, assetB]
  );

  const volumeChart = useMemo(
    () =>
      aligned.map((d) => ({
        date: d.date,
        [`Vol ${assetA}`]: d.volA,
        [`Vol ${assetB}`]: d.volB,
      })),
    [aligned, assetA, assetB]
  );

  const metricas = useMemo(() => {
    if (!similitud) return [];
    const m = similitud.metricas;
    return [
      {
        nombre: "Distancia Euclidiana",
        icono: Ruler,
        valor: fmt4(m.distancia_euclidiana),
        ayuda: "menor es mas similar",
      },
      {
        nombre: "Correlacion Pearson",
        icono: Activity,
        valor: fmt4(m.correlacion_pearson),
        ayuda:
          m.correlacion_pearson > 0.7
            ? "correlacion fuerte"
            : m.correlacion_pearson > 0.3
            ? "correlacion moderada"
            : "baja correlacion",
      },
      {
        nombre: "Dynamic Time Warping",
        icono: GitMerge,
        valor: fmt4(m.dynamic_time_warping),
        ayuda: "menor = alineamiento mas perfecto",
      },
      {
        nombre: "Similitud Coseno",
        icono: CircleDot,
        valor: fmt4(m.similitud_coseno),
        ayuda:
          m.similitud_coseno > 0.9
            ? "muy similar"
            : m.similitud_coseno > 0.7
            ? "similar"
            : "disimil",
      },
    ];
  }, [similitud]);

  const tooltipStyle = {
    background: "hsl(220,40%,8%)",
    border: "1px solid hsl(220,20%,16%)",
    borderRadius: 8,
    fontSize: 12,
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Similarity Analysis</h1>
        <p className="text-xs text-muted-foreground">
          Los cuatro algoritmos se ejecutan en el backend (Python, sin librerias de alto nivel).
        </p>
      </div>

      {/* Controles */}
      <div className="rounded-lg border border-border bg-card px-4 py-3 flex flex-wrap gap-4 items-end">
        <div className="flex-1 min-w-[140px]">
          <label className="mb-1 block text-xs text-muted-foreground uppercase tracking-wider">Activo A</label>
          <select
            value={assetA}
            onChange={(e) => setAssetA(e.target.value)}
            className="w-full rounded-md border border-border bg-background px-3 py-1.5 text-sm text-foreground"
          >
            {API_TICKERS.map((t) => (
              <option key={t.ticker} value={t.ticker}>
                {t.ticker} — {t.name}
              </option>
            ))}
          </select>
        </div>
        <div className="flex-1 min-w-[140px]">
          <label className="mb-1 block text-xs text-muted-foreground uppercase tracking-wider">Activo B</label>
          <select
            value={assetB}
            onChange={(e) => setAssetB(e.target.value)}
            className="w-full rounded-md border border-border bg-background px-3 py-1.5 text-sm text-foreground"
          >
            {API_TICKERS.map((t) => (
              <option key={t.ticker} value={t.ticker}>
                {t.ticker} — {t.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs text-muted-foreground uppercase tracking-wider">Base</label>
          <div className="flex rounded-md border border-border overflow-hidden text-xs">
            {BASE_OPTIONS.map((opt) => (
              <button
                key={opt.base}
                onClick={() => setBase(opt.base)}
                className={`px-2.5 py-1.5 transition-colors ${
                  base === opt.base
                    ? "bg-primary/20 text-primary font-semibold"
                    : "bg-card text-muted-foreground hover:text-foreground"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="mb-1 block text-xs text-muted-foreground uppercase tracking-wider">Registros visuales</label>
          <div className="flex rounded-md border border-border overflow-hidden text-xs">
            {LIMIT_OPTIONS.map((opt) => (
              <button
                key={opt}
                onClick={() => setLimit(opt)}
                className={`px-2.5 py-1.5 transition-colors ${
                  limit === opt
                    ? "bg-primary/20 text-primary font-semibold"
                    : "bg-card text-muted-foreground hover:text-foreground"
                }`}
              >
                {opt}
              </button>
            ))}
          </div>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center gap-2 py-12 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span className="text-sm">Calculando similitud…</span>
        </div>
      )}
      {!loading && error && (
        <div className="flex items-center gap-2 rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {!loading && !error && similitud && (
        <>
          {/* Tarjetas de metricas (del backend) */}
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            {metricas.map((r) => (
              <div key={r.nombre} className="rounded-lg border border-border bg-card p-4">
                <div className="flex items-center gap-2 text-muted-foreground mb-2">
                  <r.icono className="h-4 w-4" />
                  <span className="text-xs uppercase tracking-wider">{r.nombre}</span>
                </div>
                <div className="text-2xl font-mono font-bold text-foreground">{r.valor}</div>
                <span className="mt-2 inline-flex rounded-full border border-border px-2 py-0.5 text-xs text-muted-foreground">
                  {r.ayuda}
                </span>
              </div>
            ))}
          </div>

          <div className="rounded-lg border border-border bg-card p-4 flex flex-wrap gap-4 text-xs text-muted-foreground">
            <span><Waypoints className="inline h-3 w-3 mr-1" />puntos comunes alineados: <strong className="text-foreground">{similitud.puntos_comunes}</strong></span>
            <span>base: <strong className="text-foreground">{similitud.base}</strong></span>
          </div>

          {/* Precio normalizado */}
          {aligned.length > 0 && (
            <>
              <div className="rounded-lg border border-border bg-card p-4">
                <div className="mb-2 flex items-center justify-between">
                  <h2 className="text-sm font-semibold text-foreground">Precio normalizado (0–1)</h2>
                  <span className="text-xs text-muted-foreground">{aligned.length} fechas en visualizacion</span>
                </div>
                <ResponsiveContainer width="100%" height={288}>
                  <LineChart data={normalizedChart}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(220,20%,16%)" />
                    <XAxis dataKey="date" tick={{ fontSize: 10, fill: "hsl(215,15%,55%)" }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
                    <YAxis domain={[0, 1]} tick={{ fontSize: 10, fill: "hsl(215,15%,55%)" }} tickLine={false} axisLine={false} width={35} tickFormatter={(v) => v.toFixed(1)} />
                    <Tooltip contentStyle={tooltipStyle} formatter={(v: number) => v.toFixed(4)} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    <Line type="monotone" dataKey={assetA} stroke="hsl(166,100%,42%)" strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey={assetB} stroke="hsl(38,92%,50%)" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="rounded-lg border border-border bg-card p-4">
                <h2 className="mb-2 text-sm font-semibold text-foreground">Precio absoluto</h2>
                <ResponsiveContainer width="100%" height={240}>
                  <LineChart data={priceChart}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(220,20%,16%)" />
                    <XAxis dataKey="date" tick={{ fontSize: 10, fill: "hsl(215,15%,55%)" }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
                    <YAxis yAxisId="a" orientation="left" tick={{ fontSize: 10, fill: "hsl(166,100%,42%)" }} tickLine={false} axisLine={false} width={60} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                    <YAxis yAxisId="b" orientation="right" tick={{ fontSize: 10, fill: "hsl(38,92%,50%)" }} tickLine={false} axisLine={false} width={60} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                    <Tooltip contentStyle={tooltipStyle} formatter={(v: number, name: string) => [v.toLocaleString("es-CO"), name]} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    <Line yAxisId="a" type="monotone" dataKey={assetA} stroke="hsl(166,100%,42%)" strokeWidth={2} dot={false} />
                    <Line yAxisId="b" type="monotone" dataKey={assetB} stroke="hsl(38,92%,50%)" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="rounded-lg border border-border bg-card p-4">
                <h2 className="mb-2 text-sm font-semibold text-foreground">Volumen</h2>
                <ResponsiveContainer width="100%" height={150}>
                  <BarChart data={volumeChart}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(220,20%,16%)" />
                    <XAxis dataKey="date" tick={false} axisLine={false} />
                    <YAxis tick={{ fontSize: 10, fill: "hsl(215,15%,55%)" }} tickLine={false} axisLine={false} width={50} tickFormatter={(v) => `${(v / 1e9).toFixed(1)}B`} />
                    <Tooltip contentStyle={tooltipStyle} formatter={(v: number, name: string) => [v.toLocaleString("es-CO"), name]} />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    <Bar dataKey={`Vol ${assetA}`} fill="hsl(166,100%,42%)" opacity={0.5} radius={[2, 2, 0, 0]} />
                    <Bar dataKey={`Vol ${assetB}`} fill="hsl(38,92%,50%)" opacity={0.5} radius={[2, 2, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </>
          )}

          <div className="rounded-lg border border-border bg-card p-4">
            <h2 className="mb-3 text-sm font-semibold text-foreground">Complejidad algoritmica</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-xs uppercase tracking-wider text-muted-foreground">
                    <th className="pb-2 text-left">Algoritmo</th>
                    <th className="pb-2 text-left">Tiempo</th>
                    <th className="pb-2 text-left">Espacio</th>
                    <th className="pb-2 text-left">Mejor uso</th>
                  </tr>
                </thead>
                <tbody>
                  {complexityTable.map((row) => (
                    <tr key={row.algo} className="border-b border-border/50">
                      <td className="py-2 text-foreground">{row.algo}</td>
                      <td className="py-2 font-mono text-primary">{row.time}</td>
                      <td className="py-2 font-mono text-primary">{row.space}</td>
                      <td className="py-2 text-muted-foreground">{row.bestFor}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
