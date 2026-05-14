"""
reportes/pdf_builder.py
-----------------------
Constructor del documento PDF. Recibe los insumos ya calculados
(correlaciones, ranking de riesgo, graficos en bytes) y los ensambla
con reportlab.

Estructura del documento:

    1. Portada: titulo, fecha, parametros, resumen de activos.
    2. Seccion de matriz de correlacion: heatmap + top pares.
    3. Seccion de riesgo: tabla de ranking ascendente.
    4. Seccion de candlesticks: una pagina por activo seleccionado.
    5. Apendice: resumen del proceso de limpieza.
"""

import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
)

from reportes.tablas import (
    construir_tabla_resumen_limpieza,
    construir_tabla_riesgo,
    construir_tabla_top_correlaciones,
)


def _estilos():
    """Hojas de estilos del documento."""
    base = getSampleStyleSheet()
    base.add(
        ParagraphStyle(
            name="Titulo1NexVest",
            parent=base["Title"],
            fontSize=20,
            spaceAfter=8 * mm,
            alignment=TA_CENTER,
        )
    )
    base.add(
        ParagraphStyle(
            name="Subtitulo",
            parent=base["Heading2"],
            fontSize=13,
            textColor="#1f4e79",
            spaceBefore=6 * mm,
            spaceAfter=3 * mm,
        )
    )
    base.add(
        ParagraphStyle(
            name="Parrafo",
            parent=base["BodyText"],
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
        )
    )
    return base


def _imagen_desde_bytes(bytes_png, ancho_mm):
    """
    Convierte un PNG en bytes a un Image de reportlab con el ancho
    especificado en milimetros y altura proporcional al aspect ratio
    original de la imagen.

    Se lee el tamano nativo del PNG con ImageReader para calcular la
    altura preservando la proporcion.
    """
    lector = ImageReader(io.BytesIO(bytes_png))
    ancho_natural, alto_natural = lector.getSize()
    ancho_pts = ancho_mm * mm
    alto_pts = ancho_pts * (alto_natural / ancho_natural)
    return Image(io.BytesIO(bytes_png), width=ancho_pts, height=alto_pts)


def construir_pdf(
    titulo,
    parametros,
    activos_portafolio,
    matriz_correlacion_png,
    activos_correlacion,
    matriz_valores,
    ranking_riesgo,
    candlesticks_png,
    reportes_limpieza,
):
    """
    Genera el PDF y devuelve sus bytes.

    Parametros:
        titulo                   : titulo del reporte.
        parametros               : dict con parametros usados (fechas,
                                    base, etc.); se imprime en la portada.
        activos_portafolio       : lista de todos los mnemonicos en el
                                    portafolio.
        matriz_correlacion_png   : PNG ya renderizado del heatmap.
        activos_correlacion      : lista de mnemonicos ordenada del heatmap.
        matriz_valores           : valores numericos de la matriz.
        ranking_riesgo           : lista de dicts (perfil_riesgo_activo).
        candlesticks_png         : lista de (ticker, png_bytes).
        reportes_limpieza        : lista de dicts (ReporteLimpieza.to_dict()).
    """
    estilos = _estilos()
    buffer = io.BytesIO()
    documento = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=titulo,
        author="NexVest",
    )

    historia = []

    # 1) Portada
    historia.append(Paragraph(titulo, estilos["Titulo1NexVest"]))
    historia.append(
        Paragraph(
            f"Generado: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            estilos["Parrafo"],
        )
    )
    historia.append(Spacer(1, 4 * mm))

    parametros_html = "<br/>".join(
        f"<b>{clave}:</b> {valor}" for clave, valor in parametros.items()
    )
    historia.append(Paragraph(parametros_html, estilos["Parrafo"]))
    historia.append(Spacer(1, 4 * mm))

    historia.append(Paragraph("Activos analizados", estilos["Subtitulo"]))
    historia.append(
        Paragraph(", ".join(activos_portafolio), estilos["Parrafo"])
    )

    # 2) Matriz de correlacion
    historia.append(PageBreak())
    historia.append(Paragraph("Matriz de correlacion", estilos["Subtitulo"]))
    historia.append(
        Paragraph(
            "Correlacion de Pearson calculada manualmente sobre las fechas "
            "comunes a cada par de activos. Valor 1 indica movimiento "
            "perfectamente lineal en la misma direccion, -1 perfectamente "
            "inverso y 0 ausencia de relacion lineal.",
            estilos["Parrafo"],
        )
    )
    historia.append(Spacer(1, 3 * mm))
    historia.append(_imagen_desde_bytes(matriz_correlacion_png, 170))
    historia.append(Spacer(1, 4 * mm))
    historia.append(
        Paragraph("Top pares por correlacion absoluta", estilos["Subtitulo"])
    )
    historia.append(
        construir_tabla_top_correlaciones(
            activos_correlacion, matriz_valores, top_n=10
        )
    )

    # 3) Ranking de riesgo
    historia.append(PageBreak())
    historia.append(Paragraph("Clasificacion de riesgo", estilos["Subtitulo"]))
    historia.append(
        Paragraph(
            "Volatilidad anualizada = desviacion estandar de los retornos "
            "diarios * sqrt(252). Umbrales: conservador (&lt; 15%), "
            "moderado (15% - 30%), agresivo (&gt; 30%).",
            estilos["Parrafo"],
        )
    )
    historia.append(Spacer(1, 3 * mm))
    historia.append(construir_tabla_riesgo(ranking_riesgo))

    # 4) Candlesticks
    if candlesticks_png:
        historia.append(PageBreak())
        historia.append(
            Paragraph("Candlesticks con medias moviles", estilos["Subtitulo"])
        )
        historia.append(
            Paragraph(
                "Una vela por dia con cuerpo open-close y mecha low-high. "
                "Se superponen SMA20 y SMA50 calculadas manualmente.",
                estilos["Parrafo"],
            )
        )
        for ticker, png_bytes in candlesticks_png:
            historia.append(Spacer(1, 3 * mm))
            historia.append(
                Paragraph(f"{ticker}", estilos["Subtitulo"])
            )
            historia.append(_imagen_desde_bytes(png_bytes, 170))

    # 5) Apendice de limpieza
    if reportes_limpieza:
        historia.append(PageBreak())
        historia.append(
            Paragraph("Apendice: limpieza de datos", estilos["Subtitulo"])
        )
        historia.append(
            Paragraph(
                "Resumen por activo del numero de filas descartadas y los "
                "motivos. 'Convergencia = NO' indica que despues de las "
                "pasadas iterativas seguia habiendo retornos extremos; "
                "suele asociarse a acciones corporativas no ajustadas en el "
                "dato fuente.",
                estilos["Parrafo"],
            )
        )
        historia.append(Spacer(1, 3 * mm))
        historia.append(construir_tabla_resumen_limpieza(reportes_limpieza))

    documento.build(historia)
    buffer.seek(0)
    return buffer.read()
