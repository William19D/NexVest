import { useState, useEffect, useMemo } from "react";
import { TrendingUp, TrendingDown, Loader2, AlertCircle, CalendarRange, Hash } from "lucide-react";
import {
  BarChart, Bar, XAxis, Tooltip, ResponsiveContainer,
} from "recharts";
import { fetchHistoricos, type HistoricoEntry, type HistoricoResponse } from "@/lib/api";
import { sma } from "@/lib/sma";
import CandlestickChart, { type OHLC } from "@/components/CandlestickChart";
import { API_TICKERS } from "@/data/tickers";

const LIMIT_OPTIONS = [25, 50, 100, 200, 500];
type FilterMode = "limit" | "range";

function fmt(n: number) {
  return n.toLocaleString("es-CO", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function AssetExplorer() {
  const [selectedTicker, setSelectedTicker] = useState("ECOPETROL");
  const [filterMode, setFilterMode] = useState<FilterMode>("limit");
  const [limit, setLimit] = useState(100);
  const [desde, setDesde] = useState("");
  const [hasta, setHasta] = useState("");
  const [entries, setEntries] = useState<HistoricoEntry[]>([]);
  const [apiMeta, setApiMeta] = useState<{ total: number; desde: string | null; hasta: string | null } | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    const params =
      filterMode === "limit"
        ? { limit }
        : { desde: desde || undefined, hasta: hasta || undefined };
    fetchHistoricos(selectedTicker, params)
      .then((res: HistoricoResponse) => {
        setEntries(res.data);
        setApiMeta({ total: res.total, desde: res.desde, hasta: res.hasta });
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [selectedTicker, filterMode, limit, desde, hasta]);

  // Derive chart data from API entries
  const chartData = useMemo(() => {
    const closes = entries.map((e) => parseFloat(String(e.close)));
    const sma20 = sma(closes, 20);
    const sma50 = sma(closes, 50);
    return entries.map((e, i) => ({
      date: e.date.slice(0, 10),
      close: parseFloat(String(e.close)),
      open: parseFloat(String(e.open)),
      high: e.high != null ? parseFloat(String(e.high)) : parseFloat(String(e.close)),
      low: e.low != null ? parseFloat(String(e.low)) : parseFloat(String(e.close)),
      volume: e.volume,
      sma20: sma20[i],
      sma50: sma50[i],
    }));
  }, [entries]);

  // Convertimos a OHLC + arrays de SMA para el candlestick.
  const ohlc = useMemo<OHLC[]>(() => {
    return chartData.map((d) => ({
      date: d.date,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }));
  }, [chartData]);
  const sma20Serie = useMemo(() => chartData.map((d) => d.sma20), [chartData]);
  const sma50Serie = useMemo(() => chartData.map((d) => d.sma50), [chartData]);

  const latest = chartData[chartData.length - 1];
  const prev = chartData[chartData.length - 2];
  const priceChange = latest && prev ? latest.close - prev.close : 0;
  const pctChange = prev ? (priceChange / prev.close) * 100 : 0;
  const isUp = priceChange >= 0;

  const [page, setPage] = useState(1);
  const PAGE_SIZE = 20;

  // Reset page when entries change
  useEffect(() => { setPage(1); }, [entries]);

  const sortedEntries = useMemo(() => [...entries].reverse(), [entries]);
  const totalPages = Math.max(1, Math.ceil(sortedEntries.length / PAGE_SIZE));
  const pageEntries = sortedEntries.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const smaTableData = useMemo(() => {
    const closes = chartData.map((d) => d.close);
    const calc = (period: number) => {
      const vals = sma(closes, period).filter((v): v is number => v !== null);
      const last = vals[vals.length - 1] ?? 0;
      const prev2 = vals[vals.length - 2] ?? 0;
      return { value: last, trend: last >= prev2 ? ("up" as const) : ("down" as const) };
    };
    return [
      { period: "SMA 20", ...calc(20) },
      { period: "SMA 50", ...calc(50) },
      { period: "SMA 200", ...calc(200) },
    ];
  }, [chartData]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h1 className="text-2xl font-bold text-foreground">Asset Explorer</h1>
          <select
            value={selectedTicker}
            onChange={(e) => setSelectedTicker(e.target.value)}
            className="rounded-md border border-border bg-card px-3 py-1.5 text-sm text-foreground"
          >
            {API_TICKERS.map((t) => (
              <option key={t.ticker} value={t.ticker}>{t.ticker} — {t.name}</option>
            ))}
          </select>
        </div>

        {/* Filter controls */}
        <div className="rounded-lg border border-border bg-card px-4 py-3 flex flex-wrap gap-4 items-center">
          {/* Mode toggle */}
          <div className="flex rounded-md border border-border overflow-hidden text-xs font-medium">
            <button
              onClick={() => setFilterMode("limit")}
              className={`flex items-center gap-1.5 px-3 py-1.5 transition-colors ${filterMode === "limit" ? "bg-primary text-primary-foreground" : "bg-card text-muted-foreground hover:text-foreground"}`}
            >
              <Hash className="h-3 w-3" /> Últimos N
            </button>
            <button
              onClick={() => setFilterMode("range")}
              className={`flex items-center gap-1.5 px-3 py-1.5 transition-colors ${filterMode === "range" ? "bg-primary text-primary-foreground" : "bg-card text-muted-foreground hover:text-foreground"}`}
            >
              <CalendarRange className="h-3 w-3" /> Rango de fechas
            </button>
          </div>

          {filterMode === "limit" ? (
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Mostrar</span>
              <div className="flex rounded-md border border-border overflow-hidden text-xs">
                {LIMIT_OPTIONS.map((opt) => (
                  <button
                    key={opt}
                    onClick={() => setLimit(opt)}
                    className={`px-2.5 py-1.5 transition-colors ${limit === opt ? "bg-primary/20 text-primary font-semibold" : "bg-card text-muted-foreground hover:text-foreground"}`}
                  >
                    {opt}
                  </button>
                ))}
              </div>
              <span className="text-xs text-muted-foreground">registros</span>
            </div>
          ) : (
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs text-muted-foreground">Desde</span>
              <input
                type="date"
                value={desde}
                onChange={(e) => setDesde(e.target.value)}
                className="rounded-md border border-border bg-background px-3 py-1.5 text-xs text-foreground font-mono"
              />
              <span className="text-xs text-muted-foreground">Hasta</span>
              <input
                type="date"
                value={hasta}
                onChange={(e) => setHasta(e.target.value)}
                className="rounded-md border border-border bg-background px-3 py-1.5 text-xs text-foreground font-mono"
              />
              {(desde || hasta) && (
                <button
                  onClick={() => { setDesde(""); setHasta(""); }}
                  className="text-xs text-muted-foreground hover:text-destructive underline"
                >
                  Limpiar
                </button>
              )}
            </div>
          )}

          {/* API date coverage */}
          {apiMeta && !loading && (
            <div className="ml-auto flex items-center gap-3 text-xs text-muted-foreground">
              <span>
                Total en API: <span className="font-mono text-foreground">{apiMeta.total}</span>
              </span>
              {apiMeta.desde && (
                <span>
                  Rango: <span className="font-mono text-foreground">{apiMeta.desde}</span>
                  {" → "}
                  <span className="font-mono text-foreground">{apiMeta.hasta ?? "hoy"}</span>
                </span>
              )}
              <span>
                Mostrando: <span className="font-mono text-foreground">{entries.length}</span>
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Loading / Error states */}
      {loading && (
        <div className="flex items-center justify-center gap-2 py-16 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span className="text-sm">Cargando datos de {selectedTicker}…</span>
        </div>
      )}
      {!loading && error && (
        <div className="flex items-center gap-2 rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {!loading && !error && entries.length > 0 && (
        <>
          {/* Price summary bar */}
          <div className="flex flex-wrap gap-4 rounded-lg border border-border bg-card px-5 py-3">
            <div>
              <p className="text-xs text-muted-foreground">Último precio</p>
              <p className="text-2xl font-bold font-mono text-foreground">
                ${fmt(latest?.close ?? 0)}
              </p>
            </div>
            <div className="flex items-center gap-1">
              {isUp
                ? <TrendingUp className="h-4 w-4 text-primary" />
                : <TrendingDown className="h-4 w-4 text-destructive" />}
              <span className={`text-sm font-mono ${isUp ? "text-primary" : "text-destructive"}`}>
                {isUp ? "+" : ""}{fmt(priceChange)} ({isUp ? "+" : ""}{pctChange.toFixed(2)}%)
              </span>
            </div>
            <div className="ml-auto flex gap-6 text-right">
              <div>
                <p className="text-xs text-muted-foreground">Primer dato</p>
                <p className="text-xs font-mono text-foreground">{entries[0]?.date ?? "—"}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Último dato</p>
                <p className="text-xs font-mono text-foreground">{entries[entries.length - 1]?.date ?? "—"}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Registros</p>
                <p className="text-sm font-mono text-foreground">{entries.length}</p>
              </div>
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-4">
            <div className="lg:col-span-3 space-y-4">
              {/* Candlestick + SMA */}
              <div className="rounded-lg border border-border bg-card p-4">
                <div className="mb-2 flex items-center justify-between">
                  <h2 className="text-sm font-semibold text-foreground">
                    Candlestick — {selectedTicker}
                  </h2>
                  <span className="text-xs text-muted-foreground">OHLC + SMA20 + SMA50</span>
                </div>
                <CandlestickChart
                  data={ohlc}
                  sma20={sma20Serie}
                  sma50={sma50Serie}
                  height={360}
                />
              </div>

              {/* Volume chart */}
              <div className="rounded-lg border border-border bg-card p-4">
                <h3 className="mb-1 text-xs text-muted-foreground uppercase tracking-wider">Volumen</h3>
                <ResponsiveContainer width="100%" height={96}>
                  <BarChart data={chartData}>
                    <Bar dataKey="volume" name="Volumen" fill="hsl(166,100%,42%)" opacity={0.4} radius={[2, 2, 0, 0]} />
                    <XAxis dataKey="date" tick={false} axisLine={false} />
                    <Tooltip
                      contentStyle={{ background: "hsl(220,40%,8%)", border: "1px solid hsl(220,20%,16%)", borderRadius: 8, fontSize: 12 }}
                      formatter={(v: number) => [v.toLocaleString("es-CO"), "Volumen"]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Stats sidebar */}
            <div className="rounded-lg border border-border bg-card p-4">
              <h2 className="mb-4 text-sm font-semibold text-foreground">Último registro</h2>
              {latest && (() => {
                const last = entries[entries.length - 1];
                return (
                  <div className="space-y-3">
                    {[
                      ["Cierre", `$${fmt(latest.close)}`],
                      ["Apertura", `$${fmt(latest.open)}`],
                      ["Máximo", latest.high != null ? `$${fmt(parseFloat(latest.high))}` : "—"],
                      ["Mínimo", latest.low != null ? `$${fmt(parseFloat(latest.low))}` : "—"],
                      ["Promedio", last?.averagePrice ? `$${fmt(parseFloat(last.averagePrice))}` : "—"],
                      ["Volumen", latest.volume.toLocaleString("es-CO")],
                      ["Var. Abs.", last?.absoluteVariation ?? "—"],
                      ["Var. %", last?.percentageVariation ? `${last.percentageVariation}%` : "—"],
                    ].map(([label, val]) => (
                      <div key={label} className="flex justify-between border-b border-border pb-2">
                        <span className="text-xs text-muted-foreground">{label}</span>
                        <span className="text-xs font-mono text-foreground">{val}</span>
                      </div>
                    ))}
                    <div className="pt-1">
                      <span className="text-xs text-muted-foreground">Fecha</span>
                      <p className="font-mono text-xs text-foreground">{latest.date}</p>
                    </div>
                  </div>
                );
              })()}
            </div>
          </div>

          {/* Moving averages table */}
          <div className="rounded-lg border border-border bg-card p-4">
            <h2 className="mb-3 text-sm font-semibold text-foreground">Moving Averages</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-xs uppercase tracking-wider text-muted-foreground">
                    <th className="pb-2 text-left">Período</th>
                    <th className="pb-2 text-right">Valor</th>
                    <th className="pb-2 text-right">Tendencia</th>
                  </tr>
                </thead>
                <tbody>
                  {smaTableData.map((row) => (
                    <tr key={row.period} className="border-b border-border/50">
                      <td className="py-2 font-mono text-foreground">{row.period}</td>
                      <td className="py-2 text-right font-mono text-foreground">
                        {row.value > 0 ? `$${fmt(row.value)}` : "—"}
                      </td>
                      <td className="py-2 text-right">
                        {row.value > 0 ? (
                          row.trend === "up"
                            ? <TrendingUp className="inline h-4 w-4 text-primary" />
                            : <TrendingDown className="inline h-4 w-4 text-destructive" />
                        ) : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Historical data table */}
          <div className="rounded-lg border border-border bg-card p-4">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-foreground">Datos históricos</h2>
              <span className="text-xs text-muted-foreground">
                {sortedEntries.length} registros · página {page} de {totalPages}
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border text-xs uppercase tracking-wider text-muted-foreground">
                    {["Fecha", "Apertura", "Cierre", "Máximo", "Mínimo", "Promedio", "Var %", "Volumen"].map((h) => (
                      <th key={h} className="pb-2 text-right first:text-left">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {pageEntries.map((e) => {
                    const pct = parseFloat(e.percentageVariation ?? "0");
                    return (
                      <tr key={e.date} className="border-b border-border/30 hover:bg-muted/20">
                        <td className="py-1.5 font-mono text-foreground">{e.date}</td>
                        <td className="py-1.5 text-right font-mono text-foreground">${fmt(parseFloat(e.open))}</td>
                        <td className="py-1.5 text-right font-mono text-foreground">${fmt(parseFloat(e.close))}</td>
                        <td className="py-1.5 text-right font-mono text-foreground">{e.high != null ? `$${fmt(parseFloat(e.high))}` : "—"}</td>
                        <td className="py-1.5 text-right font-mono text-foreground">{e.low != null ? `$${fmt(parseFloat(e.low))}` : "—"}</td>
                        <td className="py-1.5 text-right font-mono text-foreground">{e.averagePrice ? `$${fmt(parseFloat(e.averagePrice))}` : "—"}</td>
                        <td className={`py-1.5 text-right font-mono ${pct >= 0 ? "text-primary" : "text-destructive"}`}>
                          {pct >= 0 ? "+" : ""}{pct.toFixed(2)}%
                        </td>
                        <td className="py-1.5 text-right font-mono text-muted-foreground">{e.volume.toLocaleString("es-CO")}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {/* Pagination controls */}
            {totalPages > 1 && (
              <div className="mt-3 flex items-center justify-center gap-1">
                <button
                  onClick={() => setPage(1)}
                  disabled={page === 1}
                  className="rounded px-2 py-1 text-xs text-muted-foreground hover:text-foreground disabled:opacity-30"
                >«</button>
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="rounded px-2 py-1 text-xs text-muted-foreground hover:text-foreground disabled:opacity-30"
                >‹</button>
                {Array.from({ length: totalPages }, (_, i) => i + 1)
                  .filter((p) => p === 1 || p === totalPages || Math.abs(p - page) <= 2)
                  .reduce<(number | "...")[]>((acc, p, idx, arr) => {
                    if (idx > 0 && p - (arr[idx - 1] as number) > 1) acc.push("...");
                    acc.push(p);
                    return acc;
                  }, [])
                  .map((item, idx) =>
                    item === "..." ? (
                      <span key={`ellipsis-${idx}`} className="px-1 text-xs text-muted-foreground">…</span>
                    ) : (
                      <button
                        key={item}
                        onClick={() => setPage(item as number)}
                        className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${page === item ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"}`}
                      >{item}</button>
                    )
                  )}
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="rounded px-2 py-1 text-xs text-muted-foreground hover:text-foreground disabled:opacity-30"
                >›</button>
                <button
                  onClick={() => setPage(totalPages)}
                  disabled={page === totalPages}
                  className="rounded px-2 py-1 text-xs text-muted-foreground hover:text-foreground disabled:opacity-30"
                >»</button>
              </div>
            )}
          </div>
        </>
      )}

      {!loading && !error && entries.length === 0 && (
        <div className="py-16 text-center text-sm text-muted-foreground">
          No se encontraron registros para el rango seleccionado.
        </div>
      )}
    </div>
  );
}
