"""
Controlador para el sistema de login simplificado (temporal).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.business_logic.auth.login_service import LoginService
from src.api.schemas.login_schema import LoginRequest, LoginResponse

# Router para login
router = APIRouter(prefix="/login", tags=["Login"])


@router.post(
    "",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login simplificado de usuario temporal",
    description="""
    Endpoint para login simplificado de usuarios temporales del restaurante.

    **IMPORTANTE:** Múltiples usuarios pueden compartir la misma sesión de mesa.
    Cuando varios usuarios se loguean a la misma mesa, todos comparten el mismo
    token_sesion, permitiendo colaboración en pedidos.

    **Flujo:**
    1. Valida formato del email (debe contener 'correo', 'mail' o '@')
    2. Si el correo NO existe: crea nuevo usuario
    3. Si el correo existe:
       - Si el nombre NO coincide: actualiza el nombre
       - Si coincide: no hace nada
    4. Actualiza ultimo_acceso
    5. Busca sesión activa de la mesa:
       - Si NO existe: crea nueva sesión y asocia al usuario
       - Si existe y NO está expirada: asocia al usuario a la sesión existente (comparte token)
       - Si existe y está expirada: crea nueva sesión y asocia al usuario
    6. Retorna id_usuario, id_sesion_mesa, token_sesion (compartido) y fecha_expiracion

    **Parámetros de consulta:**
    - `id_mesa`: ID de la mesa donde se realiza el login (requerido)

    **Ejemplo de uso (Sesión Compartida):**
    ```
    # Usuario 1 crea la sesión
    POST /api/v1/login?id_mesa=01HXXX...
    {
        "email": "juan@correo.com",
        "nombre": "Juan Pérez"
    }
    # Respuesta: token_sesion = "01HYYY..."

    # Usuario 2 se une a la misma mesa → comparte el mismo token
    POST /api/v1/login?id_mesa=01HXXX...
    {
        "email": "maria@correo.com",
        "nombre": "María García"
    }
    # Respuesta: token_sesion = "01HYYY..." (MISMO TOKEN)
    ```
    """,
    responses={
        200: {
            "description": "Login exitoso",
            "content": {
                "application/json": {
                    "example": {
                        "status": 200,
                        "code": "SUCCESS",
                        "id_usuario": "01HXX...",
                        "id_sesion_mesa": "01HYY...",
                        "token_sesion": "01HZZ...",
                        "message": "Login exitoso",
                        "fecha_expiracion": "2025-11-09T14:30:00"
                    }
                }
            }
        },
        400: {
            "description": "Error de validación (formato de email inválido, mesa no existe, etc.)"
        },
        500: {
            "description": "Error interno del servidor"
        }
    }
)
async def login_temporal(
    login_data: LoginRequest,
    id_mesa: str = Query(..., description="ID de la mesa donde se realiza el login"),
    db: AsyncSession = Depends(get_database_session)
) -> LoginResponse:
    """
    Realiza el login simplificado de un usuario temporal.

    Parameters
    ----------
    login_data : LoginRequest
        Datos de login (email y nombre).
    id_mesa : str
        ID de la mesa donde se realiza el login.
    db : AsyncSession
        Sesión de base de datos (inyectada por FastAPI).

    Returns
    -------
    LoginResponse
        Respuesta con id_usuario, id_sesion_mesa, token_sesion y fecha_expiracion.

    Raises
    ------
    HTTPException
        400: Si hay errores de validación
        500: Si hay errores internos del servidor
    """
    try:
        # Crear servicio
        login_service = LoginService(db)

        # Realizar login
        response = await login_service.login(login_data, id_mesa)

        # Hacer commit de la transacción
        await db.commit()

        return response

    except ValueError as e:
        # Errores de validación
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Errores internos
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )
