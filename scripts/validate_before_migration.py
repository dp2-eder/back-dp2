"""
Script de pre-validación antes de migrar ProductoAlergenoModel a PK simple.

Este script verifica que:
1. No existan duplicados (misma combinación id_producto + id_alergeno)
2. Todas las relaciones tengan FKs válidas
3. No haya registros huérfanos

Ejecutar con:
    python -m scripts.validate_before_migration
"""

import asyncio
import sys
from pathlib import Path
from typing import Tuple, List

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, func, and_
from src.models.menu.producto_alergeno_model import ProductoAlergenoModel
from src.models.menu.producto_model import ProductoModel
from src.models.menu.alergeno_model import AlergenoModel


def get_database_url() -> str:
    """Obtiene la URL de la base de datos."""
    import os
    from dotenv import load_dotenv
    load_dotenv()

    database_url = os.getenv("DATABASE_URL")
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return database_url

    # SQLite por defecto
    return "sqlite+aiosqlite:///./instance/restaurante.db"


class MigrationValidator:
    """Validador de pre-condiciones para migración."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.errors: List[str] = []
        self.warnings: List[str] = []

    async def validate_no_duplicates(self) -> bool:
        """
        Verifica que no existan duplicados (misma combinación id_producto + id_alergeno).

        Returns:
            True si no hay duplicados, False si hay.
        """
        print("\n1️⃣  VALIDANDO: No existen duplicados...")

        query = (
            select(
                ProductoAlergenoModel.id_producto,
                ProductoAlergenoModel.id_alergeno,
                func.count().label('count')
            )
            .group_by(
                ProductoAlergenoModel.id_producto,
                ProductoAlergenoModel.id_alergeno
            )
            .having(func.count() > 1)
        )

        result = await self.session.execute(query)
        duplicates = result.all()

        if duplicates:
            self.errors.append(f"   DUPLICADOS ENCONTRADOS: {len(duplicates)} combinaciones")
            for dup in duplicates:
                self.errors.append(
                    f"      - Producto: {dup.id_producto}, "
                    f"Alergeno: {dup.id_alergeno}, "
                    f"Count: {dup.count}"
                )
            print(f"   ❌ FALLO: {len(duplicates)} duplicados encontrados")
            return False

        print("   ✅ OK: No hay duplicados")
        return True

    async def validate_foreign_keys(self) -> bool:
        """
        Verifica que todas las relaciones tengan FKs válidas.

        Returns:
            True si todas las FKs son válidas, False si hay registros huérfanos.
        """
        print("\n2️⃣  VALIDANDO: FKs válidas...")

        # Verificar productos huérfanos
        query_productos_huerfanos = (
            select(ProductoAlergenoModel)
            .outerjoin(ProductoModel, ProductoAlergenoModel.id_producto == ProductoModel.id)
            .where(ProductoModel.id.is_(None))
        )

        result = await self.session.execute(query_productos_huerfanos)
        huerfanos_productos = result.scalars().all()

        if huerfanos_productos:
            self.errors.append(
                f"   PRODUCTOS HUÉRFANOS: {len(huerfanos_productos)} registros"
            )
            for record in huerfanos_productos[:5]:  # Mostrar solo primeros 5
                self.errors.append(
                    f"      - id_producto: {record.id_producto}, "
                    f"id_alergeno: {record.id_alergeno}"
                )
            print(f"   ❌ FALLO: {len(huerfanos_productos)} productos huérfanos")
            return False

        # Verificar alergenos huérfanos
        query_alergenos_huerfanos = (
            select(ProductoAlergenoModel)
            .outerjoin(AlergenoModel, ProductoAlergenoModel.id_alergeno == AlergenoModel.id)
            .where(AlergenoModel.id.is_(None))
        )

        result = await self.session.execute(query_alergenos_huerfanos)
        huerfanos_alergenos = result.scalars().all()

        if huerfanos_alergenos:
            self.errors.append(
                f"   ALERGENOS HUÉRFANOS: {len(huerfanos_alergenos)} registros"
            )
            for record in huerfanos_alergenos[:5]:
                self.errors.append(
                    f"      - id_producto: {record.id_producto}, "
                    f"id_alergeno: {record.id_alergeno}"
                )
            print(f"   ❌ FALLO: {len(huerfanos_alergenos)} alergenos huérfanos")
            return False

        print("   ✅ OK: Todas las FKs son válidas")
        return True

    async def count_records(self) -> Tuple[int, int, int]:
        """
        Cuenta registros en las tablas relacionadas.

        Returns:
            Tupla (count_productos, count_alergenos, count_relaciones)
        """
        print("\n3️⃣  CONTANDO REGISTROS...")

        # Contar productos
        result = await self.session.execute(select(func.count(ProductoModel.id)))
        count_productos = result.scalar()

        # Contar alergenos
        result = await self.session.execute(select(func.count(AlergenoModel.id)))
        count_alergenos = result.scalar()

        # Contar relaciones
        result = await self.session.execute(select(func.count()).select_from(ProductoAlergenoModel))
        count_relaciones = result.scalar()

        print(f"   📊 Productos: {count_productos}")
        print(f"   📊 Alergenos: {count_alergenos}")
        print(f"   📊 Relaciones producto-alergeno: {count_relaciones}")

        if count_relaciones == 0:
            self.warnings.append("   ⚠️  No hay relaciones producto-alergeno en la BD")

        return count_productos, count_alergenos, count_relaciones

    async def validate_all(self) -> bool:
        """
        Ejecuta todas las validaciones.

        Returns:
            True si todas las validaciones pasan, False si hay errores.
        """
        print("\n" + "="*70)
        print(" PRE-VALIDACIÓN DE MIGRACIÓN: ProductoAlergenoModel → PK Simple")
        print("="*70)

        # Contar registros
        await self.count_records()

        # Validar duplicados
        no_duplicates = await self.validate_no_duplicates()

        # Validar FKs
        valid_fks = await self.validate_foreign_keys()

        # Resumen
        print("\n" + "="*70)
        print(" RESUMEN DE VALIDACIÓN")
        print("="*70)

        if self.errors:
            print(f"\n❌ ERRORES ENCONTRADOS ({len(self.errors)}):")
            for error in self.errors:
                print(error)

        if self.warnings:
            print(f"\n⚠️  ADVERTENCIAS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(warning)

        all_valid = no_duplicates and valid_fks

        if all_valid:
            print("\n✅ TODAS LAS VALIDACIONES PASARON")
            print("   Es SEGURO ejecutar la migración Alembic")
        else:
            print("\n❌ VALIDACIÓN FALLIDA")
            print("   NO ejecutar la migración hasta resolver los errores")

        print("="*70 + "\n")

        return all_valid


async def main():
    """Función principal."""
    database_url = get_database_url()

    print("\n" + "="*70)
    print(" CONFIGURACIÓN DE BASE DE DATOS")
    print("="*70)
    print(f"   URL: {database_url}")
    print("="*70)

    # Crear engine y sesión
    engine = create_async_engine(database_url, echo=False)
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session_maker() as session:
        validator = MigrationValidator(session)
        is_valid = await validator.validate_all()

    await engine.dispose()

    # Exit code: 0 si válido, 1 si hay errores
    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    asyncio.run(main())
