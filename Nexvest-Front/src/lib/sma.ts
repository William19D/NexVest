/**
 * lib/sma.ts
 * ----------
 * Media movil simple (Simple Moving Average). Implementacion manual
 * usando una suma corredera para mantener O(n).
 *
 * Devuelve una lista del mismo largo que la entrada; los primeros
 * (ventana - 1) elementos son null porque no hay suficiente historia.
 */
export function sma(valores: number[], ventana: number): (number | null)[] {
  if (ventana < 1) {
    throw new Error("La ventana de la SMA debe ser >= 1.");
  }
  const n = valores.length;
  const resultado: (number | null)[] = new Array(n).fill(null);
  if (n === 0) return resultado;

  let suma = 0;
  for (let i = 0; i < n; i++) {
    suma = suma + valores[i];
    if (i >= ventana) {
      suma = suma - valores[i - ventana];
    }
    if (i >= ventana - 1) {
      resultado[i] = suma / ventana;
    }
  }
  return resultado;
}
