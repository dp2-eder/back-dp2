from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_database_session
from src.core.security import security
from src.business_logic.auth.admin_service import AdminService

security_scheme = HTTPBearer()

async def get_current_admin(
    auth: HTTPAuthorizationCredentials = Depends(security_scheme),
    session: AsyncSession = Depends(get_database_session)
):
    """
    Dependencia para validar el token JWT y verificar que el admin existe.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = auth.credentials

    payload = security.verify_token(token)
    if payload is None:
        raise credentials_exception

    admin_id: str = payload.get("sub")
    if admin_id is None:
        raise credentials_exception

    try:
        admin_service = AdminService(session)
        admin = await admin_service.get_admin_by_id(admin_id)

        if admin is None:
            raise credentials_exception

        return admin

    except Exception:
        raise credentials_exception
