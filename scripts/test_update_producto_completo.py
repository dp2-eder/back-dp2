"""
Script de prueba para actualización completa de productos.
Prueba 3 tipos de productos:
1. Producto simple (sin opciones, sin alérgenos)
2. Producto con alérgenos O con opciones
3. Producto completo (con alérgenos Y con opciones)
"""
import asyncio
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.core.config import get_settings
from src.business_logic.menu.producto_service import ProductoService
from src.api.schemas.producto_schema import ProductoCompletoUpdateSchema
from src.api.schemas.producto_alergeno_schema import ProductoAlergenoUpdateInput
from src.core.enums.alergeno_enums import NivelPresencia
from src.business_logic.menu.producto_alergeno_service import ProductoAlergenoService

# Importar main para inicializar todos los modelos de SQLAlchemy
import src.main  # noqa: F401


def print_separator(title):
    """Imprime un separador visual con título."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_producto_info(producto, alergenos_count=0, opciones_count=0):
    """Imprime información resumida de un producto."""
    print(f"  ID: {producto.id}")
    print(f"  Nombre: {producto.nombre}")
    print(f"  Precio: {producto.precio_base}")
    print(f"  Disponible: {producto.disponible}")
    if hasattr(producto, 'destacado'):
        print(f"  Destacado: {producto.destacado}")
    print(f"  Alergenos: {alergenos_count}")
    print(f"  Opciones: {opciones_count}")


async def backup_producto_state(producto_service, alergeno_service, producto_id):
    """Guarda el estado actual de un producto."""
    producto = await producto_service.get_producto_by_id(producto_id)

    # Intentar obtener producto con opciones
    tipos_opciones_backup = []
    try:
        producto_completo = await producto_service.get_producto_con_opciones(producto_id)
        # Convertir los tipos_opciones a formato que pueda ser usado en restore
        from src.api.schemas.producto_schema import TipoOpcionCompletoSchema, ProductoOpcionCompletoSchema

        for tipo in producto_completo.tipos_opciones:
            opciones_backup = []
            for opcion in tipo.opciones:
                opciones_backup.append(ProductoOpcionCompletoSchema(
                    id_opcion=opcion.id,  # Guardar el ID para poder restaurar
                    nombre=opcion.nombre,
                    precio_adicional=opcion.precio_adicional,
                    activo=opcion.activo,
                    orden=opcion.orden
                ))

            tipos_opciones_backup.append(TipoOpcionCompletoSchema(
                id_tipo_opcion=tipo.id_tipo_opcion,
                nombre=tipo.nombre_tipo,
                descripcion=tipo.descripcion_tipo,
                seleccion_minima=tipo.seleccion_minima,
                seleccion_maxima=tipo.seleccion_maxima,
                orden=tipo.orden_tipo,
                opciones=opciones_backup
            ))
    except:
        tipos_opciones_backup = []

    # Obtener alérgenos
    alergenos = await alergeno_service.get_alergenos_by_producto(producto_id)

    return {
        "nombre": producto.nombre,
        "descripcion": producto.descripcion,
        "precio_base": producto.precio_base,
        "imagen_path": producto.imagen_path,
        "imagen_alt_text": producto.imagen_alt_text,
        "id_categoria": producto.id_categoria,
        "disponible": producto.disponible,
        "destacado": producto.destacado,
        "tipos_opciones": tipos_opciones_backup,
        "alergenos": alergenos
    }


async def test_producto_simple(session):
    """Prueba con producto simple (sin opciones, sin alérgenos)."""
    print_separator("PRUEBA 1: Producto Simple (sin opciones, sin alérgenos)")

    producto_service = ProductoService(session)
    alergeno_service = ProductoAlergenoService(session)

    # Buscar un producto simple
    print("\n1. Buscando producto simple...")
    productos_list = await producto_service.get_productos(skip=0, limit=50)

    producto_simple = None
    for prod in productos_list.items:
        # Obtener alérgenos
        alergenos = await alergeno_service.get_alergenos_by_producto(prod.id)

        # Verificar si tiene opciones
        try:
            prod_completo = await producto_service.get_producto_con_opciones(prod.id)
            tiene_opciones = len(prod_completo.tipos_opciones) > 0
        except:
            tiene_opciones = False

        if len(alergenos) == 0 and not tiene_opciones:
            producto_simple = prod
            break

    if not producto_simple:
        print("[X] No se encontro producto simple. Saltando prueba 1.")
        return False

    print(f"[OK] Producto simple encontrado: {producto_simple.nombre}")

    # Guardar estado original
    print("\n2. Guardando estado original...")
    estado_original = await backup_producto_state(producto_service, alergeno_service, producto_simple.id)
    print_producto_info(producto_simple, 0, 0)

    # Modificar producto
    print("\n3. Modificando producto...")
    update_data = ProductoCompletoUpdateSchema(
        nombre=f"{estado_original['nombre']} [MODIFICADO]",
        descripcion="DESCRIPCIÓN MODIFICADA POR TEST",
        precio_base=Decimal("999.99"),
        imagen_path=estado_original['imagen_path'],
        imagen_alt_text="Imagen modificada",
        id_categoria=estado_original['id_categoria'],
        disponible=False,  # Cambiar disponibilidad
        destacado=True,    # Cambiar destacado
        alergenos=[],
        secciones=[],
        tipos_opciones=[]
    )

    producto_modificado = await producto_service.update_producto_completo(
        producto_simple.id,
        update_data
    )

    print("[OK] Producto modificado:")
    print_producto_info(producto_modificado, 0, 0)

    # Verificar cambios
    print("\n4. Verificando cambios...")
    assert producto_modificado.nombre.endswith("[modificado]"), "Nombre no se modifico"
    assert producto_modificado.precio_base == Decimal("999.99"), "Precio no se modificó"
    assert producto_modificado.disponible == False, "Disponibilidad no se modificó"
    assert producto_modificado.destacado == True, "Destacado no se modificó"
    print("[OK] Todos los cambios verificados correctamente")

    # Restaurar estado original
    print("\n5. Restaurando estado original...")
    restore_data = ProductoCompletoUpdateSchema(
        nombre=estado_original['nombre'],
        descripcion=estado_original['descripcion'],
        precio_base=estado_original['precio_base'],
        imagen_path=estado_original['imagen_path'],
        imagen_alt_text=estado_original['imagen_alt_text'],
        id_categoria=estado_original['id_categoria'],
        disponible=estado_original['disponible'],
        destacado=estado_original['destacado'],
        alergenos=[],
        secciones=[],
        tipos_opciones=[]
    )

    producto_restaurado = await producto_service.update_producto_completo(
        producto_simple.id,
        restore_data
    )

    print("[OK] Producto restaurado:")
    print_producto_info(producto_restaurado, 0, 0)

    print("\n[OK] PRUEBA 1 COMPLETADA EXITOSAMENTE")
    return True


async def test_producto_parcial(session):
    """Prueba con producto que tiene alérgenos O opciones."""
    print_separator("PRUEBA 2: Producto Parcial (con alérgenos O con opciones)")

    producto_service = ProductoService(session)
    alergeno_service = ProductoAlergenoService(session)

    # Buscar un producto parcial
    print("\n1. Buscando producto parcial...")
    productos_list = await producto_service.get_productos(skip=0, limit=50)

    producto_parcial = None
    alergenos_count = 0
    opciones_count = 0

    for prod in productos_list.items:
        alergenos = await alergeno_service.get_alergenos_by_producto(prod.id)

        try:
            prod_completo = await producto_service.get_producto_con_opciones(prod.id)
            opciones = sum(len(tipo.opciones) for tipo in prod_completo.tipos_opciones)
        except:
            opciones = 0

        # Tiene alérgenos PERO NO opciones, O tiene opciones PERO NO alérgenos
        if (len(alergenos) > 0 and opciones == 0) or (len(alergenos) == 0 and opciones > 0):
            producto_parcial = prod
            alergenos_count = len(alergenos)
            opciones_count = opciones
            break

    if not producto_parcial:
        print("[X] No se encontro producto parcial. Saltando prueba 2.")
        return False

    print(f"[OK] Producto parcial encontrado: {producto_parcial.nombre}")

    # Guardar estado original
    print("\n2. Guardando estado original...")
    estado_original = await backup_producto_state(producto_service, alergeno_service, producto_parcial.id)
    print_producto_info(producto_parcial, alergenos_count, opciones_count)

    # Modificar producto
    print("\n3. Modificando producto...")

    # Preparar alérgenos modificados (desactivar algunos)
    alergenos_modificados = []
    if alergenos_count > 0:
        alergenos_originales = estado_original['alergenos']
        # Mantener solo la mitad de alérgenos
        for alergeno in alergenos_originales[:len(alergenos_originales)//2 or 1]:
            alergenos_modificados.append(
                ProductoAlergenoUpdateInput(
                    id_alergeno=alergeno.id,
                    nivel_presencia=NivelPresencia.TRAZAS,  # Cambiar nivel
                    notas="MODIFICADO POR TEST"
                )
            )

    update_data = ProductoCompletoUpdateSchema(
        nombre=f"{estado_original['nombre']} [MOD]",
        descripcion="Descripción modificada en prueba 2",
        precio_base=Decimal("777.77"),
        imagen_path=estado_original['imagen_path'],
        imagen_alt_text=estado_original['imagen_alt_text'],
        id_categoria=estado_original['id_categoria'],
        disponible=not estado_original['disponible'],  # Invertir
        destacado=not estado_original['destacado'],    # Invertir
        alergenos=alergenos_modificados,
        secciones=[],
        tipos_opciones=[]  # Por ahora sin modificar opciones
    )

    producto_modificado = await producto_service.update_producto_completo(
        producto_parcial.id,
        update_data
    )

    alergenos_mod = await alergeno_service.get_alergenos_by_producto(producto_parcial.id)
    print("[OK] Producto modificado:")
    print_producto_info(producto_modificado, len(alergenos_mod), opciones_count)

    # Verificar cambios
    print("\n4. Verificando cambios...")
    assert producto_modificado.precio_base == Decimal("777.77"), "Precio no se modificó"
    print("[OK] Cambios verificados")

    # Restaurar estado original
    print("\n5. Restaurando estado original...")

    # Restaurar alérgenos
    alergenos_restaurar = []
    if alergenos_count > 0:
        for alergeno in estado_original['alergenos']:
            alergenos_restaurar.append(
                ProductoAlergenoUpdateInput(
                    id_alergeno=alergeno.id,
                    nivel_presencia=NivelPresencia.CONTIENE,
                    notas=""
                )
            )

    restore_data = ProductoCompletoUpdateSchema(
        nombre=estado_original['nombre'],
        descripcion=estado_original['descripcion'],
        precio_base=estado_original['precio_base'],
        imagen_path=estado_original['imagen_path'],
        imagen_alt_text=estado_original['imagen_alt_text'],
        id_categoria=estado_original['id_categoria'],
        disponible=estado_original['disponible'],
        destacado=estado_original['destacado'],
        alergenos=alergenos_restaurar,
        secciones=[],
        tipos_opciones=[]
    )

    producto_restaurado = await producto_service.update_producto_completo(
        producto_parcial.id,
        restore_data
    )

    alergenos_rest = await alergeno_service.get_alergenos_by_producto(producto_parcial.id)
    print("[OK] Producto restaurado:")
    print_producto_info(producto_restaurado, len(alergenos_rest), opciones_count)

    print("\n[OK] PRUEBA 2 COMPLETADA EXITOSAMENTE")
    return True


async def test_producto_completo(session):
    """Prueba con producto completo (con alérgenos Y opciones)."""
    print_separator("PRUEBA 3: Producto Completo (con alérgenos Y opciones)")

    producto_service = ProductoService(session)
    alergeno_service = ProductoAlergenoService(session)

    # Buscar un producto completo
    print("\n1. Buscando producto completo...")
    productos_list = await producto_service.get_productos(skip=0, limit=50)

    producto_completo = None
    alergenos_count = 0
    opciones_count = 0

    for prod in productos_list.items:
        alergenos = await alergeno_service.get_alergenos_by_producto(prod.id)

        try:
            prod_completo = await producto_service.get_producto_con_opciones(prod.id)
            opciones = sum(len(tipo.opciones) for tipo in prod_completo.tipos_opciones)
        except:
            opciones = 0

        if len(alergenos) > 0 and opciones > 0:
            producto_completo = prod
            alergenos_count = len(alergenos)
            opciones_count = opciones
            break

    if not producto_completo:
        print("[X] No se encontro producto completo. Saltando prueba 3.")
        return False

    print(f"[OK] Producto completo encontrado: {producto_completo.nombre}")

    # Guardar estado original
    print("\n2. Guardando estado original...")
    estado_original = await backup_producto_state(producto_service, alergeno_service, producto_completo.id)
    print_producto_info(producto_completo, alergenos_count, opciones_count)

    # Modificar producto
    print("\n3. Modificando producto (eliminando algunos alérgenos y opciones)...")

    # Reducir alérgenos a la mitad
    alergenos_modificados = []
    alergenos_originales = estado_original['alergenos']
    for alergeno in alergenos_originales[:len(alergenos_originales)//2 or 1]:
        alergenos_modificados.append(
            ProductoAlergenoUpdateInput(
                id_alergeno=alergeno.id,
                nivel_presencia=NivelPresencia.PUEDE_CONTENER,  # Cambiar nivel
                notas="MODIFICADO - PRUEBA 3"
            )
        )

    update_data = ProductoCompletoUpdateSchema(
        nombre=f"{estado_original['nombre']} [COMPLETO-MOD]",
        descripcion="PRUEBA 3: Producto completo modificado",
        precio_base=Decimal("555.55"),
        imagen_path=estado_original['imagen_path'],
        imagen_alt_text=estado_original['imagen_alt_text'],
        id_categoria=estado_original['id_categoria'],
        disponible=True,
        destacado=True,
        alergenos=alergenos_modificados,
        secciones=[],
        tipos_opciones=[]  # Vaciar opciones temporalmente
    )

    producto_modificado = await producto_service.update_producto_completo(
        producto_completo.id,
        update_data
    )

    alergenos_mod = await alergeno_service.get_alergenos_by_producto(producto_completo.id)
    print("[OK] Producto modificado:")
    print_producto_info(producto_modificado, len(alergenos_mod), 0)

    # Verificar cambios
    print("\n4. Verificando cambios...")
    assert producto_modificado.precio_base == Decimal("555.55"), "Precio no se modificó"
    assert len(alergenos_mod) <= len(alergenos_originales), "Alérgenos no se redujeron"
    print(f"[OK] Alérgenos reducidos de {len(alergenos_originales)} a {len(alergenos_mod)}")
    print("[OK] Opciones eliminadas temporalmente")

    # Restaurar estado original
    print("\n5. Restaurando estado original completo...")

    # Restaurar alérgenos
    alergenos_restaurar = []
    for alergeno in estado_original['alergenos']:
        alergenos_restaurar.append(
            ProductoAlergenoUpdateInput(
                id_alergeno=alergeno.id,
                nivel_presencia=NivelPresencia.CONTIENE,
                notas=""
            )
        )

    # Restaurar opciones con sus IDs originales
    restore_data = ProductoCompletoUpdateSchema(
        nombre=estado_original['nombre'],
        descripcion=estado_original['descripcion'],
        precio_base=estado_original['precio_base'],
        imagen_path=estado_original['imagen_path'],
        imagen_alt_text=estado_original['imagen_alt_text'],
        id_categoria=estado_original['id_categoria'],
        disponible=estado_original['disponible'],
        destacado=estado_original['destacado'],
        alergenos=alergenos_restaurar,
        secciones=[],
        tipos_opciones=estado_original['tipos_opciones']  # Restaurar opciones!
    )

    producto_restaurado = await producto_service.update_producto_completo(
        producto_completo.id,
        restore_data
    )

    alergenos_rest = await alergeno_service.get_alergenos_by_producto(producto_completo.id)

    # Verificar opciones restauradas
    try:
        producto_verificado = await producto_service.get_producto_con_opciones(producto_completo.id)
        opciones_restauradas = sum(len(tipo.opciones) for tipo in producto_verificado.tipos_opciones)
    except:
        opciones_restauradas = 0

    print("[OK] Producto restaurado:")
    print_producto_info(producto_restaurado, len(alergenos_rest), opciones_restauradas)

    print("\n[OK] PRUEBA 3 COMPLETADA EXITOSAMENTE")
    return True


async def test_agregar_y_eliminar(session):
    """Prueba AGREGAR alérgenos/opciones y luego ELIMINARLOS."""
    print_separator("PRUEBA 4: Agregar elementos nuevos y luego eliminarlos")

    producto_service = ProductoService(session)
    alergeno_service = ProductoAlergenoService(session)

    # Buscar un producto simple
    print("\n1. Buscando producto simple para agregar elementos...")
    productos_list = await producto_service.get_productos(skip=0, limit=50)

    producto_simple = None
    for prod in productos_list.items:
        alergenos = await alergeno_service.get_alergenos_by_producto(prod.id)
        try:
            prod_completo = await producto_service.get_producto_con_opciones(prod.id)
            tiene_opciones = len(prod_completo.tipos_opciones) > 0
        except:
            tiene_opciones = False

        if len(alergenos) == 0 and not tiene_opciones:
            producto_simple = prod
            break

    if not producto_simple:
        print("[X] No se encontro producto simple. Saltando prueba 4.")
        return False

    print(f"[OK] Producto simple encontrado: {producto_simple.nombre}")

    # Guardar estado original (vacío)
    print("\n2. Guardando estado original (sin alérgenos ni opciones)...")
    estado_original = await backup_producto_state(producto_service, alergeno_service, producto_simple.id)
    print_producto_info(producto_simple, 0, 0)

    # AGREGAR alérgenos y opciones NUEVOS
    print("\n3. AGREGANDO alérgenos y opciones nuevos...")

    # Obtener algunos alérgenos disponibles
    from src.repositories.menu.alergeno_repository import AlergenoRepository
    alergeno_repo = AlergenoRepository(session)
    alergenos_disponibles, _ = await alergeno_repo.get_all(skip=0, limit=2)

    # Obtener tipos de opciones disponibles
    from src.repositories.pedidos.tipo_opciones_repository import TipoOpcionRepository
    tipo_opciones_repo = TipoOpcionRepository(session)
    tipos_disponibles, _ = await tipo_opciones_repo.get_all(skip=0, limit=1)

    if not alergenos_disponibles or not tipos_disponibles:
        print("[X] No hay alérgenos o tipos de opciones disponibles")
        return False

    # Preparar datos para AGREGAR
    alergenos_nuevos = [
        ProductoAlergenoUpdateInput(
            id_alergeno=alergenos_disponibles[0].id,
            nivel_presencia=NivelPresencia.CONTIENE,
            notas="AGREGADO EN PRUEBA 4"
        )
    ]

    from src.api.schemas.producto_schema import TipoOpcionCompletoSchema, ProductoOpcionCompletoSchema

    opciones_nuevas = [
        TipoOpcionCompletoSchema(
            id_tipo_opcion=tipos_disponibles[0].id,
            nombre=tipos_disponibles[0].nombre,
            descripcion=tipos_disponibles[0].descripcion,
            seleccion_minima=1,
            seleccion_maxima=1,
            orden=0,
            opciones=[
                ProductoOpcionCompletoSchema(
                    id_opcion=None,  # None = crear nueva
                    nombre="Opcion Test 1",
                    precio_adicional=Decimal("5.00"),
                    activo=True,
                    orden=0
                ),
                ProductoOpcionCompletoSchema(
                    id_opcion=None,  # None = crear nueva
                    nombre="Opcion Test 2",
                    precio_adicional=Decimal("10.00"),
                    activo=True,
                    orden=1
                )
            ]
        )
    ]

    update_con_nuevos = ProductoCompletoUpdateSchema(
        nombre=estado_original['nombre'],
        descripcion=estado_original['descripcion'],
        precio_base=estado_original['precio_base'],
        imagen_path=estado_original['imagen_path'],
        imagen_alt_text=estado_original['imagen_alt_text'],
        id_categoria=estado_original['id_categoria'],
        disponible=estado_original['disponible'],
        destacado=estado_original['destacado'],
        alergenos=alergenos_nuevos,
        secciones=[],
        tipos_opciones=opciones_nuevas
    )

    producto_con_nuevos = await producto_service.update_producto_completo(
        producto_simple.id,
        update_con_nuevos
    )

    # Verificar que se agregaron
    alergenos_agregados = await alergeno_service.get_alergenos_by_producto(producto_simple.id)
    producto_con_opciones = await producto_service.get_producto_con_opciones(producto_simple.id)
    opciones_agregadas = sum(len(tipo.opciones) for tipo in producto_con_opciones.tipos_opciones)

    print("[OK] Elementos AGREGADOS:")
    print_producto_info(producto_con_nuevos, len(alergenos_agregados), opciones_agregadas)

    # Verificar
    print("\n4. Verificando elementos agregados...")
    assert len(alergenos_agregados) == 1, "No se agrego el alergeno"
    assert opciones_agregadas == 2, "No se agregaron las opciones"
    print("[OK] Elementos agregados correctamente")

    # ELIMINAR todo (volver al estado original vacío)
    print("\n5. ELIMINANDO todos los elementos agregados...")

    # Para eliminar opciones, necesitamos enviar los tipos con opciones=[]
    from src.api.schemas.producto_schema import TipoOpcionCompletoSchema
    tipos_vacios = [
        TipoOpcionCompletoSchema(
            id_tipo_opcion=tipo.id_tipo_opcion,
            nombre=tipo.nombre_tipo,
            descripcion=tipo.descripcion_tipo,
            seleccion_minima=tipo.seleccion_minima,
            seleccion_maxima=tipo.seleccion_maxima,
            orden=tipo.orden_tipo,
            opciones=[]  # Vacío = eliminar todas las opciones de este tipo
        )
        for tipo in producto_con_opciones.tipos_opciones
    ]

    restore_vacio = ProductoCompletoUpdateSchema(
        nombre=estado_original['nombre'],
        descripcion=estado_original['descripcion'],
        precio_base=estado_original['precio_base'],
        imagen_path=estado_original['imagen_path'],
        imagen_alt_text=estado_original['imagen_alt_text'],
        id_categoria=estado_original['id_categoria'],
        disponible=estado_original['disponible'],
        destacado=estado_original['destacado'],
        alergenos=[],  # Vacío = eliminar todos
        secciones=[],
        tipos_opciones=tipos_vacios  # Tipos con opciones=[] para desactivarlas
    )

    producto_limpio = await producto_service.update_producto_completo(
        producto_simple.id,
        restore_vacio
    )

    # Verificar que se eliminaron (desactivaron)
    alergenos_final = await alergeno_service.get_alergenos_by_producto(producto_simple.id)
    try:
        producto_final = await producto_service.get_producto_con_opciones(producto_simple.id)

        # Contar solo opciones ACTIVAS
        opciones_activas = sum(
            1 for tipo in producto_final.tipos_opciones
            for opcion in tipo.opciones
            if opcion.activo
        )

        # Total de opciones (activas + inactivas)
        opciones_total = sum(len(tipo.opciones) for tipo in producto_final.tipos_opciones)

        print(f"\n[DEBUG] Opciones totales: {opciones_total}, Activas: {opciones_activas}")
    except Exception as e:
        print(f"[DEBUG] Error al obtener opciones: {e}")
        opciones_activas = 0

    print("[OK] Producto restaurado a estado original (vacio):")
    print_producto_info(producto_limpio, len(alergenos_final), opciones_activas)

    # Verificar que volvió al estado original (opciones desactivadas = soft delete)
    print("\n6. Verificando estado final...")
    assert len(alergenos_final) == 0, "Alergenos no se eliminaron"
    assert opciones_activas == 0, "Opciones activas no se eliminaron (soft delete)"
    print("[OK] Todos los elementos eliminados correctamente (soft delete)")

    print("\n[OK] PRUEBA 4 COMPLETADA EXITOSAMENTE")
    return True


async def main():
    """Función principal que ejecuta todas las pruebas."""
    print_separator("INICIO DE PRUEBAS - UPDATE PRODUCTO COMPLETO")

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
            resultados["prueba_1"] = await test_producto_simple(session)
        except Exception as e:
            print(f"\n[X] ERROR EN PRUEBA 1: {e}")
            import traceback
            traceback.print_exc()

        try:
            resultados["prueba_2"] = await test_producto_parcial(session)
        except Exception as e:
            print(f"\n[X] ERROR EN PRUEBA 2: {e}")
            import traceback
            traceback.print_exc()

        try:
            resultados["prueba_3"] = await test_producto_completo(session)
        except Exception as e:
            print(f"\n[X] ERROR EN PRUEBA 3: {e}")
            import traceback
            traceback.print_exc()

        try:
            resultados["prueba_4"] = await test_agregar_y_eliminar(session)
        except Exception as e:
            print(f"\n[X] ERROR EN PRUEBA 4: {e}")
            import traceback
            traceback.print_exc()

    await engine.dispose()

    # Resumen final
    print_separator("RESUMEN DE PRUEBAS")
    print(f"\n  Prueba 1 (Simple):         {'[OK] PASO' if resultados['prueba_1'] else '[X] FALLO'}")
    print(f"  Prueba 2 (Parcial):        {'[OK] PASO' if resultados['prueba_2'] else '[X] FALLO'}")
    print(f"  Prueba 3 (Completo):       {'[OK] PASO' if resultados['prueba_3'] else '[X] FALLO'}")
    print(f"  Prueba 4 (Agregar/Elim):   {'[OK] PASO' if resultados['prueba_4'] else '[X] FALLO'}")

    total_exitosas = sum(resultados.values())
    print(f"\n  Total: {total_exitosas}/4 pruebas exitosas")

    if total_exitosas == 4:
        print("\n[SUCCESS] TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
    else:
        print(f"\n[WARNING] {4 - total_exitosas} prueba(s) no se ejecutaron o fallaron")

    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
