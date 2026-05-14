import { useEffect, useMemo, useState } from "react";
import { Shield, Loader2, AlertCircle } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell,
} from "recharts";
import KPICard from "@/components/KPICard";
import RiskBadge from "@/components/RiskBadge";
import { RiskCategory } from "@/types/risk";
import {
  fetchRiesgoPortafolio, type RiesgoResponse, type CategoriaRiesgo,
} from "@/lib/services";

const filtros: (RiskCategory | "All")[] = ["All", "Conservative", "Moderate", "Aggressive"];

const colorCategoria: Record<RiskCategory, string> = {
  Conservative: "hsl(142,76%,36%)",
  Moderate: "hsl(38,92%,50%)",
  Aggressive: "hsl(0,72%,51%)",
};

function categoriaDisplay(cat: CategoriaRiesgo): RiskCategory {
  if (cat === "conservador") return "Conservative";
  if (cat === "moderado") return "Moderate";
  return "Aggressive";
}

export default function RiskDashboard() {
  const [activo, setActivo] = useState<RiskCategory | "All">("All");
  const [respuesta, setRespuesta] = useState<RiesgoResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelado = false;
    setLoading(true);
    setError(null);
    fetchRiesgoPortafolio()
      .then((r) => {
        if (!cancelado) setRespuesta(r);
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

  const filas = useMemo(() => {
    if (!respuesta) return [];
    return respuesta.ranking.map((p) => ({
      ticker: p.ticker,
      observaciones: p.observaciones,
      sigmaDiario: p.desviacion_diaria,
      sigmaAnual: p.volatilidad_anualizada,
      categoria: categoriaDisplay(p.categoria),
    }));
  }, [respuesta]);

  const filtradas = useMemo(() => {
    if (activo === "All") return filas;
    return filas.filter((f) => f.categoria === activo);
  }, [filas, activo]);

  const datosRanking = useMemo(() => {
    return filas.map((f) => ({
      ticker: f.ticker,
      volatility: +(f.sigmaAnual * 100).toFixed(2),
      category: f.categoria,
    }));
  }, [filas]);

  const resumen = respuesta?.resumen ?? { conservador: 0, moderado: 0, agresivo: 0 };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Risk Dashboard</h1>
        <p className="text-xs text-muted-foreground">
          Volatilidad anualizada con sqrt(252). Categorias: conservador (&lt;15%), moderado (15-30%), agresivo (&gt;30%).
        </p>
      </div>

      {loading && (
        <div className="flex items-center justify-center gap-2 py-12 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span className="text-sm">Calculando riesgo del portafolio…</span>
        </div>
      )}
      {!loading && error && (
        <div className="flex items-center gap-2 rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {!loading && !error && respuesta && (
        <>
          <div className="grid grid-cols-3 gap-4">
            <KPICard
              label="Conservadores"
              value={resumen.conservador}
              icon={<Shield className="h-4 w-4 text-success" />}
              accent="teal"
            />
            <KPICard
              label="Moderados"
              value={resumen.moderado}
              icon={<Shield className="h-4 w-4 text-warning" />}
              accent="amber"
            />
            <KPICard
              label="Agresivos"
              value={resumen.agresivo}
              icon={<Shield className="h-4 w-4 text-danger" />}
              accent="default"
            />
          </div>

          <div className="flex gap-1 rounded-lg border border-border bg-card p-1 w-fit">
            {filtros.map((f) => (
              <button
                key={f}
                onClick={() => setActivo(f)}
                className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                  activo === f
                    ? "bg-primary/15 text-primary"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {f}
              </button>
            ))}
          </div>

          <div className="rounded-lg border border-border bg-card p-4 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-xs uppercase tracking-wider text-muted-foreground">
                  <th className="pb-2 text-left">Ticker</th>
                  <th className="pb-2 text-right">Observaciones</th>
                  <th className="pb-2 text-right">Sigma diario</th>
                  <th className="pb-2 text-right">Sigma anual</th>
                  <th className="pb-2 text-center">Categoria</th>
                </tr>
              </thead>
              <tbody>
                {filtradas.map((f) => (
                  <tr key={f.ticker} className="border-b border-border/50 hover:bg-muted/30 transition-colors">
                    <td className="py-2 font-mono text-foreground">{f.ticker}</td>
                    <td className="py-2 text-right text-muted-foreground">{f.observaciones}</td>
                    <td className="py-2 text-right font-mono text-foreground">
                      {(f.sigmaDiario * 100).toFixed(3)}%
                    </td>
                    <td className="py-2 text-right font-mono text-foreground">
                      {(f.sigmaAnual * 100).toFixed(2)}%
                    </td>
                    <td className="py-2 text-center">
                      <RiskBadge category={f.categoria} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filtradas.length === 0 && (
              <p className="py-4 text-center text-sm text-muted-foreground">
                Sin activos en esta categoria.
              </p>
            )}
          </div>

          <div className="rounded-lg border border-border bg-card p-4">
            <h2 className="mb-2 text-sm font-semibold text-foreground">Ranking de volatilidad anualizada</h2>
            <ResponsiveContainer width="100%" height={Math.max(280, datosRanking.length * 22)}>
              <BarChart data={datosRanking} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(220,20%,16%)" />
                <XAxis
                  type="number"
                  unit="%"
                  tick={{ fontSize: 10, fill: "hsl(215,15%,55%)" }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  dataKey="ticker"
                  type="category"
                  tick={{ fontSize: 9, fill: "hsl(215,15%,55%)" }}
                  tickLine={false}
                  axisLine={false}
                  width={75}
                />
                <Tooltip
                  contentStyle={{
                    background: "hsl(220,40%,8%)",
                    border: "1px solid hsl(220,20%,16%)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                  formatter={(v: number) => `${v.toFixed(2)}%`}
                />
                <Bar dataKey="volatility" radius={[0, 4, 4, 0]}>
                  {datosRanking.map((entry, i) => (
                    <Cell key={i} fill={colorCategoria[entry.category]} fillOpacity={0.75} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  );
}
