"""create usuarios_sesiones_mesas table and update sesiones_mesas

Revision ID: 20251110_usuarios_sesiones
Revises: add_simple_pk_to_producto_alergeno
Create Date: 2025-11-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '20251110_usuarios_sesiones'
down_revision: Union[str, None] = 'add_simple_pk_to_producto_alergeno'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Crea la tabla intermedia usuarios_sesiones_mesas y migra datos existentes.
    """
    # 1. Crear tabla intermedia usuarios_sesiones_mesas
    op.create_table(
        'usuarios_sesiones_mesas',
        sa.Column('id', sa.String(length=26), nullable=False),
        sa.Column('id_usuario', sa.String(length=36), nullable=False),
        sa.Column('id_sesion_mesa', sa.String(length=36), nullable=False),
        sa.Column('fecha_ingreso', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('fecha_creacion', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('fecha_modificacion', sa.TIMESTAMP(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.Column('creado_por', sa.String(length=36), nullable=True),
        sa.Column('modificado_por', sa.String(length=36), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['id_usuario'], ['usuarios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['id_sesion_mesa'], ['sesiones_mesas.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('id_usuario', 'id_sesion_mesa', name='uq_usuario_sesion_mesa'),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )

    # 2. Crear índices para la nueva tabla
    op.create_index('idx_usuario_sesion_mesa_usuario', 'usuarios_sesiones_mesas', ['id_usuario'])
    op.create_index('idx_usuario_sesion_mesa_sesion', 'usuarios_sesiones_mesas', ['id_sesion_mesa'])

    # 3. Migrar datos existentes de sesiones_mesas a usuarios_sesiones_mesas
    # Solo si hay datos existentes, crear asociaciones
    op.execute("""
        INSERT INTO usuarios_sesiones_mesas (id, id_usuario, id_sesion_mesa, fecha_ingreso, fecha_creacion)
        SELECT
            CONCAT('01', LPAD(CONV(FLOOR(RAND() * 999999999999), 10, 36), 24, '0')) as id,
            id_usuario,
            id as id_sesion_mesa,
            fecha_inicio as fecha_ingreso,
            fecha_creacion
        FROM sesiones_mesas
        WHERE id_usuario IS NOT NULL
    """)

    # 4. Eliminar índice antiguo que incluía id_usuario
    op.drop_index('idx_sesion_mesa_usuario_mesa', table_name='sesiones_mesas')

    # 5. Eliminar Foreign Key de id_usuario en sesiones_mesas
    # Nota: El nombre de la FK puede variar, ajustar según tu base de datos
    op.drop_constraint('sesiones_mesas_ibfk_1', 'sesiones_mesas', type_='foreignkey')

    # 6. Eliminar columna id_usuario de sesiones_mesas
    op.drop_column('sesiones_mesas', 'id_usuario')

    # 7. Crear nuevo índice solo para id_mesa
    op.create_index('idx_sesion_mesa_mesa', 'sesiones_mesas', ['id_mesa'])


def downgrade() -> None:
    """
    Revierte los cambios: restaura id_usuario en sesiones_mesas y elimina tabla intermedia.
    """
    # 1. Eliminar índice de id_mesa
    op.drop_index('idx_sesion_mesa_mesa', table_name='sesiones_mesas')

    # 2. Agregar columna id_usuario nuevamente a sesiones_mesas
    op.add_column('sesiones_mesas',
        sa.Column('id_usuario', sa.String(length=36), nullable=True)
    )

    # 3. Restaurar datos desde usuarios_sesiones_mesas (tomar el primer usuario de cada sesión)
    op.execute("""
        UPDATE sesiones_mesas sm
        INNER JOIN (
            SELECT id_sesion_mesa, MIN(id_usuario) as id_usuario
            FROM usuarios_sesiones_mesas
            GROUP BY id_sesion_mesa
        ) usm ON sm.id = usm.id_sesion_mesa
        SET sm.id_usuario = usm.id_usuario
    """)

    # 4. Hacer la columna NOT NULL después de restaurar datos
    op.alter_column('sesiones_mesas', 'id_usuario', nullable=False)

    # 5. Recrear Foreign Key
    op.create_foreign_key(
        'sesiones_mesas_ibfk_1',
        'sesiones_mesas', 'usuarios',
        ['id_usuario'], ['id'],
        ondelete='RESTRICT'
    )

    # 6. Recrear índice antiguo
    op.create_index('idx_sesion_mesa_usuario_mesa', 'sesiones_mesas', ['id_usuario', 'id_mesa'])

    # 7. Eliminar índices de la tabla intermedia
    op.drop_index('idx_usuario_sesion_mesa_sesion', table_name='usuarios_sesiones_mesas')
    op.drop_index('idx_usuario_sesion_mesa_usuario', table_name='usuarios_sesiones_mesas')

    # 8. Eliminar tabla intermedia
    op.drop_table('usuarios_sesiones_mesas')
