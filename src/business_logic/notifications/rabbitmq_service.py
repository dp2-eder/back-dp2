"""
Servicio para comunicación con RabbitMQ.

Maneja la conexión y publicación de tareas a RabbitMQ para procesamiento asíncrono.
"""

import json
import logging
from typing import Dict, Any, Optional
import aio_pika
from aio_pika import Message, DeliveryMode, connect_robust
from aio_pika.abc import AbstractRobustConnection, AbstractChannel


from src.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RabbitMQService:
    """
    Servicio para gestión de conexión y publicación de tareas a RabbitMQ.
    
    Este servicio maneja la comunicación con RabbitMQ para enviar tareas
    de procesamiento asíncrono, como notificaciones, reportes, etc.
    
    Attributes
    ----------
    connection : AbstractRobustConnection
        Conexión robusta a RabbitMQ
    channel : AbstractChannel
        Canal de comunicación con RabbitMQ
    exchange_name : str
        Nombre del exchange a utilizar
    """

    def __init__(self):
        """Inicializa el servicio de RabbitMQ."""
        if aio_pika is None:
            raise ImportError(
                "aio_pika no está instalado. Instalar con: pip install aio-pika"
            )
        
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[AbstractChannel] = None
        self.exchange: Optional[Any] = None
        self.exchange_name = settings.rabbitmq_exchange
        self._is_connected = False

    async def connect(self) -> None:
        """
        Establece conexión con RabbitMQ.
        
        Raises
        ------
        ConnectionError
            Si no se puede establecer conexión con RabbitMQ
        """
        if self._is_connected:
            logger.info("Ya existe una conexión activa a RabbitMQ")
            return

        try:
            # Construir URL de conexión
            rabbitmq_url = (
                f"amqp://{settings.rabbitmq_user}:{settings.rabbitmq_password}"
                f"@{settings.rabbitmq_host}:{settings.rabbitmq_port}/{settings.rabbitmq_vhost}"
            )
            
            # Establecer conexión robusta (auto-reconexión)
            self.connection = await connect_robust(rabbitmq_url)
            
            # Crear canal
            self.channel = await self.connection.channel()
            
            # Declarar exchange
            self.exchange = await self.channel.declare_exchange(
                self.exchange_name,
                type="topic",
                durable=True
            )
            
            # Declarar cola
            queue = await self.channel.declare_queue(
                settings.rabbitmq_queue,
                durable=True
            )
            
            # Bind queue to exchange
            await queue.bind(
                self.exchange_name,
                routing_key=settings.rabbitmq_routing_key
            )
            
            self._is_connected = True
            logger.info(
                f"Conexión establecida con RabbitMQ en {settings.rabbitmq_host}:{settings.rabbitmq_port}"
            )
            
        except Exception as e:
            logger.error(f"Error al conectar con RabbitMQ: {str(e)}")
            raise ConnectionError(f"No se pudo conectar a RabbitMQ: {str(e)}")

    async def disconnect(self) -> None:
        """Cierra la conexión con RabbitMQ."""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            self._is_connected = False
            logger.info("Conexión con RabbitMQ cerrada")

    async def publish_task(
        self,
        task_type: str,
        payload: Dict[str, Any],
        routing_key: Optional[str] = None,
        priority: int = 0
    ) -> bool:
        """
        Publica una tarea en RabbitMQ.
        
        Parameters
        ----------
        task_type : str
            Tipo de tarea (ej: "notification", "report", "email")
        payload : Dict[str, Any]
            Datos de la tarea en formato diccionario
        routing_key : Optional[str]
            Routing key específica para esta tarea. Si es None, usa la configurada
        priority : int
            Prioridad de la tarea (0-9, donde 9 es mayor prioridad)
            
        Returns
        -------
        bool
            True si la tarea se publicó correctamente, False en caso contrario
            
        Raises
        ------
        ConnectionError
            Si no hay conexión activa con RabbitMQ
        ValueError
            Si el payload no es serializable a JSON
        """
        if not self._is_connected or not self.channel:
            logger.error("No hay conexión activa con RabbitMQ")
            raise ConnectionError("Debe establecer conexión con RabbitMQ primero")

        try:
            # Construir mensaje con metadata
            message_body = {
                "task_type": task_type,
                "payload": payload,
                "priority": priority
            }
            
            # Serializar a JSON
            message_json = json.dumps(message_body, default=str)
            
            # Crear mensaje de RabbitMQ
            message = Message(
                body=message_json.encode(),
                delivery_mode=DeliveryMode.PERSISTENT,  # Mensaje persistente
                priority=priority,
                content_type="application/json"
            )
            
            # Publicar en el exchange
            if self.exchange:
                await self.exchange.publish(
                    message,
                    routing_key=routing_key or settings.rabbitmq_routing_key
                )
            else:
                # Fallback si por alguna razón no tenemos el exchange objeto
                # aunque connect() debería haberlo creado
                await self.channel.default_exchange.publish(
                    message,
                    routing_key=routing_key or settings.rabbitmq_routing_key
                )
            
            logger.info(
                f"Tarea '{task_type}' publicada exitosamente en RabbitMQ con prioridad {priority}"
            )
            return True
            
        except (TypeError, ValueError) as e:
            logger.error(f"Error al serializar payload: {str(e)}")
            raise ValueError(f"El payload no es válido: {str(e)}")
        except Exception as e:
            logger.error(f"Error al publicar tarea en RabbitMQ: {str(e)}")
            return False

    async def publish_notification(
        self,
        notification_type: str,
        user_id: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publica una notificación para un usuario.
        
        Parameters
        ----------
        notification_type : str
            Tipo de notificación (ej: "order_ready", "payment_confirmed")
        user_id : str
            ID del usuario destinatario
        message : str
            Mensaje de la notificación
        metadata : Optional[Dict[str, Any]]
            Metadata adicional de la notificación
            
        Returns
        -------
        bool
            True si se publicó correctamente
        """
        payload = {
            "notification_type": notification_type,
            "user_id": user_id,
            "message": message,
            "metadata": metadata or {}
        }
        
        return await self.publish_task(
            task_type="notification",
            payload=payload,
            routing_key="task.notification",
            priority=5
        )

    async def publish_order_event(
        self,
        event_type: str,
        order_id: str,
        table_id: str,
        order_data: Dict[str, Any]
    ) -> bool:
        """
        Publica un evento relacionado con un pedido.
        
        Parameters
        ----------
        event_type : str
            Tipo de evento (ej: "order_created", "order_updated", "order_completed")
        order_id : str
            ID del pedido
        table_id : str
            ID de la mesa
        order_data : Dict[str, Any]
            Datos del pedido
            
        Returns
        -------
        bool
            True si se publicó correctamente
        """
        payload = {
            "event_type": event_type,
            "order_id": order_id,
            "table_id": table_id,
            "order_data": order_data
        }
        
        return await self.publish_task(
            task_type="order_event",
            payload=payload,
            routing_key="task.order",
            priority=7
        )

    async def publish_pedido_creado(self, plato_data: Dict[str, Any]) -> bool:
        """
        Publica un evento de pedido creado para el sistema de domótica.
        
        Parameters
        ----------
        plato_data : Dict[str, Any]
            Datos del plato/pedido que espera el consumidor (PlatoInsertRequest)
            
        Returns
        -------
        bool
            True si se publicó correctamente
        """
        return await self.publish_task(
            task_type="pedido_creado",
            payload=plato_data,
            routing_key="task.pedido_creado",
            priority=9
        )

    async def publish_sync_request(self) -> bool:
        """
        Publica una solicitud de sincronización manual.
        
        Returns
        -------
        bool
            True si se publicó correctamente
        """
        return await self.publish_task(
            task_type="sync",
            payload={},
            routing_key="task.sync",
            priority=5
        )

    @property
    def is_connected(self) -> bool:
        """Retorna True si hay una conexión activa con RabbitMQ."""
        flag = self._is_connected and (self.connection and not self.connection.is_closed)
        return flag if flag else False


# Singleton instance
_rabbitmq_instance: Optional[RabbitMQService] = None


async def get_rabbitmq_service() -> RabbitMQService:
    """
    Obtiene o crea la instancia del servicio de RabbitMQ (patrón singleton).
    
    Returns
    -------
    RabbitMQService
        Instancia única del servicio de RabbitMQ
    """
    global _rabbitmq_instance
    if _rabbitmq_instance is None:
        _rabbitmq_instance = RabbitMQService()
        await _rabbitmq_instance.connect()
    return _rabbitmq_instance


async def close_rabbitmq_service() -> None:
    """Cierra la conexión del servicio de RabbitMQ."""
    global _rabbitmq_instance
    if _rabbitmq_instance is not None:
        await _rabbitmq_instance.disconnect()
        _rabbitmq_instance = None
