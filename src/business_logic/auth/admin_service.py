from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.repositories.auth.admin_repository import AdminRepository
from src.models.auth.admin_model import AdminModel
from src.core.security import security
from src.api.schemas.admin_schema import (
    AdminCreate,
    AdminResponse,
)
from src.business_logic.exceptions.admin_exceptions import (
    AdminNotFoundError,
    AdminConflictError,
)
from fastapi import HTTPException, status
from src.api.schemas.admin_schema import AdminLoginRequest, TokenResponse


class AdminService:
    """Servicio para la gestión de administradores en el sistema.

    Esta clase implementa la lógica de negocio para operaciones relacionadas
    con administradores, incluyendo seguridad (hashing) y manejo de excepciones.

    Attributes
    ----------
    repository : AdminRepository
        Repositorio para acceso a datos de administradores.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio con una sesión de base de datos.

        Parameters
        ----------
        session : AsyncSession
            Sesión asíncrona de SQLAlchemy para realizar operaciones en la base de datos.
        """
        self.repository = AdminRepository(session)

    async def create_admin(self, admin_data: AdminCreate) -> AdminResponse:
        """
        Crea un nuevo administrador en el sistema asegurando el hashing de contraseña.

        Parameters
        ----------
        admin_data : AdminCreate
            Datos para crear el nuevo administrador (incluye password en texto plano).

        Returns
        -------
        AdminResponse
            Esquema de respuesta con los datos del administrador creado (sin password).

        Raises
        ------
        AdminConflictError
            Si ya existe un administrador con el mismo email o usuario.
        """
        try:
            # 1. Hashear la contraseña antes de guardar
            hashed_password = security.get_password_hash(admin_data.password)

            # 2. Crear instancia del modelo
            admin = AdminModel(
                usuario=admin_data.usuario,
                email=admin_data.email,
                password=hashed_password
            )

            # 3. Persistir en la base de datos
            created_admin = await self.repository.create(admin)

            # 4. Convertir y retornar
            return AdminResponse.model_validate(created_admin)

        except IntegrityError:
            # Capturar errores de integridad (email o usuario duplicados)
            raise AdminConflictError(
                f"Ya existe un administrador con el email '{admin_data.email}' o usuario '{admin_data.usuario}'"
            )
        except Exception as e:
            print(f"{e}")

    async def get_admin_by_email(self, email: str) -> AdminResponse:
        """
        Obtiene un administrador por su email.

        Parameters
        ----------
        email : str
            Correo electrónico del administrador.

        Returns
        -------
        AdminResponse
            Esquema de respuesta con los datos del administrador.

        Raises
        ------
        AdminNotFoundError
            Si no se encuentra el administrador.
        """
        admin = await self.repository.get_by_email(email)

        if not admin:
            raise AdminNotFoundError(f"No se encontró el administrador con email {email}")

        return AdminResponse.model_validate(admin)

    async def get_admin_by_id(self, admin_id: str) -> AdminResponse:
        """
        Obtiene un administrador por ID

        Parameters
        ----------
        admin_id : str
            Id del administrador.

        Returns
        ------
        AdminResponse
            Esquema de respuesta con los datos del administrador.

        Raises
        ------
        AdminNotFoundError
            Si no se encuentra el administrador.
        """
        admin = await self.repository.get_by_id(admin_id)

        if not admin:
            raise AdminNotFoundError("No se encontró el administrador")

        return AdminResponse.model_validate(admin)

    async def update_last_login(self, admin_id: str) -> None:
        """
        Actualiza la fecha de último acceso del administrador.
        Este método suele llamarse después de un login exitoso.

        Parameters
        ----------
        admin_id : str
            Identificador del administrador.
        """
        await self.repository.update_ultimo_acceso(admin_id)

    async def login(self, login_data: AdminLoginRequest) -> TokenResponse:
        """
        Autentica a un administrador y genera un token JWT.
        Permite ingresar con 'usuario' o 'email'.

        Parameters
        ----------
        login_data : AdminLoginRequest
            Credenciales (email + password).

        Returns
        -------
        TokenResponse
            Token de acceso y datos básicos.

        Raises
        ------
        HTTPException
            401 si las credenciales son inválidas.
        """
        # 1. Buscar administrador (primero por email, si no, por usuario)
        admin = await self.repository.get_by_email(login_data.email)

        # 2. Verificar existencia y contraseña
        if not admin or not security.verify_password(login_data.password, admin.password):
            # Usamos un error genérico para no revelar si existe el usuario o no
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 3. Actualizar auditoría (último acceso)
        await self.update_last_login(admin.id)

        # 4. Generar Token JWT
        # Incluimos el ID en el 'sub' y un claim extra 'role'
        access_token = security.create_access_token(
            data={"sub": admin.id, "type": "admin", "usuario": admin.usuario}
        )

        # 5. Retornar respuesta
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            admin_id=admin.id,
            usuario=admin.usuario
        )
