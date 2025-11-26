"""
Controlador para el sistema de login simplificado (temporal).
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.business_logic.auth.login_service import LoginService
from src.api.schemas.login_schema import LoginRequest, LoginResponse
from src.business_logic.exceptions.mesa_exceptions import MesaNotFoundError

# Router para login
router = APIRouter(prefix="/login", tags=["Login"])


@router.post(
    "",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login simplificado de usuario temporal",
    description="""
    Endpoint para login simplificado de usuarios temporales del restaurante.

    ## Descripción General
    
    Este endpoint permite a los usuarios temporales (clientes) iniciar sesión en una mesa
    del restaurante. Múltiples usuarios pueden compartir la misma sesión de mesa,
    permitiendo colaboración en pedidos grupales.

    ## Flujo de Login

    1. **Validación de mesa** (NUEVO):
       - Verifica que la mesa exista en el sistema
       - Verifica que la mesa esté activa
       - Si falla → HTTP 404 con código `MESA_NOT_FOUND` o `MESA_INACTIVE`
    
    2. **Validación de email**:
       - El email debe contener 'correo', 'mail' o '@'
       - Si falla → HTTP 422 (validación Pydantic)
    
    3. **Gestión de usuario**:
       - Si el correo NO existe → Crea nuevo usuario
       - Si el correo existe y nombre difiere → Actualiza nombre
       - Actualiza `ultimo_acceso`
    
    4. **Gestión de sesión de mesa**:
       - Si NO existe sesión activa → Crea nueva sesión (duración: 2 horas)
       - Si existe sesión **expirada** → Marca como `FINALIZADA` y crea nueva
       - Si existe sesión **válida** → Asocia usuario a sesión existente
    
    5. **Respuesta**: Retorna credenciales de sesión

    ## Sesiones Compartidas
    
    Cuando varios usuarios se loguean a la misma mesa, todos comparten:
    - El mismo `token_sesion`
    - El mismo `id_sesion_mesa`
    - La misma `fecha_expiracion`

    ## Expiración de Sesiones
    
    Una sesión se considera **expirada** cuando:
    - Su estado es `FINALIZADA`, o
    - Han pasado más de `duracion_minutos` (por defecto 120 min) desde `fecha_inicio`
    
    Cuando un usuario intenta unirse a una sesión expirada:
    1. La sesión anterior se marca como `FINALIZADA`
    2. Se crea una nueva sesión `ACTIVA`
    3. El usuario se asocia a la nueva sesión

    ## Códigos de Error

    | HTTP | Código | Descripción |
    |------|--------|-------------|
    | 404 | `MESA_NOT_FOUND` | La mesa no existe en la base de datos |
    | 404 | `MESA_INACTIVE` | La mesa existe pero está desactivada |
    | 422 | - | Error de validación (email inválido, campos faltantes) |
    | 400 | - | Otros errores de validación de negocio |
    | 500 | - | Error interno del servidor |

    ## Ejemplo de Uso

    ### Caso 1: Primer usuario crea sesión
    ```json
    POST /api/v1/login?id_mesa=01HXXX...
    {
        "email": "juan@correo.com",
        "nombre": "Juan Pérez"
    }
    
    // Respuesta 200:
    {
        "status": 200,
        "code": "SUCCESS",
        "id_usuario": "01HABC...",
        "id_sesion_mesa": "01HDEF...",
        "token_sesion": "01HGHI...",
        "message": "Login exitoso",
        "fecha_expiracion": "2025-11-26T16:30:00"
    }
    ```

    ### Caso 2: Segundo usuario comparte sesión
    ```json
    POST /api/v1/login?id_mesa=01HXXX...
    {
        "email": "maria@correo.com",
        "nombre": "María García"
    }
    
    // Respuesta 200 (MISMO token_sesion):
    {
        "status": 200,
        "code": "SUCCESS",
        "id_usuario": "01HJKL...",  // Diferente usuario
        "id_sesion_mesa": "01HDEF...",  // MISMA sesión
        "token_sesion": "01HGHI...",  // MISMO token
        "message": "Login exitoso",
        "fecha_expiracion": "2025-11-26T16:30:00"
    }
    ```

    ### Caso 3: Mesa no existe
    ```json
    POST /api/v1/login?id_mesa=ID_INEXISTENTE
    {
        "email": "test@correo.com",
        "nombre": "Test"
    }
    
    // Respuesta 404:
    {
        "detail": {
            "message": "No se encontró la mesa con ID 'ID_INEXISTENTE'",
            "code": "MESA_NOT_FOUND"
        }
    }
    ```

    ### Caso 4: Mesa inactiva
    ```json
    POST /api/v1/login?id_mesa=01HMESA_INACTIVA
    {
        "email": "test@correo.com",
        "nombre": "Test"
    }
    
    // Respuesta 404:
    {
        "detail": {
            "message": "La mesa '5' no está activa",
            "code": "MESA_INACTIVE"
        }
    }
    ```
    """,
    responses={
        200: {
            "description": "Login exitoso - Usuario autenticado y asociado a sesión de mesa",
            "content": {
                "application/json": {
                    "example": {
                        "status": 200,
                        "code": "SUCCESS",
                        "id_usuario": "01HABC123456789DEFGHIJK",
                        "id_sesion_mesa": "01HDEF123456789GHIJKLM",
                        "token_sesion": "01HGHI123456789JKLMNOP",
                        "message": "Login exitoso",
                        "fecha_expiracion": "2025-11-26T16:30:00"
                    }
                }
            }
        },
        400: {
            "description": "Error de validación de negocio",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Error al crear usuario con email 'test@correo.com'"
                    }
                }
            }
        },
        404: {
            "description": "Mesa no encontrada o inactiva",
            "content": {
                "application/json": {
                    "examples": {
                        "mesa_no_existe": {
                            "summary": "Mesa no existe en la base de datos",
                            "value": {
                                "detail": {
                                    "message": "No se encontró la mesa con ID '01HXXX...'",
                                    "code": "MESA_NOT_FOUND"
                                }
                            }
                        },
                        "mesa_inactiva": {
                            "summary": "Mesa existe pero está desactivada",
                            "value": {
                                "detail": {
                                    "message": "La mesa '5' no está activa",
                                    "code": "MESA_INACTIVE"
                                }
                            }
                        }
                    }
                }
            }
        },
        422: {
            "description": "Error de validación de datos de entrada (Pydantic)",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "type": "value_error",
                                "loc": ["body", "email"],
                                "msg": "Value error, El email debe contener 'correo', 'mail' o '@' en su formato",
                                "input": "texto_invalido"
                            }
                        ]
                    }
                }
            }
        },
        500: {
            "description": "Error interno del servidor",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Error interno del servidor: [descripción del error]"
                    }
                }
            }
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
        404: Si la mesa no existe o no está activa
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

    except MesaNotFoundError as e:
        # Mesa no encontrada o inactiva
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": str(e),
                "code": e.error_code
            }
        )
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
