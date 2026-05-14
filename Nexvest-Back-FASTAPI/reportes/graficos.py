"""
reportes/graficos.py
--------------------
Generadores de imagenes PNG en memoria para incrustar en el PDF.
Cada funcion devuelve los bytes del PNG; ninguna escribe a disco.

Se usa matplotlib en su modo no interactivo (backend 'Agg') porque el
proceso del servidor no tiene display.
"""

import io

import matplotlib

matplotlib.use("Agg")  # Backend sin GUI; necesario en servidor.

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from reportes.medias_moviles import sma


# ---------------------------------------------------------------------------
# Heatmap de correlacion
# ---------------------------------------------------------------------------

def grafico_heatmap_correlacion(activos, matriz, titulo="Matriz de Correlacion"):
    """
    Renderiza la matriz de correlacion como heatmap y devuelve los bytes
    PNG. Cada celda muestra el valor con dos decimales.

    Parametros:
        activos: lista de mnemonicos en el mismo orden que las filas y
                 columnas de 'matriz'.
        matriz : lista de listas con valores en [-1, 1].
        titulo : titulo del grafico.

    Convencion de color: rojo para correlacion negativa, blanco para
    cero, verde para correlacion positiva.
    """
    n = len(activos)
    figura, eje = plt.subplots(figsize=(max(6, n * 0.5), max(5, n * 0.5)))

    imagen = eje.imshow(
        matriz, cmap="RdYlGn", vmin=-1.0, vmax=1.0, aspect="auto"
    )

    eje.set_xticks(range(n))
    eje.set_yticks(range(n))
    eje.set_xticklabels(activos, rotation=60, ha="right", fontsize=8)
    eje.set_yticklabels(activos, fontsize=8)

    # Escribir los valores en cada celda.
    fila = 0
    while fila < n:
        columna = 0
        while columna < n:
            valor = matriz[fila][columna]
            eje.text(
                columna,
                fila,
                f"{valor:.2f}",
                ha="center",
                va="center",
                fontsize=6,
                color="black",
            )
            columna = columna + 1
        fila = fila + 1

    eje.set_title(titulo)
    figura.colorbar(imagen, ax=eje, fraction=0.046, pad=0.04)
    figura.tight_layout()

    buffer = io.BytesIO()
    figura.savefig(buffer, format="png", dpi=120)
    plt.close(figura)
    buffer.seek(0)
    return buffer.read()


# ---------------------------------------------------------------------------
# Candlestick + SMA
# ---------------------------------------------------------------------------

def _dibujar_velas(eje, fechas, opens, highs, lows, closes):
    """
    Dibuja velas OHLC sobre el eje. Una vela consta de:
        - Una linea vertical de 'low' a 'high' (la mecha).
        - Un rectangulo de 'open' a 'close' (el cuerpo).
    Color verde si el cierre fue mayor o igual a la apertura, rojo en
    caso contrario.
    """
    ancho_cuerpo = 0.6
    indice = 0
    while indice < len(fechas):
        apertura = opens[indice]
        maximo = highs[indice]
        minimo = lows[indice]
        cierre = closes[indice]

        if apertura is None or cierre is None or maximo is None or minimo is None:
            indice = indice + 1
            continue

        color = "#2ecc71" if cierre >= apertura else "#e74c3c"

        # Mecha (linea vertical de minimo a maximo).
        eje.plot(
            [indice, indice], [minimo, maximo],
            color=color, linewidth=0.8, solid_capstyle="round"
        )

        # Cuerpo (rectangulo). Si open==close se dibuja una linea fina.
        cuerpo_bajo = min(apertura, cierre)
        cuerpo_alto = max(apertura, cierre)
        if cuerpo_alto == cuerpo_bajo:
            eje.plot(
                [indice - ancho_cuerpo / 2, indice + ancho_cuerpo / 2],
                [apertura, apertura],
                color=color, linewidth=1.0
            )
        else:
            rect = Rectangle(
                (indice - ancho_cuerpo / 2, cuerpo_bajo),
                ancho_cuerpo,
                cuerpo_alto - cuerpo_bajo,
                facecolor=color,
                edgecolor=color,
            )
            eje.add_patch(rect)

        indice = indice + 1


def grafico_candlestick(serie, ticker, ventanas_sma=(20, 50)):
    """
    Renderiza un candlestick con medias moviles simples superpuestas y
    devuelve los bytes PNG.

    Parametros:
        serie       : lista de dicts con 'fecha', 'open', 'high', 'low',
                       'close'. Debe venir ordenada ascendentemente.
        ticker      : etiqueta del activo para el titulo.
        ventanas_sma: tupla con los tamanos de ventana de las SMA a
                       dibujar. Por defecto SMA20 y SMA50.

    Si la serie es muy larga, se toma la cola (ultimos N puntos) para
    mantener la grafica legible. El limite es 250 puntos (aprox. 1 anio
    bursatil) que es lo recomendado para reportes.
    """
    LIMITE_PUNTOS = 250

    if len(serie) == 0:
        figura, eje = plt.subplots(figsize=(10, 4))
        eje.text(0.5, 0.5, "Sin datos", ha="center", va="center")
        eje.axis("off")
        buffer = io.BytesIO()
        figura.savefig(buffer, format="png", dpi=120)
        plt.close(figura)
        buffer.seek(0)
        return buffer.read()

    # Tomar los ultimos N puntos para legibilidad.
    if len(serie) > LIMITE_PUNTOS:
        recorte = serie[-LIMITE_PUNTOS:]
    else:
        recorte = serie

    fechas = []
    opens = []
    highs = []
    lows = []
    closes = []
    for fila in recorte:
        fechas.append(fila.get("fecha"))
        opens.append(fila.get("open"))
        highs.append(fila.get("high"))
        lows.append(fila.get("low"))
        closes.append(fila.get("close"))

    figura, eje = plt.subplots(figsize=(11, 5))
    _dibujar_velas(eje, fechas, opens, highs, lows, closes)

    # SMAs sobre el close.
    for ventana in ventanas_sma:
        valores_sma = sma(closes, ventana)
        # Filtrar None para no romper el plot de matplotlib.
        x_validos = []
        y_validos = []
        for i, v in enumerate(valores_sma):
            if v is not None:
                x_validos.append(i)
                y_validos.append(v)
        if x_validos:
            eje.plot(
                x_validos,
                y_validos,
                linewidth=1.2,
                label=f"SMA{ventana}",
            )

    # Etiquetas en el eje X: cada ~10 puntos para no saturar.
    n = len(fechas)
    paso = max(1, n // 10)
    x_ticks = list(range(0, n, paso))
    eje.set_xticks(x_ticks)
    eje.set_xticklabels(
        [fechas[i] for i in x_ticks], rotation=45, ha="right", fontsize=7
    )

    eje.set_title(f"Candlestick {ticker}  (ultimos {n} dias)")
    eje.set_ylabel("Precio")
    eje.legend(loc="upper left", fontsize=8)
    eje.grid(True, alpha=0.2)
    figura.tight_layout()

    buffer = io.BytesIO()
    figura.savefig(buffer, format="png", dpi=120)
    plt.close(figura)
    buffer.seek(0)
    return buffer.read()
