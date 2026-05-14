"""
Paquete de limpieza de series historicas.

Subdivision por roles:
    - deteccion : identifica filas problematicas (close cero, outliers).
    - correccion: aplica estrategias de correccion (eliminar, forward-fill).
    - reporte   : estructura el resumen de lo que se modifico.
    - pipeline  : orquesta deteccion + correccion + reporte.

API publica recomendada (a importar desde otros modulos):

    from etl.limpieza import limpiar_serie

    serie_limpia, reporte = limpiar_serie(serie_cruda)

Cada submodulo se mantiene corto y enfocado para que sea facil de revisar
y de probar.
"""

from etl.limpieza.pipeline import limpiar_serie, limpiar_portafolio
from etl.limpieza.reporte import ReporteLimpieza

__all__ = ["limpiar_serie", "limpiar_portafolio", "ReporteLimpieza"]
