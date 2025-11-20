"""Add simple PK to producto_alergeno

Revision ID: add_simple_pk_pa
Revises: <previous_revision>
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

IMPORTANTE: Reemplazar <previous_revision> con el ID de la última migración antes de ejecutar.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from ulid import ULID


# revision identifiers, used by Alembic.
revision: str = 'add_simple_pk_to_producto_alergeno'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Migración para transformar ProductoAlergenoModel de composite PK a simple PK.

    Pasos:
    1. Agregar columna 'id' con ULIDs generados
    2. Poblar IDs para registros existentes
    3. Remover composite primary key
    4. Agregar nueva primary key en 'id'
    5. Agregar UniqueConstraint en (id_producto, id_alergeno)
    6. Actualizar índices
    """

    # PASO 1: Agregar columna 'id' (nullable temporalmente para poblar datos)
    print("PASO 1: Agregando columna 'id'...")
    op.add_column(
        'productos_alergenos',
        sa.Column('id', sa.String(length=26), nullable=True)
    )

    # PASO 2: Poblar IDs para registros existentes usando Python
    print("PASO 2: Poblando IDs para registros existentes...")
    connection = op.get_bind()

    # Obtener todos los registros actuales
    result = connection.execute(
        sa.text("SELECT id_producto, id_alergeno FROM productos_alergenos")
    )
    records = result.fetchall()

    print(f"   Encontrados {len(records)} registros para poblar...")

    # Asignar ULID a cada registro
    for record in records:
        new_id = str(ULID())
        connection.execute(
            sa.text(
                "UPDATE productos_alergenos "
                "SET id = :new_id "
                "WHERE id_producto = :id_producto AND id_alergeno = :id_alergeno"
            ),
            {
                "new_id": new_id,
                "id_producto": record.id_producto,
                "id_alergeno": record.id_alergeno
            }
        )

    print(f"   {len(records)} registros poblados con IDs")

    # PASO 3: Hacer 'id' NOT NULL y agregar default para futuros inserts
    print("PASO 3: Haciendo 'id' NOT NULL...")
    op.alter_column(
        'productos_alergenos',
        'id',
        nullable=False,
        server_default=None  # El default se manejará en la aplicación
    )

    # PASO 4: Remover composite primary key
    print("PASO 4: Removiendo composite primary key...")
    # El nombre de la constraint puede variar según la BD
    # SQLite: Requiere recrear la tabla
    # PostgreSQL/MySQL: Puede usar ALTER TABLE

    # Para SQLite (recrear tabla completa):
    with op.batch_alter_table('productos_alergenos') as batch_op:
        # Remover índices existentes primero
        batch_op.drop_index('idx_producto', if_exists=True)
        batch_op.drop_index('idx_alergeno', if_exists=True)

        # Remover constraint PK antigua (SQLite lo hace automáticamente al recrear)
        # Para PostgreSQL/MySQL descomentar:
        # batch_op.drop_constraint('pk_productos_alergenos', type_='primary')

        # Agregar nueva PK en 'id'
        batch_op.create_primary_key('pk_productos_alergenos', ['id'])

        # PASO 5: Agregar UniqueConstraint
        print("PASO 5: Agregando UniqueConstraint...")
        batch_op.create_unique_constraint(
            'uq_producto_alergeno',
            ['id_producto', 'id_alergeno']
        )

        # PASO 6: Recrear índices
        print("PASO 6: Recreando índices...")
        batch_op.create_index('idx_producto', ['id_producto'])
        batch_op.create_index('idx_alergeno', ['id_alergeno'])

    print("✅ Migración completada exitosamente!")


def downgrade() -> None:
    """
    Rollback de la migración (revertir a composite PK).

    ADVERTENCIA: Este downgrade es DESTRUCTIVO ya que elimina el campo 'id'.
    Solo debe usarse en caso de emergencia.
    """
    print("⚠️  INICIANDO DOWNGRADE - Esto eliminará el campo 'id'")

    with op.batch_alter_table('productos_alergenos') as batch_op:
        # Remover índices
        batch_op.drop_index('idx_producto', if_exists=True)
        batch_op.drop_index('idx_alergeno', if_exists=True)

        # Remover UniqueConstraint
        batch_op.drop_constraint('uq_producto_alergeno', type_='unique')

        # Remover PK actual
        batch_op.drop_constraint('pk_productos_alergenos', type_='primary')

        # Recrear composite PK
        batch_op.create_primary_key(
            'pk_productos_alergenos',
            ['id_producto', 'id_alergeno']
        )

        # Recrear índices originales
        batch_op.create_index('idx_producto', ['id_producto'])
        batch_op.create_index('idx_alergeno', ['id_alergeno'])

        # Eliminar columna 'id'
        batch_op.drop_column('id')

    print("✅ Downgrade completado - Esquema revertido a composite PK")
