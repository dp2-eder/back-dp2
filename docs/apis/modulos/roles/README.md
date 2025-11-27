# Módulo: Roles

[⬅ Volver al Índice](../../README.md)

## Descripción

Gestión completa de roles de usuario en el sistema. Permite crear, listar, consultar, actualizar y eliminar roles.

## Recurso Base

```
/api/v1/roles
```

## Endpoints Disponibles

### Crear Rol
- **[POST /roles](endpoints/POST_roles.md)** — Crea un nuevo rol en el sistema

### Listar Roles
- **[GET /roles](endpoints/GET_roles.md)** — Obtiene una lista paginada de roles

### Consultar Rol Individual
- **[GET /roles/{rol_id}](endpoints/GET_roles_rol_id.md)** — Obtiene los detalles de un rol específico

### Actualizar Rol
- **[PUT /roles/{rol_id}](endpoints/PUT_roles_rol_id.md)** — Actualiza los datos de un rol existente

### Eliminar Rol
- **[DELETE /roles/{rol_id}](endpoints/DELETE_roles_rol_id.md)** — Elimina un rol del sistema

### Obtener Nombre del Rol de un Usuario
- **[GET /roles/usuario/{usuario_id}/nombre](endpoints/GET_roles_usuario_usuario_id_nombre.md)** — Obtiene únicamente el nombre del rol asignado a un usuario específico

## Schema Principal

**RolResponse:**
```json
{
  "id": "01K7ZCT8PNJA2J8EB83NHA1MK4",
  "nombre": "Administrador",
  "created_at": "2024-10-23T05:16:30.123456Z",
  "updated_at": "2024-10-23T05:16:30.123456Z"
}
```

## Reglas de Negocio

- ✅ El **nombre** del rol es **único** en el sistema
- ✅ Los roles no se eliminan físicamente (soft delete planificado)
- ✅ El nombre del rol debe tener entre 3 y 50 caracteres
- ⚠️ Actualmente no requiere autenticación

## Errores Comunes

| HTTP | Code | Descripción |
|------|------|-------------|
| 400 | `VALIDATION_ERROR` | Datos de entrada inválidos |
| 404 | `NOT_FOUND` | Rol no encontrado |
| 409 | `CONFLICT` | Rol con nombre duplicado |
| 500 | `INTERNAL_ERROR` | Error interno del servidor |
