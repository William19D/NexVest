"""
routers/analisis.py
-------------------
Endpoints de analisis algoritmico sobre las series historicas almacenadas
en MongoDB. Cada endpoint delega el calculo a los modulos manuales del
paquete 'algorithms', sin librerias de alto nivel.

Endpoints expuestos
-------------------
GET /analisis/ordenamiento
    Ejecuta y mide los 12 algoritmos de ordenamiento.

GET /analisis/similitud
    Calcula los cuatro algoritmos de similitud entre dos activos.

GET /analisis/correlacion
    Construye la matriz de correlacion de Pearson para un grupo de activos.

GET /analisis/patrones/{mnemonic}
    Cuenta apariciones de los dos patrones soportados sobre un activo
    (sliding window).

GET /analisis/volatilidad/{mnemonic}
    Devuelve volatilidad diaria, anualizada y categoria de riesgo de un
    activo.

GET /analisis/riesgo
    Clasifica todo el portafolio en conservador / moderado / agresivo y
    devuelve el ranking ascendente por volatilidad.
"""

import os
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pymongo.database import Database

from algorithms.desempeno import ejecutar_analisis_ordenamiento
from algorithms import similitud as alg_similitud
from algorithms import patrones as alg_patrones
from algorithms import volatilidad as alg_volatilidad
from database import get_db
from etl.limpieza import limpiar_serie
from reportes import generar_reporte_portafolio

from routers._carga import (
    cargar_portafolio,
    cargar_serie,
    listar_mnemonicos,
)


router = APIRouter(prefix="/analisis", tags=["Analisis"])


# ---------------------------------------------------------------------------
# 1) Ordenamiento (ya existente, sin cambios)
# ---------------------------------------------------------------------------

@router.get("/ordenamiento", summary="Analisis de 12 algoritmos de ordenamiento")
def analisis_ordenamiento(
    max_registros: int = Query(
        0, ge=0, description="Limita el dataset (0 = sin limite)."
    ),
    incluir_dataset_ordenado: bool = Query(
        False,
        description="Si true, incluye en la respuesta el dataset ordenado completo.",
    ),
):
    """
    Ejecuta el analisis completo:
    - Ordenamiento ascendente del dataset unificado por fecha y close.
    - Ranking ascendente de tiempos de los 12 algoritmos.
    - Top 15 dias de mayor volumen por activo (ordenados ascendente).

    Tambien guarda los archivos de salida en etl/resultados_analisis.
    """
    ruta_base = Path(__file__).resolve().parents[1]
    ruta_historicos = ruta_base / "etl" / "historicos"
    if os.environ.get("VERCEL"):
        carpeta_salida = Path("/tmp") / "resultados_analisis"
    else:
        carpeta_salida = ruta_base / "etl" / "resultados_analisis"

    try:
        resultado = ejecutar_analisis_ordenamiento(
            ruta_historicos=ruta_historicos,
            max_registros=max_registros,
            carpeta_salida=carpeta_salida,
            generar_grafico=True,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Error ejecutando analisis: {exc}"
        ) from exc

    response = {
        "status": "ok",
        "total_registros": resultado["total_registros"],
        "tiempos_algoritmos_asc": resultado["resultados_tiempos"],
        "top_15_mayor_volumen_por_activo": resultado["top_15_por_activo"],
        "rutas_archivos": resultado["rutas_archivos"],
    }

    if incluir_dataset_ordenado:
        response["dataset_ordenado"] = resultado.get("dataset_ordenado")

    return response


# ---------------------------------------------------------------------------
# 2) Similitud entre dos activos
# ---------------------------------------------------------------------------

@router.get(
    "/similitud",
    summary="Similitud entre dos activos (Euclidean, Pearson, DTW, Coseno)",
)
def analisis_similitud(
    a: str = Query(..., description="Mnemonico del primer activo."),
    b: str = Query(..., description="Mnemonico del segundo activo."),
    base: str = Query(
        "retorno",
        description=(
            "'precio' para comparar precios de cierre, "
            "'retorno' para comparar retornos simples diarios."
        ),
    ),
    ventana_dtw: Optional[int] = Query(
        None,
        ge=1,
        description="Tamano de la banda Sakoe-Chiba para DTW (None = sin banda).",
    ),
    desde: Optional[str] = Query(None, description="Fecha inclusiva AAAA-MM-DD."),
    hasta: Optional[str] = Query(None, description="Fecha inclusiva AAAA-MM-DD."),
    db: Database = Depends(get_db),
):
    """
    Devuelve los cuatro valores de similitud calculados manualmente sobre
    las fechas comunes de las dos series.
    """
    if base not in ("precio", "retorno"):
        raise HTTPException(
            status_code=422,
            detail="El parametro 'base' debe ser 'precio' o 'retorno'.",
        )

    try:
        serie_a = cargar_serie(db, a, desde=desde, hasta=hasta)
        serie_b = cargar_serie(db, b, desde=desde, hasta=hasta)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if len(serie_a) == 0 or len(serie_b) == 0:
        raise HTTPException(
            status_code=422,
            detail="Alguna de las dos series no tiene datos en el rango pedido.",
        )

    resultado = alg_similitud.comparar_activos(
        serie_a,
        serie_b,
        base=base,
        ventana_dtw=ventana_dtw,
    )

    return {
        "activo_a": a.upper(),
        "activo_b": b.upper(),
        "desde": desde,
        "hasta": hasta,
        "base": resultado["base"],
        "puntos_comunes": resultado["puntos_comunes"],
        "metricas": {
            "distancia_euclidiana": resultado["euclidiana"],
            "correlacion_pearson": resultado["pearson"],
            "dynamic_time_warping": resultado["dtw"],
            "similitud_coseno": resultado["coseno"],
        },
    }


# ---------------------------------------------------------------------------
# 3) Matriz de correlacion del portafolio
# ---------------------------------------------------------------------------

@router.get(
    "/correlacion",
    summary="Matriz de correlacion de Pearson para un grupo de activos",
)
def analisis_correlacion(
    tickers: Optional[List[str]] = Query(
        None,
        description=(
            "Lista de mnemonicos. Si se omite, se usa el portafolio completo."
        ),
    ),
    base: str = Query(
        "retorno",
        description="'precio' o 'retorno' (recomendado 'retorno').",
    ),
    desde: Optional[str] = Query(None, description="Fecha inclusiva AAAA-MM-DD."),
    hasta: Optional[str] = Query(None, description="Fecha inclusiva AAAA-MM-DD."),
    db: Database = Depends(get_db),
):
    """
    Construye la matriz de correlacion de Pearson aplicando 'correlacion_pearson'
    a cada par de activos sobre las fechas comunes.

    La matriz se devuelve como lista de listas para que sea facilmente
    consumida por el frontend (heatmap).
    """
    if base not in ("precio", "retorno"):
        raise HTTPException(
            status_code=422,
            detail="El parametro 'base' debe ser 'precio' o 'retorno'.",
        )

    portafolio = cargar_portafolio(db, mnemonicos=tickers, desde=desde, hasta=hasta)
    activos = sorted(portafolio.keys())
    if len(activos) < 2:
        raise HTTPException(
            status_code=422,
            detail="Se requieren al menos dos activos con datos para la matriz.",
        )

    matriz = []
    i = 0
    while i < len(activos):
        fila = []
        j = 0
        while j < len(activos):
            ticker_i = activos[i]
            ticker_j = activos[j]
            if i == j:
                fila.append(1.0)
            else:
                _, valores_i, valores_j = alg_similitud.alinear_por_fechas(
                    portafolio[ticker_i],
                    portafolio[ticker_j],
                )
                if base == "retorno":
                    valores_i = alg_similitud.calcular_retornos(valores_i)
                    valores_j = alg_similitud.calcular_retornos(valores_j)

                if len(valores_i) < 2:
                    fila.append(0.0)
                else:
                    fila.append(
                        alg_similitud.correlacion_pearson(valores_i, valores_j)
                    )
            j = j + 1
        matriz.append(fila)
        i = i + 1

    return {
        "activos": activos,
        "base": base,
        "desde": desde,
        "hasta": hasta,
        "matriz": matriz,
    }


# ---------------------------------------------------------------------------
# 4) Patrones (sliding window)
# ---------------------------------------------------------------------------

@router.get(
    "/patrones/{mnemonic}",
    summary="Frecuencia de patrones (sliding window) sobre un activo",
)
def analisis_patrones(
    mnemonic: str,
    k: int = Query(3, ge=1, description="Tamano de la ventana."),
    desde: Optional[str] = Query(None, description="Fecha inclusiva AAAA-MM-DD."),
    hasta: Optional[str] = Query(None, description="Fecha inclusiva AAAA-MM-DD."),
    db: Database = Depends(get_db),
):
    """
    Aplica los dos patrones soportados:
        - dias_consecutivos_alza
        - ruptura_maximo_ventana
    sobre el historico del mnemonico solicitado.
    """
    try:
        serie = cargar_serie(db, mnemonic, desde=desde, hasta=hasta)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if len(serie) == 0:
        raise HTTPException(
            status_code=422,
            detail="La serie esta vacia en el rango pedido.",
        )

    resultado = alg_patrones.frecuencia_de_patrones(serie, k)

    return {
        "mnemonic": mnemonic.upper(),
        "k": resultado["k"],
        "total_dias": resultado["total_dias"],
        "desde": desde,
        "hasta": hasta,
        "patrones": resultado["patrones"],
    }


# ---------------------------------------------------------------------------
# 5) Volatilidad y categoria de riesgo de un activo
# ---------------------------------------------------------------------------

@router.get(
    "/volatilidad/{mnemonic}",
    summary="Volatilidad historica y categoria de riesgo de un activo",
)
def analisis_volatilidad(
    mnemonic: str,
    desde: Optional[str] = Query(None, description="Fecha inclusiva AAAA-MM-DD."),
    hasta: Optional[str] = Query(None, description="Fecha inclusiva AAAA-MM-DD."),
    db: Database = Depends(get_db),
):
    """
    Calcula desviacion estandar diaria, volatilidad anualizada (sqrt(252))
    y la categoria de riesgo del activo.
    """
    try:
        serie = cargar_serie(db, mnemonic, desde=desde, hasta=hasta)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if len(serie) < 2:
        raise HTTPException(
            status_code=422,
            detail="Se requieren al menos dos observaciones para la volatilidad.",
        )

    perfil = alg_volatilidad.perfil_riesgo_activo(mnemonic.upper(), serie)
    return {
        "desde": desde,
        "hasta": hasta,
        "perfil": perfil,
    }


# ---------------------------------------------------------------------------
# 6) Ranking de riesgo de todo el portafolio
# ---------------------------------------------------------------------------

@router.get(
    "/riesgo",
    summary="Clasificacion de riesgo y ranking del portafolio",
)
def analisis_riesgo(
    tickers: Optional[List[str]] = Query(
        None,
        description="Lista de mnemonicos; si se omite usa todo el portafolio.",
    ),
    desde: Optional[str] = Query(None, description="Fecha inclusiva AAAA-MM-DD."),
    hasta: Optional[str] = Query(None, description="Fecha inclusiva AAAA-MM-DD."),
    db: Database = Depends(get_db),
):
    """
    Calcula el perfil de riesgo de cada activo y devuelve el ranking
    ascendente por volatilidad anualizada, ademas del conteo por categoria.
    """
    portafolio = cargar_portafolio(db, mnemonicos=tickers, desde=desde, hasta=hasta)
    if len(portafolio) == 0:
        raise HTTPException(
            status_code=404,
            detail="No se encontraron activos con datos en el rango pedido.",
        )

    resultado = alg_volatilidad.clasificar_portafolio(portafolio)
    return {
        "desde": desde,
        "hasta": hasta,
        "total_activos": resultado["total_activos"],
        "resumen": resultado["resumen"],
        "ranking": resultado["ranking"],
    }


# ---------------------------------------------------------------------------
# 7) Listado de mnemonicos disponibles (utilidad para el frontend)
# ---------------------------------------------------------------------------

@router.get(
    "/mnemonicos",
    summary="Lista de mnemonicos disponibles para analisis",
)
def listar_disponibles(db: Database = Depends(get_db)):
    return {"mnemonicos": listar_mnemonicos(db)}


# ---------------------------------------------------------------------------
# 8) Reporte tecnico en PDF
# ---------------------------------------------------------------------------

@router.get(
    "/reporte/pdf",
    summary="Reporte tecnico consolidado en PDF (matriz, riesgo, candlesticks)",
    response_class=Response,
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "Documento PDF binario.",
        }
    },
)
def reporte_pdf(
    tickers: Optional[List[str]] = Query(
        None,
        description="Mnemonicos a incluir en el reporte. None = portafolio completo.",
    ),
    tickers_candle: Optional[List[str]] = Query(
        None,
        description="Subconjunto para los candlesticks. None = primeros 3 del portafolio.",
    ),
    base: str = Query(
        "retorno",
        description="'precio' o 'retorno' para la matriz de correlacion.",
    ),
    desde: Optional[str] = Query(None, description="Fecha inclusiva AAAA-MM-DD."),
    hasta: Optional[str] = Query(None, description="Fecha inclusiva AAAA-MM-DD."),
    db: Database = Depends(get_db),
):
    """
    Devuelve un PDF binario con:
        - Portada y parametros usados.
        - Heatmap de correlacion + top 10 pares.
        - Tabla de ranking de riesgo.
        - Candlesticks con SMA20 y SMA50 para 'tickers_candle'.
        - Apendice con el reporte de limpieza de datos.
    """
    if base not in ("precio", "retorno"):
        raise HTTPException(
            status_code=422,
            detail="El parametro 'base' debe ser 'precio' o 'retorno'.",
        )

    try:
        pdf_bytes = generar_reporte_portafolio(
            db,
            tickers=tickers,
            tickers_candle=tickers_candle,
            desde=desde,
            hasta=hasta,
            base_correlacion=base,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Error generando reporte: {exc}"
        ) from exc

    headers = {
        "Content-Disposition": 'attachment; filename="nexvest_reporte.pdf"',
    }
    return Response(
        content=pdf_bytes, media_type="application/pdf", headers=headers
    )


# ---------------------------------------------------------------------------
# 9) Reporte de limpieza por activo
# ---------------------------------------------------------------------------

@router.get(
    "/limpieza/{mnemonic}",
    summary="Reporte de filas descartadas por la limpieza para un activo",
)
def reporte_limpieza_activo(
    mnemonic: str,
    desde: Optional[str] = Query(None, description="Fecha inclusiva AAAA-MM-DD."),
    hasta: Optional[str] = Query(None, description="Fecha inclusiva AAAA-MM-DD."),
    umbral_zscore: float = Query(
        6.0,
        ge=1.0,
        description="Umbral del z-score para detectar outliers de retorno.",
    ),
    db: Database = Depends(get_db),
):
    """
    Carga la serie SIN limpiar y aplica el pipeline para reportar cuantas
    filas habrian sido descartadas y por que. No se persiste nada; el
    proposito es exclusivamente de auditoria.
    """
    try:
        serie_cruda = cargar_serie(
            db, mnemonic, desde=desde, hasta=hasta, limpiar=False
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    _, reporte = limpiar_serie(
        serie_cruda,
        ticker=mnemonic.upper(),
        umbral_zscore=umbral_zscore,
    )
    return reporte.to_dict()
