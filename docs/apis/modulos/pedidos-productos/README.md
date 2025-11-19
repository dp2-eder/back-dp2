# API de Pedidos Productos

> **Gestión de items dentro de pedidos del restaurante**

## Endpoints Base

- **Base Path:** `/api/v1/pedidos-productos`
- **Tags:** `["Pedidos Productos"]`

## Endpoints Disponibles

### CRUD de Items

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/pedidos-productos` | Crear un nuevo item de pedido |
| `GET` | `/pedidos-productos` | Listar items de pedidos (con filtros) |
| `GET` | `/pedidos-productos/{item_id}` | Obtener item por ID |
| `GET` | `/pedidos-productos/pedido/{pedido_id}/items` | Obtener items de un pedido |
| `PUT` | `/pedidos-productos/{item_id}` | Actualizar item |
| `DELETE` | `/pedidos-productos/{item_id}` | Eliminar item |

## Descripción

Los **pedidos-productos** representan los items individuales dentro de un pedido. Cada item contiene:

- ✅ **Producto:** Referencia al producto del menú
- ✅ **Cantidad:** Número de unidades pedidas
- ✅ **Precios:** Precio unitario + precio de opciones
- ✅ **Subtotal:** Cálculo automático
- ✅ **Notas:** Personalizaciones del cliente

## Relaciones

```
Pedido (1) ←→ (N) PedidoProducto ←→ (1) Producto
                       ↓
                 (N) PedidoOpcion ←→ (1) ProductoOpcion
```

## Estructura de Datos

### Item de Pedido

```json
{
  "id": "01J9ITEM123ABCDEFGHIJKLMN",
  "id_pedido": "01J9PEDI123ABCDEFGHIJKLMN",
  "id_producto": "01J9PROD123ABCDEFGHIJKLMN",
  "cantidad": 2,
  "precio_unitario": 25.50,
  "precio_opciones": 3.00,
  "subtotal": 57.00,
  "notas_personalizacion": "Sin cebolla, ají picante",
  "fecha_creacion": "2025-10-28T22:30:00Z",
  "fecha_modificacion": "2025-10-28T22:30:00Z"
}
```

### Cálculo del Subtotal

```
subtotal = cantidad * (precio_unitario + precio_opciones)
```

## Filtros Disponibles

### Listar Items (`GET /pedidos-productos`)

- `skip` - Paginación (offset)
- `limit` - Límite de resultados
- `id_pedido` - Filtrar por pedido específico
- `id_producto` - Filtrar por producto específico

## Casos de Uso

### 1. Agregar Item a Pedido Existente

```http
POST /api/v1/pedidos-productos
```

### 2. Ver Items de un Pedido

```http
GET /api/v1/pedidos-productos/pedido/{pedido_id}/items
```

### 3. Modificar Cantidad de un Item

```http
PUT /api/v1/pedidos-productos/{item_id}
```

### 4. Items de un Producto Específico

```http
GET /api/v1/pedidos-productos?id_producto=01J9PROD123...
```

## Validaciones

- ✅ **Pedido existe:** El pedido debe existir
- ✅ **Producto existe:** El producto debe existir y estar disponible
- ✅ **Cantidad válida:** Mayor a 0
- ✅ **Precios válidos:** Mayor a 0
- ✅ **Recálculo automático:** Subtotal se recalcula en actualizaciones

## Enlaces de Documentación

### Endpoints
- [POST /pedidos-productos](endpoints/POST_pedidos-productos.md) - Crear item
- [GET /pedidos-productos](endpoints/GET_pedidos-productos.md) - Listar items
- [GET /pedidos-productos/{item_id}](endpoints/GET_pedidos-productos_item_id.md) - Obtener item
- [GET /pedidos-productos/pedido/{pedido_id}/items](endpoints/GET_pedidos-productos_pedido_pedido_id_items.md) - Items de pedido
- [PUT /pedidos-productos/{item_id}](endpoints/PUT_pedidos-productos_item_id.md) - Actualizar item
- [DELETE /pedidos-productos/{item_id}](endpoints/DELETE_pedidos-productos_item_id.md) - Eliminar item

### Módulos Relacionados
- [Pedidos](../pedidos/README.md) - Pedidos principales
- [Pedidos Opciones](../pedidos-opciones/README.md) - Opciones por item
- [Productos](../productos/README.md) - Productos del menú
- [Producto Opciones](../producto-opciones/README.md) - Opciones disponibles

## Flujo Recomendado

### Opción A: Pedido Completo (Recomendado)
```http
POST /api/v1/pedidos/completo
```
*Crea pedido + items en una transacción*

### Opción B: Paso a Paso
```http
# 1. Crear pedido
POST /api/v1/pedidos

# 2. Agregar items
POST /api/v1/pedidos-productos
POST /api/v1/pedidos-productos
...

# 3. Agregar opciones (opcional)
POST /api/v1/pedidos-opciones
```

## Schemas

- `PedidoProductoCreate` - Para crear item
- `PedidoProductoResponse` - Respuesta de item
- `PedidoProductoUpdate` - Para actualizar item
- `PedidoProductoList` - Lista paginada de items
