# POST /pedidos/completo

> **⭐ Crear un pedido completo con items en una sola transacción**

## META

- **Host Producción:** `https://back-dp2.onrender.com`
- **Host Local:** `http://127.0.0.1:8000`
- **Path:** `/api/v1/pedidos/completo`
- **Método:** `POST`
- **Autenticación:** No requerida
- **Content-Type:** `application/json`

## DESCRIPCIÓN

Crea un pedido completo con todos sus items en **una sola transacción atómica**. Si algún item falla la validación, se deshace toda la operación.

**Características:**
- ✅ Transacción atómica (todo o nada)
- ✅ Generación automática de `numero_pedido`
- ✅ Cálculo automático de totales
- ✅ Validación de mesa, productos y disponibilidad
- ✅ Validación de precios y opciones

## ENTRADA

### Headers

| Header | Valor | Requerido |
|--------|-------|-----------|
| `Content-Type` | `application/json` | ✅ |

### Body Schema

```json
{
  "id_mesa": "string (ULID)",
  "items": [
    {
      "id_producto": "string (ULID)",
      "cantidad": "integer (>= 1)",
      "precio_unitario": "number (> 0)",
      "opciones": [
        {
          "id_producto_opcion": "string (ULID)",
          "precio_adicional": "number (>= 0)"
        }
      ],
      "notas_personalizacion": "string | null"
    }
  ],
  "notas_cliente": "string | null",
  "notas_cocina": "string | null"
}
```

### Campos Requeridos

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id_mesa` | `string` | ID ULID de la mesa (debe existir) |
| `items` | `array` | Lista de items del pedido (mín. 1 item) |
| `items[].id_producto` | `string` | ID ULID del producto (debe existir y estar disponible) |
| `items[].cantidad` | `integer` | Cantidad del producto (≥ 1, default: 1) |
| `items[].precio_unitario` | `number` | Precio base del producto (> 0) |

### Campos Opcionales

| Campo | Tipo | Descripción | Default |
|-------|------|-------------|---------|
| `items[].opciones` | `array` | Lista de opciones seleccionadas para este producto | `[]` |
| `items[].opciones[].id_producto_opcion` | `string` | ID ULID de la opción del producto | requerido si hay opciones |
| `items[].opciones[].precio_adicional` | `number` | Precio adicional de la opción al momento del pedido | requerido si hay opciones |
| `items[].notas_personalizacion` | `string` | Notas específicas del item | `null` |
| `notas_cliente` | `string` | Notas del cliente | `null` |
| `notas_cocina` | `string` | Notas para la cocina | `null` |

## SALIDA

### Success Response (201 Created)

```json
{
  "id": "01J9ABCDEFGHIJKLMNOPQRSTUV",
  "numero_pedido": "20251028-M001-001",
  "id_mesa": "01J9ABCDEFGHIJKLMNOPQRSTUV",
  "estado": "PENDIENTE",
  "subtotal": 100.00,
  "impuestos": 0.00,
  "descuentos": 0.00,
  "total": 100.00,
  "notas_cliente": "Mesa para evento",
  "notas_cocina": "Urgente",
  "fecha_confirmado": null,
  "fecha_en_preparacion": null,
  "fecha_listo": null,
  "fecha_entregado": null,
  "fecha_cancelado": null,
  "fecha_creacion": "2025-10-28T22:30:00Z",
  "fecha_modificacion": "2025-10-28T22:30:00Z",
  "creado_por": null,
  "modificado_por": null,
  "items": [
    {
      "id": "01J9ABCDEFGHIJKLMNOPQRSTUV",
      "id_pedido": "01J9ABCDEFGHIJKLMNOPQRSTUV",
      "id_producto": "01J9ABCDEFGHIJKLMNOPQRSTUV",
      "cantidad": 2,
      "precio_unitario": 25.50,
      "precio_opciones": 3.00,
      "subtotal": 57.00,
      "notas_personalizacion": "Sin cebolla",
      "opciones": [
        {
          "id": "01J9OPCI123ABCDEFGHIJKLMN",
          "id_pedido_producto": "01J9ABCDEFGHIJKLMNOPQRSTUV",
          "id_producto_opcion": "01J9OPC123ABCDEFGHIJKLMN",
          "precio_adicional": 1.00,
          "fecha_creacion": "2025-10-28T22:30:00Z",
          "fecha_modificacion": "2025-10-28T22:30:00Z"
        },
        {
          "id": "01J9OPCI456ABCDEFGHIJKLMN",
          "id_pedido_producto": "01J9ABCDEFGHIJKLMNOPQRSTUV",
          "id_producto_opcion": "01J9OPC456ABCDEFGHIJKLMN",
          "precio_adicional": 2.00,
          "fecha_creacion": "2025-10-28T22:30:00Z",
          "fecha_modificacion": "2025-10-28T22:30:00Z"
        }
      ],
      "fecha_creacion": "2025-10-28T22:30:00Z",
      "fecha_modificacion": "2025-10-28T22:30:00Z"
    }
  ]
}
```

### Diccionario de Campos

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | `string` | ID ULID del pedido generado |
| `numero_pedido` | `string` | Número único: `YYYYMMDD-M{mesa_num}-{seq}` |
| `estado` | `string` | Estado inicial: `"PENDIENTE"` |
| `subtotal` | `number` | Suma de subtotales de todos los items |
| `impuestos` | `number` | Impuestos aplicados (default: 0.00) |
| `descuentos` | `number` | Descuentos aplicados (default: 0.00) |
| `total` | `number` | Total final (subtotal + impuestos - descuentos) |
| `fecha_confirmado` | `datetime/null` | Timestamp cuando se confirmó (null al crear) |
| `fecha_en_preparacion` | `datetime/null` | Timestamp cuando entró en preparación (null al crear) |
| `fecha_listo` | `datetime/null` | Timestamp cuando estuvo listo (null al crear) |
| `fecha_entregado` | `datetime/null` | Timestamp cuando se entregó (null al crear) |
| `fecha_cancelado` | `datetime/null` | Timestamp cuando se canceló (null al crear) |
| `fecha_creacion` | `datetime` | Timestamp de creación del pedido |
| `fecha_modificacion` | `datetime` | Timestamp de última modificación |
| `creado_por` | `string/null` | Usuario que creó el pedido (puede ser null) |
| `modificado_por` | `string/null` | Usuario que modificó por última vez (puede ser null) |
| `items[]` | `array` | Lista de items creados con sus IDs generados |
| `items[].precio_opciones` | `number` | Suma de precios de opciones seleccionadas |
| `items[].subtotal` | `number` | `cantidad * (precio_unitario + precio_opciones)` |
| `items[].opciones[]` | `array` | Lista de opciones seleccionadas para este item |
| `items[].opciones[].id_producto_opcion` | `string` | ID de la opción del producto |
| `items[].opciones[].precio_adicional` | `number` | Precio adicional de la opción al momento del pedido |

## ERRORES

### 400 Bad Request - Datos Inválidos

```json
{
  "type": "validation_error",
  "title": "Datos de entrada inválidos",
  "detail": "La mesa con ID '01J123...' no existe",
  "status": 400
}
```

**Casos comunes:**
- Mesa no existe
- Producto no existe
- Producto no disponible
- Cantidad inválida (< 1)
- Precio inválido (≤ 0)
- Lista de items vacía

### 409 Conflict - Conflicto de Integridad

```json
{
  "type": "conflict_error",
  "title": "Conflicto de integridad",
  "detail": "Ya existe un pedido activo para esta mesa",
  "status": 409
}
```

### 500 Internal Server Error

```json
{
  "type": "internal_error",
  "title": "Error interno del servidor",
  "detail": "Error interno del servidor: Database connection failed",
  "status": 500
}
```

## EJEMPLOS

### Ejemplo 1: Pedido Simple (1 item sin opciones)

**Request:**
```bash
curl -X POST "https://back-dp2.onrender.com/api/v1/pedidos/completo" \
  -H "Content-Type: application/json" \
  -d '{
    "id_mesa": "01J9MESA123ABCDEFGHIJKLMN",
    "items": [
      {
        "id_producto": "01J9PROD123ABCDEFGHIJKLMN",
        "cantidad": 1,
        "precio_unitario": 25.50,
        "opciones": [],
        "notas_personalizacion": null
      }
    ],
    "notas_cliente": "Primera vez",
    "notas_cocina": null
  }'
```

**Response (201):**
```json
{
  "id": "01J9PEDI123ABCDEFGHIJKLMN",
  "numero_pedido": "20251028-M003-001",
  "id_mesa": "01J9MESA123ABCDEFGHIJKLMN",
  "estado": "PENDIENTE",
  "subtotal": 25.50,
  "impuestos": 0.00,
  "descuentos": 0.00,
  "total": 25.50,
  "notas_cliente": "Primera vez",
  "notas_cocina": null,
  "fecha_confirmado": null,
  "fecha_en_preparacion": null,
  "fecha_listo": null,
  "fecha_entregado": null,
  "fecha_cancelado": null,
  "fecha_creacion": "2025-10-28T22:35:15Z",
  "fecha_modificacion": "2025-10-28T22:35:15Z",
  "creado_por": null,
  "modificado_por": null,
  "items": [
    {
      "id": "01J9ITEM123ABCDEFGHIJKLMN",
      "id_pedido": "01J9PEDI123ABCDEFGHIJKLMN",
      "id_producto": "01J9PROD123ABCDEFGHIJKLMN",
      "cantidad": 1,
      "precio_unitario": 25.50,
      "precio_opciones": 0.00,
      "subtotal": 25.50,
      "notas_personalizacion": null,
      "opciones": [],
      "fecha_creacion": "2025-10-28T22:35:15Z",
      "fecha_modificacion": "2025-10-28T22:35:15Z"
    }
  ]
}
```

### Ejemplo 2: Pedido Complejo (3 items con opciones)

**Request:**
```bash
curl -X POST "https://back-dp2.onrender.com/api/v1/pedidos/completo" \
  -H "Content-Type: application/json" \
  -d '{
    "id_mesa": "01J9MESA456ABCDEFGHIJKLMN",
    "items": [
      {
        "id_producto": "01J9CEVI123ABCDEFGHIJKLMN",
        "cantidad": 2,
        "precio_unitario": 30.00,
        "opciones": [
          {
            "id_producto_opcion": "01J9AJI123ABCDEFGHIJKLMN",
            "precio_adicional": 1.00
          },
          {
            "id_producto_opcion": "01J9CHO456ABCDEFGHIJKLMN",
            "precio_adicional": 3.00
          }
        ],
        "notas_personalizacion": "Sin cebolla, ají picante, con choclo"
      },
      {
        "id_producto": "01J9ARRO456ABCDEFGHIJKLMN",
        "cantidad": 1,
        "precio_unitario": 22.00,
        "opciones": [
          {
            "id_producto_opcion": "01J9TAM789ABCDEFGHIJKLMN",
            "precio_adicional": 15.00
          }
        ],
        "notas_personalizacion": "Para 2 personas"
      },
      {
        "id_producto": "01J9BEBI789ABCDEFGHIJKLMN",
        "cantidad": 3,
        "precio_unitario": 5.00,
        "opciones": [
          {
            "id_producto_opcion": "01J9TEM123ABCDEFGHIJKLMN",
            "precio_adicional": 1.50
          }
        ],
        "notas_personalizacion": "Heladas"
      }
    ],
    "notas_cliente": "Celebración cumpleaños",
    "notas_cocina": "Servir todo junto por favor"
  }'
```

**Response (201):**
```json
{
  "id": "01J9PEDI456ABCDEFGHIJKLMN",
  "numero_pedido": "20251028-M005-002",
  "id_mesa": "01J9MESA456ABCDEFGHIJKLMN",
  "estado": "PENDIENTE",
  "subtotal": 124.50,
  "impuestos": 0.00,
  "descuentos": 0.00,
  "total": 124.50,
  "notas_cliente": "Celebración cumpleaños",
  "notas_cocina": "Servir todo junto por favor",
  "fecha_confirmado": null,
  "fecha_en_preparacion": null,
  "fecha_listo": null,
  "fecha_entregado": null,
  "fecha_cancelado": null,
  "fecha_creacion": "2025-10-28T22:40:22Z",
  "fecha_modificacion": "2025-10-28T22:40:22Z",
  "creado_por": null,
  "modificado_por": null,
  "items": [
    {
      "id": "01J9ITEM456ABCDEFGHIJKLMN",
      "id_pedido": "01J9PEDI456ABCDEFGHIJKLMN",
      "id_producto": "01J9CEVI123ABCDEFGHIJKLMN",
      "cantidad": 2,
      "precio_unitario": 30.00,
      "precio_opciones": 4.00,
      "subtotal": 68.00,
      "notas_personalizacion": "Sin cebolla, ají picante, con choclo",
      "opciones": [
        {
          "id": "01J9OPC1456ABCDEFGHIJKLMN",
          "id_pedido_producto": "01J9ITEM456ABCDEFGHIJKLMN",
          "id_producto_opcion": "01J9AJI123ABCDEFGHIJKLMN",
          "precio_adicional": 1.00,
          "fecha_creacion": "2025-10-28T22:40:22Z",
          "fecha_modificacion": "2025-10-28T22:40:22Z"
        },
        {
          "id": "01J9OPC2789ABCDEFGHIJKLMN",
          "id_pedido_producto": "01J9ITEM456ABCDEFGHIJKLMN",
          "id_producto_opcion": "01J9CHO456ABCDEFGHIJKLMN",
          "precio_adicional": 3.00,
          "fecha_creacion": "2025-10-28T22:40:22Z",
          "fecha_modificacion": "2025-10-28T22:40:22Z"
        }
      ],
      "fecha_creacion": "2025-10-28T22:40:22Z",
      "fecha_modificacion": "2025-10-28T22:40:22Z"
    },
    {
      "id": "01J9ITEM789ABCDEFGHIJKLMN",
      "id_pedido": "01J9PEDI456ABCDEFGHIJKLMN",
      "id_producto": "01J9ARRO456ABCDEFGHIJKLMN",
      "cantidad": 1,
      "precio_unitario": 22.00,
      "precio_opciones": 15.00,
      "subtotal": 37.00,
      "notas_personalizacion": "Para 2 personas",
      "opciones": [
        {
          "id": "01J9OPC3123ABCDEFGHIJKLMN",
          "id_pedido_producto": "01J9ITEM789ABCDEFGHIJKLMN",
          "id_producto_opcion": "01J9TAM789ABCDEFGHIJKLMN",
          "precio_adicional": 15.00,
          "fecha_creacion": "2025-10-28T22:40:22Z",
          "fecha_modificacion": "2025-10-28T22:40:22Z"
        }
      ],
      "fecha_creacion": "2025-10-28T22:40:22Z",
      "fecha_modificacion": "2025-10-28T22:40:22Z"
    },
    {
      "id": "01J9ITEM123ABCDEFGHIJKLMN",
      "id_pedido": "01J9PEDI456ABCDEFGHIJKLMN",
      "id_producto": "01J9BEBI789ABCDEFGHIJKLMN",
      "cantidad": 3,
      "precio_unitario": 5.00,
      "precio_opciones": 1.50,
      "subtotal": 19.50,
      "notas_personalizacion": "Heladas",
      "opciones": [
        {
          "id": "01J9OPC4456ABCDEFGHIJKLMN",
          "id_pedido_producto": "01J9ITEM123ABCDEFGHIJKLMN",
          "id_producto_opcion": "01J9TEM123ABCDEFGHIJKLMN",
          "precio_adicional": 1.50,
          "fecha_creacion": "2025-10-28T22:40:22Z",
          "fecha_modificacion": "2025-10-28T22:40:22Z"
        }
      ],
      "fecha_creacion": "2025-10-28T22:40:22Z",
      "fecha_modificacion": "2025-10-28T22:40:22Z"
    }
  ]
}
```

### Ejemplo 3: Error - Mesa No Existe

**Request:**
```bash
curl -X POST "https://back-dp2.onrender.com/api/v1/pedidos/completo" \
  -H "Content-Type: application/json" \
  -d '{
    "id_mesa": "01J9INEXISTENTE123456789",
    "items": [
      {
        "id_producto": "01J9PROD123ABCDEFGHIJKLMN",
        "cantidad": 1,
        "precio_unitario": 25.50
      }
    ]
  }'
```

**Response (400):**
```json
{
  "type": "validation_error",
  "title": "Datos de entrada inválidos",
  "detail": "No se encontró la mesa con ID 01J9INEXISTENTE123456789",
  "status": 400
}
```

## CÁLCULOS AUTOMÁTICOS

### Precio de Opciones por Item
```
precio_opciones = suma(precio_adicional para cada opción en el item)
```

### Subtotal por Item
```
subtotal_item = cantidad * (precio_unitario + precio_opciones)
```

### Total del Pedido
```
subtotal_pedido = suma(subtotal_item para cada item)
total_pedido = subtotal_pedido + impuestos - descuentos
```

### Número de Pedido
```
formato: YYYYMMDD-M{mesa_numero}-{secuencia}
ejemplo: 20251028-M003-001
```

### Ejemplo de Cálculo Completo

**Item con opciones:**
- Producto: Ceviche (precio_unitario = $30.00)
- Opciones: Ají picante ($1.00) + Con choclo ($3.00)
- Cantidad: 2

**Cálculo:**
1. `precio_opciones = 1.00 + 3.00 = $4.00`
2. `subtotal_item = 2 * (30.00 + 4.00) = 2 * 34.00 = $68.00`

## URLs COMPLETAS

### Producción
```
POST https://back-dp2.onrender.com/api/v1/pedidos/completo
```

### Local
```
POST http://127.0.0.1:8000/api/v1/pedidos/completo
```

## NOTAS TÉCNICAS

- ⚠️ **Transacción Atómica:** Si cualquier item falla, se revierte todo el pedido
- 🔄 **Generación Automática:** El `numero_pedido` se genera automáticamente
- 📊 **Cálculos:** Todos los subtotales y totales se calculan automáticamente
- ✅ **Validaciones:** Se valida existencia de mesa, productos y disponibilidad
- 🏷️ **Estados:** El pedido siempre se crea en estado `PENDIENTE`
