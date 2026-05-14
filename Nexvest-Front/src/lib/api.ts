/**
 * lib/api.ts
 * ----------
 * Capa base de la API: expone la URL del backend y un helper http<T>()
 * para hacer peticiones GET tipadas. La logica de cada dominio
 * (historicos, similitud, correlacion, patrones, riesgo) vive en
 * lib/services/<dominio>.ts.
 */

export const API_URL = import.meta.env.VITE_API_URL as string;

export interface QueryParams {
  [clave: string]: string | number | boolean | string[] | undefined;
}

/**
 * Construye una URL absoluta a partir del path y los parametros. Para
 * arreglos se repite la clave (ej: tickers=VOO&tickers=IVV), formato
 * que entiende FastAPI con Query(List[str]).
 */
function construirUrl(path: string, params?: QueryParams): string {
  const url = new URL(`${API_URL}${path}`);
  if (!params) return url.toString();

  for (const clave of Object.keys(params)) {
    const valor = params[clave];
    if (valor === undefined || valor === null) continue;
    if (Array.isArray(valor)) {
      for (const item of valor) {
        url.searchParams.append(clave, String(item));
      }
    } else {
      url.searchParams.set(clave, String(valor));
    }
  }
  return url.toString();
}

/**
 * GET tipado al backend. Lanza Error con el detalle del servidor si la
 * respuesta no es 2xx.
 */
export async function http<T>(path: string, params?: QueryParams): Promise<T> {
  const url = construirUrl(path, params);
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
  return (await res.json()) as T;
}

// Re-exports de compatibilidad: paginas existentes importan estas
// utilidades desde "@/lib/api". El codigo nuevo deberia preferir
// "@/lib/services".
export {
  fetchHistoricos,
  fetchMnemonicos,
  type HistoricoEntry,
  type HistoricoResponse,
} from "./services/historicos";

