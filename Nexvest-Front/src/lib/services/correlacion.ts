/**
 * services/correlacion.ts
 * -----------------------
 * Matriz de correlacion de Pearson para un subconjunto del portafolio.
 */

import { http } from "../api";
import type { BaseSimilitud } from "./similitud";

export interface CorrelacionResponse {
  activos: string[];
  base: BaseSimilitud;
  desde: string | null;
  hasta: string | null;
  matriz: number[][];
}

export interface ParametrosCorrelacion {
  tickers?: string[];
  base?: BaseSimilitud;
  desde?: string;
  hasta?: string;
}

export function fetchMatrizCorrelacion(
  params: ParametrosCorrelacion = {}
): Promise<CorrelacionResponse> {
  return http<CorrelacionResponse>("/analisis/correlacion", {
    tickers: params.tickers,
    base: params.base ?? "retorno",
    desde: params.desde,
    hasta: params.hasta,
  });
}
