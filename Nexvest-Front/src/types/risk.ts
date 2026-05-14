/**
 * types/risk.ts
 * -------------
 * Categorias de riesgo en formato de display (en ingles, capitalizado).
 * El backend devuelve las categorias en espanol minusculas; se mapean
 * con categoriaDisplay() donde corresponda.
 */
export type RiskCategory = "Conservative" | "Moderate" | "Aggressive";
