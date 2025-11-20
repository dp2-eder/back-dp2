"""
Servicio para gestionar las opciones de productos (secciones y complementos).
"""

from typing import List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.repositories.menu.producto_repository import ProductoRepository
from src.repositories.pedidos.tipo_opciones_repository import TipoOpcionRepository
from src.repositories.pedidos.producto_opcion_repository import ProductoOpcionRepository
from src.models.pedidos.tipo_opciones_model import TipoOpcionModel
from src.models.pedidos.producto_opcion_model import ProductoOpcionModel
from src.api.schemas.producto_opciones_manage_schema import (
    AgregarOpcionesProductoRequest,
    AgregarOpcionesProductoResponse,
    OpcionesProductoListResponse,
    SeccionOpcionesResponse,
    OpcionComplementoResponse,
)
from src.business_logic.exceptions.producto_exceptions import ProductoNotFoundError


class ProductoOpcionesManageService:
    """Servicio para gestionar secciones de opciones y complementos de productos."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.producto_repository = ProductoRepository(session)
        self.tipo_opcion_repository = TipoOpcionRepository(session)
        self.producto_opcion_repository = ProductoOpcionRepository(session)

    async def listar_opciones_producto(self, producto_id: str) -> OpcionesProductoListResponse:
        """
        Lista todas las secciones de opciones con sus complementos para un producto.

        Parameters
        ----------
        producto_id : str
            ID del producto.

        Returns
        -------
        OpcionesProductoListResponse
            Lista de secciones con complementos.

        Raises
        ------
        ProductoNotFoundError
            Si el producto no existe.
        """
        # Verificar que el producto existe
        producto = await self.producto_repository.get_by_id(producto_id)
        if not producto:
            raise ProductoNotFoundError(f"Producto con ID '{producto_id}' no encontrado")

        # Obtener todas las opciones del producto (activas e inactivas)
        opciones = await self.producto_opcion_repository.get_by_producto(
            producto_id,
            solo_activos=False
        )

        # Agrupar opciones por tipo de opción
        secciones_dict = {}

        for opcion in opciones:
            tipo_id = opcion.id_tipo_opcion

            # Si no hemos visto este tipo antes, inicializar
            if tipo_id not in secciones_dict:
                tipo_opcion = await self.tipo_opcion_repository.get_by_id(tipo_id)
                if tipo_opcion:
                    secciones_dict[tipo_id] = {
                        'tipo_opcion': tipo_opcion,
                        'complementos': []
                    }

            # Agregar complemento a la sección
            if tipo_id in secciones_dict:
                secciones_dict[tipo_id]['complementos'].append(
                    OpcionComplementoResponse(
                        id=opcion.id,
                        nombre=opcion.nombre,
                        precio_adicional=opcion.precio_adicional,
                        activo=opcion.activo,
                        orden=opcion.orden or 0
                    )
                )

        # Convertir a lista de SeccionOpcionesResponse
        secciones_response = []
        for tipo_id, data in secciones_dict.items():
            tipo_opcion = data['tipo_opcion']
            secciones_response.append(
                SeccionOpcionesResponse(
                    id_tipo_opcion=tipo_opcion.id,
                    nombre=tipo_opcion.nombre,
                    codigo=tipo_opcion.codigo,
                    descripcion=tipo_opcion.descripcion,
                    seleccion_minima=tipo_opcion.seleccion_minima,
                    seleccion_maxima=tipo_opcion.seleccion_maxima,
                    orden=tipo_opcion.orden,
                    activo=tipo_opcion.activo,
                    complementos=sorted(
                        data['complementos'],
                        key=lambda x: x.orden
                    )
                )
            )

        # Ordenar secciones por orden
        secciones_response.sort(key=lambda x: x.orden or 0)

        return OpcionesProductoListResponse(
            id_producto=producto.id,
            nombre_producto=producto.nombre,
            total_secciones=len(secciones_response),
            secciones=secciones_response
        )

    async def agregar_opciones_producto(
        self,
        producto_id: str,
        request: AgregarOpcionesProductoRequest
    ) -> AgregarOpcionesProductoResponse:
        """
        Agrega secciones de opciones con complementos a un producto.

        Parameters
        ----------
        producto_id : str
            ID del producto.
        request : AgregarOpcionesProductoRequest
            Datos de las secciones y complementos a agregar.

        Returns
        -------
        AgregarOpcionesProductoResponse
            Resultado de la operación.

        Raises
        ------
        ProductoNotFoundError
            Si el producto no existe.
        """
        # Verificar que el producto existe
        producto = await self.producto_repository.get_by_id(producto_id)
        if not producto:
            raise ProductoNotFoundError(f"Producto con ID '{producto_id}' no encontrado")

        secciones_creadas = 0
        complementos_creados = 0
        detalles = []

        for seccion_input in request.secciones:
            # 1. Buscar o crear el tipo de opción
            tipo_opcion = await self._buscar_o_crear_tipo_opcion(seccion_input)
            secciones_creadas += 1

            # 2. Crear los complementos (opciones del producto)
            complementos_response = []
            for idx, complemento_input in enumerate(seccion_input.complementos):
                opcion_model = ProductoOpcionModel(
                    id_producto=producto_id,
                    id_tipo_opcion=tipo_opcion.id,
                    nombre=complemento_input.nombre,
                    precio_adicional=complemento_input.precio_adicional,
                    activo=True,
                    orden=complemento_input.orden if complemento_input.orden is not None else idx
                )

                opcion_creada = await self.producto_opcion_repository.create(opcion_model)
                complementos_creados += 1

                complementos_response.append(
                    OpcionComplementoResponse(
                        id=opcion_creada.id,
                        nombre=opcion_creada.nombre,
                        precio_adicional=opcion_creada.precio_adicional,
                        activo=opcion_creada.activo,
                        orden=opcion_creada.orden or 0
                    )
                )

            # 3. Agregar a detalles
            detalles.append(
                SeccionOpcionesResponse(
                    id_tipo_opcion=tipo_opcion.id,
                    nombre=tipo_opcion.nombre,
                    codigo=tipo_opcion.codigo,
                    descripcion=tipo_opcion.descripcion,
                    seleccion_minima=tipo_opcion.seleccion_minima,
                    seleccion_maxima=tipo_opcion.seleccion_maxima,
                    orden=tipo_opcion.orden,
                    activo=tipo_opcion.activo,
                    complementos=complementos_response
                )
            )

        return AgregarOpcionesProductoResponse(
            mensaje=f"Se agregaron {secciones_creadas} sección(es) con {complementos_creados} complemento(s) al producto",
            secciones_creadas=secciones_creadas,
            complementos_creados=complementos_creados,
            detalles=detalles
        )

    async def _buscar_o_crear_tipo_opcion(self, seccion_input) -> TipoOpcionModel:
        """
        Busca un tipo de opción existente por nombre o crea uno nuevo.

        Parameters
        ----------
        seccion_input : SeccionOpcionesInput
            Datos de la sección.

        Returns
        -------
        TipoOpcionModel
            Tipo de opción existente o recién creado.
        """
        # Generar código a partir del nombre (slug)
        codigo = self._generar_codigo_unico(seccion_input.nombre_seccion)

        # Buscar tipo de opción existente por código
        tipo_existente = await self.tipo_opcion_repository.get_by_codigo(codigo)

        if tipo_existente:
            # Si existe, actualizar seleccion_minima y seleccion_maxima si son diferentes
            if (tipo_existente.seleccion_minima != seccion_input.seleccion_minima or
                tipo_existente.seleccion_maxima != seccion_input.seleccion_maxima):
                tipo_actualizado = await self.tipo_opcion_repository.update(
                    tipo_existente.id,
                    seleccion_minima=seccion_input.seleccion_minima,
                    seleccion_maxima=seccion_input.seleccion_maxima,
                    descripcion=seccion_input.descripcion
                )
                return tipo_actualizado if tipo_actualizado else tipo_existente
            return tipo_existente

        # Si no existe, crear nuevo tipo de opción
        nuevo_tipo = TipoOpcionModel(
            codigo=codigo,
            nombre=seccion_input.nombre_seccion,
            descripcion=seccion_input.descripcion,
            activo=True,
            seleccion_minima=seccion_input.seleccion_minima,
            seleccion_maxima=seccion_input.seleccion_maxima,
            orden=0
        )

        return await self.tipo_opcion_repository.create(nuevo_tipo)

    def _generar_codigo_unico(self, nombre: str) -> str:
        """
        Genera un código único a partir del nombre.

        Parameters
        ----------
        nombre : str
            Nombre de la sección.

        Returns
        -------
        str
            Código generado (slug).
        """
        import re
        import unicodedata

        # Normalizar: quitar acentos
        nombre_normalizado = unicodedata.normalize('NFKD', nombre)
        nombre_normalizado = nombre_normalizado.encode('ASCII', 'ignore').decode('ASCII')

        # Convertir a minúsculas y reemplazar espacios por guiones bajos
        codigo = nombre_normalizado.lower()
        codigo = re.sub(r'[^a-z0-9_]+', '_', codigo)
        codigo = re.sub(r'_+', '_', codigo)  # Eliminar guiones duplicados
        codigo = codigo.strip('_')  # Quitar guiones al inicio/final

        # Limitar longitud a 50 caracteres
        return codigo[:50]
