"""
Security configuration for authentication and authorization.
"""

import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt

from src.core.config import get_settings

class SecurityConfig:
    """Security configuration class."""

    def __init__(self):
        self.settings = get_settings()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash using native bcrypt.

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password (bcrypt hash string)

        Returns:
            True if password matches, False otherwise
        """
        # bcrypt requiere bytes, convertimos si vienen como str
        if isinstance(plain_password, str):
            plain_bytes = plain_password.encode('utf-8')
        else:
            plain_bytes = plain_password

        if isinstance(hashed_password, str):
            hash_bytes = hashed_password.encode('utf-8')
        else:
            hash_bytes = hashed_password

        try:
            # checkpw extrae la sal del hash_bytes automáticamente y verifica
            return bcrypt.checkpw(plain_bytes, hash_bytes)
        except ValueError:
            # En caso de formato de hash inválido
            return False

    def get_password_hash(self, password: str) -> str:
        """
        Hash a password using native bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password as string (ready for DB storage)
        """
        if isinstance(password, str):
            pwd_bytes = password.encode('utf-8')
        else:
            pwd_bytes = password

        # Generar sal y hashear
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pwd_bytes, salt)

        # Retornar como string para almacenar en la BD (VARCHAR)
        return hashed.decode('utf-8')

    def create_access_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token.

        Args:
            data: Data to encode in token
            expires_delta: Token expiration time

        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.settings.access_token_expire_minutes
            )

        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(
            to_encode,
            self.settings.secret_key,
            algorithm=self.settings.algorithm
        )
        return encoded_jwt

    def create_refresh_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT refresh token.

        Args:
            data: Data to encode in token
            expires_delta: Token expiration time

        Returns:
            Encoded JWT refresh token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                days=self.settings.refresh_token_expire_days
            )

        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(
            to_encode,
            self.settings.secret_key,
            algorithm=self.settings.algorithm
        )
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[dict]:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token to verify

        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.secret_key,
                algorithms=[self.settings.algorithm]
            )
            return payload
        except JWTError:
            return None

    def extract_user_id_from_token(self, token: str) -> Optional[str]:
        """
        Extract user ID from JWT token.

        Args:
            token: JWT token

        Returns:
            User ID (ULID string) or None if not found
        """
        payload = self.verify_token(token)
        if payload:
            # Convertimos a string por seguridad, ya que ULID es string
            return str(payload.get("sub")) if payload.get("sub") else None
        return None


# Global security instance
security = SecurityConfig()
