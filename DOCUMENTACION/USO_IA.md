# NexVest - Declaracion de uso de IA generativa

Este documento responde a la exigencia del PDF de la asignatura:

> "El uso de herramientas de inteligencia artificial generativa como apoyo al
> desarrollo del proyecto debera ser declarado explicitamente. Dichas
> herramientas podran utilizarse como soporte, pero no podran reemplazar el
> diseno algoritmico ni el analisis formal solicitado en el curso."

---

## 1. Herramientas utilizadas

| Herramienta | Version / Modelo | Uso principal |
|---|---|---|
| Claude (Anthropic) | Claude Opus 4.7 (1M context) via Claude Code | Asistencia en redaccion de codigo Python/TypeScript, refactorizacion, redaccion de documentacion en espanol, debug. |

No se utilizo ningun otro asistente generativo (Copilot, ChatGPT,
Gemini, etc.).

---

## 2. Para que SE USO la IA

### 2.1 Apoyo en codigo

- Sugerencias de estructura de archivos (separacion por roles en `etl/limpieza`, `reportes/`, `lib/services/`).
- Escritura de boilerplate repetitivo: rutas FastAPI, helpers de fetch tipados, configuracion de Tailwind/Vite.
- Sugerencias para componentes visuales sin librerias (candlestick SVG).
- Identificacion de bugs sutiles (por ejemplo, manejo de `Image kind="proportional"` en reportlab que requiere altura explicita).

### 2.2 Apoyo en documentacion

- Borradores en espanol de los archivos `.md` de la carpeta `DOCUMENTACION/`.
- Refactor de README esqueleto a una estructura util para reproducibilidad.

### 2.3 Apoyo en testing

- Sugerencias de tests unitarios y smoke tests programaticos contra los endpoints.
- Verificacion automatica de propiedades algoritmicas (autocorrelacion = 1, matriz simetrica, etc.).

### 2.4 Apoyo en debug

- Diagnostico de outliers extremos (CLH, EXITO, PROMIGAS) que producian
  volatilidades absurdas; la IA sugirio investigar los valores extremos y
  ayudo a iterar sobre el pipeline de limpieza hasta que convergiera.

---

## 3. Para que NO SE USO la IA

Las decisiones de fondo que la rubrica considera "diseno algoritmico" y
"analisis formal" fueron tomadas y validadas por el equipo:

- **Eleccion de los 4 algoritmos de similitud** (Euclidean, Pearson, DTW,
  Coseno) y su interpretacion en el contexto financiero.
- **Definicion del segundo patron** ("ruptura de maximo de k dias") y su
  formalizacion matematica.
- **Umbrales de clasificacion de riesgo** (15% conservador, 30% moderado).
- **Estrategia de limpieza** (eliminar vs forward-fill, umbral del z-score,
  iterativo con cota de pasadas, criterio del retorno absoluto > 50%).
- **Analisis de complejidad** que aparece en [COMPLEJIDAD.md](COMPLEJIDAD.md):
  las cotas O(n), O(n log n), O(n*m), O(n*k) fueron calculadas y verificadas
  manualmente.
- **Eleccion del stack tecnologico** (FastAPI + MongoDB + React + Vite).
- **Eleccion de no usar librerias prohibidas**: la IA podria haber sugerido
  por defecto `yfinance` o `numpy.corrcoef` para hacer las cosas mas rapido;
  el equipo lo rechazo de antemano por las reglas de la rubrica.

---

## 4. Validacion de cada sugerencia

Toda salida generada por IA fue:

1. **Leida en su totalidad** antes de aceptarla.
2. **Verificada en ejecucion** (compilacion + tests unitarios + smoke tests
   end-to-end contra el backend real y la base de datos real).
3. **Adaptada** a las convenciones del proyecto (espanol en codigo,
   sin emojis, bucles explicitos, funciones pequenas separadas por rol).
4. **Re-verificada** despues de cualquier refactor para asegurar que el
   comportamiento se mantuvo.

En particular, **ninguna implementacion algoritmica exigida por la rubrica
proviene literalmente de la IA sin haber sido leida y entendida**. Los
docstrings paso a paso de [`similitud.py`](../Nexvest-Back-FASTAPI/algorithms/similitud.py), [`patrones.py`](../Nexvest-Back-FASTAPI/algorithms/patrones.py), [`volatilidad.py`](../Nexvest-Back-FASTAPI/algorithms/volatilidad.py) y [`algoritmos_ordenamiento.py`](../Nexvest-Back-FASTAPI/algorithms/algoritmos_ordenamiento.py) reflejan ese ejercicio
de comprension.

---

## 5. Restricciones impuestas a la IA durante el desarrollo

Para no caer en "soluciones magicas" que la rubrica desaconseja, durante el
desarrollo se le pidio explicitamente a la IA:

- Implementar todos los algoritmos **sin librerias de alto nivel** (sin
  `numpy`, sin `scipy`, sin `sklearn` para los algoritmos del proyecto).
- Mantener los archivos **cortos** y separados por rol (ningun archivo supera
  ~300 lineas; los modulos suelen ser de 50-200 lineas).
- **No usar emojis** en el codigo ni en los docstrings.
- Escribir comentarios y documentacion **en espanol**, con explicaciones paso
  a paso, evitando construcciones "magicas" de Python (`list.sort(key=...)`,
  comprehensions anidadas) cuando dificultaban la lectura.

---

## 6. Conclusion

La IA fue una herramienta de productividad: aceleron la redaccion de codigo
boilerplate, la documentacion y el debug. Las decisiones de diseno, los
algoritmos exigidos por la rubrica, el analisis de complejidad y la
verificacion del comportamiento son responsabilidad del equipo y se pueden
trazar en el codigo y en los documentos de esta carpeta.
