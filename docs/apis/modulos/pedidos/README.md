# API de Pedidos

> **Gestión completa de pedidos del restaurante**

## Endpoints Base

- **Base Path:** `/api/v1/pedidos`
- **Tags:** `["Pedidos"]`

## Endpoints Disponibles

### CRUD Básico

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/pedidos` | Crear un nuevo pedido |
| `POST` | `/pedidos/completo` | **🌟 Crear pedido completo con items** |
| `GET` | `/pedidos` | Listar pedidos (con filtros) |
| `GET` | `/pedidos/{pedido_id}` | Obtener pedido por ID |
| `GET` | `/pedidos/numero/{numero_pedido}` | Obtener pedido por número |
| `PUT` | `/pedidos/{pedido_id}` | Actualizar pedido |
| `PATCH` | `/pedidos/{pedido_id}/estado` | Cambiar estado del pedido |
| `DELETE` | `/pedidos/{pedido_id}` | Eliminar pedido |

### Endpoints Relacionados

| Módulo | Endpoint | Descripción |
|--------|----------|-------------|
| [Pedidos Productos](../pedidos-productos/README.md) | `/pedidos-productos` | Gestión de items dentro de pedidos |
| [Pedidos Opciones](../pedidos-opciones/README.md) | `/pedidos-opciones` | Gestión de opciones seleccionadas por item |

## Flujo de Pedido Completo

### 1. Crear Pedido Completo ⭐ (Recomendado)

```http
POST /api/v1/pedidos/completo
```

Este endpoint permite crear un pedido completo con todos sus items en **una sola transacción atómica**.

**Ventajas:**
- ✅ Transacción atómica (todo o nada)
- ✅ Cálculo automático de totales
- ✅ Validación completa de productos y disponibilidad
- ✅ Un solo llamado al backend

### 2. Crear Pedido Paso a Paso

```http
# 1. Crear pedido vacío
POST /api/v1/pedidos

# 2. Agregar items uno por uno
POST /api/v1/pedidos-productos

# 3. Agregar opciones por item (opcional)
POST /api/v1/pedidos-opciones
```

## Estados del Pedido

| Estado | Descripción | Transiciones Válidas |
|--------|-------------|---------------------|
| `PENDIENTE` | Pedido recién creado | → `EN_PREPARACION`, `CANCELADO` |
| `EN_PREPARACION` | Cocina preparando | → `LISTO`, `CANCELADO` |
| `LISTO` | Listo para servir | → `ENTREGADO` |
| `ENTREGADO` | Entregado al cliente | → `FINALIZADO` |
| `FINALIZADO` | Pedido completado | (Final) |
| `CANCELADO` | Pedido cancelado | (Final) |

## Filtros Disponibles

### Listar Pedidos (`GET /pedidos`)

- `skip` - Paginación (offset)
- `limit` - Límite de resultados
- `estado` - Filtrar por estado
- `id_mesa` - Filtrar por mesa

### Casos de Uso Comunes

#### 1. Pedidos Pendientes (Dashboard Cocina)
```
GET /api/v1/pedidos?estado=PENDIENTE&limit=50
```

#### 2. Pedidos de una Mesa
```
GET /api/v1/pedidos?id_mesa=01J123456789ABCDEFGHIJKLMN
```

#### 3. Histórico de Pedidos
```
GET /api/v1/pedidos?skip=0&limit=100
```

## Enlaces de Documentación

### Endpoints Principales
- [POST /pedidos/completo](endpoints/POST_pedidos_completo.md) - **⭐ Crear pedido completo**
- [POST /pedidos](endpoints/POST_pedidos.md) - Crear pedido básico
- [GET /pedidos](endpoints/GET_pedidos.md) - Listar pedidos
- [GET /pedidos/{pedido_id}](endpoints/GET_pedidos_pedido_id.md) - Obtener pedido
- [GET /pedidos/numero/{numero_pedido}](endpoints/GET_pedidos_numero_numero_pedido.md) - Obtener por número
- [PUT /pedidos/{pedido_id}](endpoints/PUT_pedidos_pedido_id.md) - Actualizar pedido
- [PATCH /pedidos/{pedido_id}/estado](endpoints/PATCH_pedidos_pedido_id_estado.md) - Cambiar estado
- [DELETE /pedidos/{pedido_id}](endpoints/DELETE_pedidos_pedido_id.md) - Eliminar pedido

### Módulos Relacionados
- [Pedidos Productos](../pedidos-productos/README.md) - Items de pedidos
- [Pedidos Opciones](../pedidos-opciones/README.md) - Opciones por item
- [Productos](../productos/README.md) - Productos del menú
- [Mesas](../mesas/README.md) - Gestión de mesas

## Schemas

Los schemas principales se encuentran en:
- `PedidoCompletoCreate` - Para crear pedido completo
- `PedidoCompletoResponse` - Respuesta de pedido completo
- `PedidoCreate` - Para crear pedido básico
- `PedidoResponse` - Respuesta de pedido
- `PedidoList` - Lista paginada de pedidos
