"""
Servicio de administración para la gestión de sesiones de mesa.

Este servicio proporciona funcionalidades administrativas para:
- Limpiar sesiones activas duplicadas
- Finalizar sesiones expiradas
- Verificar el estado de las sesiones
"""

from typing import Dict, List, Any
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.mesas.sesion_mesa_model import SesionMesaModel
from src.core.enums.sesion_mesa_enums import EstadoSesionMesa
from src.repositories.mesas.sesion_mesa_repository import SesionMesaRepository


class AdminSesionesService:
    """Servicio para administración de sesiones de mesa.

    Attributes
    ----------
    session : AsyncSession
        Sesión asíncrona de SQLAlchemy para realizar operaciones en la base de datos.
    sesion_mesa_repository : SesionMesaRepository
        Repositorio para acceso a datos de sesiones de mesa.
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio con una sesión de base de datos.

        Parameters
        ----------
        session : AsyncSession
            Sesión asíncrona de SQLAlchemy para realizar operaciones en la base de datos.
        """
        self.session = session
        self.sesion_mesa_repository = SesionMesaRepository(session)

    async def get_estado_sesiones(self) -> Dict[str, Any]:
        """
        Obtiene un resumen del estado actual de las sesiones en el sistema.

        Returns
        -------
        Dict[str, Any]
            Diccionario con estadísticas de sesiones:
            - total_activas: Total de sesiones activas
            - mesas_con_duplicados: Lista de mesas con múltiples sesiones activas
            - sesiones_por_mesa: Detalle de sesiones por mesa
        """
        # Contar sesiones activas por mesa
        stmt = (
            select(
                SesionMesaModel.id_mesa,
                func.count(SesionMesaModel.id).label('count')
            )
            .where(SesionMesaModel.estado == EstadoSesionMesa.ACTIVA)
            .group_by(SesionMesaModel.id_mesa)
        )
        
        result = await self.session.execute(stmt)
        mesas_con_sesiones = result.all()
        
        total_activas = sum(row.count for row in mesas_con_sesiones)
        mesas_con_duplicados = [
            {
                "id_mesa": row.id_mesa,
                "sesiones_activas": row.count
            }
            for row in mesas_con_sesiones
            if row.count > 1
        ]
        
        sesiones_por_mesa = [
            {
                "id_mesa": row.id_mesa,
                "sesiones_activas": row.count,
                "tiene_duplicados": row.count > 1
            }
            for row in mesas_con_sesiones
        ]
        
        return {
            "total_sesiones_activas": total_activas,
            "total_mesas": len(mesas_con_sesiones),
            "mesas_con_duplicados": len(mesas_con_duplicados),
            "detalles_duplicados": mesas_con_duplicados,
            "sesiones_por_mesa": sesiones_por_mesa
        }

    async def fix_duplicate_active_sessions(self) -> Dict[str, Any]:
        """
        Corrige sesiones activas duplicadas en la base de datos.

        Para cada mesa con múltiples sesiones activas:
        1. Identifica la sesión más reciente (por fecha_inicio)
        2. Mantiene solo la sesión más reciente como ACTIVA
        3. Finaliza todas las demás sesiones activas de esa mesa

        Returns
        -------
        Dict[str, Any]
            Diccionario con el resultado de la operación:
            - success: bool - Si la operación fue exitosa
            - mesas_procesadas: int - Número de mesas procesadas
            - sesiones_finalizadas: int - Número de sesiones finalizadas
            - sesiones_mantenidas: int - Número de sesiones mantenidas
            - detalles: List - Detalles de cada mesa procesada

        Raises
        ------
        Exception
            Si ocurre un error durante el proceso
        """
        try:
            # 1. Encontrar mesas con múltiples sesiones activas
            stmt = (
                select(
                    SesionMesaModel.id_mesa,
                    func.count(SesionMesaModel.id).label('count')
                )
                .where(SesionMesaModel.estado == EstadoSesionMesa.ACTIVA)
                .group_by(SesionMesaModel.id_mesa)
                .having(func.count(SesionMesaModel.id) > 1)
            )
            
            result = await self.session.execute(stmt)
            mesas_duplicadas = result.all()
            
            if not mesas_duplicadas:
                return {
                    "success": True,
                    "message": "No se encontraron sesiones duplicadas",
                    "mesas_procesadas": 0,
                    "sesiones_finalizadas": 0,
                    "sesiones_mantenidas": 0,
                    "detalles": []
                }
            
            total_finalizadas = 0
            detalles_procesamiento = []
            
            # 2. Para cada mesa con duplicados
            for mesa_row in mesas_duplicadas:
                id_mesa = mesa_row.id_mesa
                count = mesa_row.count
                
                # Obtener todas las sesiones activas de esta mesa ordenadas por fecha
                stmt_sesiones = (
                    select(SesionMesaModel)
                    .where(
                        SesionMesaModel.id_mesa == id_mesa,
                        SesionMesaModel.estado == EstadoSesionMesa.ACTIVA
                    )
                    .order_by(SesionMesaModel.fecha_inicio.desc())
                )
                
                result_sesiones = await self.session.execute(stmt_sesiones)
                sesiones = result_sesiones.scalars().all()
                
                # Mantener solo la primera (más reciente)
                sesion_a_mantener = sesiones[0]
                sesiones_a_finalizar = sesiones[1:]
                
                sesiones_finalizadas_mesa = []
                
                # Finalizar las demás
                for sesion in sesiones_a_finalizar:
                    sesion.estado = EstadoSesionMesa.FINALIZADA
                    sesion.fecha_fin = datetime.now()
                    total_finalizadas += 1
                    
                    sesiones_finalizadas_mesa.append({
                        "id_sesion": sesion.id,
                        "token_sesion": sesion.token_sesion,
                        "fecha_inicio": sesion.fecha_inicio.isoformat()
                    })
                
                detalles_procesamiento.append({
                    "id_mesa": id_mesa,
                    "sesiones_encontradas": count,
                    "sesion_mantenida": {
                        "id_sesion": sesion_a_mantener.id,
                        "token_sesion": sesion_a_mantener.token_sesion,
                        "fecha_inicio": sesion_a_mantener.fecha_inicio.isoformat()
                    },
                    "sesiones_finalizadas": sesiones_finalizadas_mesa
                })
            
            # 3. Commit de los cambios
            await self.session.commit()
            
            return {
                "success": True,
                "message": f"Se corrigieron {len(mesas_duplicadas)} mesas con sesiones duplicadas",
                "mesas_procesadas": len(mesas_duplicadas),
                "sesiones_finalizadas": total_finalizadas,
                "sesiones_mantenidas": len(mesas_duplicadas),
                "detalles": detalles_procesamiento
            }
            
        except Exception as e:
            await self.session.rollback()
            raise Exception(f"Error al corregir sesiones duplicadas: {str(e)}")

    async def finalizar_sesiones_expiradas(self) -> Dict[str, Any]:
        """
        Finaliza todas las sesiones activas que ya han expirado.

        Una sesión está expirada si:
        - Su estado es ACTIVA pero fecha_inicio + duracion_minutos < ahora

        Returns
        -------
        Dict[str, Any]
            Diccionario con el resultado de la operación:
            - success: bool
            - sesiones_finalizadas: int
            - detalles: List con información de cada sesión finalizada
        """
        try:
            # Obtener todas las sesiones activas
            stmt = select(SesionMesaModel).where(
                SesionMesaModel.estado == EstadoSesionMesa.ACTIVA
            )
            
            result = await self.session.execute(stmt)
            sesiones_activas = result.scalars().all()
            
            sesiones_finalizadas = []
            
            for sesion in sesiones_activas:
                if sesion.esta_expirada():
                    sesion.estado = EstadoSesionMesa.FINALIZADA
                    sesion.fecha_fin = datetime.now()
                    
                    sesiones_finalizadas.append({
                        "id_sesion": sesion.id,
                        "id_mesa": sesion.id_mesa,
                        "token_sesion": sesion.token_sesion,
                        "fecha_inicio": sesion.fecha_inicio.isoformat(),
                        "fecha_expiracion": sesion.calcular_fecha_expiracion().isoformat()
                    })
            
            await self.session.commit()
            
            return {
                "success": True,
                "message": f"Se finalizaron {len(sesiones_finalizadas)} sesiones expiradas",
                "sesiones_finalizadas": len(sesiones_finalizadas),
                "detalles": sesiones_finalizadas
            }
            
        except Exception as e:
            await self.session.rollback()
            raise Exception(f"Error al finalizar sesiones expiradas: {str(e)}")
