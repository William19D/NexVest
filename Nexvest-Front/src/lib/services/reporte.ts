/**
 * services/reporte.ts
 * -------------------
 * Descarga del reporte tecnico en PDF. A diferencia del resto de los
 * servicios, este no devuelve JSON sino un Blob binario que se entrega
 * al navegador para descarga.
 */

import { API_URL } from "../api";

export interface ParametrosReporte {
  tickers?: string[];
  tickers_candle?: string[];
  base?: "precio" | "retorno";
  desde?: string;
  hasta?: string;
}

function construirQuery(params: ParametrosReporte): string {
  const url = new URL(`${API_URL}/analisis/reporte/pdf`);
  if (params.tickers) {
    for (const t of params.tickers) url.searchParams.append("tickers", t);
  }
  if (params.tickers_candle) {
    for (const t of params.tickers_candle)
      url.searchParams.append("tickers_candle", t);
  }
  if (params.base) url.searchParams.set("base", params.base);
  if (params.desde) url.searchParams.set("desde", params.desde);
  if (params.hasta) url.searchParams.set("hasta", params.hasta);
  return url.toString();
}

/**
 * Pide el PDF al backend y devuelve un Blob listo para descarga.
 */
export async function fetchReportePdf(
  params: ParametrosReporte = {}
): Promise<Blob> {
  const url = construirQuery(params);
  const res = await fetch(url);
  if (!res.ok) {
    let detalle = res.statusText;
    try {
      const cuerpo = await res.json();
      if (cuerpo && typeof cuerpo === "object" && "detail" in cuerpo) {
        detalle = String((cuerpo as { detail: unknown }).detail);
      }
    } catch {
      /* el cuerpo no era JSON */
    }
    throw new Error(`HTTP ${res.status}: ${detalle}`);
  }
  return await res.blob();
}

/**
 * Helper que descarga un Blob como archivo, simulando un click en un
 * <a download>. Centralizado aqui para no repetir DOM en cada pagina.
 */
export function descargarBlob(blob: Blob, nombreArchivo: string): void {
  const url = URL.createObjectURL(blob);
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = nombreArchivo;
  document.body.appendChild(enlace);
  enlace.click();
  document.body.removeChild(enlace);
  URL.revokeObjectURL(url);
}
