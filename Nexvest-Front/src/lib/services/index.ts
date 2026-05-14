/**
 * services/index.ts
 * -----------------
 * Punto unico de re-export para que los componentes puedan importar con:
 *
 *     import { fetchSimilitud, fetchRiesgoPortafolio } from "@/lib/services";
 */

export * from "./historicos";
export * from "./similitud";
export * from "./correlacion";
export * from "./patrones";
export * from "./riesgo";
export * from "./reporte";
