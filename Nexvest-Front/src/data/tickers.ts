/**
 * data/tickers.ts
 * ---------------
 * Catalogo de tickers disponibles en el backend. Centralizado aqui para
 * que cualquier pagina (AssetExplorer, SimilarityAnalysis, etc.) consuma
 * la misma lista sin duplicar.
 */

export interface TickerInfo {
  ticker: string;
  name: string;
}

export const API_TICKERS: TickerInfo[] = [
  { ticker: "ECOPETROL", name: "Ecopetrol S.A." },
  { ticker: "ISA", name: "ISA S.A." },
  { ticker: "GEB", name: "Grupo Energía Bogotá" },
  { ticker: "PFBCOLOM", name: "Bancolombia Pref." },
  { ticker: "NUTRESA", name: "Grupo Nutresa" },
  { ticker: "GRUPOSURA", name: "Grupo SURA" },
  { ticker: "CELSIA", name: "Celsia S.A." },
  { ticker: "EXITO", name: "Grupo Éxito" },
  { ticker: "CEMARGOS", name: "Cementos Argos" },
  { ticker: "CNEC", name: "Canacol Energy" },
  { ticker: "CORFICOLCF", name: "Corficolombiana" },
  { ticker: "PROMIGAS", name: "Promigas S.A." },
  { ticker: "MINEROS", name: "Mineros S.A." },
  { ticker: "CLH", name: "Concesiones ALCO" },
  { ticker: "PFDAVVNDA", name: "Davivienda Pref." },
  { ticker: "VOO", name: "Vanguard S&P 500 ETF" },
  { ticker: "CSPX.L", name: "iShares Core S&P 500" },
  { ticker: "SPY", name: "SPDR S&P 500 ETF" },
  { ticker: "QQQ", name: "Invesco QQQ Trust" },
  { ticker: "IVV", name: "iShares S&P 500 ETF" },
  { ticker: "GLD", name: "SPDR Gold Shares" },
];
