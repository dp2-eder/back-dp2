# Catálogo de APIs — Restaurant Backend

> **Documentación oficial de los endpoints del backend del sistema de restaurante**

## 📋 OpenAPI Specification

**OpenAPI 3.1:** [`/openapi.json`](https://back-dp2.onrender.com/openapi.json) (generado automáticamente por FastAPI)

## 📚 Módulos

### Autenticación

- **[Autenticación](modulos/auth/README.md)** — Sistema de login, registro y gestión de usuarios

### Gestión de Recursos

- **[Roles](modulos/roles/README.md)** — Gestión de roles de usuario
- **[Categorías](modulos/categorias/README.md)** — Gestión de categorías de productos
- **[Alérgenos](modulos/alergenos/README.md)** — Gestión de alérgenos
- **[Productos](modulos/productos/README.md)** — Gestión de productos del menú
- **[Tipos de Opciones](modulos/tipos-opciones/README.md)** — Gestión de tipos de opciones para productos
- **[Producto Opciones](modulos/producto-opciones/README.md)** — Gestión de opciones específicas de productos

### Gestión de Pedidos

- **[Pedidos](modulos/pedidos/README.md)** — ⭐ Gestión completa de pedidos (incluye pedido completo)
- **[Pedidos Productos](modulos/pedidos-productos/README.md)** — Gestión de items dentro de pedidos
- **[Pedidos Opciones](modulos/pedidos-opciones/README.md)** — Gestión de opciones seleccionadas por item

### Operaciones Especiales

- **[Sincronización](modulos/sync/README.md)** — Endpoints de sincronización con sistema externo (Domótica)
- **[Default](modulos/default/README.md)** — Endpoints raíz y health check

## ⚙️ Información Meta

- **[Overview](meta/overview.md)** — Arquitectura general del sistema
- **[Hosts](meta/hosts.md)** — Configuración de hosts por ambiente
- **[Autenticación](meta/auth.md)** — Esquemas de autenticación
- **[Convenciones](meta/conventions.md)** — Convenciones de API (fechas, paginación, errores)

## 🎯 Guía Rápida

### Base Path

Todos los endpoints (excepto `/` y `/health`) usan el prefijo:

```
/api/v1
```

### Hosts por Ambiente

- **Producción:** `https://back-dp2.onrender.com`
- **Local:** `http://127.0.0.1:8000`

### Ejemplo de URL Completa

```
{HOST}/api/v1/{recurso}
```

**Ejemplo:** `https://back-dp2.onrender.com/api/v1/productos?skip=0&limit=20`

## ⭐ Caso de Uso Principal: Crear Pedido Completo

### Endpoint Recomendado

```http
POST /api/v1/pedidos/completo
```

**¿Por qué usar este endpoint?**
- ✅ **Transacción atómica:** Todo o nada
- ✅ **Un solo llamado:** Pedido + items en una sola request
- ✅ **Cálculos automáticos:** Totales y números de pedido
- ✅ **Validación completa:** Mesa, productos, disponibilidad

### Ejemplo Rápido

```bash
curl -X POST "https://back-dp2.onrender.com/api/v1/pedidos/completo" \
  -H "Content-Type: application/json" \
  -d '{
    "id_mesa": "01J9MESA123ABCDEFGHIJKLMN",
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
        "notas_personalizacion": "Sin cebolla, ají picante"
      }
    ],
    "notas_cliente": "Mesa para evento"
  }'
```

**Respuesta:** Pedido completo creado con estado `PENDIENTE` y todos los cálculos automáticos.

📖 **Documentación completa:** [POST /pedidos/completo](modulos/pedidos/endpoints/POST_pedidos_completo.md)

## ⭐ Endpoints Clave para Productos

### Información Completa de Productos

```http
# 1. Información básica del producto
GET /api/v1/productos/{producto_id}

# 2. Opciones de personalización disponibles  
GET /api/v1/productos/{producto_id}/opciones

# 3. Alérgenos del producto
GET /api/v1/productos/{producto_id}/alergenos
```

**¿Por qué usar estos endpoints?**
- ✅ **Opciones:** Esencial para crear formularios de personalización
- ✅ **Alérgenos:** Crítico para seguridad alimentaria y advertencias
- ✅ **Integración:** Se conectan directamente con el flujo de pedidos

### Ejemplo de Integración Completa

```bash
# Obtener opciones para personalización
curl "https://back-dp2.onrender.com/api/v1/productos/01J9CEVI123.../opciones"

# Obtener alérgenos para advertencias  
curl "https://back-dp2.onrender.com/api/v1/productos/01J9CEVI123.../alergenos"

# Crear pedido con opciones seleccionadas
curl -X POST "https://back-dp2.onrender.com/api/v1/pedidos/completo" \
  -d '{
    "items": [{
      "id_producto": "01J9CEVI123...",
      "opciones": [
        {"id_producto_opcion": "01J9OPC789...", "precio_adicional": 1.00}
      ]
    }]
  }'
```

📖 **Documentación detallada:**
- [GET /productos/{id}/opciones](modulos/productos/endpoints/GET_productos_producto_id_opciones.md)
- [GET /productos/{id}/alergenos](modulos/productos/endpoints/GET_productos_producto_id_alergenos.md)

## 📖 Formato de Documentación

Cada endpoint está documentado con:

- ✅ **META** — Información del endpoint (host, path, método, autenticación)
- ✅ **ENTRADA** — Query params, path params, headers, body
- ✅ **SALIDA** — Respuesta exitosa con ejemplos y diccionarios
- ✅ **ERRORES** — Códigos de error con Problem+JSON
- ✅ **URLs** — URLs completas y comandos cURL para Producción y Local

## 🚀 Navegación Rápida

| Módulo | Recurso Base | Descripción |
|--------|--------------|-------------|
| **Pedidos** | `/pedidos` | ⭐ **CRUD de pedidos + pedido completo** |
| **Pedidos Productos** | `/pedidos-productos` | **Gestión de items dentro de pedidos** |
| **Pedidos Opciones** | `/pedidos-opciones` | **Gestión de opciones por item** |
| Roles | `/roles` | CRUD de roles del sistema |
| Categorías | `/categorias` | CRUD de categorías + vista con productos |
| Alérgenos | `/alergenos` | CRUD de alérgenos |
| Productos | `/productos` | CRUD de productos + vistas especiales (cards, **opciones**, **alérgenos**) |
| Tipos Opciones | `/tipos-opciones` | CRUD de tipos de opciones |
| Producto Opciones | `/producto-opciones` | CRUD de opciones de productos |
| Sincronización | `/sync` | Sincronización con Domótica (platos, mesas, enrich) |
| Default | `/` | Root y health check |
