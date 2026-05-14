"""
etl/limpieza/reporte.py
-----------------------
Estructura del reporte de limpieza. Es solo un contenedor de datos para
que el pipeline pueda devolver de forma ordenada que se modifico y por
que.
"""


class ReporteLimpieza:
    """
    Resumen del trabajo realizado por el pipeline de limpieza.

    Campos:
        - ticker: identificador del activo (cadena o None).
        - filas_entrada: total de filas recibidas.
        - filas_salida : total de filas tras la limpieza.
        - close_no_positivo : cantidad de filas con close <= 0 detectadas.
        - outliers_zscore   : cantidad de filas marcadas como outliers.
        - fechas_duplicadas : cantidad de fechas repetidas eliminadas.
        - estrategia       : nombre de la estrategia aplicada.
        - umbral_zscore    : umbral usado para outliers.
    """

    def __init__(
        self,
        ticker=None,
        filas_entrada=0,
        filas_salida=0,
        close_no_positivo=0,
        outliers_zscore=0,
        fechas_duplicadas=0,
        estrategia="eliminar",
        umbral_zscore=6.0,
        outliers_residuales=0,
        convergencia=True,
    ):
        self.ticker = ticker
        self.filas_entrada = filas_entrada
        self.filas_salida = filas_salida
        self.close_no_positivo = close_no_positivo
        self.outliers_zscore = outliers_zscore
        self.fechas_duplicadas = fechas_duplicadas
        self.estrategia = estrategia
        self.umbral_zscore = umbral_zscore
        # Cantidad de retornos extremos que siguen presentes despues de
        # agotar las pasadas. Si es > 0, el campo 'convergencia' es False
        # y conviene revisar manualmente la serie (puede tratarse de una
        # accion corporativa no ajustada o un cambio de regimen).
        self.outliers_residuales = outliers_residuales
        self.convergencia = convergencia

    def to_dict(self):
        """Devuelve el reporte como diccionario serializable a JSON."""
        return {
            "ticker": self.ticker,
            "filas_entrada": self.filas_entrada,
            "filas_salida": self.filas_salida,
            "filas_descartadas": self.filas_entrada - self.filas_salida,
            "close_no_positivo": self.close_no_positivo,
            "outliers_zscore": self.outliers_zscore,
            "fechas_duplicadas": self.fechas_duplicadas,
            "estrategia": self.estrategia,
            "umbral_zscore": self.umbral_zscore,
            "outliers_residuales": self.outliers_residuales,
            "convergencia": self.convergencia,
        }
