"""
Paquete de generacion de reportes PDF.

Subdivision por roles (archivos cortos y enfocados):

    - medias_moviles : calculo manual de SMA (Simple Moving Average).
    - graficos       : conversion de datos numericos a imagenes PNG en
                       memoria (heatmap de correlacion, candlestick + SMA).
    - tablas         : helpers para construir tablas de reportlab a partir
                       de listas de dicts.
    - pdf_builder    : ensambla el documento PDF final con titulo,
                       resumen, tablas y graficos.
    - generador      : punto de entrada de alto nivel. Recibe la base de
                       datos y un par de parametros, y devuelve los bytes
                       del PDF listo para descargar.

API publica:

    from reportes import generar_reporte_portafolio
"""

from reportes.generador import generar_reporte_portafolio

__all__ = ["generar_reporte_portafolio"]
