"""
Endpoints para sincronización con sistema externo Domotica INC.

Este módulo proporciona rutas para recibir datos de sincronización del sistema Domotica
a través del scrapper, y procesarlos para actualizar la base de datos local.
"""

from typing import List, Dict, Any, Set, Tuple
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from decimal import Decimal, InvalidOperation

from src.core.database import get_database_session
from src.api.schemas.scrapper_schemas import ProductoDomotica, MesaDomotica
from src.business_logic.menu.categoria_service import CategoriaService
from src.business_logic.menu.producto_service import ProductoService
from src.api.schemas.producto_schema import ProductoCreate, ProductoUpdate, ProductoBase
from src.api.schemas.categoria_schema import CategoriaCreate, CategoriaUpdate

# Configuración del logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sync", tags=["Sincronización"])


@router.post(
    "/platos",
    status_code=status.HTTP_200_OK,
    summary="Sincronizar platos desde Domotica",
    description="Recibe datos de platos extraídos mediante scraping del sistema Domotica y los sincroniza con la base de datos local utilizando operaciones por lotes para mejor rendimiento.",
)
async def sync_platos(
    productos_domotica: List[ProductoDomotica] = Body(...),
    session: AsyncSession = Depends(get_database_session),
) -> Dict[str, Any]:
    """
    Sincroniza los platos extraídos del sistema Domotica con la base de datos local.

    Realiza las siguientes operaciones:
    1. Obtiene todas las categorías y productos existentes
    2. Crea las categorías nuevas en lote
    3. Actualiza las categorías existentes en lote
    4. Crea los productos nuevos en lote
    5. Actualiza los productos existentes en lote
    6. Marca como inactivos los productos que ya no existen en Domotica

    Parameters
    ----------
    productos_domotica : List[ProductoDomotica]
        Lista de productos extraídos del sistema Domotica
    session : AsyncSession
        Sesión de base de datos

    Returns
    -------
    Dict[str, Any]
        Resumen de la operación con contadores de elementos creados/actualizados

    Raises
    ------
    HTTPException
        Si ocurre un error durante el proceso de sincronización
    """
    try:
        categoria_service = CategoriaService(session)
        producto_service = ProductoService(session)
        resultados = {
            "categorias_creadas": 0,
            "categorias_actualizadas": 0,
            "productos_creados": 0,
            "productos_actualizados": 0,
        }

        categorias_to_sync = set([prod.categoria for prod in productos_domotica])
        existing_categorias = await categoria_service.get_categorias()
        existing_map = {cat.nombre: cat for cat in existing_categorias.items}
        existing_set = set(existing_map.keys())

        categorias_crear = [
            CategoriaCreate(
                nombre=cat, descripcion=f"Categoría {cat} creada desde sincronización"
            )
            for cat in categorias_to_sync
            if cat not in existing_set
        ]
        resultados["categorias_creadas"] = len(
            await categoria_service.batch_create_categorias(categorias_crear)
        )

        categorias_desactivar = [
            existing_map[cat].id
            for cat in existing_set
            if cat not in categorias_to_sync
        ]
        resultados["categorias_desactivadas"] = (
            await categoria_service.deactivate_categorias(categorias_desactivar)
        )

        categorias_activar = [
            existing_map[cat].id for cat in existing_set if cat in categorias_to_sync
        ]
        resultados["categorias_activadas"] = (
            await categoria_service.activate_categorias(categorias_activar)
        )

        productos_to_sync = {
            (prod.categoria, prod.nombre): prod for prod in productos_domotica
        }
        from src.models.menu.producto_model import ProductoModel
        from src.models.menu.categoria_model import CategoriaModel
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        result = await session.execute(
            select(ProductoModel).options(selectinload(ProductoModel.categoria))
        )
        existing_productos = result.scalars().all()
        existing_prod_map = {
            (prod.categoria.nombre, prod.nombre): prod for prod in existing_productos
        }
        existing_prod_set = set(existing_prod_map.keys())
        productos_crear = [
            ProductoCreate(
                nombre=prod.nombre,
                descripcion=f"Producto {prod.nombre} creado desde sincronización",
                precio_base=Decimal(prod.precio) if prod.precio else Decimal("0.00"),
                id_categoria=existing_map[prod.categoria].id,
            )
            for key, prod in productos_to_sync.items()
            if key not in existing_prod_set
        ]
        resultados["productos_creados"] = len(
            await producto_service.batch_create_productos(productos_crear)
        )

        ids_update = []
        data_update = []

        for key, prod_domotica in productos_to_sync.items():
            if key in existing_prod_map:
                prod_db = existing_prod_map[key]
                ids_update.append(prod_db.id)
                data_update.append(
                    {
                        "precio_base": (
                            Decimal(prod_domotica.precio)
                            if prod_domotica.precio
                            else Decimal("0.00")
                        ),
                        "disponible": True,
                    }
                )

        if ids_update:
            resultados["productos_actualizados"] = (
                await producto_service.repository.batch_update(ids_update, data_update)
            )

        ids_deactivate = []
        data_deactivate = []

        for key, prod_db in existing_prod_map.items():
            if key not in productos_to_sync:
                ids_deactivate.append(prod_db.id)
                data_deactivate.append({"disponible": False})

        if ids_deactivate:
            resultados["productos_desactivados"] = (
                await producto_service.repository.batch_update(
                    ids_deactivate, data_deactivate
                )
            )

        return resultados

    except Exception as e:
        logger.exception(f"Error durante la sincronización de platos: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error durante la sincronización de platos",
        )


@router.post(
    "/mesas",
    status_code=status.HTTP_200_OK,
    summary="Sincronizar mesas desde Domotica",
    description="Recibe datos de mesas extraídos mediante scraping del sistema Domotica. Crea zonas si no existen y registra mesas.",
)
async def sync_mesas(
    mesas_domotica: List[MesaDomotica] = Body(...),
    session: AsyncSession = Depends(get_database_session),
) -> Dict[str, Any]:
    """
    Recibe y registra las mesas extraídas del sistema Domotica.

    Flujo de operación:
    1. Obtiene el local "Barra Arena" por código
    2. Extrae zonas únicas del JSON recibido
    3. Crea/obtiene zonas (evita duplicados)
    4. Crea mesas con id_zona correspondiente (evita duplicados)

    Parameters
    ----------
    mesas_domotica : List[MesaDomotica]
        Lista de mesas extraídas del sistema Domotica
    session : AsyncSession
        Sesión de base de datos

    Returns
    -------
    Dict[str, Any]
        Resumen de la operación con contadores de zonas y mesas creadas

    Raises
    ------
    HTTPException
        Si ocurre un error durante el proceso
    """
    try:
        from src.business_logic.mesas.mesa_service import MesaService
        from src.business_logic.mesas.local_service import LocalService
        from src.business_logic.mesas.zona_service import ZonaService
        from src.api.schemas.mesa_schema import MesaCreate, EstadoMesa
        from src.api.schemas.zona_schema import ZonaCreate
        from src.models.mesas.zona_model import ZonaModel
        from sqlalchemy import select

        # Contadores para reporte
        resultados = {
            "zonas_creadas": 0,
            "zonas_existentes": 0,
            "mesas_creadas": 0,
            "mesas_existentes": 0,
        }

        # PASO 1: Obtener Local "Barra Arena"
        local_service = LocalService(session)
        local = await local_service.get_local_by_codigo("BA-001")

        # PASO 2: Extraer zonas únicas del JSON
        zonas_unicas = set(mesa.zona for mesa in mesas_domotica)
        logger.info(f"[SYNC MESAS] Zonas únicas extraídas: {zonas_unicas}")

        # PASO 3: Crear/Obtener zonas
        zona_map = {}  # {nombre_zona: id_zona}
        zona_service = ZonaService(session)

        for nombre_zona in zonas_unicas:
            # Buscar si ya existe zona con ese nombre para este local
            result = await session.execute(
                select(ZonaModel).where(
                    ZonaModel.id_local == local.id, ZonaModel.nombre == nombre_zona
                )
            )
            zona = result.scalars().first()

            if zona:
                # Zona ya existe
                logger.info(
                    f"[SYNC MESAS] Zona '{nombre_zona}' ya existe (ID: {zona.id})"
                )
                zona_map[nombre_zona] = zona.id
                resultados["zonas_existentes"] += 1
            else:
                # Crear nueva zona
                nueva_zona = await zona_service.create_zona(
                    ZonaCreate(
                        id_local=local.id,
                        nombre=nombre_zona,
                        descripcion=f"Zona {nombre_zona} creada desde sincronización",
                        nivel=0,
                        capacidad_maxima=None,
                    )
                )
                logger.info(
                    f"[SYNC MESAS] Zona '{nombre_zona}' creada (ID: {nueva_zona.id})"
                )
                zona_map[nombre_zona] = nueva_zona.id
                resultados["zonas_creadas"] += 1

        # PASO 4: Transformar mesas con id_zona
        mesa_service = MesaService(session)
        mesas_a_crear = []

        for mesa in mesas_domotica:
            # Determinar capacidad
            capacidad = getattr(mesa, "capacidad", None)
            if capacidad is None:
                capacidad = 4

            # Determinar estado
            estado_str = getattr(mesa, "estado", None)
            if estado_str:
                try:
                    estado = (
                        EstadoMesa(estado_str.lower())
                        if estado_str.lower() in [e.value for e in EstadoMesa]
                        else EstadoMesa.DISPONIBLE
                    )
                except Exception:
                    estado = EstadoMesa.DISPONIBLE
            else:
                estado = EstadoMesa.DISPONIBLE

            # Crear MesaCreate con id_zona
            mesas_a_crear.append(
                MesaCreate(
                    numero=mesa.nombre,
                    capacidad=capacidad,
                    id_zona=zona_map[mesa.zona],
                    nota=mesa.nota if hasattr(mesa, "nota") else None,
                    estado=estado,
                )
            )

        # PASO 5: Crear mesas en batch (el servicio ya valida duplicados)
        logger.info(f"[SYNC MESAS] Intentando crear {len(mesas_a_crear)} mesas")
        mesas_creadas = await mesa_service.batch_create_mesas(mesas_a_crear)
        resultados["mesas_creadas"] = len(mesas_creadas)
        resultados["mesas_existentes"] = len(mesas_a_crear) - len(mesas_creadas)

        logger.info(f"[SYNC MESAS] Resumen: {resultados}")

        return {
            "status": "success",
            "message": f"Sincronización completada: {resultados['zonas_creadas']} zonas creadas, {resultados['mesas_creadas']} mesas creadas",
            "resultados": resultados,
            "zonas_procesadas": list(zonas_unicas),
        }

    except HTTPException:
        # Re-raise HTTPException directamente
        raise
    except Exception as e:
        logger.exception(f"Error durante la sincronización de mesas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error durante la sincronización: {str(e)}",
        )
