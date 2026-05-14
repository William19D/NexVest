"""
reportes/tablas.py
------------------
Helpers para construir objetos Table de reportlab a partir de listas de
diccionarios. Mantener este modulo aislado evita que el constructor del
PDF se llene de codigo de formateo.
"""

from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle


def construir_tabla_riesgo(ranking):
    """
    Construye una Table con el ranking de riesgo.

    Parametros:
        ranking: lista de dicts con las claves 'ticker', 'observaciones',
                 'desviacion_diaria', 'volatilidad_anualizada', 'categoria'.

    Devuelve un objeto Table de reportlab listo para insertar en el PDF.
    """
    encabezado = [
        "Ticker",
        "Observaciones",
        "Sigma diario",
        "Vol. anual",
        "Categoria",
    ]
    filas = [encabezado]
    for fila in ranking:
        filas.append([
            fila["ticker"],
            str(fila["observaciones"]),
            f"{fila['desviacion_diaria'] * 100:.3f}%",
            f"{fila['volatilidad_anualizada'] * 100:.2f}%",
            fila["categoria"],
        ])

    tabla = Table(
        filas,
        colWidths=[30 * mm, 30 * mm, 30 * mm, 30 * mm, 30 * mm],
        repeatRows=1,
    )

    estilos = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("ALIGN", (-1, 1), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]

    # Pintar la categoria segun nivel de riesgo.
    indice_fila = 1
    while indice_fila < len(filas):
        categoria = filas[indice_fila][-1]
        if categoria == "conservador":
            color = colors.HexColor("#c8e6c9")
        elif categoria == "moderado":
            color = colors.HexColor("#fff3c4")
        else:
            color = colors.HexColor("#ffcdd2")
        estilos.append(
            ("BACKGROUND", (-1, indice_fila), (-1, indice_fila), color)
        )
        indice_fila = indice_fila + 1

    tabla.setStyle(TableStyle(estilos))
    return tabla


def construir_tabla_top_correlaciones(activos, matriz, top_n=10):
    """
    A partir de una matriz de correlacion, construye una Table con los
    'top_n' pares mas correlacionados (en valor absoluto).

    Parametros:
        activos : lista de mnemonicos (filas/columnas de la matriz).
        matriz  : lista de listas con valores en [-1, 1].
        top_n   : cantidad de pares a incluir.
    """
    # Recolectar pares (i, j) con i < j.
    pares = []
    i = 0
    while i < len(activos):
        j = i + 1
        while j < len(activos):
            pares.append((activos[i], activos[j], matriz[i][j]))
            j = j + 1
        i = i + 1

    # Ordenar por magnitud absoluta de la correlacion descendente.
    pares.sort(key=lambda p: abs(p[2]), reverse=True)
    seleccionados = pares[:top_n]

    encabezado = ["Activo A", "Activo B", "Correlacion"]
    filas = [encabezado]
    for a, b, valor in seleccionados:
        filas.append([a, b, f"{valor:.4f}"])

    tabla = Table(
        filas,
        colWidths=[55 * mm, 55 * mm, 40 * mm],
        repeatRows=1,
    )
    tabla.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (-1, 1), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ])
    )
    return tabla


def construir_tabla_resumen_limpieza(reportes_limpieza):
    """
    Construye una Table con el resumen del proceso de limpieza por
    activo. Cada fila viene de ReporteLimpieza.to_dict().
    """
    encabezado = [
        "Ticker",
        "Entrada",
        "Salida",
        "close<=0",
        "Outliers",
        "Convergencia",
    ]
    filas = [encabezado]
    for rep in reportes_limpieza:
        filas.append([
            rep["ticker"],
            str(rep["filas_entrada"]),
            str(rep["filas_salida"]),
            str(rep["close_no_positivo"]),
            str(rep["outliers_zscore"]),
            "si" if rep["convergencia"] else "NO",
        ])

    tabla = Table(
        filas,
        colWidths=[28 * mm, 22 * mm, 22 * mm, 22 * mm, 22 * mm, 30 * mm],
        repeatRows=1,
    )
    tabla.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ])
    )
    return tabla
