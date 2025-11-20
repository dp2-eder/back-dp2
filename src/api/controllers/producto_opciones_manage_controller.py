"""
Endpoints para gestionar opciones de productos (secciones y complementos).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.business_logic.menu.producto_opciones_manage_service import ProductoOpcionesManageService
from src.api.schemas.producto_opciones_manage_schema import (
    AgregarOpcionesProductoRequest,
    AgregarOpcionesProductoResponse,
    OpcionesProductoListResponse,
)
from src.business_logic.exceptions.producto_exceptions import (
    ProductoNotFoundError,
    ProductoValidationError,
)

router = APIRouter(prefix="/productos", tags=["Opciones de Productos"])


@router.get(
    "/{producto_id}/opciones-manage",
    response_model=OpcionesProductoListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar secciones de opciones de un producto",
    description="Obtiene todas las secciones de opciones con sus complementos para un producto específico.",
)
async def listar_opciones_producto(
    producto_id: str,
    session: AsyncSession = Depends(get_database_session)
) -> OpcionesProductoListResponse:
    """
    Lista todas las secciones de opciones con sus complementos de un producto.

    Una sección es un tipo de opción (ej: "Extras", "Nivel de Ají") que agrupa
    complementos relacionados (ej: "Queso Extra", "Ají Suave").

    Args:
        producto_id: ID del producto a consultar.
        session: Sesión de base de datos.

    Returns:
        Lista de secciones con sus complementos.

    Raises:
        HTTPException:
            - 404: Si no se encuentra el producto.
            - 500: Si ocurre un error interno del servidor.

    Example Response:
        ```json
        {
          "id_producto": "01KA9TRZE8PRODUCTO123",
          "nombre_producto": "Pizza Margherita",
          "total_secciones": 2,
          "secciones": [
            {
              "id_tipo_opcion": "01KA9TRZE8TAMANO123",
              "nombre": "Tamaño",
              "codigo": "tamano",
              "descripcion": "Seleccione el tamaño",
              "seleccion_minima": 1,
              "seleccion_maxima": 1,
              "orden": 0,
              "activo": true,
              "complementos": [
                {
                  "id": "01KAF7HZSYOPCION123",
                  "nombre": "Personal",
                  "precio_adicional": "0.00",
                  "activo": true,
                  "orden": 0
                }
              ]
            }
          ]
        }
        ```
    """
    try:
        service = ProductoOpcionesManageService(session)
        return await service.listar_opciones_producto(producto_id)
    except ProductoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )


@router.post(
    "/{producto_id}/opciones-manage",
    response_model=AgregarOpcionesProductoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar secciones de opciones a un producto",
    description="Agrega una o más secciones (tipos de opciones) con sus complementos a un producto. Si la sección ya existe, la reutiliza.",
)
async def agregar_opciones_producto(
    producto_id: str,
    request: AgregarOpcionesProductoRequest,
    session: AsyncSession = Depends(get_database_session)
) -> AgregarOpcionesProductoResponse:
    """
    Agrega secciones de opciones con complementos a un producto.

    Este endpoint permite al frontend enviar un formulario con:
    - Nombre de la sección (ej: "Extras", "Nivel de Ají")
    - Lista de complementos con nombre y precio

    Si la sección (tipo de opción) ya existe en el sistema, se reutiliza.
    Los complementos siempre se crean nuevos para el producto.

    Args:
        producto_id: ID del producto al que agregar opciones.
        request: Datos de las secciones y complementos a agregar.
        session: Sesión de base de datos.

    Returns:
        Confirmación con detalles de las secciones y complementos creados.

    Raises:
        HTTPException:
            - 400: Si los datos de entrada son inválidos.
            - 404: Si no se encuentra el producto.
            - 500: Si ocurre un error interno del servidor.

    Example Request:
        ```json
        {
          "secciones": [
            {
              "nombre_seccion": "Extras",
              "descripcion": "Ingredientes adicionales",
              "seleccion_minima": 0,
              "seleccion_maxima": 5,
              "complementos": [
                {
                  "nombre": "Queso Extra",
                  "precio_adicional": "2.50",
                  "orden": 0
                },
                {
                  "nombre": "Aceitunas",
                  "precio_adicional": "1.50",
                  "orden": 1
                }
              ]
            },
            {
              "nombre_seccion": "Nivel de Ají",
              "descripcion": "Seleccione el nivel de picante",
              "seleccion_minima": 1,
              "seleccion_maxima": 1,
              "complementos": [
                {
                  "nombre": "Sin Ají",
                  "precio_adicional": "0.00",
                  "orden": 0
                },
                {
                  "nombre": "Ají Suave",
                  "precio_adicional": "0.00",
                  "orden": 1
                },
                {
                  "nombre": "Ají Picante",
                  "precio_adicional": "0.50",
                  "orden": 2
                }
              ]
            }
          ]
        }
        ```

    Example Response:
        ```json
        {
          "mensaje": "Se agregaron 2 sección(es) con 5 complemento(s) al producto",
          "secciones_creadas": 2,
          "complementos_creados": 5,
          "detalles": [...]
        }
        ```
    """
    try:
        service = ProductoOpcionesManageService(session)
        return await service.agregar_opciones_producto(producto_id, request)
    except ProductoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ProductoValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}",
        )
