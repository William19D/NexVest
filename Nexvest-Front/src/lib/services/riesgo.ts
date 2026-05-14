/**
 * services/riesgo.ts
 * ------------------
 * Volatilidad por activo y ranking de riesgo del portafolio.
 */

import { http } from "../api";

export type CategoriaRiesgo = "conservador" | "moderado" | "agresivo";

export interface PerfilRiesgo {
  ticker: string;
  observaciones: number;
  desviacion_diaria: number;
  volatilidad_anualizada: number;
  categoria: CategoriaRiesgo;
}

export interface VolatilidadResponse {
  desde: string | null;
  hasta: string | null;
  perfil: PerfilRiesgo;
}

export interface ResumenRiesgo {
  conservador: number;
  moderado: number;
  agresivo: number;
}

export interface RiesgoResponse {
  desde: string | null;
  hasta: string | null;
  total_activos: number;
  resumen: ResumenRiesgo;
  ranking: PerfilRiesgo[];
}

export function fetchVolatilidad(
  mnemonic: string,
  params?: { desde?: string; hasta?: string }
): Promise<VolatilidadResponse> {
  return http<VolatilidadResponse>(`/analisis/volatilidad/${mnemonic}`, {
    desde: params?.desde,
    hasta: params?.hasta,
  });
}

export function fetchRiesgoPortafolio(params?: {
  tickers?: string[];
  desde?: string;
  hasta?: string;
}): Promise<RiesgoResponse> {
  return http<RiesgoResponse>("/analisis/riesgo", {
    tickers: params?.tickers,
    desde: params?.desde,
    hasta: params?.hasta,
  });
}
