"""Add id_rol to usuarios table

Revision ID: 20251115_add_id_rol_to_usuarios
Revises: 20251111_add_usuario_creador
Create Date: 2025-11-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251115_add_id_rol_to_usuarios'
down_revision = '20251111_add_id_usuario_creador_to_sesiones_mesas'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Agrega columna id_rol a tabla usuarios.

    Cambios:
    - Agregar columna id_rol (nullable para backwards compatibility)
    - Crear FK hacia roles
    - Crear índice para performance
    """
    # 1. Agregar columna id_rol (nullable)
    op.add_column('usuarios',
        sa.Column(
            'id_rol',
            sa.String(length=26),
            nullable=True,
            comment='Rol asignado al usuario (opcional para backwards compatibility)'
        )
    )

    # 2. Crear Foreign Key hacia roles
    op.create_foreign_key(
        'fk_usuarios_rol',
        'usuarios', 'roles',
        ['id_rol'], ['id'],
        ondelete='SET NULL'  # Si se borra el rol, setear a NULL
    )

    # 3. Crear índice para mejorar performance en consultas
    op.create_index(
        'idx_usuarios_rol',
        'usuarios',
        ['id_rol']
    )


def downgrade() -> None:
    """
    Revierte los cambios: elimina columna id_rol.
    """
    # Revertir en orden inverso

    # 1. Eliminar índice
    op.drop_index('idx_usuarios_rol', table_name='usuarios')

    # 2. Eliminar Foreign Key
    op.drop_constraint('fk_usuarios_rol', 'usuarios', type_='foreignkey')

    # 3. Eliminar columna
    op.drop_column('usuarios', 'id_rol')
