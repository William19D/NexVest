/**
 * services/similitud.ts
 * ---------------------
 * Comparacion entre dos activos con los 4 algoritmos del backend:
 * Euclidean, Pearson, DTW y Coseno.
 */

import { http } from "../api";

export type BaseSimilitud = "precio" | "retorno";

export interface MetricasSimilitud {
  distancia_euclidiana: number;
  correlacion_pearson: number;
  dynamic_time_warping: number;
  similitud_coseno: number;
}

export interface SimilitudResponse {
  activo_a: string;
  activo_b: string;
  desde: string | null;
  hasta: string | null;
  base: BaseSimilitud;
  puntos_comunes: number;
  metricas: MetricasSimilitud;
}

export interface ParametrosSimilitud {
  a: string;
  b: string;
  base?: BaseSimilitud;
  ventana_dtw?: number;
  desde?: string;
  hasta?: string;
}

export function fetchSimilitud(
  params: ParametrosSimilitud
): Promise<SimilitudResponse> {
  return http<SimilitudResponse>("/analisis/similitud", {
    a: params.a,
    b: params.b,
    base: params.base ?? "retorno",
    ventana_dtw: params.ventana_dtw,
    desde: params.desde,
    hasta: params.hasta,
  });
}
