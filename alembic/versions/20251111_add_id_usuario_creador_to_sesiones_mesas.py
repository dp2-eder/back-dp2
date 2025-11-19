"""Add id_usuario_creador to sesiones_mesas

Revision ID: 20251111_add_usuario_creador
Revises: 20251110_add_id_sesion_mesa_to_pedidos
Create Date: 2025-11-11 07:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251111_add_usuario_creador'
down_revision = '20251110_add_id_sesion_mesa_to_pedidos'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Agrega el campo id_usuario_creador a la tabla sesiones_mesas.

    Este campo identifica al usuario que creó la sesión de mesa,
    lo cual es necesario para asociar pedidos al usuario correcto
    cuando se crea un pedido mediante token de sesión.
    """
    # Agregar columna (nullable=True temporalmente para datos existentes)
    op.add_column('sesiones_mesas',
        sa.Column(
            'id_usuario_creador',
            sa.String(length=36),
            nullable=True,  # Temporalmente nullable para datos existentes
            comment='Usuario que creó la sesión de mesa'
        )
    )

    # Poblar el campo para sesiones existentes usando el primer usuario de la tabla intermedia
    # Esto solo es necesario si hay datos existentes en la base de datos
    op.execute("""
        UPDATE sesiones_mesas sm
        SET id_usuario_creador = (
            SELECT usm.id_usuario
            FROM usuarios_sesiones_mesas usm
            WHERE usm.id_sesion_mesa = sm.id
            ORDER BY usm.fecha_ingreso ASC
            LIMIT 1
        )
        WHERE sm.id_usuario_creador IS NULL
          AND EXISTS (
              SELECT 1
              FROM usuarios_sesiones_mesas usm2
              WHERE usm2.id_sesion_mesa = sm.id
          )
    """)

    # Crear foreign key
    op.create_foreign_key(
        'fk_sesiones_mesas_usuario_creador',
        'sesiones_mesas', 'usuarios',
        ['id_usuario_creador'], ['id'],
        ondelete='RESTRICT'
    )

    # Crear índice para mejorar rendimiento de búsquedas
    op.create_index(
        'idx_sesiones_mesas_usuario_creador',
        'sesiones_mesas',
        ['id_usuario_creador']
    )

    # Hacer NOT NULL después de poblar datos
    # NOTA: En SQLite esto requiere recrear la tabla, así que lo dejamos nullable
    # En producción con PostgreSQL/MySQL se puede hacer:
    # op.alter_column('sesiones_mesas', 'id_usuario_creador', nullable=False)


def downgrade() -> None:
    """
    Elimina el campo id_usuario_creador de la tabla sesiones_mesas.
    """
    op.drop_index('idx_sesiones_mesas_usuario_creador', table_name='sesiones_mesas')
    op.drop_constraint('fk_sesiones_mesas_usuario_creador', 'sesiones_mesas', type_='foreignkey')
    op.drop_column('sesiones_mesas', 'id_usuario_creador')
