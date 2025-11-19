"""
Script de prueba para actualización de imágenes de productos.
Prueba 4 escenarios:
1. Producto SIN imagen -> AGREGAR imagen
2. Producto CON imagen -> CAMBIAR por otra imagen
3. Producto CON imagen -> ELIMINAR imagen (dejar sin imagen)
4. Producto SIN imagen -> AGREGAR imagen -> ELIMINAR imagen (ciclo completo)
"""
import asyncio
from pathlib import Path
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from io import BytesIO

from src.core.config import get_settings
from src.business_logic.menu.producto_service import ProductoService
from src.api.schemas.producto_schema import ProductoUpdate

# Importar main para inicializar todos los modelos de SQLAlchemy
import src.main  # noqa: F401


# Directorio temporal para guardar imágenes de prueba
TEMP_DIR = Path("temp_test_images")


def print_separator(title):
    """Imprime un separador visual con título."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_producto_info(producto):
    """Imprime información resumida de un producto."""
    print(f"  ID: {producto.id}")
    print(f"  Nombre: {producto.nombre}")
    print(f"  Imagen: {producto.imagen_path if producto.imagen_path else '[SIN IMAGEN]'}")


def create_test_image(filename: str, width: int = 800, height: int = 600, color: tuple = (255, 0, 0)) -> Path:
    """Crea una imagen de prueba localmente."""
    TEMP_DIR.mkdir(exist_ok=True)
    file_path = TEMP_DIR / filename

    # Crear una imagen simple usando bytes directos (formato BMP simple)
    # Header BMP de 54 bytes + pixels RGB
    bmp_header = bytearray([
        0x42, 0x4D,  # Signature 'BM'
        0x36, 0x00, 0x0C, 0x00,  # File size (will be updated)
        0x00, 0x00, 0x00, 0x00,  # Reserved
        0x36, 0x00, 0x00, 0x00,  # Offset to pixel data
        0x28, 0x00, 0x00, 0x00,  # DIB header size
        0x00, 0x00, 0x00, 0x00,  # Width (will be updated)
        0x00, 0x00, 0x00, 0x00,  # Height (will be updated)
        0x01, 0x00,  # Planes
        0x18, 0x00,  # Bits per pixel (24)
        0x00, 0x00, 0x00, 0x00,  # Compression (none)
        0x00, 0x00, 0x0C, 0x00,  # Image size
        0x13, 0x0B, 0x00, 0x00,  # X pixels per meter
        0x13, 0x0B, 0x00, 0x00,  # Y pixels per meter
        0x00, 0x00, 0x00, 0x00,  # Colors in palette
        0x00, 0x00, 0x00, 0x00,  # Important colors
    ])

    # Update width and height in header
    bmp_header[18:22] = width.to_bytes(4, 'little')
    bmp_header[22:26] = height.to_bytes(4, 'little')

    # Calculate row size (must be multiple of 4)
    row_size = ((width * 3 + 3) // 4) * 4
    image_size = row_size * height

    # Update file size and image size
    file_size = 54 + image_size
    bmp_header[2:6] = file_size.to_bytes(4, 'little')
    bmp_header[34:38] = image_size.to_bytes(4, 'little')

    # Create pixel data (BGR format for BMP)
    pixel_data = bytearray()
    for y in range(height):
        row = bytearray()
        for x in range(width):
            # BMP stores pixels in BGR order
            row.extend([color[2], color[1], color[0]])
        # Pad row to multiple of 4 bytes
        padding = row_size - len(row)
        row.extend([0] * padding)
        pixel_data.extend(row)

    # Write to file
    with open(file_path, "wb") as f:
        f.write(bmp_header + pixel_data)

    print(f"[OK] Imagen creada: {filename} ({file_size / 1024:.1f} KB)")
    return file_path


async def upload_imagen_producto(producto_service, producto_id: str, image_path: Path) -> dict:
    """Simula la carga de una imagen usando el servicio."""
    # Leer el archivo
    with open(image_path, "rb") as f:
        image_data = f.read()

    # Simular UploadFile
    from io import BytesIO
    from fastapi import UploadFile

    file_obj = BytesIO(image_data)
    file_obj.name = image_path.name

    upload_file = UploadFile(
        filename=image_path.name,
        file=file_obj
    )

    # Usar el controlador directamente
    from pathlib import Path as PathLib
    import aiofiles
    from ulid import ULID
    import os
    from src.core.storage_config import (
        PRODUCTOS_IMAGES_DIR,
        ALLOWED_IMAGE_EXTENSIONS,
        MAX_IMAGE_SIZE
    )

    producto_actual = await producto_service.get_producto_by_id(producto_id)

    file_ext = PathLib(upload_file.filename).suffix.lower()
    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError(f"Tipo de archivo no permitido: {file_ext}")

    contents = await upload_file.read()
    if len(contents) > MAX_IMAGE_SIZE:
        raise ValueError(f"Archivo muy grande: {len(contents)} bytes")

    nuevo_filename = f"{str(ULID())}{file_ext}"
    nuevo_file_path = PRODUCTOS_IMAGES_DIR / nuevo_filename

    async with aiofiles.open(nuevo_file_path, "wb") as f:
        await f.write(contents)

    # Eliminar imagen antigua si existe
    imagen_antigua = producto_actual.imagen_path
    if imagen_antigua and imagen_antigua.startswith("/static/"):
        archivo_antiguo_path = PathLib(imagen_antigua.lstrip("/"))
        if archivo_antiguo_path.exists():
            try:
                os.remove(archivo_antiguo_path)
            except Exception as e:
                print(f"Warning: No se pudo eliminar imagen antigua: {e}")

    nueva_ruta = f"/static/images/productos/{nuevo_filename}"
    await producto_service.repository.update(producto_id, imagen_path=nueva_ruta)

    return {"imagen_path": nueva_ruta, "mensaje": "Imagen actualizada correctamente"}


async def eliminar_imagen_producto(producto_service, producto_id: str):
    """Elimina la imagen de un producto (deja sin imagen)."""
    await producto_service.repository.update(producto_id, imagen_path=None)
    print("[OK] Imagen eliminada del producto")


async def backup_producto_imagen(producto_service, producto_id: str) -> dict:
    """Guarda el estado de la imagen de un producto."""
    producto = await producto_service.get_producto_by_id(producto_id)
    return {
        "imagen_path": producto.imagen_path,
        "tiene_imagen": producto.imagen_path is not None
    }


async def restaurar_producto_imagen(producto_service, producto_id: str, backup: dict):
    """Restaura el estado de la imagen de un producto."""
    await producto_service.repository.update(
        producto_id,
        imagen_path=backup["imagen_path"]
    )
    if backup["tiene_imagen"]:
        print(f"[OK] Imagen restaurada: {backup['imagen_path']}")
    else:
        print("[OK] Producto restaurado sin imagen")


async def test_producto_sin_imagen_agregar(session):
    """Prueba 1: Producto SIN imagen -> AGREGAR imagen."""
    print_separator("PRUEBA 1: Producto sin imagen -> Agregar imagen")

    producto_service = ProductoService(session)

    # Buscar un producto sin imagen
    print("\n1. Buscando producto sin imagen...")
    productos_list = await producto_service.get_productos(skip=0, limit=50)

    producto_sin_imagen = None
    for prod in productos_list.items:
        if not prod.imagen_path:
            producto_sin_imagen = prod
            break

    if not producto_sin_imagen:
        print("[X] No se encontro producto sin imagen. Saltando prueba 1.")
        return False

    print(f"[OK] Producto sin imagen encontrado: {producto_sin_imagen.nombre}")

    # Guardar estado original
    print("\n2. Guardando estado original...")
    estado_original = await backup_producto_imagen(producto_service, producto_sin_imagen.id)
    print_producto_info(producto_sin_imagen)

    # Crear imagen de prueba
    print("\n3. Creando imagen de prueba...")
    imagen_path = create_test_image("test_imagen1.jpg", color=(255, 0, 0))  # Roja

    # Agregar imagen
    print("\n4. Agregando imagen al producto...")
    resultado = await upload_imagen_producto(producto_service, producto_sin_imagen.id, imagen_path)

    # Verificar que se agregó
    producto_actualizado = await producto_service.get_producto_by_id(producto_sin_imagen.id)
    print("[OK] Imagen agregada:")
    print_producto_info(producto_actualizado)

    assert producto_actualizado.imagen_path is not None, "Imagen no se agregó"
    assert producto_actualizado.imagen_path.startswith("/static/images/productos/"), "Ruta incorrecta"
    print("[OK] Imagen agregada correctamente")

    # Restaurar estado original
    print("\n5. Restaurando estado original (sin imagen)...")
    await restaurar_producto_imagen(producto_service, producto_sin_imagen.id, estado_original)

    producto_restaurado = await producto_service.get_producto_by_id(producto_sin_imagen.id)
    print_producto_info(producto_restaurado)

    assert producto_restaurado.imagen_path == estado_original["imagen_path"], "No se restauró correctamente"

    print("\n[OK] PRUEBA 1 COMPLETADA EXITOSAMENTE")
    return True


async def test_producto_con_imagen_cambiar(session):
    """Prueba 2: Producto CON imagen -> CAMBIAR por otra imagen."""
    print_separator("PRUEBA 2: Producto con imagen -> Cambiar imagen")

    producto_service = ProductoService(session)

    # Buscar un producto con imagen
    print("\n1. Buscando producto con imagen...")
    productos_list = await producto_service.get_productos(skip=0, limit=50)

    producto_con_imagen = None
    for prod in productos_list.items:
        if prod.imagen_path:
            producto_con_imagen = prod
            break

    if not producto_con_imagen:
        print("[X] No se encontro producto con imagen. Saltando prueba 2.")
        return False

    print(f"[OK] Producto con imagen encontrado: {producto_con_imagen.nombre}")

    # Guardar estado original
    print("\n2. Guardando estado original...")
    estado_original = await backup_producto_imagen(producto_service, producto_con_imagen.id)
    print_producto_info(producto_con_imagen)

    # Crear nueva imagen de prueba
    print("\n3. Creando nueva imagen de prueba...")
    imagen_path = create_test_image("test_imagen2.png", color=(0, 255, 0))  # Verde

    # Cambiar imagen
    print("\n4. Cambiando imagen del producto...")
    resultado = await upload_imagen_producto(producto_service, producto_con_imagen.id, imagen_path)

    # Verificar que se cambió
    producto_actualizado = await producto_service.get_producto_by_id(producto_con_imagen.id)
    print("[OK] Imagen cambiada:")
    print_producto_info(producto_actualizado)

    assert producto_actualizado.imagen_path != estado_original["imagen_path"], "Imagen no cambió"
    assert producto_actualizado.imagen_path.startswith("/static/images/productos/"), "Ruta incorrecta"
    print("[OK] Imagen cambiada correctamente")

    # Restaurar estado original
    print("\n5. Restaurando imagen original...")
    await restaurar_producto_imagen(producto_service, producto_con_imagen.id, estado_original)

    producto_restaurado = await producto_service.get_producto_by_id(producto_con_imagen.id)
    print_producto_info(producto_restaurado)

    assert producto_restaurado.imagen_path == estado_original["imagen_path"], "No se restauró correctamente"

    print("\n[OK] PRUEBA 2 COMPLETADA EXITOSAMENTE")
    return True


async def test_producto_con_imagen_eliminar(session):
    """Prueba 3: Producto CON imagen -> ELIMINAR imagen."""
    print_separator("PRUEBA 3: Producto con imagen -> Eliminar imagen")

    producto_service = ProductoService(session)

    # Buscar un producto con imagen
    print("\n1. Buscando producto con imagen...")
    productos_list = await producto_service.get_productos(skip=0, limit=50)

    producto_con_imagen = None
    for prod in productos_list.items:
        if prod.imagen_path:
            producto_con_imagen = prod
            break

    if not producto_con_imagen:
        print("[X] No se encontro producto con imagen. Saltando prueba 3.")
        return False

    print(f"[OK] Producto con imagen encontrado: {producto_con_imagen.nombre}")

    # Guardar estado original
    print("\n2. Guardando estado original...")
    estado_original = await backup_producto_imagen(producto_service, producto_con_imagen.id)
    print_producto_info(producto_con_imagen)

    # Eliminar imagen
    print("\n3. Eliminando imagen del producto...")
    await eliminar_imagen_producto(producto_service, producto_con_imagen.id)

    # Verificar que se eliminó
    producto_sin_imagen = await producto_service.get_producto_by_id(producto_con_imagen.id)
    print("[OK] Imagen eliminada:")
    print_producto_info(producto_sin_imagen)

    assert producto_sin_imagen.imagen_path is None, "Imagen no se eliminó"
    print("[OK] Imagen eliminada correctamente")

    # Restaurar estado original
    print("\n4. Restaurando imagen original...")
    await restaurar_producto_imagen(producto_service, producto_con_imagen.id, estado_original)

    producto_restaurado = await producto_service.get_producto_by_id(producto_con_imagen.id)
    print_producto_info(producto_restaurado)

    assert producto_restaurado.imagen_path == estado_original["imagen_path"], "No se restauró correctamente"

    print("\n[OK] PRUEBA 3 COMPLETADA EXITOSAMENTE")
    return True


async def test_ciclo_completo_imagen(session):
    """Prueba 4: Producto SIN imagen -> AGREGAR -> ELIMINAR (ciclo completo)."""
    print_separator("PRUEBA 4: Ciclo completo (Agregar -> Eliminar)")

    producto_service = ProductoService(session)

    # Buscar un producto sin imagen
    print("\n1. Buscando producto sin imagen...")
    productos_list = await producto_service.get_productos(skip=0, limit=50)

    producto_sin_imagen = None
    for prod in productos_list.items:
        if not prod.imagen_path:
            producto_sin_imagen = prod
            break

    if not producto_sin_imagen:
        print("[X] No se encontro producto sin imagen. Saltando prueba 4.")
        return False

    print(f"[OK] Producto sin imagen encontrado: {producto_sin_imagen.nombre}")

    # Guardar estado original
    print("\n2. Guardando estado original (sin imagen)...")
    estado_original = await backup_producto_imagen(producto_service, producto_sin_imagen.id)
    print_producto_info(producto_sin_imagen)
    assert estado_original["tiene_imagen"] == False, "Producto tiene imagen inicial"

    # PASO 1: AGREGAR imagen
    print("\n3. AGREGANDO imagen al producto...")
    imagen_path = create_test_image("test_imagen3.png", color=(0, 0, 255))  # Azul
    resultado = await upload_imagen_producto(producto_service, producto_sin_imagen.id, imagen_path)

    producto_con_imagen = await producto_service.get_producto_by_id(producto_sin_imagen.id)
    print("[OK] Imagen agregada:")
    print_producto_info(producto_con_imagen)
    assert producto_con_imagen.imagen_path is not None, "Imagen no se agregó"

    # PASO 2: ELIMINAR imagen
    print("\n4. ELIMINANDO imagen del producto...")
    await eliminar_imagen_producto(producto_service, producto_sin_imagen.id)

    producto_final = await producto_service.get_producto_by_id(producto_sin_imagen.id)
    print("[OK] Imagen eliminada:")
    print_producto_info(producto_final)
    assert producto_final.imagen_path is None, "Imagen no se eliminó"

    # Verificar estado final
    print("\n5. Verificando estado final...")
    assert producto_final.imagen_path == estado_original["imagen_path"], "Estado final no coincide con original"
    print("[OK] Producto volvió al estado original (sin imagen)")

    print("\n[OK] PRUEBA 4 COMPLETADA EXITOSAMENTE")
    return True


async def cleanup_temp_files():
    """Limpia archivos temporales."""
    if TEMP_DIR.exists():
        for file in TEMP_DIR.iterdir():
            file.unlink()
        TEMP_DIR.rmdir()
        print("[OK] Archivos temporales eliminados")


async def main():
    """Función principal que ejecuta todas las pruebas."""
    print_separator("INICIO DE PRUEBAS - UPDATE IMAGEN PRODUCTO")

    # Crear engine y session
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    resultados = {
        "prueba_1": False,
        "prueba_2": False,
        "prueba_3": False,
        "prueba_4": False
    }

    async with async_session() as session:
        # Ejecutar pruebas
        try:
            resultados["prueba_1"] = await test_producto_sin_imagen_agregar(session)
        except Exception as e:
            print(f"\n[X] ERROR EN PRUEBA 1: {e}")
            import traceback
            traceback.print_exc()

        try:
            resultados["prueba_2"] = await test_producto_con_imagen_cambiar(session)
        except Exception as e:
            print(f"\n[X] ERROR EN PRUEBA 2: {e}")
            import traceback
            traceback.print_exc()

        try:
            resultados["prueba_3"] = await test_producto_con_imagen_eliminar(session)
        except Exception as e:
            print(f"\n[X] ERROR EN PRUEBA 3: {e}")
            import traceback
            traceback.print_exc()

        try:
            resultados["prueba_4"] = await test_ciclo_completo_imagen(session)
        except Exception as e:
            print(f"\n[X] ERROR EN PRUEBA 4: {e}")
            import traceback
            traceback.print_exc()

    await engine.dispose()

    # Limpiar archivos temporales
    await cleanup_temp_files()

    # Resumen final
    print_separator("RESUMEN DE PRUEBAS")
    print(f"\n  Prueba 1 (Sin img -> Agregar):     {'[OK] PASO' if resultados['prueba_1'] else '[X] FALLO'}")
    print(f"  Prueba 2 (Con img -> Cambiar):     {'[OK] PASO' if resultados['prueba_2'] else '[X] FALLO'}")
    print(f"  Prueba 3 (Con img -> Eliminar):    {'[OK] PASO' if resultados['prueba_3'] else '[X] FALLO'}")
    print(f"  Prueba 4 (Ciclo completo):         {'[OK] PASO' if resultados['prueba_4'] else '[X] FALLO'}")

    total_exitosas = sum(resultados.values())
    print(f"\n  Total: {total_exitosas}/4 pruebas exitosas")

    if total_exitosas == 4:
        print("\n[SUCCESS] TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
    else:
        print(f"\n[WARNING] {4 - total_exitosas} prueba(s) no se ejecutaron o fallaron")

    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
