"""
Controlador para operaciones administrativas de sesiones de mesa.

Este controlador proporciona endpoints para:
- Verificar el estado de las sesiones
- Corregir sesiones activas duplicadas
- Finalizar sesiones expiradas
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.business_logic.mesas.admin_sesiones_service import AdminSesionesService
from src.api.schemas.admin_sesiones_schema import (
    EstadoSesionesResponse,
    FixDuplicatesResponse,
    FinalizarExpiradasResponse
)

# Router para administración de sesiones
router = APIRouter(prefix="/admin/sesiones", tags=["Admin - Sesiones"])


@router.get(
    "/estado",
    response_model=EstadoSesionesResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener estado de sesiones activas",
    description="""
    Endpoint administrativo para obtener un resumen del estado actual de las sesiones.
    
    **Información retornada:**
    - Total de sesiones activas en el sistema
    - Total de mesas con sesiones activas
    - Número de mesas con sesiones duplicadas
    - Detalle de cada mesa con sesiones duplicadas
    - Lista completa de sesiones por mesa
    
    **Uso:**
    Este endpoint es útil para diagnosticar problemas con sesiones duplicadas
    antes de ejecutar la corrección.
    """,
    responses={
        200: {
            "description": "Estado obtenido exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "status": 200,
                        "total_sesiones_activas": 5,
                        "total_mesas": 3,
                        "mesas_con_duplicados": 1,
                        "detalles_duplicados": [
                            {
                                "id_mesa": "01K9TM84NJ4GAVQP5G91QXSMWS",
                                "sesiones_activas": 3
                            }
                        ],
                        "sesiones_por_mesa": [
                            {
                                "id_mesa": "01K9TM84NJ4GAVQP5G91QXSMWS",
                                "sesiones_activas": 3,
                                "tiene_duplicados": True
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "Error interno del servidor"
        }
    }
)
async def get_estado_sesiones(
    db: AsyncSession = Depends(get_database_session)
) -> EstadoSesionesResponse:
    """
    Obtiene el estado actual de las sesiones en el sistema.

    Parameters
    ----------
    db : AsyncSession
        Sesión de base de datos (inyectada por FastAPI).

    Returns
    -------
    EstadoSesionesResponse
        Información del estado de las sesiones.

    Raises
    ------
    HTTPException
        500: Si hay errores internos del servidor
    """
    try:
        service = AdminSesionesService(db)
        resultado = await service.get_estado_sesiones()
        
        return EstadoSesionesResponse(
            status=200,
            **resultado
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estado de sesiones: {str(e)}"
        )


@router.post(
    "/fix-duplicates",
    response_model=FixDuplicatesResponse,
    status_code=status.HTTP_200_OK,
    summary="Corregir sesiones activas duplicadas",
    description="""
    Endpoint administrativo para corregir sesiones activas duplicadas en la base de datos.
    
    **⚠️ IMPORTANTE: Este endpoint modifica datos en la base de datos**
    
    **Proceso de corrección:**
    1. Identifica todas las mesas con múltiples sesiones activas
    2. Para cada mesa:
       - Mantiene la sesión más reciente (por fecha_inicio) como ACTIVA
       - Finaliza todas las demás sesiones activas de esa mesa
    3. Retorna un reporte detallado de los cambios realizados
    
    **Caso de uso:**
    - Cuando el endpoint `/api/v1/login` retorna error "Multiple rows were found"
    - Después de migraciones o actualizaciones que dejaron datos inconsistentes
    - Como parte del mantenimiento preventivo del sistema
    
    **Seguridad:**
    - La sesión más reciente siempre se preserva
    - Las sesiones finalizadas mantienen su historial
    - La operación es transaccional (todo o nada)
    """,
    responses={
        200: {
            "description": "Corrección ejecutada exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "status": 200,
                        "success": True,
                        "message": "Se corrigieron 1 mesas con sesiones duplicadas",
                        "mesas_procesadas": 1,
                        "sesiones_finalizadas": 2,
                        "sesiones_mantenidas": 1,
                        "detalles": [
                            {
                                "id_mesa": "01K9TM84NJ4GAVQP5G91QXSMWS",
                                "sesiones_encontradas": 3,
                                "sesion_mantenida": {
                                    "id_sesion": "01HYYY...",
                                    "token_sesion": "01HZZZ...",
                                    "fecha_inicio": "2025-11-12T10:30:00"
                                },
                                "sesiones_finalizadas": [
                                    {
                                        "id_sesion": "01HXXX...",
                                        "token_sesion": "01HWWW...",
                                        "fecha_inicio": "2025-11-12T08:00:00"
                                    }
                                ]
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "Error interno del servidor"
        }
    }
)
async def fix_duplicate_sessions(
    db: AsyncSession = Depends(get_database_session)
) -> FixDuplicatesResponse:
    """
    Corrige sesiones activas duplicadas en la base de datos.

    Parameters
    ----------
    db : AsyncSession
        Sesión de base de datos (inyectada por FastAPI).

    Returns
    -------
    FixDuplicatesResponse
        Resultado de la corrección con detalles de los cambios realizados.

    Raises
    ------
    HTTPException
        500: Si hay errores internos del servidor
    """
    try:
        service = AdminSesionesService(db)
        resultado = await service.fix_duplicate_active_sessions()
        
        return FixDuplicatesResponse(
            status=200,
            **resultado
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al corregir sesiones duplicadas: {str(e)}"
        )


@router.post(
    "/finalizar-expiradas",
    response_model=FinalizarExpiradasResponse,
    status_code=status.HTTP_200_OK,
    summary="Finalizar sesiones expiradas",
    description="""
    Endpoint administrativo para finalizar sesiones que ya han expirado.
    
    **Proceso:**
    1. Busca todas las sesiones en estado ACTIVA
    2. Verifica cuáles han expirado (fecha_inicio + duracion_minutos < ahora)
    3. Marca las sesiones expiradas como FINALIZADA
    4. Retorna un reporte de las sesiones finalizadas
    
    **Una sesión está expirada si:**
    - Su estado es ACTIVA
    - Han transcurrido más de `duracion_minutos` desde `fecha_inicio`
    - Por defecto, duracion_minutos = 120 (2 horas)
    
    **Caso de uso:**
    - Limpieza periódica del sistema
    - Mantenimiento preventivo
    - Liberar recursos de sesiones antiguas
    """,
    responses={
        200: {
            "description": "Sesiones expiradas finalizadas exitosamente"
        },
        500: {
            "description": "Error interno del servidor"
        }
    }
)
async def finalizar_sesiones_expiradas(
    db: AsyncSession = Depends(get_database_session)
) -> FinalizarExpiradasResponse:
    """
    Finaliza todas las sesiones activas que ya han expirado.

    Parameters
    ----------
    db : AsyncSession
        Sesión de base de datos (inyectada por FastAPI).

    Returns
    -------
    FinalizarExpiradasResponse
        Resultado de la operación con detalles de las sesiones finalizadas.

    Raises
    ------
    HTTPException
        500: Si hay errores internos del servidor
    """
    try:
        service = AdminSesionesService(db)
        resultado = await service.finalizar_sesiones_expiradas()
        
        return FinalizarExpiradasResponse(
            status=200,
            **resultado
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al finalizar sesiones expiradas: {str(e)}"
        )
