"""add id_sesion_mesa to pedidos

Revision ID: 20251110_sesion_pedidos
Revises: 20251110_usuarios_sesiones
Create Date: 2025-11-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20251110_add_id_sesion_mesa_to_pedidos'
down_revision: Union[str, None] = '20251110_usuarios_sesiones'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Agrega columna id_sesion_mesa a tabla pedidos.

    Cambios:
    - Agregar columna id_sesion_mesa (nullable para backwards compatibility)
    - Crear FK hacia sesiones_mesas
    - Crear índice para performance
    """
    # 1. Agregar columna id_sesion_mesa (nullable)
    op.add_column('pedidos',
        sa.Column(
            'id_sesion_mesa',
            sa.String(length=36),
            nullable=True,
            comment='Sesión de mesa a la que pertenece este pedido (opcional para backwards compatibility)'
        )
    )

    # 2. Crear Foreign Key hacia sesiones_mesas
    op.create_foreign_key(
        'fk_pedidos_sesion_mesa',
        'pedidos', 'sesiones_mesas',
        ['id_sesion_mesa'], ['id'],
        ondelete='RESTRICT'  # No borrar pedidos si se borra sesión
    )

    # 3. Crear índice para mejorar performance en consultas
    op.create_index(
        'idx_pedidos_sesion_mesa',
        'pedidos',
        ['id_sesion_mesa']
    )


def downgrade() -> None:
    """
    Revierte los cambios: elimina columna id_sesion_mesa.
    """
    # Revertir en orden inverso

    # 1. Eliminar índice
    op.drop_index('idx_pedidos_sesion_mesa', table_name='pedidos')

    # 2. Eliminar Foreign Key
    op.drop_constraint('fk_pedidos_sesion_mesa', 'pedidos', type_='foreignkey')

    # 3. Eliminar columna
    op.drop_column('pedidos', 'id_sesion_mesa')
