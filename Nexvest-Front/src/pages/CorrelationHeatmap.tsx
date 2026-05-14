import { useEffect, useMemo, useState } from "react";
import { Loader2, AlertCircle, FileDown } from "lucide-react";
import {
  fetchMatrizCorrelacion, type CorrelacionResponse, type BaseSimilitud,
  fetchReportePdf, descargarBlob,
} from "@/lib/services";

function colorCelda(valor: number): string {
  if (valor >= 0.8) return "bg-primary/60 text-primary-foreground";
  if (valor >= 0.5) return "bg-primary/30 text-foreground";
  if (valor >= 0.2) return "bg-primary/15 text-foreground";
  if (valor > -0.2) return "bg-muted text-muted-foreground";
  if (valor > -0.5) return "bg-danger/15 text-foreground";
  return "bg-danger/40 text-foreground";
}

function interpretar(valor: number): string {
  if (valor >= 0.9) return "muy alta";
  if (valor >= 0.7) return "alta";
  if (valor >= 0.4) return "moderada";
  if (valor >= -0.4) return "debil";
  if (valor >= -0.7) return "negativa moderada";
  return "negativa fuerte";
}

interface ParPearson {
  a: string;
  b: string;
  valor: number;
}

function paresOrdenados(activos: string[], matriz: number[][]): ParPearson[] {
  const pares: ParPearson[] = [];
  for (let i = 0; i < activos.length; i++) {
    for (let j = i + 1; j < activos.length; j++) {
      pares.push({ a: activos[i], b: activos[j], valor: matriz[i][j] });
    }
  }
  pares.sort((p, q) => Math.abs(q.valor) - Math.abs(p.valor));
  return pares;
}

export default function CorrelationHeatmap() {
  const [base, setBase] = useState<BaseSimilitud>("retorno");
  const [respuesta, setRespuesta] = useState<CorrelacionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generandoPdf, setGenerandoPdf] = useState(false);
  const [errorPdf, setErrorPdf] = useState<string | null>(null);

  const exportarPdf = async () => {
    setGenerandoPdf(true);
    setErrorPdf(null);
    try {
      const blob = await fetchReportePdf({ base });
      const fechaArchivo = new Date().toISOString().slice(0, 10);
      descargarBlob(blob, `nexvest_reporte_${fechaArchivo}.pdf`);
    } catch (e) {
      const mensaje = e instanceof Error ? e.message : String(e);
      setErrorPdf(mensaje);
    } finally {
      setGenerandoPdf(false);
    }
  };

  useEffect(() => {
    let cancelado = false;
    setLoading(true);
    setError(null);
    fetchMatrizCorrelacion({ base })
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
  }, [base]);

  const topPares = useMemo(() => {
    if (!respuesta) return [];
    return paresOrdenados(respuesta.activos, respuesta.matriz).slice(0, 10);
  }, [respuesta]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Matriz de Correlacion</h1>
          <p className="text-xs text-muted-foreground">Pearson sobre fechas comunes, calculado en backend.</p>
        </div>
        <div className="flex gap-3 items-center">
          <div className="flex rounded-md border border-border overflow-hidden text-xs">
            {(["retorno", "precio"] as BaseSimilitud[]).map((b) => (
              <button
                key={b}
                onClick={() => setBase(b)}
                className={`px-3 py-1.5 transition-colors ${
                  base === b
                    ? "bg-primary/20 text-primary font-semibold"
                    : "bg-card text-muted-foreground hover:text-foreground"
                }`}
              >
                {b === "retorno" ? "Retornos" : "Precios"}
              </button>
            ))}
          </div>
          <button
            onClick={exportarPdf}
            disabled={generandoPdf || loading}
            className="flex items-center gap-2 rounded-md bg-accent px-4 py-1.5 text-sm font-medium text-accent-foreground hover:bg-accent/90 transition-colors disabled:opacity-60 disabled:cursor-wait"
          >
            {generandoPdf ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" /> Generando…
              </>
            ) : (
              <>
                <FileDown className="h-4 w-4" /> Exportar PDF
              </>
            )}
          </button>
        </div>
      </div>

      {errorPdf && (
        <div className="flex items-center gap-2 rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-2 text-xs text-destructive">
          <AlertCircle className="h-3.5 w-3.5 shrink-0" />
          Error al generar PDF: {errorPdf}
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center gap-2 py-12 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span className="text-sm">Calculando matriz…</span>
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
          <div className="rounded-lg border border-border bg-card p-4 overflow-x-auto">
            <div className="inline-block min-w-[600px]">
              <div className="flex">
                <div className="w-24 shrink-0" />
                {respuesta.activos.map((t) => (
                  <div
                    key={t}
                    className="w-16 shrink-0 text-center text-[10px] font-mono text-muted-foreground -rotate-45 origin-center mb-2"
                  >
                    {t.slice(0, 8)}
                  </div>
                ))}
              </div>
              {respuesta.activos.map((rowTicker, rowIdx) => (
                <div key={rowTicker} className="flex items-center">
                  <div className="w-24 shrink-0 text-[10px] font-mono text-muted-foreground truncate pr-2 text-right">
                    {rowTicker}
                  </div>
                  {respuesta.activos.map((_, colIdx) => {
                    const valor = respuesta.matriz[rowIdx][colIdx];
                    return (
                      <div
                        key={colIdx}
                        className={`w-16 h-10 shrink-0 flex items-center justify-center text-[10px] font-mono border border-background/50 ${colorCelda(valor)}`}
                      >
                        {valor.toFixed(2)}
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>

            <div className="mt-4 flex items-center gap-2 text-xs text-muted-foreground">
              <span>-1.0</span>
              <div className="flex h-3 flex-1 rounded overflow-hidden">
                <div className="flex-1 bg-danger/60" />
                <div className="flex-1 bg-danger/30" />
                <div className="flex-1 bg-muted" />
                <div className="flex-1 bg-primary/30" />
                <div className="flex-1 bg-primary/60" />
              </div>
              <span>+1.0</span>
            </div>
          </div>

          <div className="rounded-lg border border-border bg-card p-4">
            <h2 className="mb-3 text-sm font-semibold text-foreground">
              Top 10 pares por magnitud de correlacion
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-xs uppercase tracking-wider text-muted-foreground">
                    <th className="pb-2 text-left">Activo A</th>
                    <th className="pb-2 text-left">Activo B</th>
                    <th className="pb-2 text-right">Correlacion</th>
                    <th className="pb-2 text-left">Interpretacion</th>
                  </tr>
                </thead>
                <tbody>
                  {topPares.map((par, i) => (
                    <tr key={i} className="border-b border-border/50">
                      <td className="py-2 font-mono text-foreground">{par.a}</td>
                      <td className="py-2 font-mono text-foreground">{par.b}</td>
                      <td
                        className={`py-2 text-right font-mono font-semibold ${
                          par.valor >= 0.8
                            ? "text-primary"
                            : par.valor < -0.5
                            ? "text-danger"
                            : "text-foreground"
                        }`}
                      >
                        {par.valor.toFixed(4)}
                      </td>
                      <td className="py-2 text-muted-foreground">{interpretar(par.valor)}</td>
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
