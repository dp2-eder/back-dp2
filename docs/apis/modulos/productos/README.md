# Módulo: Productos

[⬅ Volver al Índice](../../README.md)

## Descripción

Gestión completa de productos del menú. Permite crear, listar, consultar, actualizar y eliminar productos, además de obtener vistas especializadas como productos por categoría (cards) y productos con sus opciones.

## Recurso Base

```
/api/v1/productos
```

## Endpoints Disponibles

### CRUD Estándar
- **[POST /productos](endpoints/POST_productos.md)** — Crea un nuevo producto
- **[GET /productos](endpoints/GET_productos.md)** — Lista productos (paginado, filtrable por categoría)
- **[GET /productos/{producto_id}](endpoints/GET_productos_producto_id.md)** — Obtiene un producto por ID
- **[PUT /productos/{producto_id}](endpoints/PUT_productos_producto_id.md)** — Actualiza un producto
- **[DELETE /productos/{producto_id}](endpoints/DELETE_productos_producto_id.md)** — Elimina un producto

### Vistas Especializadas
- **[GET /productos/cards](endpoints/GET_productos_cards.md)** — Lista **todos** los productos en formato card
- **[GET /productos/categoria/{categoria_id}/cards](endpoints/GET_productos_categoria_categoria_id_cards.md)** — Lista productos **por categoría** en formato card
- **[GET /productos/{producto_id}/opciones](endpoints/GET_productos_producto_id_opciones.md)** — ⭐ Obtiene producto con sus **opciones** agrupadas por tipo
- **[GET /productos/{producto_id}/alergenos](endpoints/GET_productos_producto_id_alergenos.md)** — ⭐ Obtiene **alérgenos** de un producto

### Actualización Masiva
- **[PUT /productos/{producto_id}/completo](endpoints/PUT_productos_producto_id_completo.md)** — 🔥 Actualiza **completamente** un producto con todos sus datos: básicos, alérgenos, secciones y opciones en una sola operación

## Schema Principal

```json
{
  "id": "01K7ZCT8PNJA2J8EB83NHA1MK4",
  "nombre": "Ceviche Clásico",
  "descripcion": "Pescado fresco del día marinado en limón",
  "precio_base": "25.00",
  "imagen_path": "/static/productos/ceviche-clasico.jpg",
  "disponible": true,
  "id_categoria": "01K7ZCT9QRST3K9FC94OIB2NL5",
  "created_at": "2024-10-23T05:16:30.123456Z",
  "updated_at": "2024-10-23T05:16:30.123456Z"
}
```

## Reglas de Negocio

- ✅ El **nombre** del producto es **único** en el sistema
- ✅ Cada producto pertenece a **una categoría**
- ✅ El precio base es obligatorio y debe ser >= 0
- ✅ El campo `disponible` permite marcar productos "fuera de stock"
- ✅ Un producto puede tener múltiples alérgenos y opciones asociadas

## Casos de Uso Relacionados

**HU-C05:** Cliente explorando — Explorar la oferta vigente por categorías  
**HU-C06:** Cliente con objetivo concreto — Encontrar un producto por texto  
**HU-C07:** Cliente que personaliza — Añadir extras disponibles a mi selección  
**HU-C10:** Cliente con restricciones — Ver alérgenos del producto elegido  
**HU-A01:** Admin — Gestionar imágenes de productos  
**HU-A02:** Admin — Mapear producto con ID externo (sincronización)  
**HU-A05:** Admin — Marcar producto "fuera de stock"

## Errores Comunes

| HTTP | Code | Descripción |
|------|------|-------------|
| 400 | `VALIDATION_ERROR` | Datos de entrada inválidos |
| 404 | `NOT_FOUND` | Producto o categoría no encontrados |
| 409 | `CONFLICT` | Producto con nombre duplicado |
| 500 | `INTERNAL_ERROR` | Error interno del servidor |
