import { useEffect, useMemo, useState } from "react";
import { Play, Hash, Loader2, AlertCircle, CalendarDays, Clock } from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine,
} from "recharts";
import {
  fetchPatrones, fetchHistoricos,
  type PatronesResponse, type HistoricoEntry,
} from "@/lib/services";
import { API_TICKERS } from "@/data/tickers";

type TipoPatron = "dias_consecutivos_alza" | "ruptura_maximo_ventana";

const PATRONES_DISPONIBLES: { tipo: TipoPatron; nombre: string; descripcion: string }[] = [
  {
    tipo: "dias_consecutivos_alza",
    nombre: "Dias consecutivos al alza",
    descripcion: "k subidas estrictas consecutivas del precio de cierre.",
  },
  {
    tipo: "ruptura_maximo_ventana",
    nombre: "Ruptura de maximo de k dias",
    descripcion: "close[t] > max(close[t-k..t-1]).",
  },
];

export default function PatternDetection() {
  const [ticker, setTicker] = useState("ECOPETROL");
  const [tipo, setTipo] = useState<TipoPatron>("dias_consecutivos_alza");
  const [k, setK] = useState(3);

  const [respuesta, setRespuesta] = useState<PatronesResponse | null>(null);
  const [historico, setHistorico] = useState<HistoricoEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Disparo: solo cuando el usuario aprieta "Run".
  const [trigger, setTrigger] = useState(0);

  useEffect(() => {
    let cancelado = false;
    setLoading(true);
    setError(null);
    Promise.all([
      fetchPatrones({ mnemonic: ticker, k }),
      fetchHistoricos(ticker, { limit: 1000 }),
    ])
      .then(([respPat, respHist]) => {
        if (cancelado) return;
        setRespuesta(respPat);
        setHistorico(respHist.data);
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
    // trigger en deps fuerza re-fetch al apretar "Run" aun con mismos parametros
  }, [trigger, ticker, k]);

  const resultadoActivo = useMemo(() => {
    if (!respuesta) return null;
    return respuesta.patrones.find((p) => p.patron === tipo) ?? null;
  }, [respuesta, tipo]);

  const datosGrafica = useMemo(() => {
    return historico.map((e) => ({
      date: e.date,
      close: parseFloat(String(e.close)),
    }));
  }, [historico]);

  const fechasMarcadas = useMemo(() => {
    if (!resultadoActivo) return new Set<string>();
    return new Set(resultadoActivo.fechas);
  }, [resultadoActivo]);

  const totalApariciones = resultadoActivo?.total_apariciones ?? 0;
  const ultimaFecha = resultadoActivo?.fechas?.length
    ? resultadoActivo.fechas[resultadoActivo.fechas.length - 1]
    : "—";
  const frecuenciaPorAnio = useMemo(() => {
    if (!respuesta || !resultadoActivo) return 0;
    const anios = respuesta.total_dias / 252;
    if (anios <= 0) return 0;
    return resultadoActivo.total_apariciones / anios;
  }, [respuesta, resultadoActivo]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Pattern Detection</h1>
        <p className="text-xs text-muted-foreground">
          Sliding window O(n) sobre los precios de cierre. Calculo en backend.
        </p>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-end flex-wrap">
        <div>
          <label className="mb-1 block text-xs text-muted-foreground uppercase tracking-wider">Activo</label>
          <select
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            className="rounded-md border border-border bg-card px-3 py-1.5 text-sm text-foreground"
          >
            {API_TICKERS.map((t) => (
              <option key={t.ticker} value={t.ticker}>
                {t.ticker}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs text-muted-foreground uppercase tracking-wider">Patron</label>
          <select
            value={tipo}
            onChange={(e) => setTipo(e.target.value as TipoPatron)}
            className="rounded-md border border-border bg-card px-3 py-1.5 text-sm text-foreground"
          >
            {PATRONES_DISPONIBLES.map((p) => (
              <option key={p.tipo} value={p.tipo}>
                {p.nombre}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs text-muted-foreground uppercase tracking-wider">Ventana k</label>
          <input
            type="number"
            min={1}
            max={30}
            value={k}
            onChange={(e) => setK(Math.max(1, Number(e.target.value)))}
            className="w-20 rounded-md border border-border bg-card px-3 py-1.5 text-sm font-mono text-foreground"
          />
        </div>
        <button
          onClick={() => setTrigger((t) => t + 1)}
          className="flex items-center gap-2 rounded-md bg-primary px-6 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Play className="h-4 w-4" /> Run
        </button>
      </div>

      <div className="rounded-lg border border-border bg-card px-4 py-3 text-xs text-muted-foreground">
        {PATRONES_DISPONIBLES.find((p) => p.tipo === tipo)?.descripcion}
      </div>

      {loading && (
        <div className="flex items-center justify-center gap-2 py-12 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span className="text-sm">Detectando patrones…</span>
        </div>
      )}
      {!loading && error && (
        <div className="flex items-center gap-2 rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {!loading && !error && resultadoActivo && (
        <>
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2 rounded-lg border border-border bg-card p-4">
              <h2 className="mb-2 text-sm font-semibold text-foreground">Linea de tiempo (cierre)</h2>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={datosGrafica}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(220,20%,16%)" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 10, fill: "hsl(215,15%,55%)" }}
                    tickLine={false}
                    axisLine={false}
                    interval="preserveStartEnd"
                  />
                  <YAxis
                    tick={{ fontSize: 10, fill: "hsl(215,15%,55%)" }}
                    tickLine={false}
                    axisLine={false}
                    width={60}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "hsl(220,40%,8%)",
                      border: "1px solid hsl(220,20%,16%)",
                      borderRadius: 8,
                      fontSize: 12,
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="close"
                    stroke="hsl(215,15%,55%)"
                    strokeWidth={1.5}
                    dot={(props) => {
                      const fecha = props.payload?.date as string;
                      if (fechasMarcadas.has(fecha)) {
                        return (
                          <circle
                            cx={props.cx}
                            cy={props.cy}
                            r={3}
                            fill="hsl(166,100%,42%)"
                            stroke="none"
                          />
                        );
                      }
                      return <circle r={0} />;
                    }}
                  />
                </LineChart>
              </ResponsiveContainer>
              <p className="mt-2 text-xs text-muted-foreground">
                Puntos verdes: dias donde se detecto el patron seleccionado.
              </p>
            </div>

            <div className="rounded-lg border border-border bg-card p-4">
              <h2 className="mb-4 text-sm font-semibold text-foreground">Frecuencia</h2>
              <div className="space-y-4">
                {[
                  {
                    label: "Total apariciones",
                    valor: String(totalApariciones),
                    Icono: Hash,
                  },
                  {
                    label: "Frecuencia anual",
                    valor: frecuenciaPorAnio.toFixed(2),
                    Icono: Clock,
                  },
                  {
                    label: "Ultima aparicion",
                    valor: ultimaFecha,
                    Icono: CalendarDays,
                  },
                ].map((stat) => (
                  <div key={stat.label} className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary/10">
                      <stat.Icono className="h-4 w-4 text-primary" />
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">{stat.label}</div>
                      <div className="text-sm font-mono font-semibold text-foreground">{stat.valor}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-card p-4">
            <h2 className="mb-3 text-sm font-semibold text-foreground">
              Apariciones detectadas ({totalApariciones})
            </h2>
            {totalApariciones === 0 ? (
              <p className="text-sm text-muted-foreground">
                No se detectaron apariciones para los parametros seleccionados.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-xs uppercase tracking-wider text-muted-foreground">
                      <th className="pb-2 text-left">#</th>
                      <th className="pb-2 text-left">Fecha</th>
                      <th className="pb-2 text-left">Indice en la serie</th>
                    </tr>
                  </thead>
                  <tbody>
                    {resultadoActivo.fechas.slice(-30).map((fecha, i) => (
                      <tr key={i} className="border-b border-border/50">
                        <td className="py-2 text-muted-foreground">
                          {resultadoActivo.fechas.length - 29 + i}
                        </td>
                        <td className="py-2 font-mono text-foreground">{fecha}</td>
                        <td className="py-2 text-muted-foreground">
                          {resultadoActivo.indices[resultadoActivo.indices.length - 30 + i] ??
                            resultadoActivo.indices[i]}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {resultadoActivo.fechas.length > 30 && (
                  <p className="mt-2 text-xs text-muted-foreground">
                    Mostrando ultimas 30 apariciones de {totalApariciones}.
                  </p>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
