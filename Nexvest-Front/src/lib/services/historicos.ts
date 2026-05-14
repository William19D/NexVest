/**
 * services/historicos.ts
 * ----------------------
 * Acceso a las series historicas crudas (endpoints bajo /historicos y la
 * utilidad /analisis/mnemonicos).
 */

import { http } from "../api";

export interface HistoricoEntry {
  date: string;
  board?: string;
  close: string | number;
  high: string | number | null;
  low: string | number | null;
  open: string | number;
  mnemonic?: string;
  averagePrice?: string;
  absoluteVariation?: string;
  percentageVariation?: string;
  targetDate?: string;
  volume: number;
}

export interface HistoricoResponse {
  mnemonic: string;
  total: number;
  desde: string | null;
  hasta: string | null;
  data: HistoricoEntry[];
}

export function fetchHistoricos(
  mnemonic: string,
  params?: { desde?: string; hasta?: string; limit?: number }
): Promise<HistoricoResponse> {
  return http<HistoricoResponse>(`/historicos/${mnemonic}`, {
    desde: params?.desde,
    hasta: params?.hasta,
    limit: params?.limit,
  });
}

export async function fetchMnemonicos(): Promise<string[]> {
  const respuesta = await http<{ mnemonicos: string[] }>(
    "/analisis/mnemonicos"
  );
  return respuesta.mnemonicos;
}
