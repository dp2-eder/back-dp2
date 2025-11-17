"""
Servicio para el sistema de login simplificado (temporal).
"""

from datetime import datetime, timezone
from ulid import ULID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repositories.auth.usuario_repository import UsuarioRepository
from src.repositories.mesas.sesion_mesa_repository import SesionMesaRepository
from src.models.auth.usuario_model import UsuarioModel
from src.models.mesas.sesion_mesa_model import SesionMesaModel
from src.core.enums.sesion_mesa_enums import EstadoSesionMesa
from src.api.schemas.login_schema import LoginRequest, LoginResponse


class LoginService:
    """Servicio para el login simplificado de usuarios temporales.

    Attributes
    ----------
    usuario_repository : UsuarioRepository
        Repositorio para acceso a datos de usuarios.
    sesion_mesa_repository : SesionMesaRepository
        Repositorio para acceso a datos de sesiones de mesa.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio con una sesión de base de datos.

        Parameters
        ----------
        session : AsyncSession
            Sesión asíncrona de SQLAlchemy para realizar operaciones en la base de datos.
        """
        self.usuario_repository = UsuarioRepository(session)
        self.sesion_mesa_repository = SesionMesaRepository(session)
        self.session = session

    async def login(self, login_data: LoginRequest, id_mesa: str) -> LoginResponse:
        """
        Realiza el login simplificado de un usuario.

        Flujo:
        1. Validar formato del email
        2. Buscar si existe el correo:
           - Si NO existe: crear nuevo usuario
           - Si existe: verificar nombre
             - Si el nombre NO coincide: actualizar nombre
             - Si coincide: no hacer nada
        3. Actualizar ultimo_acceso
        4. Crear/obtener sesión de mesa temporal activa
        5. Retornar id_usuario, id_sesion_mesa, token_sesion

        Parameters
        ----------
        login_data : LoginRequest
            Datos de login (email y nombre).
        id_mesa : str
            ID de la mesa donde se realiza el login.

        Returns
        -------
        LoginResponse
            Respuesta con id_usuario, id_sesion_mesa, token_sesion y fecha_expiracion.

        Raises
        ------
        ValueError
            Si el formato del email es inválido o la mesa no existe.
        """
        # Validar formato del email
        if not UsuarioModel.validar_formato_email(login_data.email):
            raise ValueError(
                "El email debe contener 'correo', 'mail' o '@' en su formato"
            )

        # Buscar si existe el correo
        usuario = await self.usuario_repository.get_by_email(login_data.email)

        if usuario is None:
            # NO existe: crear nuevo usuario
            usuario = UsuarioModel(
                email=login_data.email,
                nombre=login_data.nombre,
                ultimo_acceso=datetime.now(timezone.utc)
            )
            try:
                usuario = await self.usuario_repository.create(usuario)
            except IntegrityError:
                raise ValueError(f"Error al crear usuario con email '{login_data.email}'")
        else:
            # Existe: verificar si el nombre coincide
            if usuario.nombre != login_data.nombre:
                # Nombre NO coincide: actualizar nombre
                usuario = await self.usuario_repository.update(
                    usuario.id,
                    nombre=login_data.nombre,
                    ultimo_acceso=datetime.now(timezone.utc)
                )
            else:
                # Nombre coincide: solo actualizar ultimo_acceso
                usuario = await self.usuario_repository.update_ultimo_acceso(usuario.id)

        if usuario is None or usuario.id is None:
            raise ValueError("No se pudo crear o recuperar un usuario válido.")

        # Buscar sesión activa de la mesa (sin importar el usuario)
        sesion_mesa = await self.sesion_mesa_repository.get_active_by_mesa(id_mesa)

        if sesion_mesa is None:
            # No existe sesión activa para esta mesa: crear nueva
            token_sesion = str(ULID())
            sesion_mesa = SesionMesaModel(
                id_mesa=id_mesa,
                id_usuario_creador=usuario.id,
                token_sesion=token_sesion,
                estado=EstadoSesionMesa.ACTIVA,
                duracion_minutos=120  # 2 horas por defecto
            )
            try:
                sesion_mesa = await self.sesion_mesa_repository.create(sesion_mesa)
            except IntegrityError:
                raise ValueError(f"Error al crear sesión de mesa para mesa '{id_mesa}'")

            # Agregar usuario a la sesión
            try:
                await self.sesion_mesa_repository.add_usuario_to_sesion(
                    sesion_mesa.id, usuario.id
                )
            except IntegrityError:
                raise ValueError(f"Error al asociar usuario '{usuario.id}' a sesión")

        else:
            # Existe sesión activa: verificar si está expirada
            if sesion_mesa.esta_expirada():
                # Si está expirada, PRIMERO finalizarla y LUEGO crear una nueva sesión
                try:
                    await self.sesion_mesa_repository.finalizar_sesion(sesion_mesa.id)
                except Exception:
                    pass  # Continuar aunque falle la finalización
                
                token_sesion = str(ULID())
                sesion_mesa = SesionMesaModel(
                    id_mesa=id_mesa,
                    id_usuario_creador=usuario.id,
                    token_sesion=token_sesion,
                    estado=EstadoSesionMesa.ACTIVA,
                    duracion_minutos=120
                )
                try:
                    sesion_mesa = await self.sesion_mesa_repository.create(sesion_mesa)
                except IntegrityError:
                    raise ValueError(f"Error al crear nueva sesión de mesa")

                # Agregar usuario a la nueva sesión
                try:
                    await self.sesion_mesa_repository.add_usuario_to_sesion(
                        sesion_mesa.id, usuario.id
                    )
                except IntegrityError:
                    raise ValueError(f"Error al asociar usuario '{usuario.id}' a nueva sesión")
            else:
                # Sesión activa y válida: verificar si el usuario ya está en ella
                usuario_in_sesion = await self.sesion_mesa_repository.usuario_in_sesion(
                    sesion_mesa.id, usuario.id
                )

                if not usuario_in_sesion:
                    # Usuario NO está en la sesión: agregarlo
                    try:
                        await self.sesion_mesa_repository.add_usuario_to_sesion(
                            sesion_mesa.id, usuario.id
                        )
                    except IntegrityError:
                        raise ValueError(f"Error al asociar usuario '{usuario.id}' a sesión existente")
                # Si el usuario YA está en la sesión, no hacer nada (reutilizar)

        # Calcular fecha de expiración
        fecha_expiracion = sesion_mesa.calcular_fecha_expiracion()

        # Construir respuesta
        return LoginResponse(
            status=200,
            code="SUCCESS",
            id_usuario=usuario.id,
            id_sesion_mesa=sesion_mesa.id,
            token_sesion=sesion_mesa.token_sesion,
            message="Login exitoso",
            fecha_expiracion=fecha_expiracion
        )
