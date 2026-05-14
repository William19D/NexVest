/**
 * services/patrones.ts
 * --------------------
 * Deteccion de patrones por sliding window sobre un activo.
 */

import { http } from "../api";

export interface PatronResultado {
  patron: string;
  k: number;
  total_apariciones: number;
  indices: number[];
  fechas: string[];
}

export interface PatronesResponse {
  mnemonic: string;
  k: number;
  total_dias: number;
  desde: string | null;
  hasta: string | null;
  patrones: PatronResultado[];
}

export interface ParametrosPatrones {
  mnemonic: string;
  k?: number;
  desde?: string;
  hasta?: string;
}

export function fetchPatrones(
  params: ParametrosPatrones
): Promise<PatronesResponse> {
  return http<PatronesResponse>(`/analisis/patrones/${params.mnemonic}`, {
    k: params.k ?? 3,
    desde: params.desde,
    hasta: params.hasta,
  });
}
